from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.rate_limit import limiter
from app.features.users.models import User
from app.features.users.schemas import PublicUserResponse
from app.features.users.service_public import PublicUserService


router = APIRouter()


@router.get("/users", response_model=list[PublicUserResponse])
@limiter.limit("30/minute")
async def public_list_users(
    request: Request,
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.get_current_user),
    q: str | None = Query(None, description="Search by username/preferred_name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    return await PublicUserService(db).list_users(q=q, skip=skip, limit=limit)


@router.get("/users/by-username/{username}", response_model=PublicUserResponse)
@limiter.limit("60/minute")
async def public_get_user_by_username(
    request: Request,
    username: str,
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.get_current_user),
) -> Any:
    return await PublicUserService(db).get_user_by_username(username=username)
