from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select

from app.repositories.base import BaseRepository
from app.models.generated_content import GeneratedVocabularyItem, GeneratedLesson
from app.models.enrollment import Enrollment


class GeneratedVocabularyRepository(BaseRepository[GeneratedVocabularyItem]):
    def __init__(self, db):
        super().__init__(GeneratedVocabularyItem, db)

    async def get_daily_review_items(self, user_id: UUID) -> List[GeneratedVocabularyItem]:
        now = datetime.utcnow()
        query = (
            select(GeneratedVocabularyItem)
            .join(GeneratedLesson)
            .join(Enrollment)
            .where(
                Enrollment.user_id == user_id,
                GeneratedVocabularyItem.next_review_at <= now,
            )
        )
        res = await self.db.execute(query)
        return res.scalars().all()

    async def get_by_id_and_user(self, item_id: UUID, user_id: UUID) -> Optional[GeneratedVocabularyItem]:
        query = (
            select(GeneratedVocabularyItem)
            .join(GeneratedLesson)
            .join(Enrollment)
            .where(
                GeneratedVocabularyItem.id == item_id,
                Enrollment.user_id == user_id,
            )
        )
        res = await self.db.execute(query)
        return res.scalars().first()
