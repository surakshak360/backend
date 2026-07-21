from typing import Optional, Literal
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserResponse(BaseModel):
    id: str
    phone: str
    email: EmailStr
    role: Literal["citizen", "officer", "admin", "analyst"]
    language: str
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class UserUpdate(BaseModel):
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[Literal["citizen", "officer", "admin", "analyst"]] = None
    language: Optional[str] = None
    is_verified: Optional[bool] = None
