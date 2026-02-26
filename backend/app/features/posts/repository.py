from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.features.common.db import BaseRepository
from app.features.posts.models import Post, PostLike


class PostRepository(BaseRepository[Post]):
    def __init__(self, db: AsyncSession):
        super().__init__(Post, db)

    async def list_public(self, *, skip: int = 0, limit: int = 50):
        q = select(Post).where(Post.is_public.is_(True)).order_by(Post.created_at.desc()).offset(skip).limit(limit)
        res = await self.db.execute(q)
        return res.scalars().all()

    async def list_for_author(self, author_user_id, *, skip: int = 0, limit: int = 50):
        q = (
            select(Post)
            .where(Post.author_user_id == author_user_id)
            .order_by(Post.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.db.execute(q)
        return res.scalars().all()


class PostLikeRepository(BaseRepository[PostLike]):
    def __init__(self, db: AsyncSession):
        super().__init__(PostLike, db)

    async def get_by_post_and_user(self, post_id, user_id):
        q = select(PostLike).where(PostLike.post_id == post_id).where(PostLike.user_id == user_id)
        res = await self.db.execute(q)
        return res.scalars().first()

    async def unlike(self, post_id, user_id) -> None:
        await self.db.execute(delete(PostLike).where(PostLike.post_id == post_id).where(PostLike.user_id == user_id))
        await self.db.flush()
