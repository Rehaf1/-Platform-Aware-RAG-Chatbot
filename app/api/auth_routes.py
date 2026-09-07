"""
Real account endpoints -- login (for both chat users and admins), and
admin-only account creation. This replaces the "paste a JWT you minted
yourself" flow with actual email+password authentication, while still
issuing the same JWT under the hood (jwt_auth.py's create_access_token)
so nothing downstream of login has to change.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.db.crud import (
    get_user_by_email,
    create_user_account,
    get_or_create_platform,
    get_or_create_tenant,
)
from app.auth.password import hash_password, verify_password
from app.auth.jwt_auth import create_access_token, get_trusted_context, TrustedContext
from app.auth.authorization import require_admin

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login -- used by both chat users and admins
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    platform_id: str
    tenant_id: str
    user_role: Optional[str]


@router.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = get_user_by_email(db, request.email)

    # Deliberately identical error for "no such user" and "wrong
    # password" -- distinguishing them lets an attacker enumerate valid
    # emails, same principle as test_security.py's
    # test_401_response_does_not_leak_whether_platform_exists.
    invalid_credentials = HTTPException(status_code=401, detail="Invalid email or password.")

    if user is None or not user.password_hash:
        raise invalid_credentials
    if not verify_password(request.password, user.password_hash):
        raise invalid_credentials

    token = create_access_token(
        platform_id=user.platform.platform_id,
        tenant_id=user.tenant.tenant_id,
        user_id=user.external_user_id,
        user_role=user.role.name if user.role else None,
    )

    return LoginResponse(
        access_token=token,
        platform_id=user.platform.platform_id,
        tenant_id=user.tenant.tenant_id,
        user_role=user.role.name if user.role else None,
    )


# ---------------------------------------------------------------------------
# POST /api/v1/admin/accounts -- admin-only, creates a chat-user (or
# another admin) account. Nobody self-registers.
# ---------------------------------------------------------------------------

class CreateAccountRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    platform_id: str
    tenant_id: str
    role: str = Field(..., description="e.g. 'compliance_manager', 'auditor', 'admin'")


class CreateAccountResponse(BaseModel):
    email: str
    platform_id: str
    tenant_id: str
    role: str


@router.post("/admin/accounts", response_model=CreateAccountResponse)
def create_account(
    request: CreateAccountRequest,
    ctx: TrustedContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> CreateAccountResponse:
    """
    Only an authenticated admin can call this. The new account's
    platform/tenant are set explicitly by the admin here -- never
    inferred from the requester's own token -- so an admin can
    provision accounts for tenants other than their own if their
    organization's admin role spans multiple tenants.
    """
    existing = get_user_by_email(db, request.email)
    if existing is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    platform_row = get_or_create_platform(db, request.platform_id)
    tenant_row = get_or_create_tenant(db, platform_row, request.tenant_id)

    user = create_user_account(
        db,
        email=request.email,
        password_hash=hash_password(request.password),
        platform=platform_row,
        tenant=tenant_row,
        role_name=request.role,
    )

    return CreateAccountResponse(
        email=user.email,
        platform_id=request.platform_id,
        tenant_id=request.tenant_id,
        role=request.role,
    )
