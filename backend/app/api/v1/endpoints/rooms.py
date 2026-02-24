from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.characters import Room, RoomParticipant
from app.repositories.room import RoomRepository, RoomParticipantRepository
from app.schemas.room import RoomCreate, RoomOut, RoomUpdate
from app.core.exceptions import EntityNotFoundException, ServiceException


router = APIRouter()


@router.get("/me", response_model=list[RoomOut])
async def list_my_rooms(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    repo = RoomRepository(db)
    return await repo.list_for_owner(current_user.id, skip=skip, limit=limit)


@router.get("/me/{room_id}", response_model=RoomOut)
async def get_room(
    room_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    repo = RoomRepository(db)
    room = await repo.get_full(room_id)
    if not room or room.owner_user_id != current_user.id:
        raise EntityNotFoundException("Room", room_id)
    return room


@router.post("/me", response_model=RoomOut)
async def create_room(
    body: RoomCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    if not body.participant_character_ids:
        raise ServiceException("participant_character_ids is empty")

    room_repo = RoomRepository(db)
    part_repo = RoomParticipantRepository(db)

    room = Room(
        owner_user_id=current_user.id,
        title=body.title,
        description=body.description or "",
        is_public=bool(body.is_public),
        is_nsfw=bool(body.is_nsfw),
    )
    await room_repo.create(room, commit=False)

    for cid in body.participant_character_ids:
        part = RoomParticipant(room_id=room.id, character_id=cid, priority=0, is_pinned=False)
        await part_repo.create(part, commit=False)

    await db.commit()

    room_full = await room_repo.get_full(room.id)
    assert room_full is not None
    return room_full


@router.patch("/me/{room_id}", response_model=RoomOut)
async def update_room(
    room_id: UUID,
    body: RoomUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    repo = RoomRepository(db)
    room = await repo.get(room_id)
    if not room or room.owner_user_id != current_user.id:
        raise EntityNotFoundException("Room", room_id)
    await repo.update(room, body, commit=True)
    room_full = await repo.get_full(room_id)
    assert room_full is not None
    return room_full


@router.delete("/me/{room_id}")
async def delete_room(
    room_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    repo = RoomRepository(db)
    room = await repo.get(room_id)
    if not room or room.owner_user_id != current_user.id:
        raise EntityNotFoundException("Room", room_id)
    await repo.delete(room_id, commit=True)
    return {"status": "ok"}
