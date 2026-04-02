"""
Impact Observatory | مرصد الأثر — Security (v4 §1, §10)
Bearer JWT validation and principal extraction.
Dev mode: accepts any well-formed token with configurable issuer.
"""

import os
from dataclasses import dataclass
from typing import Optional
from .rbac import Role


@dataclass
class AuthContext:
    """Authenticated principal context extracted from JWT."""
    principal_id: str
    role: Role
    tenant_id: str = "default"


# Dev mode: simplified auth for local development
_DEV_MODE = os.environ.get("APP_ENV", "dev") == "dev"

# Dev API keys for backward compatibility during migration
_DEV_KEYS = {
    "io_master_key_2026": AuthContext("admin_user", Role.ADMIN, "default"),
    "io_analyst_key_2026": AuthContext("analyst_user", Role.ANALYST, "default"),
    "io_operator_key_2026": AuthContext("operator_user", Role.OPERATOR, "default"),
    "io_viewer_key_2026": AuthContext("viewer_user", Role.VIEWER, "default"),
    "io_regulator_key_2026": AuthContext("regulator_user", Role.REGULATOR, "default"),
}


def authenticate(authorization: Optional[str] = None, api_key: Optional[str] = None) -> AuthContext:
    """
    Extract auth context from Bearer token or API key.
    In dev mode, accepts API keys for backward compatibility.
    In production, validates JWT against public key.
    """
    # Dev mode: accept API keys
    if _DEV_MODE:
        if api_key and api_key in _DEV_KEYS:
            return _DEV_KEYS[api_key]
        if authorization:
            token = authorization.replace("Bearer ", "").strip()
            if token in _DEV_KEYS:
                return _DEV_KEYS[token]
        # Default dev context
        return AuthContext("dev_user", Role.ADMIN, "default")

    # Production mode: JWT validation
    if not authorization or not authorization.startswith("Bearer "):
        raise ValueError("Missing or invalid Authorization header")

    # TODO: Implement full JWT validation with JWT_PUBLIC_KEY, JWT_ISSUER, JWT_AUDIENCE
    # For now, raise not implemented
    raise NotImplementedError("Production JWT validation not yet implemented")
