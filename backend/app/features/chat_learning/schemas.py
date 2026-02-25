from pydantic import BaseModel
from uuid import UUID
from typing import Any


class ChatLearningLessonOut(BaseModel):
    id: UUID
    owner_user_id: UUID
    chat_session_id: UUID
    source_turn_from: int
    source_turn_to: int
    title: str
    topic_snapshot: str | None = None
    content_text: str
    vocabulary: Any | None = None
    exercises: Any | None = None
    provider: str | None = None
    model: str | None = None
    quality_status: str | None = None
    created_at: Any | None = None

    class Config:
        from_attributes = True


class ChatLearningGenerateRequest(BaseModel):
    turn_window: int = 80
    generation_mode: str = "balanced"
