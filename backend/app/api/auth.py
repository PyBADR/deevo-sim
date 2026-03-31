from typing import Optional, Set
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from functools import wraps
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# API Key configuration - in production, use secure storage like AWS Secrets Manager
_API_KEYS = {
    "test-key-admin": {
        "roles": {"admin", "analyst", "viewer"},
        "active": True,
        "created_at": datetime.utcnow()
    },
    "test-key-analyst": {
        "roles": {"analyst", "viewer"},
        "active": True,
        "created_at": datetime.utcnow()
    },
    "test-key-viewer": {
        "roles": {"viewer"},
        "active": True,
        "created_at": datetime.utcnow()
    }
}

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def api_key_auth(api_key: Optional[str] = Depends(api_key_header)) -> str:
    """Validate API key from request header"""
    if not api_key:
        logger.warning("API request without API key")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key required. Provide X-API-Key header."
        )
    
    if api_key not in _API_KEYS:
        logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    key_info = _API_KEYS[api_key]
    if not key_info["active"]:
        logger.warning(f"Inactive API key used: {api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is inactive"
        )
    
    return api_key

async def get_api_key_roles(api_key: str = Depends(api_key_auth)) -> Set[str]:
    """Get roles associated with API key"""
    if api_key in _API_KEYS:
        return _API_KEYS[api_key]["roles"]
    return set()

def require_role(*required_roles: str):
    """Dependency to require specific roles"""
    async def role_checker(roles: Set[str] = Depends(get_api_key_roles)):
        if not any(role in roles for role in required_roles):
            logger.warning(f"Insufficient permissions. Required: {required_roles}, Have: {roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(required_roles)}"
            )
        return roles
    return role_checker

def register_api_key(api_key: str, roles: Set[str]) -> bool:
    """Register a new API key with roles"""
    if api_key in _API_KEYS:
        logger.warning(f"Attempt to register existing API key: {api_key[:10]}...")
        return False
    
    _API_KEYS[api_key] = {
        "roles": roles,
        "active": True,
        "created_at": datetime.utcnow()
    }
    logger.info(f"New API key registered with roles: {roles}")
    return True

def revoke_api_key(api_key: str) -> bool:
    """Revoke an API key"""
    if api_key not in _API_KEYS:
        return False
    
    _API_KEYS[api_key]["active"] = False
    logger.info(f"API key revoked: {api_key[:10]}...")
    return True

def has_role(api_key: str, role: str) -> bool:
    """Check if API key has specific role"""
    if api_key not in _API_KEYS:
        return False
    
    return role in _API_KEYS[api_key]["roles"]

def get_all_api_keys_info() -> dict:
    """Get info about all registered API keys (excluding actual keys for security)"""
    return {
        key: {
            "active": info["active"],
            "roles": list(info["roles"]),
            "created_at": info["created_at"].isoformat()
        }
        for key, info in _API_KEYS.items()
    }
