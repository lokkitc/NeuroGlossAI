from uuid import UUID

from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository


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
