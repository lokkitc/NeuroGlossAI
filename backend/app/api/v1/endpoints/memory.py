from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api import deps
from app.features.users.models import User
from app.features.memory.models import MemoryItem
from app.features.memory.repository import MemoryRepository
from app.features.memory.schemas import MemoryCreate, MemoryOut, MemoryUpdate
from app.core.exceptions import EntityNotFoundException


router = APIRouter()


@router.get("/me", response_model=list[MemoryOut])
async def list_memory(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Any:
    repo = MemoryRepository(db)
    return await repo.list_for_owner(current_user.id, skip=skip, limit=limit)


@router.post("/me", response_model=MemoryOut)
async def create_memory(
    body: MemoryCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    repo = MemoryRepository(db)
    row = MemoryItem(
        owner_user_id=current_user.id,
        title=body.title or "",
        content=body.content,
        character_id=body.character_id,
        room_id=body.room_id,
        session_id=body.session_id,
        is_pinned=bool(body.is_pinned),
        is_enabled=bool(body.is_enabled),
        tags=body.tags,
        importance=int(body.importance or 0),
    )
    return await repo.create(row, commit=True)


@router.patch("/me/{memory_id}", response_model=MemoryOut)
async def update_memory(
    memory_id: UUID,
    body: MemoryUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    repo = MemoryRepository(db)
    row = await repo.get(memory_id)
    if not row or row.owner_user_id != current_user.id:
        raise EntityNotFoundException("MemoryItem", memory_id)
    return await repo.update(row, body, commit=True)


@router.delete("/me/{memory_id}")
async def delete_memory(
    memory_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    repo = MemoryRepository(db)
    row = await repo.get(memory_id)
    if not row or row.owner_user_id != current_user.id:
        raise EntityNotFoundException("MemoryItem", memory_id)
    await repo.delete(memory_id, commit=True)
    return {"status": "ok"}
