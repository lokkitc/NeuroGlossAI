from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from typing import Optional, Dict

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 32:
            raise ValueError('Username must be 3-32 characters')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserUpdateLanguages(BaseModel):
    target_language: str
    native_language: str

# Общая схема обновления пользователя для PATCH
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None # Предполагаем, что добавим это в модель позже
    target_language: Optional[str] = None
    native_language: Optional[str] = None
    interests: Optional[list[str]] = None
    # Примечание: XP обычно обновляется через системные события (завершение уроков), а не через прямой патч API пользователем
    
class UserResponse(UserBase):
    id: UUID
    xp: int
    language_levels: Dict[str, str]
    target_language: str
    native_language: str
    interests: list[str] = []
    # avatar_url: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
