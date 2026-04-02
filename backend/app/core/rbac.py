"""
Impact Observatory | مرصد الأثر — RBAC (v4 §10)
5-role permission matrix: viewer, analyst, operator, admin, regulator.
"""

from enum import Enum
from typing import Set


class Role(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    OPERATOR = "operator"
    ADMIN = "admin"
    REGULATOR = "regulator"


class Permission(str, Enum):
    CREATE_SCENARIO = "create_scenario"
    LAUNCH_RUN = "launch_run"
    LAUNCH_RUN_WITH_OVERRIDES = "launch_run_with_overrides"
    READ_FINANCIAL = "read_financial"
    READ_BANKING = "read_banking"
    READ_INSURANCE = "read_insurance"
    READ_FINTECH = "read_fintech"
    READ_DECISION = "read_decision"
    READ_EXPLANATION = "read_explanation"
    READ_BUSINESS_IMPACT = "read_business_impact"
    READ_TIMELINE = "read_timeline"
    READ_REGULATORY_TIMELINE = "read_regulatory_timeline"
    READ_EXECUTIVE_EXPLANATION = "read_executive_explanation"
    OVERRIDE_THRESHOLDS = "override_thresholds"
    FORCE_RERUN = "force_rerun"
    MANAGE_MANIFESTS = "manage_manifests"
    ARCHIVE_SCENARIO = "archive_scenario"
    READ_AUDIT_LOGS = "read_audit_logs"
    GENERATE_COMPLIANCE_REPORT = "generate_compliance_report"


# v4 §10.2 — Permission Matrix (exact)
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.VIEWER: {
        Permission.READ_FINANCIAL,
        Permission.READ_BANKING,
        Permission.READ_INSURANCE,
        Permission.READ_FINTECH,
        Permission.READ_EXPLANATION,
        Permission.READ_BUSINESS_IMPACT,
        Permission.READ_TIMELINE,
        Permission.READ_REGULATORY_TIMELINE,
        Permission.READ_EXECUTIVE_EXPLANATION,
    },
    Role.ANALYST: {
        Permission.CREATE_SCENARIO,
        Permission.LAUNCH_RUN,
        Permission.READ_FINANCIAL,
        Permission.READ_BANKING,
        Permission.READ_INSURANCE,
        Permission.READ_FINTECH,
        Permission.READ_DECISION,
        Permission.READ_EXPLANATION,
        Permission.READ_BUSINESS_IMPACT,
        Permission.READ_TIMELINE,
        Permission.READ_REGULATORY_TIMELINE,
        Permission.READ_EXECUTIVE_EXPLANATION,
    },
    Role.OPERATOR: {
        Permission.CREATE_SCENARIO,
        Permission.LAUNCH_RUN,
        Permission.LAUNCH_RUN_WITH_OVERRIDES,
        Permission.READ_FINANCIAL,
        Permission.READ_BANKING,
        Permission.READ_INSURANCE,
        Permission.READ_FINTECH,
        Permission.READ_DECISION,
        Permission.READ_EXPLANATION,
        Permission.READ_BUSINESS_IMPACT,
        Permission.READ_TIMELINE,
        Permission.READ_REGULATORY_TIMELINE,
        Permission.READ_EXECUTIVE_EXPLANATION,
        Permission.OVERRIDE_THRESHOLDS,
        Permission.FORCE_RERUN,
    },
    Role.ADMIN: {
        Permission.CREATE_SCENARIO,
        Permission.LAUNCH_RUN,
        Permission.LAUNCH_RUN_WITH_OVERRIDES,
        Permission.READ_FINANCIAL,
        Permission.READ_BANKING,
        Permission.READ_INSURANCE,
        Permission.READ_FINTECH,
        Permission.READ_DECISION,
        Permission.READ_EXPLANATION,
        Permission.READ_BUSINESS_IMPACT,
        Permission.READ_TIMELINE,
        Permission.READ_REGULATORY_TIMELINE,
        Permission.READ_EXECUTIVE_EXPLANATION,
        Permission.OVERRIDE_THRESHOLDS,
        Permission.FORCE_RERUN,
        Permission.MANAGE_MANIFESTS,
        Permission.ARCHIVE_SCENARIO,
        Permission.READ_AUDIT_LOGS,
        Permission.GENERATE_COMPLIANCE_REPORT,
    },
    Role.REGULATOR: {
        Permission.CREATE_SCENARIO,
        Permission.LAUNCH_RUN,
        Permission.LAUNCH_RUN_WITH_OVERRIDES,
        Permission.READ_FINANCIAL,
        Permission.READ_BANKING,
        Permission.READ_INSURANCE,
        Permission.READ_FINTECH,
        Permission.READ_DECISION,
        Permission.READ_EXPLANATION,
        Permission.READ_BUSINESS_IMPACT,
        Permission.READ_TIMELINE,
        Permission.READ_REGULATORY_TIMELINE,
        Permission.READ_EXECUTIVE_EXPLANATION,
        Permission.OVERRIDE_THRESHOLDS,
        Permission.READ_AUDIT_LOGS,
        Permission.GENERATE_COMPLIANCE_REPORT,
    },
}


def has_permission(role: Role, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())


def require_permissions(*permissions: Permission):
    """Returns the set of roles that have ALL the specified permissions."""
    allowed = set()
    for role, perms in ROLE_PERMISSIONS.items():
        if all(p in perms for p in permissions):
            allowed.add(role)
    return allowed
