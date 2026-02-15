from typing import Any
from fastapi import APIRouter, Depends
from app.api import deps
from app.models.user import User

router = APIRouter()

@router.post("/buy-freeze")
async def buy_freeze(
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    # Заглушка для логики геймификации
    # В реальном приложении: проверить баланс камней, списать камни, установить streak.frozen = True
    return {"status": "success", "message": "Streak freeze bought (simulation)"}
