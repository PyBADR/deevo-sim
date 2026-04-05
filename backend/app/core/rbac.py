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
    # Operator Layer — decision management
    CREATE_DECISION  = "create_decision"   # create an OperatorDecision record (ANALYST+)
    EXECUTE_DECISION = "execute_decision"  # execute a decision / trigger action (OPERATOR+)
    # Outcome Intelligence Layer
    READ_OUTCOME     = "read_outcome"      # read outcomes (ANALYST+)
    RECORD_OUTCOME   = "record_outcome"    # create/transition outcomes (OPERATOR+)
    # ROI / Decision Value Layer
    READ_VALUE       = "read_value"        # read computed decision values (ANALYST+)
    COMPUTE_VALUE    = "compute_value"     # compute/recompute decision values (OPERATOR+)
    # Intelligence Adapter Layer
    INGEST_INTELLIGENCE = "ingest_intelligence"  # submit external intelligence for normalization (OPERATOR+)
    READ_INTELLIGENCE   = "read_intelligence"    # read normalized intelligence signals (ANALYST+)
    # Decision Authority Layer (DAL)
    PROPOSE_AUTHORITY               = "propose_authority"               # create authority envelope (ANALYST+)
    SUBMIT_AUTHORITY                = "submit_authority"                # submit for review (ANALYST+)
    APPROVE_AUTHORITY               = "approve_authority"               # approve a decision (ADMIN)
    REJECT_AUTHORITY                = "reject_authority"                # reject a decision (ADMIN)
    RETURN_AUTHORITY                = "return_authority"                # return for revision (ADMIN)
    ESCALATE_AUTHORITY              = "escalate_authority"              # escalate decision (OPERATOR+)
    EXECUTE_AUTHORITY               = "execute_authority"               # execute approved decision (OPERATOR+)
    REVOKE_AUTHORITY                = "revoke_authority"                # revoke decision (ADMIN)
    OVERRIDE_AUTHORITY              = "override_authority"              # admin override (ADMIN)
    READ_AUTHORITY                  = "read_authority"                  # read authority state (ANALYST+)
    READ_AUTHORITY_AUDIT            = "read_authority_audit"            # read full audit trail (ANALYST+)
    ANNOTATE_AUTHORITY              = "annotate_authority"              # annotate without status change (ANALYST+)
    REPORT_AUTHORITY_EXECUTION_FAILURE = "report_authority_execution_failure"  # report failure (OPERATOR+)
    WITHDRAW_AUTHORITY              = "withdraw_authority"              # withdraw decision (ANALYST+)


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
        Permission.CREATE_DECISION,
        Permission.READ_OUTCOME,
        Permission.READ_VALUE,
        Permission.READ_INTELLIGENCE,
        # DAL
        Permission.PROPOSE_AUTHORITY,
        Permission.SUBMIT_AUTHORITY,
        Permission.READ_AUTHORITY,
        Permission.READ_AUTHORITY_AUDIT,
        Permission.ANNOTATE_AUTHORITY,
        Permission.WITHDRAW_AUTHORITY,
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
        Permission.CREATE_DECISION,
        Permission.EXECUTE_DECISION,
        Permission.READ_OUTCOME,
        Permission.RECORD_OUTCOME,
        Permission.READ_VALUE,
        Permission.COMPUTE_VALUE,
        Permission.READ_INTELLIGENCE,
        Permission.INGEST_INTELLIGENCE,
        # DAL
        Permission.PROPOSE_AUTHORITY,
        Permission.SUBMIT_AUTHORITY,
        Permission.ESCALATE_AUTHORITY,
        Permission.EXECUTE_AUTHORITY,
        Permission.REPORT_AUTHORITY_EXECUTION_FAILURE,
        Permission.READ_AUTHORITY,
        Permission.READ_AUTHORITY_AUDIT,
        Permission.ANNOTATE_AUTHORITY,
        Permission.WITHDRAW_AUTHORITY,
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
        Permission.CREATE_DECISION,
        Permission.EXECUTE_DECISION,
        Permission.READ_OUTCOME,
        Permission.RECORD_OUTCOME,
        Permission.READ_VALUE,
        Permission.COMPUTE_VALUE,
        Permission.READ_INTELLIGENCE,
        Permission.INGEST_INTELLIGENCE,
        # DAL — ADMIN has all authority permissions
        Permission.PROPOSE_AUTHORITY,
        Permission.SUBMIT_AUTHORITY,
        Permission.APPROVE_AUTHORITY,
        Permission.REJECT_AUTHORITY,
        Permission.RETURN_AUTHORITY,
        Permission.ESCALATE_AUTHORITY,
        Permission.EXECUTE_AUTHORITY,
        Permission.REVOKE_AUTHORITY,
        Permission.OVERRIDE_AUTHORITY,
        Permission.READ_AUTHORITY,
        Permission.READ_AUTHORITY_AUDIT,
        Permission.ANNOTATE_AUTHORITY,
        Permission.REPORT_AUTHORITY_EXECUTION_FAILURE,
        Permission.WITHDRAW_AUTHORITY,
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
        Permission.CREATE_DECISION,
        Permission.EXECUTE_DECISION,
        Permission.READ_OUTCOME,
        Permission.RECORD_OUTCOME,
        Permission.READ_VALUE,
        Permission.COMPUTE_VALUE,
        Permission.READ_INTELLIGENCE,
        Permission.INGEST_INTELLIGENCE,
        # DAL — Regulator: read-only + annotate
        Permission.READ_AUTHORITY,
        Permission.READ_AUTHORITY_AUDIT,
        Permission.ANNOTATE_AUTHORITY,
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
