from pydantic import BaseModel
from uuid import UUID
from typing import Any


class ChatSessionCreate(BaseModel):
    title: str = ""
    character_id: UUID | None = None
    room_id: UUID | None = None


class ChatTurnCreate(BaseModel):
    content: str


class ChatTurnOut(BaseModel):
    id: UUID
    session_id: UUID
    turn_index: int
    role: str
    character_id: UUID | None = None
    content: str
    meta: dict | None = None

    class Config:
        from_attributes = True


class ChatSessionOut(BaseModel):
    id: UUID
    owner_user_id: UUID
    character_id: UUID | None = None
    room_id: UUID | None = None
    enrollment_id: UUID | None = None
    active_level_template_id: UUID | None = None
    title: str
    is_archived: bool

    class Config:
        from_attributes = True


class ChatSessionDetail(ChatSessionOut):
    turns: list[ChatTurnOut] = []


class ChatTurnResponse(BaseModel):
    session: ChatSessionOut
    user_turn: ChatTurnOut
    assistant_turns: list[ChatTurnOut]
    memory_used: list[dict[str, Any]] = []
