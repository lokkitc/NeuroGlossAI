from pydantic import BaseModel
from uuid import UUID
from typing import Any


class PostMediaItem(BaseModel):
    url: str
    public_id: str | None = None
    width: int | None = None
    height: int | None = None
    bytes: int | None = None
    format: str | None = None


class PostCreate(BaseModel):
    title: str = ""
    content: str = ""
    character_id: UUID | None = None
    media: list[PostMediaItem] | None = None
    is_public: bool = False


class PostUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    character_id: UUID | None = None
    media: list[PostMediaItem] | None = None
    is_public: bool | None = None


class PostOut(BaseModel):
    id: UUID
    author_user_id: UUID
    character_id: UUID | None = None
    title: str
    content: str
    media: Any | None = None
    is_public: bool
    created_at: Any | None = None

    class Config:
        from_attributes = True
