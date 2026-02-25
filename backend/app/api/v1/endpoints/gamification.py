from typing import Any
from fastapi import APIRouter, Depends
from app.api import deps
from app.features.users.models import User

router = APIRouter()

@router.post("/buy-freeze")
async def buy_freeze(
    current_user: User = Depends(deps.get_current_user)
) -> Any:
                                      
                                                                                                    
    return {"status": "success", "message": "Streak freeze bought (simulation)"}
