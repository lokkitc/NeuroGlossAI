from pydantic import BaseModel
from uuid import UUID


class MemoryCreate(BaseModel):
    title: str = ""
    content: str
    character_id: UUID | None = None
    room_id: UUID | None = None
    session_id: UUID | None = None
    is_pinned: bool = False
    is_enabled: bool = True
    tags: list[str] | None = None
    importance: int = 0


class MemoryUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    is_pinned: bool | None = None
    is_enabled: bool | None = None
    tags: list[str] | None = None
    importance: int | None = None


class MemoryOut(BaseModel):
    id: UUID
    owner_user_id: UUID
    character_id: UUID | None = None
    room_id: UUID | None = None
    session_id: UUID | None = None
    title: str
    content: str
    is_pinned: bool
    is_enabled: bool
    tags: list[str] | None = None
    importance: int

    class Config:
        from_attributes = True
