from typing import Any, List, Optional, Dict
import asyncio
import re
from fastapi import APIRouter, Depends, Body, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.schemas.course import ActiveCourseResponse, CourseGenerateRequest, ProgressUpdateRequest
from app.services.course_service import CourseService
from app.services.learning_service import LearningService
from app.core.exceptions import EntityNotFoundException, ServiceException

router = APIRouter()

"""Эндпойнты курса (path).

Содержит:
- получение активного курса
- генерацию курса по интересам
- полную генерацию (курс + несколько уроков)
- повтор генерации уроков/частей урока
"""

class FullCourseGenerationRequest(BaseModel):
    interests: List[str] = []
    theme: str | None = None
    level: str = "A1"
    max_topics: int = 3
    sleep_seconds: float = 0.0
    regenerate_path: bool = True
    force_regenerate_lessons: bool = False
    generation_mode: str = "balanced"


class RetryLessonsRequest(BaseModel):
    level_template_ids: List[str] = []
    # Если задано, используется для регенерации
    level: str = "A1"
    topic_by_level_template_id: Optional[Dict[str, str]] = None
    sleep_seconds: float = 0.0
    mode: str = "full"  # полный | основа | упражнения
    generation_mode: str = "balanced"


@router.get("/", response_model=ActiveCourseResponse)
async def get_user_path(
    current_user: User = Depends(deps.get_current_user),
    service: CourseService = Depends(deps.get_course_service)
) -> Any:
    """
    Получить активный курс (template + progress) для текущего пользователя.
    """
    data = await service.get_active_course_view(current_user)
    if not data:
        raise EntityNotFoundException(entity_name="Enrollment", entity_id="active")
    return data

@router.post("/generate", response_model=ActiveCourseResponse)
async def generate_user_path(
    request: Request,
    body: CourseGenerateRequest = Body(
        default=CourseGenerateRequest(),
        examples={
            "themed": {
                "summary": "Themed course generation",
                "value": {
                    "interests": [],
                    "theme": "Mobile Legends Bang Bang",
                    "level": "A1",
                    "regenerate": True,
                },
            }
        },
    ),
    current_user: User = Depends(deps.get_current_user),
    service: CourseService = Depends(deps.get_course_service)
) -> Any:
    """
    Принудительная перегенерация курса пользователя с использованием ИИ.
    """
    await service.generate_course_for_user(
        user=current_user,
        interests=body.interests,
        theme=body.theme,
        level=body.level,
        regenerate=body.regenerate,
    )
    data = await service.get_active_course_view(current_user)
    if not data:
        raise EntityNotFoundException(entity_name="Enrollment", entity_id="active")
    return data


