from uuid import UUID

from sqlalchemy import select

from app.features.lessons.models import GeneratedLesson
from app.features.users.models import User
from app.features.common.db import BaseRepository


class AdminUserRepository(BaseRepository[User]):
    def __init__(self, db):
        super().__init__(User, db)

    async def list_users(self, *, skip: int = 0, limit: int = 50) -> list[User]:
        res = await self.db.execute(
            select(User)
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return res.scalars().all()

    async def get_by_id(self, *, user_id: UUID) -> User | None:
        res = await self.db.execute(select(User).where(User.id == user_id))
        return res.scalars().first()


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
