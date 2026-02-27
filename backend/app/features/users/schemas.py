from pydantic import BaseModel, EmailStr, field_validator, Field
from uuid import UUID
from typing import Optional, Dict, Any
from urllib.parse import urlparse


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
    selected_theme_id: Optional[UUID] = None
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
    selected_theme_id: Optional[UUID] = None

    assistant_tone: Optional[str] = None
    assistant_verbosity: Optional[int] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("avatar_url", "thumbnail_url", "banner_url", mode="before")
    @classmethod
    def _normalize_storageapi_urls(cls, v):
        if v is None:
            return None
        if not isinstance(v, str):
            v = str(v)
        url = v.strip()
        if not url:
            return None

        parsed = urlparse(url)
        host = parsed.netloc
        if not host.endswith("storageapi.dev"):
            return url

        parts = host.split(".")
        if len(parts) < 3:
            return url

        bucket = parts[0]
        base_host = ".".join(parts[1:])
        path = parsed.path or ""
        if not path.startswith("/"):
            path = f"/{path}"

        if path.startswith(f"/{bucket}/"):
            return url

        fixed = f"{parsed.scheme or 'https'}://{base_host}/{bucket}{path}"
        if parsed.query:
            fixed = f"{fixed}?{parsed.query}"
        return fixed

    @field_validator("preferences", mode="before")
    @classmethod
    def _coerce_preferences(cls, v):
        if v is None:
            return {}
        if isinstance(v, dict):
            return v
        return {}

    class Config:
        from_attributes = True


class PublicUserResponse(BaseModel):
    id: UUID
    username: str
    preferred_name: Optional[str] = None
    bio: Optional[str] = None

    selected_theme_id: Optional[UUID] = None

    avatar_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    banner_url: Optional[str] = None

    class Config:
        from_attributes = True


class AdminUserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    is_admin: bool = False
    xp: int = 0
    native_language: str | None = None
    target_language: str | None = None
    created_at: Any | None = None

    avatar_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    banner_url: Optional[str] = None
    preferred_name: Optional[str] = None
    bio: Optional[str] = None
    timezone: Optional[str] = None
    ui_theme: Optional[str] = None
    selected_theme_id: Optional[UUID] = None

    assistant_tone: Optional[str] = None
    assistant_verbosity: Optional[int] = None
    interests: list[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)

    language_levels: Dict[str, str] = Field(default_factory=dict)

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
