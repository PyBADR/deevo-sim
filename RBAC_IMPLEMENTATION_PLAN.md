# RBAC Implementation Plan — Step 8 (LOCKED)

**Date:** 2026-04-02
**V4 Spec:** §10 (RBAC), §22 (Multi-Tenant)
**Roles:** 5 — viewer, analyst, operator, admin, regulator
**Permissions:** 19 backend, 17 frontend
**Goal:** Unified permission matrix, tenant isolation, API + UI enforcement

---

## 1. Role Permissions Matrix

### 1.1 Backend Permissions (`backend/app/core/rbac.py`) — EXISTS, 19 permissions

| Permission | viewer | analyst | operator | admin | regulator |
|-----------|:------:|:-------:|:--------:|:-----:|:---------:|
| `CREATE_SCENARIO` | | ✅ | ✅ | ✅ | ✅ |
| `LAUNCH_RUN` | | ✅ | ✅ | ✅ | ✅ |
| `LAUNCH_RUN_WITH_OVERRIDES` | | | ✅ | ✅ | ✅ |
| `READ_FINANCIAL` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `READ_BANKING` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `READ_INSURANCE` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `READ_FINTECH` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `READ_DECISION` | | ✅ | ✅ | ✅ | ✅ |
| `READ_EXPLANATION` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `READ_BUSINESS_IMPACT` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `READ_TIMELINE` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `READ_REGULATORY_TIMELINE` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `READ_EXECUTIVE_EXPLANATION` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `OVERRIDE_THRESHOLDS` | | | ✅ | ✅ | ✅ |
| `FORCE_RERUN` | | | ✅ | ✅ | |
| `MANAGE_MANIFESTS` | | | | ✅ | |
| `ARCHIVE_SCENARIO` | | | | ✅ | |
| `READ_AUDIT_LOGS` | | | | ✅ | ✅ |
| `GENERATE_COMPLIANCE_REPORT` | | | | ✅ | ✅ |

**Total per role:** viewer=9, analyst=12, operator=15, admin=19, regulator=16

### 1.2 Frontend Permissions (`frontend/lib/server/rbac.ts`) — EXISTS, 17 permissions

| Permission | viewer | analyst | operator | admin | regulator |
|-----------|:------:|:-------:|:--------:|:-----:|:---------:|
| `read_scenarios` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `read_runs` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `read_financial` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `read_stress` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `read_regulatory` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `read_explanation` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `read_decision` | | ✅ | ✅ | ✅ | ✅ |
| `create_scenario` | | ✅ | ✅ | ✅ | |
| `launch_run` | | ✅ | ✅ | ✅ | |
| `export_data` | | ✅ | ✅ | ✅ | ✅ |
| `override_decision` | | | ✅ | ✅ | ✅ |
| `force_rerun` | | | ✅ | ✅ | |
| `manage_manifests` | | | | ✅ | |
| `manage_users` | | | | ✅ | |
| `read_audit` | | | | ✅ | ✅ |
| `read_compliance` | | | | | ✅ |
| `archive_run` | | | | ✅ | |

### 1.3 Permission Drift Analysis

| Issue | Backend | Frontend | Resolution |
|-------|---------|----------|------------|
| **Granularity mismatch** | Separate `READ_BANKING`, `READ_INSURANCE`, `READ_FINTECH` | Single `read_stress` covers all three | **Align frontend** — split `read_stress` into `read_banking`, `read_insurance`, `read_fintech` to match backend |
| **Missing frontend permissions** | `READ_BUSINESS_IMPACT`, `READ_TIMELINE`, `READ_REGULATORY_TIMELINE`, `READ_EXECUTIVE_EXPLANATION` | Not present | **Add to frontend** — these exist in backend, frontend needs matching checks |
| **Regulator CREATE_SCENARIO** | ✅ (has it) | ❌ (missing) | **Add to frontend** — regulators can create scenarios in backend |
| **Regulator LAUNCH_RUN** | ✅ (has it) | ❌ (missing) | **Add to frontend** — regulators can launch runs in backend |
| **LAUNCH_RUN_WITH_OVERRIDES** | Exists | Missing entirely | **Add to frontend** — needed for operator/admin/regulator override flows |
| **GENERATE_COMPLIANCE_REPORT** | Exists | `read_compliance` (different name) | **Rename frontend** to match backend convention |
| **manage_users** | Not in backend | In frontend | **Add to backend** — `MANAGE_USERS` permission for admin |

