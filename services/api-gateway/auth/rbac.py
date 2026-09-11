"""
auth/rbac.py — Role-based access control guards.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.jwt_handler import decode_token
from database import db_cursor

bearer_scheme = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """Decode JWT and return current user payload."""
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    return payload


def require_roles(*allowed_roles: str):
    """Dependency factory that checks if the current user has one of the allowed roles."""
    def role_guard(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {list(allowed_roles)}"
            )
        return current_user
    return role_guard


def require_case_access(case_id: str, current_user: dict) -> None:
    """Verify that the current user is a participant in the given case."""
    with db_cursor() as cur:
        cur.execute("""
            SELECT 1 FROM case_participants
            WHERE case_id = %s AND participant_id = %s AND removed_at IS NULL
            LIMIT 1
        """, (case_id, current_user["sub"]))
        row = cur.fetchone()
    if not row:
        # Return 404 to not reveal case existence
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or access denied."
        )
