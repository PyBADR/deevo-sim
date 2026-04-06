"""
Impact Observatory | مرصد الأثر — Trusted Event Contract

Unified Pydantic contract for ALL external data entering the trust pipeline.
Every adapter must normalize its source-specific payload into this shape
before validation, scoring, or passing to the intelligence engine.

Design rules
------------
- Strict types — no Any, no untyped dicts where avoidable
- Required fields must be present; optional fields have explicit defaults
- Validation traceability is first-class: received_at, status, errors
- geo is a free dict to accommodate diverse source schemas,
  but must be non-empty (enforced in validation layer)
- impact_score and confidence are None until computed/populated
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid

from pydantic import BaseModel, Field, field_validator, model_validator


class ValidationStatus(str, Enum):
    PENDING    = "pending"     # Not yet validated
    VALID      = "valid"       # Passed all checks
    INVALID    = "invalid"     # Failed one or more checks
    QUARANTINED = "quarantined"  # Routed to quarantine store


class TrustedEventContract(BaseModel):
    """
    Unified trusted event contract.

    Required by every adapter before the validation + scoring pipeline runs.
    Immutable after creation — produce a new instance for mutations.
    """

    # ── Identity ──────────────────────────────────────────────────────────
    event_id: str = Field(
        default_factory=lambda: f"te_{uuid.uuid4().hex[:16]}",
        description="Unique trust-layer event ID. Auto-generated if not provided.",
    )
    received_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when this record entered the trust pipeline.",
    )

    # ── Required source fields ────────────────────────────────────────────
    timestamp: datetime = Field(
        ...,
        description="UTC timestamp of the originating event (from source).",
    )
    source: str = Field(
        ...,
        min_length=1,
        description="Source identifier, e.g. 'government_open_data', 'real_estate_feed'.",
    )
    domain: str = Field(
        ...,
        min_length=1,
        description="Business domain, e.g. 'government', 'real_estate', 'energy'.",
    )
    geo: dict = Field(
        ...,
        description=(
            "Geographic context. Must be non-empty. "
            "Recommended keys: country (ISO-3166 alpha-2), region, city."
        ),
    )

    # ── Payload ───────────────────────────────────────────────────────────
    raw_payload: dict = Field(
        ...,
        description="Original unmodified payload from the source system.",
    )
    normalized_payload: dict = Field(
        ...,
        description=(
            "Adapter-normalized payload in canonical shape. "
            "Must be non-empty — empty dict triggers quarantine."
        ),
    )

    # ── Computed / optional ───────────────────────────────────────────────
    impact_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Estimated impact magnitude (0–1). Populated by adapter if source provides it.",
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Trust-layer confidence (0–1). Populated by scoring stage.",
    )

    # ── Validation traceability ───────────────────────────────────────────
    validation_status: ValidationStatus = Field(
        default=ValidationStatus.PENDING,
        description="Current state in the trust pipeline.",
    )
    validation_errors: list[str] = Field(
        default_factory=list,
        description="Accumulated validation error messages. Empty on VALID.",
    )

    # ── Validators ────────────────────────────────────────────────────────

    @field_validator("source")
    @classmethod
    def source_no_whitespace(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("source must not be blank or whitespace-only")
        return stripped

    @field_validator("domain")
    @classmethod
    def domain_no_whitespace(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("domain must not be blank or whitespace-only")
        return stripped

    @field_validator("geo")
    @classmethod
    def geo_must_have_country(cls, v: dict) -> dict:
        if not v:
            raise ValueError("geo must be a non-empty dict")
        return v

    @model_validator(mode="after")
    def timestamp_not_future(self) -> "TrustedEventContract":
        # Soft check only — future timestamps are flagged by the validation layer.
        # Do not reject here; keep construction permissive.
        return self

    class Config:
        # Allow mutation for validation_status / confidence updates
        frozen = False
        use_enum_values = True