---

## 2. Override Rules

### 2.1 Decision Override Flow (Human-in-the-Loop)

```
DecisionAction.status lifecycle:
  PENDING_REVIEW → APPROVED → EXECUTING → COMPLETED
                → REJECTED

Who can transition:
  PENDING_REVIEW → APPROVED:   operator, admin, regulator (requires OVERRIDE_THRESHOLDS)
  PENDING_REVIEW → REJECTED:   operator, admin, regulator (requires OVERRIDE_THRESHOLDS)
  APPROVED → EXECUTING:        operator, admin (requires OVERRIDE_THRESHOLDS)
  EXECUTING → COMPLETED:       system only (automated confirmation)
```

**Backend enforcement:**
```python
# In services/decision/engine.py:
def approve_action(action_id: str, auth: AuthContext) -> DecisionAction:
    if not has_permission(auth.role, Permission.OVERRIDE_THRESHOLDS):
        raise InsufficientRoleError(auth.role.value)
    # ... approve logic with audit trail
```

**Audit requirement:** Every override must produce an audit log entry with:
- `principal_id` (who approved)
- `action_id` (what was approved)
- `previous_status` → `new_status`
- `timestamp`
- `reason` (mandatory free-text)
- `tenant_id`

### 2.2 Threshold Override Rules

| Override | Who Can | Constraint | Audit |
|----------|---------|-----------|-------|
| Scenario severity override | operator, admin, regulator | `severity` must stay in [0.0, 1.0] | Log original + overridden value |
| Regulatory threshold override | operator, admin, regulator | Cannot set below absolute minimums (LCR < 0.5, CAR < 0.04) | Log + mandatory reason |
| Decision action override | operator, admin, regulator | Cannot override system-generated rank | Log + mandatory reason |
| Force re-run | operator, admin | Max 3 re-runs per scenario per day | Log each re-run |
| Manifest management | admin only | Version-controlled, rollback available | Full diff log |
| User role assignment | admin only | Cannot self-elevate beyond current role | Log + approval chain |

### 2.3 Regulator Special Privileges

| Privilege | Details |
|-----------|---------|
| **Read-only audit access** | Full read access to all audit logs across all tenants (cross-tenant read in multi-tenant mode) |
| **Compliance report generation** | Can generate formal regulatory reports (PDPL, IFRS 17, Basel III) |
| **Override thresholds** | Can override regulatory thresholds (for "what-if" analysis) |
| **Cannot force re-run** | Regulators observe, they don't re-run scenarios |
| **Cannot manage manifests** | Regulators don't control system configuration |
| **Cannot archive** | Regulators cannot delete or archive data |

---

## 3. Tenant Isolation Enforcement

### 3.1 Current State

Tenant isolation is **minimal**:
- `AuthContext.tenant_id` exists (default: `"default"`)
- No tenant filtering in any query or API endpoint
- No tenant column in any data model
- Single-tenant only

### 3.2 Target: Row-Level Tenant Isolation (§22)

**Principle:** Every data object belongs to exactly one tenant. No cross-tenant data leakage except for regulator audit access.

#### Data Model Changes

Every persisted model gets a `tenant_id` field:

```python
class TenantAware(BaseModel):
    """Mixin for tenant-scoped models."""
    tenant_id: str = Field(..., min_length=1, max_length=64, description="Tenant identifier")
```

Applied to: `Scenario`, `Run`, `FinancialImpact`, `BankingStress`, `InsuranceStress`, `FintechStress`, `DecisionAction`, `DecisionPlan`, `RegulatoryState`, `ExplanationPack`, `BusinessImpactSummary`, `LossTrajectoryPoint`, `TimeToFailure`, `RegulatoryBreachEvent`, `TimeStepState`, `AuditLogEntry`.

#### Query Enforcement

Every database query includes tenant filter:

