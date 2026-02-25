from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api import deps
from app.features.users.models import User
from app.core.exceptions import EntityNotFoundException
from app.features.chat.repository import ChatSessionRepository
from app.features.chat_learning.repository import ChatLearningLessonRepository
from app.features.chat_learning.schemas import ChatLearningLessonOut, ChatLearningGenerateRequest
from app.features.chat_learning.service import ChatLearningService


router = APIRouter()


@router.get("/sessions/{session_id}/learning/lessons", response_model=list[ChatLearningLessonOut])
async def list_learning_lessons(
    session_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    sess = await ChatSessionRepository(db).get(session_id)
    if not sess or sess.owner_user_id != current_user.id:
        raise EntityNotFoundException("ChatSession", session_id)

    repo = ChatLearningLessonRepository(db)
    return await repo.list_for_session(current_user.id, session_id, skip=skip, limit=limit)


@router.post("/sessions/{session_id}/learning/lessons", response_model=ChatLearningLessonOut)
async def generate_learning_lesson(
    session_id: UUID,
    body: ChatLearningGenerateRequest,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    svc = ChatLearningService(db)
    return await svc.generate_lesson_for_session(
        owner_user_id=current_user.id,
        chat_session_id=session_id,
        turn_window=body.turn_window,
        generation_mode=str(body.generation_mode or "balanced"),
    )
