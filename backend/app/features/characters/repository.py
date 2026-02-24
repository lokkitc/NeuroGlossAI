from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.features.characters.models import Character
from app.repositories.base import BaseRepository


class CharacterRepository(BaseRepository[Character]):
    def __init__(self, db: AsyncSession):
        super().__init__(Character, db)

    async def get_by_owner_and_slug(self, owner_user_id, slug: str) -> Character | None:
        q = select(Character).where(Character.owner_user_id == owner_user_id).where(Character.slug == slug)
        res = await self.db.execute(q)
        return res.scalars().first()

    async def list_for_owner(self, owner_user_id, *, skip: int = 0, limit: int = 50):
        q = (
            select(Character)
            .where(Character.owner_user_id == owner_user_id)
            .order_by(Character.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.db.execute(q)
        return res.scalars().all()

    async def list_public(self, *, skip: int = 0, limit: int = 50, nsfw: bool | None = None):
        q = select(Character).where(Character.is_public.is_(True))
        if nsfw is not None:
            q = q.where(Character.is_nsfw.is_(nsfw))
        q = q.order_by(Character.created_at.desc()).offset(skip).limit(limit)
        res = await self.db.execute(q)
        return res.scalars().all()
