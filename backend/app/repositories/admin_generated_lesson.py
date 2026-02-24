from uuid import UUID

from sqlalchemy import select

from app.models.generated_content import GeneratedLesson
from app.repositories.base import BaseRepository


class AdminGeneratedLessonRepository(BaseRepository[GeneratedLesson]):
    def __init__(self, db):
        super().__init__(GeneratedLesson, db)

    async def list_lessons(self, *, skip: int = 0, limit: int = 50) -> list[GeneratedLesson]:
        res = await self.db.execute(
            select(GeneratedLesson)
            .order_by(GeneratedLesson.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return res.scalars().all()

    async def get_by_id(self, *, lesson_id: UUID) -> GeneratedLesson | None:
        res = await self.db.execute(select(GeneratedLesson).where(GeneratedLesson.id == lesson_id))
        return res.scalars().first()
