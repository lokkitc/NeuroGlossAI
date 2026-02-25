from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.features.rooms.models import Room, RoomParticipant
from app.features.common.db import BaseRepository


class RoomRepository(BaseRepository[Room]):
    def __init__(self, db: AsyncSession):
        super().__init__(Room, db)

    async def list_for_owner(self, owner_user_id, *, skip: int = 0, limit: int = 50):
        q = (
            select(Room)
            .where(Room.owner_user_id == owner_user_id)
            .order_by(Room.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.db.execute(q)
        return res.scalars().all()

    async def get_full(self, room_id):
        q = (
            select(Room)
            .where(Room.id == room_id)
            .options(selectinload(Room.participants).selectinload(RoomParticipant.character))
        )
        res = await self.db.execute(q)
        return res.scalars().first()


class RoomParticipantRepository(BaseRepository[RoomParticipant]):
    def __init__(self, db: AsyncSession):
        super().__init__(RoomParticipant, db)

    async def get_by_room_and_character(self, room_id, character_id):
        q = select(RoomParticipant).where(RoomParticipant.room_id == room_id).where(RoomParticipant.character_id == character_id)
        res = await self.db.execute(q)
        return res.scalars().first()

    async def list_for_room(self, room_id):
        q = (
            select(RoomParticipant)
            .where(RoomParticipant.room_id == room_id)
            .order_by(RoomParticipant.priority.desc(), RoomParticipant.created_at.asc())
        )
        res = await self.db.execute(q)
        return res.scalars().all()
