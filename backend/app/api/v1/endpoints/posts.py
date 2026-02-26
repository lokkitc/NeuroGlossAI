from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api import deps
from app.core.exceptions import EntityNotFoundException, ServiceException
from app.features.users.models import User
from app.features.posts.models import Post, PostLike
from app.features.posts.repository import PostRepository, PostLikeRepository
from app.features.posts.schemas import PostCreate, PostOut


router = APIRouter()


@router.get("/public", response_model=list[PostOut])
async def list_public_posts(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    return await PostRepository(db).list_public(skip=skip, limit=limit)


@router.get("/me", response_model=list[PostOut])
async def list_my_posts(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    return await PostRepository(db).list_for_author(current_user.id, skip=skip, limit=limit)


@router.post("/me", response_model=PostOut)
async def create_post(
    body: PostCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    repo = PostRepository(db)
    row = Post(
        author_user_id=current_user.id,
        character_id=body.character_id,
        title=body.title or "",
        content=body.content or "",
        media=[m.model_dump() for m in (body.media or [])] if body.media is not None else None,
        is_public=bool(body.is_public),
    )
    return await repo.create(row, commit=True)


@router.delete("/me/{post_id}")
async def delete_post(
    post_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    repo = PostRepository(db)
    post = await repo.get(post_id)
    if not post or post.author_user_id != current_user.id:
        raise EntityNotFoundException("Post", post_id)
    await repo.delete(post_id, commit=True)
    return {"status": "ok"}


@router.post("/{post_id}/like")
async def like_post(
    post_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    posts = PostRepository(db)
    likes = PostLikeRepository(db)

    post = await posts.get(post_id)
    if not post or not post.is_public:
        raise EntityNotFoundException("Post", post_id)

    existing = await likes.get_by_post_and_user(post_id, current_user.id)
    if existing is not None:
        return {"status": "ok"}

    row = PostLike(post_id=post_id, user_id=current_user.id)
    try:
        await likes.create(row, commit=True)
    except Exception:
        raise ServiceException("Failed to like")

    return {"status": "ok"}


@router.delete("/{post_id}/like")
async def unlike_post(
    post_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    posts = PostRepository(db)

    post = await posts.get(post_id)
    if not post or not post.is_public:
        raise EntityNotFoundException("Post", post_id)

    await PostLikeRepository(db).unlike(post_id, current_user.id, commit=True)
    return {"status": "ok"}