```python
# PostgreSQL (via SQLAlchemy or raw SQL):
SELECT * FROM runs WHERE run_id = :run_id AND tenant_id = :tenant_id

# Neo4j (Cypher):
MATCH (e:Entity {tenant_id: $tenant_id}) RETURN e

# Redis (key prefix):
f"tenant:{tenant_id}:run:{run_id}"
```

#### API Middleware

```python
# In app/middleware/tenant.py (NEW):
async def tenant_middleware(request: Request, call_next):
    auth = authenticate(request.headers.get("Authorization"), request.headers.get("X-IO-API-Key"))
    request.state.tenant_id = auth.tenant_id
    request.state.auth = auth
    response = await call_next(request)
    return response
```

Every service method receives `tenant_id` from `request.state`:

```python
async def get_run(run_id: str, tenant_id: str) -> RunResult:
    result = await db.query("SELECT * FROM runs WHERE run_id=$1 AND tenant_id=$2", run_id, tenant_id)
    if not result:
        raise RunNotFoundError(run_id)  # Returns 404, not 403 (prevent tenant enumeration)
    return result
```

**Critical:** If a run exists but belongs to a different tenant, return 404 (not 403). This prevents tenant enumeration attacks.

#### Cross-Tenant Regulator Access

Regulators need read access across tenants for audit and compliance:

```python
def get_tenant_filter(auth: AuthContext, permission: Permission) -> str | None:
    """Returns tenant_id filter, or None for cross-tenant access."""
    if auth.role == Role.REGULATOR and permission in {
        Permission.READ_AUDIT_LOGS,
        Permission.GENERATE_COMPLIANCE_REPORT,
        Permission.READ_REGULATORY_TIMELINE,
    }:
        return None  # No tenant filter — cross-tenant read
    return auth.tenant_id  # Normal tenant-scoped query
```

### 3.3 Tenant Configuration

```python
class TenantConfig(BaseModel):
    """Per-tenant configuration."""
    tenant_id: str
    tenant_name: str
    tenant_name_ar: str
    jurisdiction: str          # "SA", "AE", "KW", "BH", "QA", "OM"
    regulatory_profile: RegulatoryProfile  # Default thresholds for this tenant
    max_scenarios: int = 100   # Resource limits
    max_runs_per_day: int = 50
    data_retention_days: int = 365
    allowed_roles: set[Role] = {Role.VIEWER, Role.ANALYST, Role.OPERATOR, Role.ADMIN}
    created_at: str
    active: bool = True
```

### 3.4 Multi-Tenant Migration Strategy

| Phase | Scope | Risk |
|-------|-------|------|
| **P1 (Current)** | Single-tenant, `tenant_id="default"` everywhere | Zero — no change |
| **P2** | Add `tenant_id` column to all DB tables, default to `"default"` | LOW — additive migration |
| **P3** | Add tenant middleware, enforce `tenant_id` in all queries | MEDIUM — must verify every query |
| **P4** | Enable regulator cross-tenant access | LOW — additive |
| **P5** | Enable tenant provisioning (create/archive tenants) | MEDIUM — new admin flow |

---

## 4. API Access Matrix

### 4.1 Which APIs Each Role Can Access

