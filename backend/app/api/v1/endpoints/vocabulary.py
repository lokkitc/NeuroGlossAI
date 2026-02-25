from typing import Any, List
from fastapi import APIRouter, Depends

from app.api import deps
from app.features.users.models import User
from app.features.vocabulary.schemas import VocabularyReviewRequest, VocabularyItemResponse
from app.features.learning.service import LearningService
from app.core.exceptions import EntityNotFoundException

router = APIRouter()

@router.get("/daily-review", response_model=List[VocabularyItemResponse])
async def get_daily_review(
    current_user: User = Depends(deps.get_current_user),
    service: LearningService = Depends(deps.get_learning_service)
) -> Any:
    return await service.get_daily_review_items(current_user.id)

@router.post("/review")
async def review_word(
    review_in: VocabularyReviewRequest,
    current_user: User = Depends(deps.get_current_user),
    service: LearningService = Depends(deps.get_learning_service)
) -> Any:
    result = await service.process_vocabulary_review(current_user.id, review_in)
    if not result:
        raise EntityNotFoundException(entity_name="VocabularyItem", entity_id=review_in.vocabulary_id)
    return result
