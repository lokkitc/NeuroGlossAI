from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api import deps
from app.features.users.models import User
from app.features.posts.service import PostService
from app.features.posts.schemas import PostCreate, PostOut


router = APIRouter()


@router.get("/public", response_model=list[PostOut])
async def list_public_posts(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    return await PostService(db).list_public(skip=skip, limit=limit)


@router.get("/me", response_model=list[PostOut])
async def list_my_posts(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    return await PostService(db).list_for_author(author_user_id=current_user.id, skip=skip, limit=limit)


@router.post("/me", response_model=PostOut)
async def create_post(
    body: PostCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await PostService(db).create_post(author_user_id=current_user.id, body=body)


@router.delete("/me/{post_id}")
async def delete_post(
    post_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await PostService(db).delete_post(post_id=post_id, author_user_id=current_user.id)


@router.post("/{post_id}/like")
async def like_post(
    post_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await PostService(db).like_post(post_id=post_id, user_id=current_user.id)


@router.delete("/{post_id}/like")
async def unlike_post(
    post_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await PostService(db).unlike_post(post_id=post_id, user_id=current_user.id)
