from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.features.memory.models import MemoryItem
from app.features.common.db import BaseRepository


class MemoryRepository(BaseRepository[MemoryItem]):
    def __init__(self, db: AsyncSession):
        super().__init__(MemoryItem, db)

    async def list_for_owner(self, owner_user_id, *, skip: int = 0, limit: int = 100):
        q = (
            select(MemoryItem)
            .where(MemoryItem.owner_user_id == owner_user_id)
            .order_by(MemoryItem.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.db.execute(q)
        return res.scalars().all()

    async def list_pinned(self, owner_user_id, *, character_id=None, room_id=None, limit: int = 50):
        q = (
            select(MemoryItem)
            .where(MemoryItem.owner_user_id == owner_user_id)
            .where(MemoryItem.is_enabled.is_(True))
            .where(MemoryItem.is_pinned.is_(True))
        )
        if character_id is not None:
            q = q.where(MemoryItem.character_id == character_id)
        if room_id is not None:
            q = q.where(MemoryItem.room_id == room_id)
        q = q.order_by(MemoryItem.importance.desc(), MemoryItem.updated_at.desc()).limit(limit)
        res = await self.db.execute(q)
        return res.scalars().all()

    async def list_candidates(self, owner_user_id, *, character_id=None, room_id=None, limit: int = 200):
        q = (
            select(MemoryItem)
            .where(MemoryItem.owner_user_id == owner_user_id)
            .where(MemoryItem.is_enabled.is_(True))
            .where(MemoryItem.is_pinned.is_(False))
        )
        if character_id is not None:
            q = q.where(MemoryItem.character_id == character_id)
        if room_id is not None:
            q = q.where(MemoryItem.room_id == room_id)
        q = q.order_by(MemoryItem.importance.desc(), MemoryItem.updated_at.desc()).limit(limit)
        res = await self.db.execute(q)
        return res.scalars().all()
