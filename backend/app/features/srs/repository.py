from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.features.common.db import BaseRepository
from app.features.srs.models import Lexeme, UserLexeme, LessonLexeme


class LexemeRepository(BaseRepository[Lexeme]):
    def __init__(self, db):
        super().__init__(Lexeme, db)

    async def get_by_lang_and_normalized(self, *, target_language: str, normalized: str) -> Optional[Lexeme]:
        res = await self.db.execute(select(Lexeme).where(Lexeme.target_language == target_language).where(Lexeme.normalized == normalized))
        return res.scalars().first()


class UserLexemeRepository(BaseRepository[UserLexeme]):
    def __init__(self, db):
        super().__init__(UserLexeme, db)

    async def get_by_id_and_user(self, *, user_lexeme_id: UUID, user_id: UUID) -> Optional[UserLexeme]:
        res = await self.db.execute(
            select(UserLexeme)
            .options(selectinload(UserLexeme.lexeme))
            .where(UserLexeme.id == user_lexeme_id)
            .where(UserLexeme.user_id == user_id)
        )
        return res.scalars().first()

    async def get_by_user_and_lexeme(self, *, user_id: UUID, lexeme_id: UUID) -> Optional[UserLexeme]:
        res = await self.db.execute(select(UserLexeme).where(UserLexeme.user_id == user_id).where(UserLexeme.lexeme_id == lexeme_id))
        return res.scalars().first()

    async def get_daily_review(self, *, user_id: UUID, now: datetime) -> list[UserLexeme]:
        res = await self.db.execute(
            select(UserLexeme)
            .options(selectinload(UserLexeme.lexeme))
            .where(UserLexeme.user_id == user_id)
            .where(UserLexeme.next_review_at <= now)
            .order_by(UserLexeme.next_review_at.asc())
        )
        return res.scalars().all()


class LessonLexemeRepository(BaseRepository[LessonLexeme]):
    def __init__(self, db):
        super().__init__(LessonLexeme, db)

    async def get_by_lesson_and_lexeme(self, *, generated_lesson_id: UUID, lexeme_id: UUID) -> Optional[LessonLexeme]:
        res = await self.db.execute(
            select(LessonLexeme)
            .where(LessonLexeme.generated_lesson_id == generated_lesson_id)
            .where(LessonLexeme.lexeme_id == lexeme_id)
        )
        return res.scalars().first()
