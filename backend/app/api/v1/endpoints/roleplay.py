from typing import Any
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from app.api import deps
from app.features.learning.service import LearningService
from app.features.users.models import User
from app.core.rate_limit import limiter

router = APIRouter()

class ChatRequest(BaseModel):
    scenario: str
    role: str
    message: str
    history: list = []
    target_language: str
    level: str

@router.post("/chat")
@limiter.limit("20/minute")
async def chat_roleplay(
    request: Request,
    chat_in: ChatRequest,
    current_user: User = Depends(deps.get_current_user),
    service: LearningService = Depends(deps.get_learning_service)
) -> Any:
                                                                                              
    response_text = await service.process_roleplay_message(
        scenario=chat_in.scenario,
        role=chat_in.role,
        message=chat_in.message,
        history=chat_in.history,
        target_language=chat_in.target_language,
        level=chat_in.level
    )
    return {"response": response_text}
