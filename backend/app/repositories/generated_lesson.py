from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.generated_content import GeneratedLesson, GeneratedVocabularyItem


class GeneratedLessonRepository(BaseRepository[GeneratedLesson]):
    def __init__(self, db):
        super().__init__(GeneratedLesson, db)

    async def get_by_enrollment(self, enrollment_id: UUID, skip: int = 0, limit: int = 10) -> List[GeneratedLesson]:
        query = (
            select(GeneratedLesson)
            .options(selectinload(GeneratedLesson.vocabulary_items))
            .where(GeneratedLesson.enrollment_id == enrollment_id)
            .order_by(GeneratedLesson.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.db.execute(query)
        return res.scalars().all()

    async def get_by_id_and_enrollment(self, lesson_id: UUID, enrollment_id: UUID) -> Optional[GeneratedLesson]:
        query = (
            select(GeneratedLesson)
            .options(selectinload(GeneratedLesson.vocabulary_items))
            .where(GeneratedLesson.id == lesson_id, GeneratedLesson.enrollment_id == enrollment_id)
        )
        res = await self.db.execute(query)
        return res.scalars().first()

    async def get_by_enrollment_and_level(self, enrollment_id: UUID, level_template_id: UUID) -> Optional[GeneratedLesson]:
        query = (
            select(GeneratedLesson)
            .options(selectinload(GeneratedLesson.vocabulary_items))
            .where(
                GeneratedLesson.enrollment_id == enrollment_id,
                GeneratedLesson.level_template_id == level_template_id,
            )
        )
        res = await self.db.execute(query)
        return res.scalars().first()

    async def create_with_vocabulary(
        self,
        lesson: GeneratedLesson,
        vocabulary_items: list[GeneratedVocabularyItem],
    ) -> GeneratedLesson:
        self.db.add(lesson)
        await self.db.flush()

        for item in vocabulary_items:
            item.generated_lesson_id = lesson.id
            self.db.add(item)

        await self.db.commit()
        await self.db.refresh(lesson)
        return await self.get_by_id_and_enrollment(lesson.id, lesson.enrollment_id)
