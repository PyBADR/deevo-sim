"""Enforcement Audit Integration — hash-chain compatible audit helpers.

All enforcement actions are logged through the existing governance audit chain.
This module extends VALID_AUDIT_EVENT_TYPES and VALID_AUDIT_SUBJECT_TYPES
at import time so that enforcement audit entries are recognized.

Seven convenience factories for enforcement-specific audit events.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from src.data_foundation.governance.governance_audit import (
    create_audit_entry,
)
from src.data_foundation.governance.schemas import (
    GovernanceAuditEntry,
    VALID_AUDIT_EVENT_TYPES,
    VALID_AUDIT_SUBJECT_TYPES,
)

__all__ = [
    "audit_enforcement_policy_created",
    "audit_enforcement_policy_updated",
    "audit_enforcement_evaluated",
    "audit_decision_blocked",
    "audit_approval_required",
    "audit_fallback_applied",
    "audit_shadow_mode_activated",
    "ENFORCEMENT_AUDIT_EVENT_TYPES",
    "ENFORCEMENT_AUDIT_SUBJECT_TYPES",
]

# Extend the governance audit type sets with enforcement-specific types
ENFORCEMENT_AUDIT_EVENT_TYPES = {
    "ENFORCEMENT_POLICY_CREATED",
    "ENFORCEMENT_POLICY_UPDATED",
    "ENFORCEMENT_EVALUATED",
    "DECISION_BLOCKED",
    "APPROVAL_REQUIRED",
    "FALLBACK_APPLIED",
    "SHADOW_MODE_ACTIVATED",
}

ENFORCEMENT_AUDIT_SUBJECT_TYPES = {
    "ENFORCEMENT_POLICY",
    "ENFORCEMENT_DECISION",
}

# Register enforcement types with governance audit system
VALID_AUDIT_EVENT_TYPES.update(ENFORCEMENT_AUDIT_EVENT_TYPES)
VALID_AUDIT_SUBJECT_TYPES.update(ENFORCEMENT_AUDIT_SUBJECT_TYPES)


# ═══════════════════════════════════════════════════════════════════════════════
# Convenience Factories
# ═══════════════════════════════════════════════════════════════════════════════

def audit_enforcement_policy_created(
    policy_id: str, actor: str, detail: Dict[str, Any] | None = None,
    *, previous_hash: str | None = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        "ENFORCEMENT_POLICY_CREATED", "ENFORCEMENT_POLICY", policy_id,
        actor, detail, previous_audit_hash=previous_hash,
    )


def audit_enforcement_policy_updated(
    policy_id: str, actor: str, detail: Dict[str, Any] | None = None,
    *, previous_hash: str | None = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        "ENFORCEMENT_POLICY_UPDATED", "ENFORCEMENT_POLICY", policy_id,
        actor, detail, previous_audit_hash=previous_hash,
    )


def audit_enforcement_evaluated(
    enforcement_id: str, actor: str, detail: Dict[str, Any] | None = None,
    *, previous_hash: str | None = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        "ENFORCEMENT_EVALUATED", "ENFORCEMENT_DECISION", enforcement_id,
        actor, detail, previous_audit_hash=previous_hash,
    )


def audit_decision_blocked(
    enforcement_id: str, actor: str, detail: Dict[str, Any] | None = None,
    *, previous_hash: str | None = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        "DECISION_BLOCKED", "ENFORCEMENT_DECISION", enforcement_id,
        actor, detail, previous_audit_hash=previous_hash,
    )


def audit_approval_required(
    enforcement_id: str, actor: str, detail: Dict[str, Any] | None = None,
    *, previous_hash: str | None = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        "APPROVAL_REQUIRED", "ENFORCEMENT_DECISION", enforcement_id,
        actor, detail, previous_audit_hash=previous_hash,
    )


def audit_fallback_applied(
    enforcement_id: str, actor: str, detail: Dict[str, Any] | None = None,
    *, previous_hash: str | None = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        "FALLBACK_APPLIED", "ENFORCEMENT_DECISION", enforcement_id,
        actor, detail, previous_audit_hash=previous_hash,
    )


def audit_shadow_mode_activated(
    enforcement_id: str, actor: str, detail: Dict[str, Any] | None = None,
    *, previous_hash: str | None = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        "SHADOW_MODE_ACTIVATED", "ENFORCEMENT_DECISION", enforcement_id,
        actor, detail, previous_audit_hash=previous_hash,
    )
