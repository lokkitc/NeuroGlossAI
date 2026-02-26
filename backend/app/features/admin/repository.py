from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.sql import func

from app.features.lessons.models import GeneratedLesson
from app.features.users.models import User
from app.features.common.db import BaseRepository


class AdminUserRepository(BaseRepository[User]):
    def __init__(self, db):
        super().__init__(User, db)

    async def list_users(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        q: str | None = None,
        is_admin: bool | None = None,
    ) -> list[User]:
        stmt = select(User)

        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(or_(User.username.ilike(like), User.email.ilike(like)))

        if is_admin is not None:
            stmt = stmt.where(User.is_admin.is_(bool(is_admin)))

        stmt = stmt.order_by(User.created_at.desc()).offset(skip).limit(limit)

        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_by_id(self, *, user_id: UUID) -> User | None:
        res = await self.db.execute(select(User).where(User.id == user_id))
        return res.scalars().first()

    async def get_by_username(self, *, username: str) -> User | None:
        res = await self.db.execute(select(User).where(func.lower(User.username) == func.lower(username)))
        return res.scalars().first()

    async def get_by_email(self, *, email: str) -> User | None:
        res = await self.db.execute(select(User).where(func.lower(User.email) == func.lower(email)))
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
