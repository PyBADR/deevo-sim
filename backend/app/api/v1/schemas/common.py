"""
Impact Observatory | مرصد الأثر — Common API schemas (v4 §4.1)
Standard success envelope and warning object.
"""

from pydantic import BaseModel, Field
from typing import Any, List, Optional
from datetime import datetime, timezone
import uuid


class Warning(BaseModel):
    """v4 §15 — Canonical warning object."""
    code: str = Field(..., description="Uppercase snake case warning code")
    message: str = Field(..., min_length=1, max_length=500)
    stage: str = Field(..., description="Pipeline stage that generated the warning")

    model_config = {"extra": "ignore"}


class SuccessEnvelope(BaseModel):
    """v4 §4.1 — Standard success response envelope."""
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    data: Any = Field(...)
    warnings: List[Warning] = Field(default_factory=list)

    model_config = {"extra": "ignore"}


def success_response(data: Any, warnings: Optional[List[Warning]] = None) -> dict:
    """Create a v4 standard success envelope."""
    return SuccessEnvelope(
        data=data,
        warnings=warnings or [],
    ).model_dump()
