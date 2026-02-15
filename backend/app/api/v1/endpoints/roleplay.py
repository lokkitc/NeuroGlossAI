from typing import Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.api import deps
from app.services.learning_service import LearningService
from app.models.user import User

router = APIRouter()

class ChatRequest(BaseModel):
    scenario: str
    role: str
    message: str
    history: list = []
    target_language: str
    level: str

@router.post("/chat")
async def chat_roleplay(
    chat_in: ChatRequest,
    current_user: User = Depends(deps.get_current_user),
    service: LearningService = Depends(deps.get_learning_service)
) -> Any:
    # Явная обработка ошибок не требуется, Глобальный Обработчик перехватит исключения Сервиса
    response_text = await service.process_roleplay_message(
        scenario=chat_in.scenario,
        role=chat_in.role,
        message=chat_in.message,
        history=chat_in.history,
        target_language=chat_in.target_language,
        level=chat_in.level
    )
    return {"response": response_text}
