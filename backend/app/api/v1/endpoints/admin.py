from typing import Any

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.features.users.models import User
from app.features.admin.service import AdminService
from uuid import UUID


router = APIRouter()


@router.get("/users")
async def admin_list_users(
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.require_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    return await AdminService(db).list_users(skip=skip, limit=limit)


@router.post("/users/{user_id}/set-admin")
async def admin_set_user_admin(
    user_id: UUID,
    is_admin: bool = True,
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.require_admin),
) -> Any:
    return await AdminService(db).set_user_admin(user_id=user_id, is_admin=is_admin)


@router.get("/generated-lessons")
async def admin_list_generated_lessons(
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.require_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    return await AdminService(db).list_generated_lessons(skip=skip, limit=limit)


@router.get("/generated-lessons/{lesson_id}")
async def admin_get_generated_lesson(
    lesson_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.require_admin),
) -> Any:
    return await AdminService(db).get_generated_lesson(lesson_id=lesson_id)


@router.post("/generated-lessons/{lesson_id}/regen-exercises")
async def admin_regen_exercises(
    lesson_id: UUID,
    generation_mode: str = "strict",
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.require_admin),
) -> Any:
    return await AdminService(db).regen_exercises(lesson_id=lesson_id, generation_mode=generation_mode)


@router.post("/generated-lessons/{lesson_id}/regen-core")
async def admin_regen_core(
    lesson_id: UUID,
    level: str = "A1",
    generation_mode: str = "strict",
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.require_admin),
) -> Any:
    return await AdminService(db).regen_core(lesson_id=lesson_id, level=level, generation_mode=generation_mode)


@router.post("/purge-except-users")
async def admin_purge_except_users(
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.require_admin),
    confirm: str = Body(default="", embed=True),
) -> Any:
    return await AdminService(db).purge_all_except_users(confirm=confirm)
