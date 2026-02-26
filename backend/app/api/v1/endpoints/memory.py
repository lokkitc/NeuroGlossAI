from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api import deps
from app.features.users.models import User
from app.features.memory.service import MemoryService
from app.features.memory.schemas import MemoryCreate, MemoryOut, MemoryUpdate


router = APIRouter()


@router.get("/me", response_model=list[MemoryOut])
async def list_memory(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Any:
    return await MemoryService(db).list_for_owner(owner_user_id=current_user.id, skip=skip, limit=limit)


@router.post("/me", response_model=MemoryOut)
async def create_memory(
    body: MemoryCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await MemoryService(db).create_memory(owner_user_id=current_user.id, body=body)


@router.patch("/me/{memory_id}", response_model=MemoryOut)
async def update_memory(
    memory_id: UUID,
    body: MemoryUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await MemoryService(db).update_memory(memory_id=memory_id, owner_user_id=current_user.id, body=body)


@router.delete("/me/{memory_id}")
async def delete_memory(
    memory_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await MemoryService(db).delete_memory(memory_id=memory_id, owner_user_id=current_user.id)
