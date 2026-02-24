from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.chat_learning import ChatLearningLesson
from app.repositories.base import BaseRepository


class ChatLearningLessonRepository(BaseRepository[ChatLearningLesson]):
    def __init__(self, db: AsyncSession):
        super().__init__(ChatLearningLesson, db)

    async def list_for_session(self, owner_user_id, chat_session_id, *, skip: int = 0, limit: int = 50):
        q = (
            select(ChatLearningLesson)
            .where(ChatLearningLesson.owner_user_id == owner_user_id)
            .where(ChatLearningLesson.chat_session_id == chat_session_id)
            .order_by(ChatLearningLesson.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.db.execute(q)
        return res.scalars().all()
