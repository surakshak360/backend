from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    phone: Optional[str] = Field(None, json_schema_extra={"example": "+919876543210"})
    email: EmailStr = Field(..., json_schema_extra={"example": "user@example.com"})
    password: str = Field(..., min_length=6)
    role: Literal["citizen", "officer", "admin", "analyst"] = "citizen"
    language: Optional[str] = "en"


class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str
