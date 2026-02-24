from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.features.chat.models import ChatSession, ChatTurn, ChatSessionSummary, ModerationEvent
from app.repositories.base import BaseRepository
from app.features.memory.repository import MemoryRepository


class ChatSessionRepository(BaseRepository[ChatSession]):
    def __init__(self, db: AsyncSession):
        super().__init__(ChatSession, db)

    async def list_for_owner(self, owner_user_id, *, skip: int = 0, limit: int = 50):
        q = (
            select(ChatSession)
            .where(ChatSession.owner_user_id == owner_user_id)
            .order_by(ChatSession.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.db.execute(q)
        return res.scalars().all()

    async def get_full(self, session_id):
        q = (
            select(ChatSession)
            .where(ChatSession.id == session_id)
            .options(
                selectinload(ChatSession.turns),
                selectinload(ChatSession.summaries),
            )
        )
        res = await self.db.execute(q)
        return res.scalars().first()

    async def next_turn_index(self, session_id) -> int:
        q = select(func.max(ChatTurn.turn_index)).where(ChatTurn.session_id == session_id)
        res = await self.db.execute(q)
        v = res.scalar()
        return int(v or 0) + 1


class ChatTurnRepository(BaseRepository[ChatTurn]):
    def __init__(self, db: AsyncSession):
        super().__init__(ChatTurn, db)

    async def list_recent(self, session_id, *, limit: int = 80):
        q = (
            select(ChatTurn)
            .where(ChatTurn.session_id == session_id)
            .order_by(ChatTurn.turn_index.desc())
            .limit(limit)
        )
        res = await self.db.execute(q)
        return list(reversed(res.scalars().all()))


class ChatSummaryRepository(BaseRepository[ChatSessionSummary]):
    def __init__(self, db: AsyncSession):
        super().__init__(ChatSessionSummary, db)

    async def get_latest(self, session_id):
        q = (
            select(ChatSessionSummary)
            .where(ChatSessionSummary.session_id == session_id)
            .order_by(ChatSessionSummary.created_at.desc())
            .limit(1)
        )
        res = await self.db.execute(q)
        return res.scalars().first()


class ModerationEventRepository(BaseRepository[ModerationEvent]):
    def __init__(self, db: AsyncSession):
        super().__init__(ModerationEvent, db)