@router.post("/generate-full")
async def generate_full_course(
    request: Request,
    body: FullCourseGenerationRequest = Body(
        default=FullCourseGenerationRequest(),
        examples={
            "themed": {
                "summary": "Themed full generation (path + lessons)",
                "value": {
                    "interests": [],
                    "theme": "Mobile Legends Bang Bang",
                    "level": "A1",
                    "max_topics": 3,
                    "sleep_seconds": 0,
                    "regenerate_path": True,
                    "force_regenerate_lessons": False,
                    "generation_mode": "balanced",
                },
            }
        },
    ),
    current_user: User = Depends(deps.get_current_user),
    path_service: CourseService = Depends(deps.get_course_service),
    learning_service: LearningService = Depends(deps.get_learning_service),
) -> Any:
    """Один вызов, который генерирует курс целиком: курс + уроки.

    По умолчанию ограничивает генерацию уроков (лимит тем), чтобы не сжечь лимиты.
    """

    if body.max_topics < 1:
        return {"status": "skipped", "reason": "лимит тем должен быть >= 1"}

    if body.regenerate_path:
        await path_service.generate_course_for_user(
            user=current_user,
            interests=body.interests,
            theme=body.theme,
            level=body.level,
            regenerate=True,
        )

    enrollment = await path_service.get_active_enrollment(current_user.id)
    if not enrollment:
        raise EntityNotFoundException(entity_name="Enrollment", entity_id="active")

    course = await path_service.get_course_template_full(enrollment.course_template_id)
    if not course:
        raise EntityNotFoundException(entity_name="CourseTemplate", entity_id=enrollment.course_template_id)

    # Возвращаем: активный курс + сгенерированные уроки
    active = await path_service.get_active_course_view(current_user)

    lesson_targets: list[dict] = []
    for section in getattr(course, "sections", []) or []:
        for unit in getattr(section, "units", []) or []:
            topic = getattr(unit, "topic", None)
            if not topic:
                continue

            level_template_id = None
            for level_obj in getattr(unit, "levels", []) or []:
                if getattr(level_obj, "type", None) == "lesson" and getattr(level_obj, "order", None) == 1:
                    level_template_id = getattr(level_obj, "id", None)
                    break

            if level_template_id is None:
                continue

            lesson_targets.append({"topic": str(topic), "level_template_id": level_template_id})

    lesson_targets = lesson_targets[: body.max_topics]

    generated_lessons = []
    failed_topics: list[dict] = []
    needs_review_topics: list[dict] = []
    prior_topics: list[str] = []
    used_words: list[str] = []
    retry_after_seconds: float | None = None
    for idx, target in enumerate(lesson_targets):
        topic = target["topic"]
        level_template_id = target.get("level_template_id")
        try:
            lesson = await learning_service.create_generated_lesson_from_ai(
                enrollment=enrollment,
                user=current_user,
                level_template_id=level_template_id,
                topic=topic,
                level=body.level,
                prior_topics=prior_topics,
                used_words=used_words,
                force_regenerate=body.force_regenerate_lessons,
                generation_mode=str(body.generation_mode or "balanced"),
            )
            generated_lessons.append(lesson)

            if getattr(lesson, "quality_status", None) == "needs_review":
                needs_review_topics.append({"topic": topic, "reason": "exercises_unavailable"})

            prior_topics.append(topic)
            # Собираем использованные слова, чтобы снижать повторения между уроками
            for item in getattr(lesson, "vocabulary_items", []) or []:
                word = getattr(item, "word", None)
                if word:
                    used_words.append(str(word))
        except ServiceException as e:
            error_text = str(e)
            failed_topics.append({"topic": topic, "error": error_text})

            # Если провайдер исчерпал дневные лимиты, он может попросить повтор через много минут.
            # В этом случае останавливаем генерацию остальных тем, чтобы не тратить запросы.
            match = re.search(r"retry_after_seconds=([0-9]+)", error_text)
            if match:
                try:
                    retry_after_seconds = float(match.group(1))
                except ValueError:
                    retry_after_seconds = None

            if retry_after_seconds is not None and retry_after_seconds >= 120.0:
                break

        if body.sleep_seconds and idx < len(lesson_targets) - 1:
            await asyncio.sleep(body.sleep_seconds)

    status_value = "success" if not failed_topics else "partial_success"
    successful_topics = [getattr(l, "topic_snapshot", None) or "" for l in generated_lessons]
    successful_topics = [t for t in successful_topics if t]
    return {
        "status": status_value,
        "requested_topics": [t["topic"] for t in lesson_targets],
        "topics": successful_topics,
        "failed_topics": failed_topics,
        "needs_review_topics": needs_review_topics,
        "retry_after_seconds": retry_after_seconds,
        "course": jsonable_encoder(active),
        "lessons": jsonable_encoder(generated_lessons),
    }


