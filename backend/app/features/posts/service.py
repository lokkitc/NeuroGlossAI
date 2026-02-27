from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from uuid import UUID

from app.core.exceptions import EntityNotFoundException, ServiceException
from app.features.common.db import begin_if_needed
from app.features.posts.models import Post, PostLike
from app.features.posts.repository import PostRepository, PostLikeRepository
from app.features.posts.schemas import PostCreate
from app.features.characters.models import Character


class PostService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.posts = PostRepository(db)
        self.likes = PostLikeRepository(db)

    def _attach_preview_fields(self, rows: list[Post]) -> list[Post]:
        for row in rows:
            if getattr(row, "author", None) is not None:
                setattr(row, "author_username", getattr(row.author, "username", None))
                setattr(row, "author_avatar_url", getattr(row.author, "avatar_url", None))
            if getattr(row, "character", None) is not None:
                setattr(row, "character_display_name", getattr(row.character, "display_name", None))
                setattr(row, "character_avatar_url", getattr(row.character, "avatar_url", None))
        return rows

    async def list_public(self, *, skip: int, limit: int):
        rows = await self.posts.list_public(skip=skip, limit=limit)
        return self._attach_preview_fields(rows)

    async def list_public_for_author(self, *, author_user_id: UUID, skip: int, limit: int):
        rows = await self.posts.list_public_for_author(author_user_id, skip=skip, limit=limit)
        return self._attach_preview_fields(rows)

    async def list_public_for_character(self, *, character_id: UUID, skip: int, limit: int):
        rows = await self.posts.list_public_for_character(character_id, skip=skip, limit=limit)
        return self._attach_preview_fields(rows)

    async def list_for_author(self, *, author_user_id: UUID, skip: int, limit: int):
        rows = await self.posts.list_for_author(author_user_id, skip=skip, limit=limit)
        return self._attach_preview_fields(rows)

    async def create_post(self, *, author_user_id: UUID, body: PostCreate) -> Post:
        if body.character_id is not None:
            res = await self.db.execute(select(Character).where(Character.id == body.character_id))
            ch = res.scalars().first()
            if ch is None or ch.owner_user_id != author_user_id:
                raise EntityNotFoundException("Character", body.character_id)

        row = Post(
            author_user_id=author_user_id,
            character_id=body.character_id,
            title=body.title or "",
            content=body.content or "",
            media=[m.model_dump() for m in (body.media or [])] if body.media is not None else None,
            is_public=bool(body.is_public),
        )

        async with begin_if_needed(self.db):
            await self.posts.create(row)

        await self.db.refresh(row)

        # Ensure preview fields are available for response_model mapping.
        if getattr(row, "author", None) is not None:
            setattr(row, "author_username", getattr(row.author, "username", None))
            setattr(row, "author_avatar_url", getattr(row.author, "avatar_url", None))
        if getattr(row, "character", None) is not None:
            setattr(row, "character_display_name", getattr(row.character, "display_name", None))
            setattr(row, "character_avatar_url", getattr(row.character, "avatar_url", None))

        return row

    async def delete_post(self, *, post_id: UUID, author_user_id: UUID) -> dict[str, Any]:
        post = await self.posts.get(post_id)
        if not post or post.author_user_id != author_user_id:
            raise EntityNotFoundException("Post", post_id)

        async with begin_if_needed(self.db):
            await self.posts.delete(post_id)

        return {"status": "ok"}

    async def set_post_public(self, *, post_id: UUID, author_user_id: UUID, is_public: bool) -> Post:
        post = await self.posts.get(post_id)
        if not post or post.author_user_id != author_user_id:
            raise EntityNotFoundException("Post", post_id)

        async with begin_if_needed(self.db):
            post.is_public = bool(is_public)
            self.db.add(post)

        await self.db.refresh(post)

        if getattr(post, "author", None) is not None:
            setattr(post, "author_username", getattr(post.author, "username", None))
            setattr(post, "author_avatar_url", getattr(post.author, "avatar_url", None))
        if getattr(post, "character", None) is not None:
            setattr(post, "character_display_name", getattr(post.character, "display_name", None))
            setattr(post, "character_avatar_url", getattr(post.character, "avatar_url", None))

        return post

    async def like_post(self, *, post_id: UUID, user_id: UUID) -> dict[str, Any]:
        post = await self.posts.get(post_id)
        if not post or not post.is_public:
            raise EntityNotFoundException("Post", post_id)

        existing = await self.likes.get_by_post_and_user(post_id, user_id)
        if existing is not None:
            return {"status": "ok"}

        row = PostLike(post_id=post_id, user_id=user_id)
        try:
            async with begin_if_needed(self.db):
                await self.likes.create(row)
        except IntegrityError:
            return {"status": "ok"}
        except Exception:
            raise ServiceException("Failed to like")

        return {"status": "ok"}

    async def unlike_post(self, *, post_id: UUID, user_id: UUID) -> dict[str, Any]:
        post = await self.posts.get(post_id)
        if not post or not post.is_public:
            raise EntityNotFoundException("Post", post_id)

        async with begin_if_needed(self.db):
            await self.likes.unlike(post_id, user_id)

        return {"status": "ok"}
