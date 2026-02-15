"""Эндпойнты профиля пользователя.

Содержит:
- обновление языков
- экспорт данных
- сброс прогресса
- частичное обновление профиля
"""

from typing import Any
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload
from app.api import deps
from app.schemas.user import UserResponse, UserUpdateLanguages, UserUpdate
from app.models.user import User
from app.models.streak import Streak
from app.models.enrollment import Enrollment
from app.models.course_template import CourseTemplate, CourseSectionTemplate, CourseUnitTemplate, CourseLevelTemplate
from app.models.progress import UserLevelProgress
from app.models.generated_content import GeneratedLesson, GeneratedVocabularyItem
from app.models.srs import LessonLexeme, UserLexeme

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
async def export_user_data(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """Полный экспорт данных пользователя одним объектом (для отладки и бэкапа)."""

    streaks_result = await db.execute(select(Streak).where(Streak.user_id == current_user.id))
    streaks = streaks_result.scalars().all()

    # Долгосрочная модель (шаблоны курса + записи курса + прогресс + сгенерированный контент)
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
    # Контент долгосрочной модели: словарь -> уроки -> прогресс -> записи курса
    enrollments = await db.execute(select(Enrollment).where(Enrollment.user_id == current_user.id))
    enrollments = enrollments.scalars().all()
    enrollment_ids = [e.id for e in enrollments]
    course_template_ids = [e.course_template_id for e in enrollments]

    if enrollment_ids:
        # Словарь зависит от уроков
        glessons = await db.execute(select(GeneratedLesson).where(GeneratedLesson.enrollment_id.in_(enrollment_ids)))
        glessons = glessons.scalars().all()
        glesson_ids = [l.id for l in glessons]

        if glesson_ids:
            # Удаляем связи урока со словарём (таблица lesson_lexemes), иначе FK не даст удалить урок.
            await db.execute(delete(LessonLexeme).where(LessonLexeme.generated_lesson_id.in_(glesson_ids)))
            await db.execute(delete(GeneratedVocabularyItem).where(GeneratedVocabularyItem.generated_lesson_id.in_(glesson_ids)))
            await db.execute(delete(GeneratedLesson).where(GeneratedLesson.id.in_(glesson_ids)))

        # Удаляем привязки слов пользователя к записям курса, иначе FK не даст удалить enrollment.
        await db.execute(delete(UserLexeme).where(UserLexeme.enrollment_id.in_(enrollment_ids)))

        await db.execute(delete(UserLevelProgress).where(UserLevelProgress.enrollment_id.in_(enrollment_ids)))
        await db.execute(delete(Enrollment).where(Enrollment.id.in_(enrollment_ids)))

    # Шаблоны, созданные специально для пользователя, тоже можно удалить (по возможности)
    if course_template_ids:
        # Удаляем снизу вверх
        await db.execute(delete(CourseLevelTemplate).where(CourseLevelTemplate.unit_template_id.in_(
            select(CourseUnitTemplate.id).where(CourseUnitTemplate.section_template_id.in_(
                select(CourseSectionTemplate.id).where(CourseSectionTemplate.course_template_id.in_(course_template_ids))
            ))
        )))
        await db.execute(delete(CourseUnitTemplate).where(CourseUnitTemplate.section_template_id.in_(
            select(CourseSectionTemplate.id).where(CourseSectionTemplate.course_template_id.in_(course_template_ids))
        )))
        await db.execute(delete(CourseSectionTemplate).where(CourseSectionTemplate.course_template_id.in_(course_template_ids)))
        await db.execute(delete(CourseTemplate).where(CourseTemplate.id.in_(course_template_ids)))

    # Сбрасываем карту уровней языка (так как контент удалён), но сохраняем опыт
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
        # Проверка уникальности, если email меняется (опущено для краткости)
        current_user.email = user_in.email
    
    if user_in.username:
        current_user.username = user_in.username
        
    if user_in.target_language:
        current_user.target_language = user_in.target_language
        
    if user_in.native_language:
        current_user.native_language = user_in.native_language

    # Обработка прочих полей (например ссылка на аватар), если они добавлены в модель
    
    await db.commit()
    await db.refresh(current_user)
    return current_user
