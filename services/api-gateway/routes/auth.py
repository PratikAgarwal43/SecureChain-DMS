"""
routes/auth.py — Login, logout, and token refresh endpoints.
"""
import uuid
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from passlib.context import CryptContext
from database import db_cursor
from auth.jwt_handler import create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/auth", tags=["Authentication"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginRequest(BaseModel):
    employee_id: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    name: str
    employee_id: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    with db_cursor() as cur:
        cur.execute("""
            SELECT u.id, u.name, u.employee_id, u.password_hash, u.is_active,
                   r.name AS role
            FROM users u
            JOIN roles r ON r.id = u.role_id
            WHERE u.employee_id = %s
        """, (body.employee_id,))
        user = cur.fetchone()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    if not pwd_context.verify(body.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token_data = {
        "sub": str(user["id"]),
        "employee_id": user["employee_id"],
        "role": user["role"],
        "name": user["name"],
    }

    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "role": user["role"],
        "name": user["name"],
        "employee_id": user["employee_id"],
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(body: RefreshRequest):
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    token_data = {k: v for k, v in payload.items() if k not in ("exp", "type")}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "role": payload.get("role", ""),
        "name": payload.get("name", ""),
        "employee_id": payload.get("employee_id", ""),
    }
