from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api import deps
from app.features.users.models import User
from app.features.rooms.service import RoomService
from app.features.rooms.schemas import RoomCreate, RoomOut, RoomUpdate


router = APIRouter()


@router.get("/me", response_model=list[RoomOut])
async def list_my_rooms(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    return await RoomService(db).list_for_owner(owner_user_id=current_user.id, skip=skip, limit=limit)


@router.get("/me/{room_id}", response_model=RoomOut)
async def get_room(
    room_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await RoomService(db).get_full_for_owner(room_id=room_id, owner_user_id=current_user.id)


@router.post("/me", response_model=RoomOut)
async def create_room(
    body: RoomCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await RoomService(db).create_room(owner_user_id=current_user.id, body=body)


@router.patch("/me/{room_id}", response_model=RoomOut)
async def update_room(
    room_id: UUID,
    body: RoomUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await RoomService(db).update_room(room_id=room_id, owner_user_id=current_user.id, body=body)


@router.delete("/me/{room_id}")
async def delete_room(
    room_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await RoomService(db).delete_room(room_id=room_id, owner_user_id=current_user.id)