| API Endpoint | viewer | analyst | operator | admin | regulator | Permission Required |
|-------------|:------:|:-------:|:--------:|:-----:|:---------:|-------------------|
| `POST /runs` | | ✅ | ✅ | ✅ | ✅ | `LAUNCH_RUN` |
| `POST /runs` (with overrides) | | | ✅ | ✅ | ✅ | `LAUNCH_RUN_WITH_OVERRIDES` |
| `GET /runs/{id}/financial` | ✅ | ✅ | ✅ | ✅ | ✅ | `READ_FINANCIAL` |
| `GET /runs/{id}/banking` | ✅ | ✅ | ✅ | ✅ | ✅ | `READ_BANKING` |
| `GET /runs/{id}/insurance` | ✅ | ✅ | ✅ | ✅ | ✅ | `READ_INSURANCE` |
| `GET /runs/{id}/fintech` | ✅ | ✅ | ✅ | ✅ | ✅ | `READ_FINTECH` |
| `GET /runs/{id}/decision` | | ✅ | ✅ | ✅ | ✅ | `READ_DECISION` |
| `GET /runs/{id}/explanation` | ✅ | ✅ | ✅ | ✅ | ✅ | `READ_EXPLANATION` |
| `GET /runs/{id}/business-impact` | ✅ | ✅ | ✅ | ✅ | ✅ | `READ_BUSINESS_IMPACT` |
| `GET /runs/{id}/timeline` | ✅ | ✅ | ✅ | ✅ | ✅ | `READ_TIMELINE` |
| `GET /runs/{id}/regulatory-timeline` | ✅ | ✅ | ✅ | ✅ | ✅ | `READ_REGULATORY_TIMELINE` |
| `GET /runs/{id}/executive-explanation` | ✅ | ✅ | ✅ | ✅ | ✅ | `READ_EXECUTIVE_EXPLANATION` |
| `POST /scenarios` | | ✅ | ✅ | ✅ | ✅ | `CREATE_SCENARIO` |
| `PUT /scenarios/{id}/archive` | | | | ✅ | | `ARCHIVE_SCENARIO` |
| `POST /runs/{id}/rerun` | | | ✅ | ✅ | | `FORCE_RERUN` |
| `PUT /decisions/{id}/approve` | | | ✅ | ✅ | ✅ | `OVERRIDE_THRESHOLDS` |
| `PUT /decisions/{id}/reject` | | | ✅ | ✅ | ✅ | `OVERRIDE_THRESHOLDS` |
| `GET /audit/logs` | | | | ✅ | ✅ | `READ_AUDIT_LOGS` |
| `POST /reports/compliance` | | | | ✅ | ✅ | `GENERATE_COMPLIANCE_REPORT` |
| `GET /manifests` | | | | ✅ | | `MANAGE_MANIFESTS` |
| `PUT /manifests/{id}` | | | | ✅ | | `MANAGE_MANIFESTS` |

### 4.2 Which Dashboard Views Each Role Can See

| Dashboard Tab | viewer | analyst | operator | admin | regulator | Gate |
|--------------|:------:|:-------:|:--------:|:-----:|:---------:|------|
| **Overview** | ✅ (KPIs only) | ✅ (full) | ✅ (full) | ✅ (full) | ✅ (full) | Viewer sees KPIs + stress gauges but not decision action cards |
| **Banking** | ✅ | ✅ | ✅ | ✅ | ✅ | All read |
| **Insurance** | ✅ | ✅ | ✅ | ✅ | ✅ | All read |
| **Fintech** | ✅ | ✅ | ✅ | ✅ | ✅ | All read |
| **Decisions** | | ✅ (read) | ✅ (read + approve) | ✅ (read + approve) | ✅ (read + approve) | Viewer cannot see this tab at all |
| **Timeline** | ✅ | ✅ | ✅ | ✅ | ✅ | All read |
| **Graph** | ✅ | ✅ | ✅ | ✅ | ✅ | All read |
| **Map** | ✅ | ✅ | ✅ | ✅ | ✅ | All read |
| **Regulatory** | | | | ✅ | ✅ | Audit logs + compliance only for admin/regulator |

### 4.3 UI Component Visibility by Role

| Component | viewer | analyst | operator | admin | regulator |
|-----------|:------:|:-------:|:--------:|:-----:|:---------:|
| "Run Scenario" button | hidden | visible | visible | visible | visible |
| Severity override slider | hidden | hidden | visible | visible | visible |
| Decision "Approve" button | hidden | hidden | visible | visible | visible |
| Decision "Reject" button | hidden | hidden | visible | visible | visible |
| "Force Re-run" button | hidden | hidden | visible | visible | hidden |
| DecisionActionCard (full) | hidden | read-only | interactive | interactive | interactive |
| DecisionActionCard (summary) | visible | — | — | — | — |
| Audit Log tab | hidden | hidden | hidden | visible | visible |
| Compliance Report button | hidden | hidden | hidden | visible | visible |
| Manifest Settings | hidden | hidden | hidden | visible | hidden |
| User Management | hidden | hidden | hidden | visible | hidden |

### 4.4 Frontend Enforcement Pattern

