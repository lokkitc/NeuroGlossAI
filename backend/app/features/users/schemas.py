from pydantic import BaseModel, EmailStr, field_validator, Field
from uuid import UUID
from typing import Optional, Dict, Any


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 32:
            raise ValueError("Username must be 3-32 characters")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdateLanguages(BaseModel):
    target_language: str
    native_language: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    banner_url: Optional[str] = None
    preferred_name: Optional[str] = None
    bio: Optional[str] = None
    timezone: Optional[str] = None
    ui_theme: Optional[str] = None
    assistant_tone: Optional[str] = None
    assistant_verbosity: Optional[int] = None
    preferences: Optional[Dict[str, Any]] = None
    target_language: Optional[str] = None
    native_language: Optional[str] = None
    interests: Optional[list[str]] = None


class UserResponse(UserBase):
    id: UUID
    xp: int
    is_admin: bool = False
    language_levels: Dict[str, str]
    target_language: str
    native_language: str
    interests: list[str] = Field(default_factory=list)

    avatar_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    banner_url: Optional[str] = None
    preferred_name: Optional[str] = None
    bio: Optional[str] = None
    timezone: Optional[str] = None
    ui_theme: Optional[str] = None

    assistant_tone: Optional[str] = None
    assistant_verbosity: Optional[int] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str | None = None
    session_id: str | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    user_id: Optional[UUID] = None
