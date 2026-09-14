import uuid
from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    employee_id: str
    name: str
    email: Optional[str] = None
    role: str = "OFFICER"
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    id: Union[uuid.UUID, str, int]
    employee_id: str
    name: str
    email: Optional[str] = None
    role: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    employee_id: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