@router.post("/retry-lessons")
async def retry_lessons(
    request: Request,
    body: RetryLessonsRequest = Body(default=RetryLessonsRequest()),
    current_user: User = Depends(deps.get_current_user),
    path_service: CourseService = Depends(deps.get_course_service),
    learning_service: LearningService = Depends(deps.get_learning_service),
) -> Any:
    enrollment = await path_service.get_active_enrollment(current_user.id)
    if not enrollment:
        raise EntityNotFoundException(entity_name="Enrollment", entity_id="active")

    if not body.level_template_ids:
        return {"status": "skipped", "reason": "level_template_ids is empty"}

    regenerated = []
    failed: list[dict] = []
    mode = (body.mode or "full").strip().lower()
    if mode not in {"full", "core", "exercises"}:
        mode = "full"

    generation_mode = str(body.generation_mode or "balanced")
    for idx, lvl_id in enumerate(body.level_template_ids):
        try:
            level_template_uuid = UUID(str(lvl_id))
            topic = None
            if isinstance(body.topic_by_level_template_id, dict):
                topic = body.topic_by_level_template_id.get(str(lvl_id))

            if mode == "full":
                lesson = await learning_service.create_generated_lesson_from_ai(
                    enrollment=enrollment,
                    user=current_user,
                    level_template_id=level_template_uuid,
                    topic=topic or "retry",
                    level=body.level,
                    force_regenerate=True,
                    generation_mode=generation_mode,
                )
                regenerated.append(lesson)
            elif mode == "core":
                existing = await learning_service.generated_repo.get_by_enrollment_and_level(
                    enrollment.id, level_template_uuid
                )
                if existing is None:
                    # Если урока ещё нет — откатываемся к полной генерации.
                    lesson = await learning_service.create_generated_lesson_from_ai(
                        enrollment=enrollment,
                        user=current_user,
                        level_template_id=level_template_uuid,
                        topic=topic or "retry",
                        level=body.level,
                        force_regenerate=True,
                        generation_mode=generation_mode,
                    )
                    regenerated.append(lesson)
                else:
                    lesson = await learning_service.regenerate_core_only(
                        lesson=existing,
                        user=current_user,
                        level=body.level,
                        generation_mode=generation_mode,
                    )
                    regenerated.append(lesson)
            else:  # exercises
                existing = await learning_service.generated_repo.get_by_enrollment_and_level(
                    enrollment.id, level_template_uuid
                )
                if existing is None:
                    lesson = await learning_service.create_generated_lesson_from_ai(
                        enrollment=enrollment,
                        user=current_user,
                        level_template_id=level_template_uuid,
                        topic=topic or "retry",
                        level=body.level,
                        force_regenerate=True,
                        generation_mode=generation_mode,
                    )
                    regenerated.append(lesson)
                else:
                    lesson = await learning_service.regenerate_exercises_only(
                        lesson=existing,
                        user=current_user,
                        generation_mode=generation_mode,
                    )
                    regenerated.append(lesson)
        except ServiceException as e:
            failed.append({"level_template_id": str(lvl_id), "error": str(e)})
        except ValueError as e:
            failed.append({"level_template_id": str(lvl_id), "error": f"invalid_uuid:{str(e)}"})

        if body.sleep_seconds and idx < len(body.level_template_ids) - 1:
            await asyncio.sleep(body.sleep_seconds)

    status_value = "success" if not failed else "partial_success"
    return {
        "status": status_value,
        "mode": mode,
        "generation_mode": generation_mode,
        "regenerated": jsonable_encoder(regenerated),
        "failed": failed,
    }

@router.patch("/progress", response_model=dict)
async def update_path_progress(
    update_data: ProgressUpdateRequest,
    current_user: User = Depends(deps.get_current_user),
    service: CourseService = Depends(deps.get_course_service)
) -> Any:
    """
    Инкрементальное обновление прогресса пути.
    """
    result = await service.update_progress(
        user=current_user,
        level_template_id=update_data.level_template_id,
        status=update_data.status,
        stars=update_data.stars,
        xp_gained=update_data.xp_gained,
    )
    if not result:
        raise EntityNotFoundException(entity_name="UserLevelProgress", entity_id=update_data.level_template_id)
    return result
