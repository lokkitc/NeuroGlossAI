from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.exceptions import EntityNotFoundException, ServiceException
from app.features.common.db import begin_if_needed
from app.features.rooms.models import Room, RoomParticipant
from app.features.rooms.repository import RoomRepository, RoomParticipantRepository
from app.features.rooms.schemas import RoomCreate, RoomUpdate


class RoomService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.rooms = RoomRepository(db)
        self.participants = RoomParticipantRepository(db)

    async def list_for_owner(self, *, owner_user_id: UUID, skip: int, limit: int):
        return await self.rooms.list_for_owner(owner_user_id, skip=skip, limit=limit)

    async def get_full_for_owner(self, *, room_id: UUID, owner_user_id: UUID):
        room = await self.rooms.get_full(room_id)
        if not room or room.owner_user_id != owner_user_id:
            raise EntityNotFoundException("Room", room_id)
        return room

    async def create_room(self, *, owner_user_id: UUID, body: RoomCreate):
        if not body.participant_character_ids:
            raise ServiceException("participant_character_ids is empty")

        room = Room(
            owner_user_id=owner_user_id,
            title=body.title,
            description=body.description or "",
            is_public=bool(body.is_public),
            is_nsfw=bool(body.is_nsfw),
        )

        async with begin_if_needed(self.db):
            await self.rooms.create(room)
            for cid in body.participant_character_ids:
                part = RoomParticipant(room_id=room.id, character_id=cid, priority=0, is_pinned=False)
                await self.participants.create(part)

        room_full = await self.rooms.get_full(room.id)
        if room_full is None:
            raise EntityNotFoundException("Room", room.id)
        return room_full

    async def update_room(self, *, room_id: UUID, owner_user_id: UUID, body: RoomUpdate):
        room = await self.rooms.get(room_id)
        if not room or room.owner_user_id != owner_user_id:
            raise EntityNotFoundException("Room", room_id)

        async with begin_if_needed(self.db):
            await self.rooms.update(room, body)

        room_full = await self.rooms.get_full(room_id)
        if room_full is None:
            raise EntityNotFoundException("Room", room_id)
        return room_full

    async def delete_room(self, *, room_id: UUID, owner_user_id: UUID) -> dict[str, Any]:
        room = await self.rooms.get(room_id)
        if not room or room.owner_user_id != owner_user_id:
            raise EntityNotFoundException("Room", room_id)

        async with begin_if_needed(self.db):
            await self.rooms.delete(room_id)

        return {"status": "ok"}
