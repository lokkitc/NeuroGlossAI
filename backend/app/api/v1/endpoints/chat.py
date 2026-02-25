from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api import deps
from app.features.users.models import User
from app.features.chat.schemas import ChatSessionCreate, ChatSessionOut, ChatSessionDetail, ChatTurnCreate, ChatTurnResponse
from app.features.chat.service import ChatService
from app.core.exceptions import EntityNotFoundException


router = APIRouter()


@router.get("/sessions", response_model=list[ChatSessionOut])
async def list_sessions(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    repo = ChatService(db).sessions
    return await repo.list_for_owner(current_user.id, skip=skip, limit=limit)


@router.post("/sessions", response_model=ChatSessionOut)
async def create_session(
    body: ChatSessionCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    svc = ChatService(db)
    sess = await svc.create_session(
        owner_user_id=current_user.id,
        character_id=body.character_id,
        room_id=body.room_id,
        title=body.title or "",
    )
    return sess


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    repo = ChatService(db).sessions
    sess = await repo.get_full(session_id)
    if not sess or sess.owner_user_id != current_user.id:
        raise EntityNotFoundException("ChatSession", session_id)
    return sess


@router.post("/sessions/{session_id}/turn", response_model=ChatTurnResponse)
async def create_turn(
    session_id: UUID,
    body: ChatTurnCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    svc = ChatService(db)
    result = await svc.generate_turn(owner_user_id=current_user.id, session_id=session_id, user_message=body.content)
    return {
        "session": result["session"],
        "user_turn": result["user_turn"],
        "assistant_turns": result["assistant_turns"],
        "memory_used": result["memory_used"],
    }
