import os
from dataclasses import dataclass
from typing import Optional

import jwt
from fastapi import Header, HTTPException, status


JWT_SECRET = os.environ.get("JWT_SECRET", "dev-only-insecure-secret-change-me")
JWT_ALGORITHM = "HS256"

@dataclass
class TrustedContext:
    platform_id: str
    tenant_id: str
    user_role: Optional[str]
    user_id: str
    language: str = "en"

def create_access_token(
    *, platform_id: str, tenant_id: str, user_id: str, user_role: Optional[str] = None
) -> str:
    payload = {
        "platform_id": platform_id,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "user_role": user_role,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def get_trusted_context(
    authorization: Optional[str] = Header(None, description="Bearer <JWT>"),
) -> TrustedContext:
    """
    FastAPI dependency — runs automatically on every protected request.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header (expected 'Bearer <token>')",
        )

    token = authorization.removeprefix("Bearer ").strip()
    payload = _decode_token(token)

    platform_id = payload.get("platform_id")
    tenant_id = payload.get("tenant_id")
    user_id = payload.get("user_id")

    if not platform_id or not tenant_id or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing required claims (platform_id, tenant_id, user_id)",
        )

    return TrustedContext(
        platform_id=platform_id,
        tenant_id=tenant_id,
        user_role=payload.get("user_role"),
        user_id=user_id,
    )