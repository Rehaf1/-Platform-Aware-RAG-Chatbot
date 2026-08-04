from fastapi import Depends, HTTPException, status
from app.auth.jwt_auth import TrustedContext, get_trusted_context


def require_admin(
    ctx: TrustedContext = Depends(get_trusted_context),
) -> TrustedContext:
    """
    FastAPI dependency — use on any endpoint that only administrators
    should be able to call (document upload/delete/reindex).
    """
    if ctx.user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required for this action",
        )
    return ctx