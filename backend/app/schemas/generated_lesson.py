from pydantic import BaseModel, UUID4
from typing import List, Optional, Any, Dict
from datetime import datetime


class GeneratedVocabularyItemResponse(BaseModel):
    id: UUID4
    user_lexeme_id: Optional[UUID4] = None
    word: Optional[str] = None
    translation: Optional[str] = None
    context_sentence: Optional[str] = None

    class Config:
        from_attributes = True


class GeneratedLessonResponse(BaseModel):
    id: UUID4
    enrollment_id: UUID4
    level_template_id: UUID4

    topic_snapshot: Optional[str] = None

    content_text: str
    exercises: Optional[List[Dict[str, Any]]] = None

    quality_status: str
    created_at: datetime

    vocabulary_items: List[GeneratedVocabularyItemResponse]

    class Config:
        from_attributes = True


class GeneratedLessonCreate(BaseModel):
    level_template_id: UUID4
    topic: str
    level: str = "A1"
    generation_mode: str = "balanced"
