from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "analyst"  # admin, analyst, viewer
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="User password (minimum 6 characters)")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = Field(None, description="Google OAuth ID Token / Credential string")
    email: Optional[EmailStr] = Field(None, description="Google verified email address")
    name: Optional[str] = Field(None, description="Google user display name")
    picture: Optional[str] = Field(None, description="Google user avatar URL")
    role: Optional[str] = Field("analyst", description="Assigned role for new registrations")


class GoogleConfigResponse(BaseModel):
    client_id: str
    enabled: bool


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


TokenResponse.model_rebuild()
