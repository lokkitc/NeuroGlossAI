"""Эндпойнты профиля пользователя.

Содержит:
- обновление языков
- экспорт данных
- сброс прогресса
- частичное обновление профиля
"""

from typing import Any
from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload
from app.api import deps
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.exceptions import NeuroGlossException
from app.features.users.schemas import UserResponse, UserUpdateLanguages, UserUpdate
from app.features.users.models import User
from app.features.user_progress.models import Streak, Enrollment, UserLevelProgress, UserLevelAttempt
from app.features.lessons.models import GeneratedLesson, GeneratedVocabularyItem
from app.features.srs.models import LessonLexeme, UserLexeme
from app.features.course.models import CourseTemplate, CourseSectionTemplate, CourseUnitTemplate

router = APIRouter()

@router.put("/me/languages", response_model=UserResponse)
async def update_languages(
    languages: UserUpdateLanguages,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Обновление родного и целевого языков пользователя (Текущий курс).
    """
    current_user.target_language = languages.target_language
    current_user.native_language = languages.native_language
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get("/me/export")
@limiter.limit("2/minute")
async def export_user_data(
    request: Request,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """Полный экспорт данных пользователя одним объектом (для отладки и бэкапа)."""

    if not settings.ENABLE_USER_EXPORT:
        raise NeuroGlossException(status_code=404, detail="Not Found")

    streaks_result = await db.execute(select(Streak).where(Streak.user_id == current_user.id))
    streaks = streaks_result.scalars().all()

                                                                                             
    enrollments_result = await db.execute(
        select(Enrollment)
        .where(Enrollment.user_id == current_user.id)
        .order_by(Enrollment.created_at.desc())
    )
    enrollments = enrollments_result.scalars().all()

    enrollment_ids = [e.id for e in enrollments]
    course_template_ids = [e.course_template_id for e in enrollments]

    templates = []
    if course_template_ids:
        templates_result = await db.execute(
            select(CourseTemplate)
            .options(
                selectinload(CourseTemplate.sections)
                .selectinload(CourseSectionTemplate.units)
                .selectinload(CourseUnitTemplate.levels)
            )
            .where(CourseTemplate.id.in_(course_template_ids))
        )
        templates = templates_result.scalars().all()

    progresses = []
    if enrollment_ids:
        progresses_result = await db.execute(
            select(UserLevelProgress).where(UserLevelProgress.enrollment_id.in_(enrollment_ids))
        )
        progresses = progresses_result.scalars().all()

    generated_lessons = []
    if enrollment_ids:
        generated_lessons_result = await db.execute(
            select(GeneratedLesson)
            .options(selectinload(GeneratedLesson.vocabulary_items))
            .where(GeneratedLesson.enrollment_id.in_(enrollment_ids))
            .order_by(GeneratedLesson.created_at.desc())
        )
        generated_lessons = generated_lessons_result.scalars().all()

    return {
        "user": jsonable_encoder(current_user, exclude={"hashed_password"}),
        "streaks": jsonable_encoder(streaks),
        "lessons": [],
        "path": [],
        "enrollments": jsonable_encoder(enrollments),
        "course_templates": jsonable_encoder(templates),
        "progress": jsonable_encoder(progresses),
        "generated_lessons": jsonable_encoder(generated_lessons),
    }

@router.post("/me/reset", response_model=UserResponse)
async def reset_progress(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Сброс контента пользователя: удаляет активные записи курса пользователя, прогресс, сгенерированные уроки и словарь.
    Не сбрасывает опыт или общую статистику геймификации (как запрошено).
    """
                                                                               
    enrollments = await db.execute(select(Enrollment).where(Enrollment.user_id == current_user.id))
    enrollments = enrollments.scalars().all()
    enrollment_ids = [e.id for e in enrollments]

    if enrollment_ids:
                                   
        glessons = await db.execute(select(GeneratedLesson).where(GeneratedLesson.enrollment_id.in_(enrollment_ids)))
        glessons = glessons.scalars().all()
        glesson_ids = [l.id for l in glessons]

        if glesson_ids:
                                                                                                      
            await db.execute(delete(LessonLexeme).where(LessonLexeme.generated_lesson_id.in_(glesson_ids)))
            await db.execute(delete(GeneratedVocabularyItem).where(GeneratedVocabularyItem.generated_lesson_id.in_(glesson_ids)))
            await db.execute(delete(GeneratedLesson).where(GeneratedLesson.id.in_(glesson_ids)))

                                                                                                  
        await db.execute(delete(UserLexeme).where(UserLexeme.enrollment_id.in_(enrollment_ids)))

                                                                                       
        await db.execute(delete(UserLevelAttempt).where(UserLevelAttempt.enrollment_id.in_(enrollment_ids)))
        await db.execute(delete(UserLevelProgress).where(UserLevelProgress.enrollment_id.in_(enrollment_ids)))
        await db.execute(delete(Enrollment).where(Enrollment.id.in_(enrollment_ids)))

                                                 
                                                                                                                        

                                                                                
    current_user.language_levels = {} 
    
    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    Частичное обновление собственного профиля пользователя.
    Используйте это для настроек, информации о профиле и т.д.
    """
    if user_in.email:
                                                                            
        current_user.email = user_in.email
    
    if user_in.username:
        current_user.username = user_in.username
        
    if user_in.target_language:
        current_user.target_language = user_in.target_language
        
    if user_in.native_language:
        current_user.native_language = user_in.native_language

    if user_in.avatar_url is not None:
        current_user.avatar_url = user_in.avatar_url

    if user_in.thumbnail_url is not None:
        current_user.thumbnail_url = user_in.thumbnail_url

    if user_in.banner_url is not None:
        current_user.banner_url = user_in.banner_url

    if user_in.preferred_name is not None:
        current_user.preferred_name = user_in.preferred_name

    if user_in.bio is not None:
        current_user.bio = user_in.bio

    if user_in.timezone is not None:
        current_user.timezone = user_in.timezone

    if user_in.ui_theme is not None:
        current_user.ui_theme = user_in.ui_theme

    if user_in.assistant_tone is not None:
        current_user.assistant_tone = user_in.assistant_tone

    if user_in.assistant_verbosity is not None:
        current_user.assistant_verbosity = user_in.assistant_verbosity

    if user_in.preferences is not None:
        current_user.preferences = user_in.preferences

    if user_in.interests is not None:
        current_user.interests = user_in.interests

                                                                                     
    
    await db.commit()
    await db.refresh(current_user)
    return current_user