```typescript
// In DashboardShell or any component:
import { useAppStore } from '@/store/app-store'
import { hasPermission } from '@/lib/server/rbac'

function DashboardShell() {
    const viewMode = useAppStore(s => s.viewMode)  // "executive" | "analyst" | "regulatory"
    const userRole = useAppStore(s => s.userRole)   // Role from auth context

    // Map viewMode to effective role for display filtering:
    // viewMode is a UI preference, userRole is the security boundary
    const canSeeDecisions = hasPermission(userRole, 'read_decision')
    const canApproveDecisions = hasPermission(userRole, 'override_decision')
    const canRunScenarios = hasPermission(userRole, 'launch_run')
    const canSeeAudit = hasPermission(userRole, 'read_audit')

    return (
        <>
            <TabBar
                tabs={[
                    { id: 'overview', visible: true },
                    { id: 'banking', visible: true },
                    { id: 'insurance', visible: true },
                    { id: 'fintech', visible: true },
                    { id: 'decisions', visible: canSeeDecisions },
                    { id: 'timeline', visible: true },
                    { id: 'graph', visible: true },
                    { id: 'map', visible: true },
                    { id: 'regulatory', visible: canSeeAudit },
                ]}
            />
            {/* Decision actions hidden for viewer */}
            {canSeeDecisions && <DecisionActionCard interactive={canApproveDecisions} />}
        </>
    )
}
```

---

## 5. Authentication Flow

### 5.1 Current State (`backend/app/core/security.py`)

- **Dev mode:** API key lookup from 5 hardcoded keys → `AuthContext(principal_id, role, tenant_id)`
- **Production:** JWT validation — `NotImplementedError` (not yet implemented)
- `AuthContext` carries: `principal_id`, `role`, `tenant_id`

### 5.2 Target: JWT Authentication (P2)

```
Frontend                    Backend
   │                          │
   │ GET /auth/token          │
   │ (OAuth2 / OIDC)          │
   │ ─────────────────────►   │
   │                          │ Validate credentials
   │  ◄──── JWT (signed)      │ Extract: sub, role, tenant_id
   │                          │
   │ GET /runs/{id}/banking   │
   │ Authorization: Bearer JWT│
   │ ─────────────────────►   │
   │                          │ verify_jwt(token)
   │                          │ → AuthContext(sub, role, tenant_id)
   │                          │ → has_permission(role, READ_BANKING)
   │                          │ → tenant_filter(tenant_id)
   │  ◄──── 200 + data        │
```

**JWT claims:**
```json
{
    "sub": "user_12345",
    "role": "analyst",
    "tenant_id": "sa_bank_group_1",
    "iss": "impact-observatory",
    "aud": "io-api",
    "exp": 1743580800,
    "iat": 1743577200
}
```

### 5.3 Frontend Auth State

```typescript
// Add to Zustand store:
interface AuthState {
    isAuthenticated: boolean
    principalId: string | null
    userRole: Role
    tenantId: string
    token: string | null
}
```

---

## 6. Zustand Store Additions

```typescript
// In src/store/app-store.ts:
interface AppStore {
    // ... existing ...

    // RBAC (Step 8):
    userRole: Role              // From JWT or dev key
    tenantId: string            // From JWT or "default"
    principalId: string | null  // From JWT

    // Derived permissions (computed, not stored):
    // Use hasPermission(userRole, permission) directly
}
```

---

## 7. Decision Gate

This plan is **LOCKED**. Before implementing:

1. **Backend prerequisite:** `core/rbac.py` already has the correct 19-permission matrix — no changes needed to backend RBAC logic
2. **Frontend prerequisite:** `lib/server/rbac.ts` must be aligned with backend (add missing permissions: `read_banking`, `read_insurance`, `read_fintech`, `read_business_impact`, `read_timeline`, `read_regulatory_timeline`, `read_executive_explanation`, `launch_run_with_overrides`)
3. **Auth prerequisite:** Dev mode API keys are sufficient for V1. JWT implementation deferred to P2.
4. **Tenant prerequisite:** Single-tenant `"default"` for V1. Multi-tenant deferred to P3.
5. **UI prerequisite:** Dashboard shell must be restructured (Step 3) before adding RBAC-gated visibility

Awaiting your command to begin execution.
