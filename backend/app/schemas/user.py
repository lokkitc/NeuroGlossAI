from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional, Dict

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

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
