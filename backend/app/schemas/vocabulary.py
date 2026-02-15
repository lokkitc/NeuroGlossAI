from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class VocabularyItemResponse(BaseModel):
    word: str
    translation: str
    context_sentence: str
    id: UUID
    mastery_level: int
    next_review_at: datetime

    class Config:
        from_attributes = True

class VocabularyReviewRequest(BaseModel):
    vocabulary_id: UUID
    rating: int # 1-5
