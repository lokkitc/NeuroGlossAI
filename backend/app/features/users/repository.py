from typing import Optional

from sqlalchemy import select, or_

from app.repositories.base import BaseRepository
from app.features.users.models import User


class UserRepository(BaseRepository[User]):
    def __init__(self, db):
        super().__init__(User, db)

    async def get_by_username(self, username: str) -> Optional[User]:
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_username_or_email(self, identifier: str) -> Optional[User]:
        query = select(User).where(or_(User.username == identifier, User.email == identifier))
        result = await self.db.execute(query)
        return result.scalars().first()
