from typing import Any
from fastapi import APIRouter, Depends, Request, Body
from uuid import UUID
from pydantic import BaseModel

from app.api import deps
from app.services.learning_service import LearningService
from app.services.course_service import CourseService
from app.models.user import User
from app.schemas.generated_lesson import GeneratedLessonCreate, GeneratedLessonResponse
from app.core.exceptions import EntityNotFoundException, ServiceException
from app.core.rate_limit import limiter

router = APIRouter()


class RegenCoreRequest(BaseModel):
    level: str = "A1"
    generation_mode: str = "balanced"

@router.post("/generate", response_model=GeneratedLessonResponse)
@limiter.limit("5/minute")
async def generate_lesson(
    request: Request,
    lesson_in: GeneratedLessonCreate,
    current_user: User = Depends(deps.get_current_user),
    service: LearningService = Depends(deps.get_learning_service),
    course_service: CourseService = Depends(deps.get_course_service),
) -> Any:
    enrollment = await course_service.get_active_enrollment(current_user.id)
    if not enrollment:
        raise EntityNotFoundException(entity_name="Enrollment", entity_id="active")

    return await service.create_generated_lesson_from_ai(
        enrollment=enrollment,
        user=current_user,
        level_template_id=lesson_in.level_template_id,
        topic=lesson_in.topic,
        level=lesson_in.level,
        generation_mode=str(getattr(lesson_in, "generation_mode", "balanced") or "balanced"),
    )

@router.get("/", response_model=list[GeneratedLessonResponse])
async def get_lessons(
    current_user: User = Depends(deps.get_current_user),
    service: LearningService = Depends(deps.get_learning_service),
    course_service: CourseService = Depends(deps.get_course_service),
    skip: int = 0,
    limit: int = 10
) -> Any:
    enrollment = await course_service.get_active_enrollment(current_user.id)
    if not enrollment:
        return []
    return await service.get_user_generated_lessons(enrollment.id, skip, limit)

@router.get("/{id}", response_model=GeneratedLessonResponse)
async def get_lesson(
    id: UUID,
    current_user: User = Depends(deps.get_current_user),
    service: LearningService = Depends(deps.get_learning_service),
    course_service: CourseService = Depends(deps.get_course_service),
) -> Any:
    enrollment = await course_service.get_active_enrollment(current_user.id)
    if not enrollment:
        raise EntityNotFoundException(entity_name="Enrollment", entity_id="active")

    lesson = await service.get_generated_lesson_by_id(id, enrollment.id)
    if not lesson:
        raise EntityNotFoundException(entity_name="Lesson", entity_id=id)
    return lesson

@router.post("/{id}/complete")
async def complete_lesson(
    id: UUID,
    current_user: User = Depends(deps.get_current_user),
    service: LearningService = Depends(deps.get_learning_service),
    course_service: CourseService = Depends(deps.get_course_service),
) -> Any:
    """
    Пометить урок как завершенный.
    В настоящее время просто заглушка для потенциальной будущей логики (аналитика, верификация).
    Фактическое обновление прогресса происходит через /path/progress.
    """
    enrollment = await course_service.get_active_enrollment(current_user.id)
    if not enrollment:
        raise EntityNotFoundException(entity_name="Enrollment", entity_id="active")

    lesson = await service.get_generated_lesson_by_id(id, enrollment.id)
    if not lesson:
        raise EntityNotFoundException(entity_name="Lesson", entity_id=id)
    
    # В будущем мы могли бы пометить урок как завершенный в БД здесь.
    return {"status": "success", "message": "Lesson completed"}


@router.post("/{id}/regen-exercises", response_model=GeneratedLessonResponse)
@limiter.limit("5/minute")
async def regenerate_exercises(
    request: Request,
    id: UUID,
    current_user: User = Depends(deps.get_current_user),
    service: LearningService = Depends(deps.get_learning_service),
    course_service: CourseService = Depends(deps.get_course_service),
) -> Any:
    enrollment = await course_service.get_active_enrollment(current_user.id)
    if not enrollment:
        raise EntityNotFoundException(entity_name="Enrollment", entity_id="active")

    lesson = await service.get_generated_lesson_by_id(id, enrollment.id)
    if not lesson:
        raise EntityNotFoundException(entity_name="Lesson", entity_id=id)

    return await service.regenerate_exercises_only(lesson=lesson, user=current_user)


@router.post("/{id}/regen-core", response_model=GeneratedLessonResponse)
@limiter.limit("5/minute")
async def regenerate_core(
    request: Request,
    id: UUID,
    body: RegenCoreRequest = Body(default=RegenCoreRequest()),
    current_user: User = Depends(deps.get_current_user),
    service: LearningService = Depends(deps.get_learning_service),
    course_service: CourseService = Depends(deps.get_course_service),
) -> Any:
    enrollment = await course_service.get_active_enrollment(current_user.id)
    if not enrollment:
        raise EntityNotFoundException(entity_name="Enrollment", entity_id="active")

    lesson = await service.get_generated_lesson_by_id(id, enrollment.id)
    if not lesson:
        raise EntityNotFoundException(entity_name="Lesson", entity_id=id)

    return await service.regenerate_core_only(
        lesson=lesson,
        user=current_user,
        level=body.level,
        generation_mode=str(body.generation_mode or "balanced"),
    )
