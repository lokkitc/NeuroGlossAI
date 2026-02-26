from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.exceptions import EntityNotFoundException
from app.features.common.db import begin_if_needed
from app.features.memory.models import MemoryItem
from app.features.memory.repository import MemoryRepository
from app.features.memory.schemas import MemoryCreate, MemoryUpdate


class MemoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.memories = MemoryRepository(db)

    async def list_for_owner(self, *, owner_user_id: UUID, skip: int, limit: int):
        return await self.memories.list_for_owner(owner_user_id, skip=skip, limit=limit)

    async def create_memory(self, *, owner_user_id: UUID, body: MemoryCreate) -> MemoryItem:
        row = MemoryItem(
            owner_user_id=owner_user_id,
            title=body.title or "",
            content=body.content,
            character_id=body.character_id,
            room_id=body.room_id,
            session_id=body.session_id,
            is_pinned=bool(body.is_pinned),
            is_enabled=bool(body.is_enabled),
            tags=body.tags,
            importance=int(body.importance or 0),
        )

        async with begin_if_needed(self.db):
            await self.memories.create(row)

        await self.db.refresh(row)
        return row

    async def update_memory(self, *, memory_id: UUID, owner_user_id: UUID, body: MemoryUpdate) -> MemoryItem:
        row = await self.memories.get(memory_id)
        if not row or row.owner_user_id != owner_user_id:
            raise EntityNotFoundException("MemoryItem", memory_id)

        async with begin_if_needed(self.db):
            await self.memories.update(row, body)

        await self.db.refresh(row)
        return row

    async def delete_memory(self, *, memory_id: UUID, owner_user_id: UUID) -> dict:
        row = await self.memories.get(memory_id)
        if not row or row.owner_user_id != owner_user_id:
            raise EntityNotFoundException("MemoryItem", memory_id)

        async with begin_if_needed(self.db):
            await self.memories.delete(memory_id)

        return {"status": "ok"}
