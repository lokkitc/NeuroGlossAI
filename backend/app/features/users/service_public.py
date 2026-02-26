from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.core.exceptions import EntityNotFoundException
from app.features.users.models import User


class PublicUserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_users(self, *, q: str | None, skip: int, limit: int) -> list[User]:
        stmt = select(User)

        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(or_(User.username.ilike(like), User.preferred_name.ilike(like)))

        stmt = stmt.order_by(User.created_at.desc()).offset(skip).limit(limit)
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_user_by_username(self, *, username: str) -> User:
        res = await self.db.execute(select(User).where(func.lower(User.username) == func.lower(username)))
        user = res.scalars().first()
        if user is None:
            raise EntityNotFoundException(entity_name="User", entity_id=str(username))
        return user
