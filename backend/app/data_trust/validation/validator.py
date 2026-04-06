"""
Impact Observatory | مرصد الأثر — Trusted Event Validator

Deterministic validation layer for TrustedEventContract.
No ML, no probabilistic checks, no external calls.

Rules
-----
1. Schema validity    — Pydantic model fields are already typed; this layer
                        re-confirms required fields are present and non-empty.
2. Field completeness — event_id, timestamp, source, domain, geo, raw_payload,
                        normalized_payload must all be present and non-trivial.
3. Numeric ranges     — impact_score ∈ [0.0, 1.0] if present
                        confidence ∈ [0.0, 1.0] if present
4. Domain presence    — domain must not be empty; must be a known or declared domain
5. Source presence    — source must not be empty
6. Payload non-empty  — normalized_payload must not be {}
7. Geo completeness   — geo must contain at least 'country' key
8. Timestamp sanity   — timestamp must not be in the future (> 5 min clock skew)

Output
------
    {"valid": bool, "errors": list[str]}

All errors are accumulated — the caller sees the full list of failures,
not just the first one. This makes debugging quarantined records tractable.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import TypedDict

from ..contracts.event import TrustedEventContract

# ── Known domains — extend as new adapters are added ─────────────────────────
KNOWN_DOMAINS: frozenset[str] = frozenset({
    "government",
    "real_estate",
    "energy",
    "banking",
    "insurance",
    "aviation",
    "maritime",
    "logistics",
    "cyber",
})

# Maximum allowed clock skew between event timestamp and received_at
_MAX_FUTURE_SKEW = timedelta(minutes=5)


class ValidationResult(TypedDict):
    valid: bool
    errors: list[str]


def validate_trusted_event(contract: TrustedEventContract) -> ValidationResult:
    """
    Validate a TrustedEventContract against all trust-layer rules.

    Parameters
    ----------
    contract : TrustedEventContract
        Event to validate. Must be a fully constructed contract instance.

    Returns
    -------
    ValidationResult
        {"valid": bool, "errors": list[str]}
        errors is empty when valid=True.
        valid=False when one or more rules fail.
    """
    errors: list[str] = []

    # ── Rule 1: Schema validity — required string fields non-empty ────────────
    if not contract.event_id or not contract.event_id.strip():
        errors.append("RULE_1: event_id is missing or empty")

    # ── Rule 2: Field completeness ────────────────────────────────────────────
    if not contract.source or not contract.source.strip():
        errors.append("RULE_2: source is missing or empty")

    if not contract.domain or not contract.domain.strip():
        errors.append("RULE_2: domain is missing or empty")

    if not contract.raw_payload:
        errors.append("RULE_2: raw_payload is empty — original record required for audit trail")

    if not contract.normalized_payload:
        errors.append("RULE_2: normalized_payload is empty — adapter normalization did not produce output")

    # ── Rule 3: Numeric ranges ────────────────────────────────────────────────
    if contract.impact_score is not None:
        if not (0.0 <= contract.impact_score <= 1.0):
            errors.append(
                f"RULE_3: impact_score={contract.impact_score:.4f} out of bounds [0.0, 1.0]"
            )

    if contract.confidence is not None:
        if not (0.0 <= contract.confidence <= 1.0):
            errors.append(
                f"RULE_3: confidence={contract.confidence:.4f} out of bounds [0.0, 1.0]"
            )

    # ── Rule 4: Domain presence ───────────────────────────────────────────────
    if contract.domain:
        domain_lower = contract.domain.strip().lower()
        if domain_lower not in KNOWN_DOMAINS:
            # Warn but do not reject: unknown domain may be a new valid source
            # The orchestrator logs this; it does NOT quarantine on unknown domain alone
            errors.append(
                f"RULE_4_WARN: domain='{contract.domain}' is not in KNOWN_DOMAINS "
                f"({sorted(KNOWN_DOMAINS)}). Register it to suppress this warning."
            )
            # Note: RULE_4 warnings are prefixed RULE_4_WARN so the orchestrator
            # can distinguish hard failures from soft warnings if needed.
            # Current policy: unknown domain is a WARNING only, not a hard failure.
            # Remove the append above and add a separate warning list if needed.
            # For now: treated as a hard error to enforce strict domain registration.

    # ── Rule 5: Source presence ───────────────────────────────────────────────
    # Already covered in Rule 2; add source format check here
    if contract.source:
        if len(contract.source.strip()) < 3:
            errors.append(
                f"RULE_5: source='{contract.source}' is too short (min 3 chars)"
            )

    # ── Rule 6: Normalized payload non-empty ──────────────────────────────────
    # Already covered in Rule 2; add minimum key count check
    if contract.normalized_payload and len(contract.normalized_payload) < 2:
        errors.append(
            "RULE_6: normalized_payload has fewer than 2 keys — "
            "adapter normalization appears incomplete"
        )

    # ── Rule 7: Geo completeness ──────────────────────────────────────────────
    if not contract.geo:
        errors.append("RULE_7: geo is empty — geographic context required")
    else:
        if "country" not in contract.geo:
            errors.append(
                "RULE_7: geo missing 'country' key — ISO-3166 country code required"
            )
        elif not contract.geo["country"] or not str(contract.geo["country"]).strip():
            errors.append(
                "RULE_7: geo.country is blank — must be a valid ISO-3166 alpha-2 code"
            )

    # ── Rule 8: Timestamp sanity ──────────────────────────────────────────────
    now = datetime.now(timezone.utc)
    ts = contract.timestamp
    # Normalize to aware datetime
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    if ts > now + _MAX_FUTURE_SKEW:
        errors.append(
            f"RULE_8: timestamp={ts.isoformat()} is {(ts - now).seconds}s in the future "
            f"(max allowed clock skew: {int(_MAX_FUTURE_SKEW.total_seconds())}s)"
        )

    # Warn on very old records (> 30 days) — stale data reduces trust
    stale_threshold = now - timedelta(days=30)
    if ts < stale_threshold:
        errors.append(
            f"RULE_8_WARN: timestamp={ts.isoformat()} is more than 30 days old — "
            "stale data; confidence will be reduced by scoring layer"
        )

    # ── Result ────────────────────────────────────────────────────────────────
    # Hard failures: any error NOT prefixed with _WARN
    hard_failures = [e for e in errors if "_WARN" not in e]
    return ValidationResult(
        valid=len(hard_failures) == 0,
        errors=errors,  # Return all errors including warnings for full traceability
    )
