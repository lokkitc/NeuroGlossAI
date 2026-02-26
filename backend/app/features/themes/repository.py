from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.features.common.db import BaseRepository
from app.features.themes.models import Theme


class ThemeRepository(BaseRepository[Theme]):
    def __init__(self, db: AsyncSession):
        super().__init__(Theme, db)

    async def list_available(self, *, user_id, theme_type: str | None = None, skip: int = 0, limit: int = 50):
        q = select(Theme).where(or_(Theme.is_public.is_(True), Theme.owner_user_id == user_id))
        if theme_type:
            q = q.where(Theme.theme_type == theme_type)
        q = q.order_by(Theme.created_at.desc()).offset(skip).limit(limit)
        res = await self.db.execute(q)
        return res.scalars().all()

    async def get_available(self, *, theme_id, user_id) -> Theme | None:
        q = select(Theme).where(Theme.id == theme_id).where(or_(Theme.is_public.is_(True), Theme.owner_user_id == user_id))
        res = await self.db.execute(q)
        return res.scalars().first()

    async def get_by_owner_and_slug(self, *, owner_user_id, slug: str) -> Theme | None:
        q = select(Theme).where(Theme.owner_user_id == owner_user_id).where(Theme.slug == slug)
        res = await self.db.execute(q)
        return res.scalars().first()
