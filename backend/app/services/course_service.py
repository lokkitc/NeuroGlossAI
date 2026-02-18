from __future__ import annotations

"""Сервис курса.

Отвечает за:
- генерацию шаблона курса через сервис модели
- создание записи курса пользователя и прогресса по уровням
- выдачу представления активного курса для клиента
- обновление прогресса и публикацию событий
"""

from typing import Any, Optional
import uuid
import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.models.user import User
from app.models.course_template import (
    CourseTemplate,
    CourseSectionTemplate,
    CourseUnitTemplate,
    CourseLevelTemplate,
)
from app.models.enrollment import Enrollment
from app.models.progress import UserLevelProgress, ProgressStatus
from app.models.attempts import UserLevelAttempt
from app.services.ai_service import ai_service
from app.core.events.base import event_bus, LevelCompletedEvent

logger = logging.getLogger(__name__)


_slug_safe_re = re.compile(r"[^a-z0-9]+")


def _slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = _slug_safe_re.sub("_", value).strip("_")
    return value or "course"


class CourseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_enrollment(self, user_id: uuid.UUID) -> Enrollment | None:
        query = (
            select(Enrollment)
            .where(Enrollment.user_id == user_id)
            .where(Enrollment.status == "active")
            .order_by(Enrollment.created_at.desc())
            .options(selectinload(Enrollment.course_template))
            .limit(1)
        )
        res = await self.db.execute(query)
        return res.scalars().first()

    async def get_course_template_full(self, course_template_id: uuid.UUID) -> CourseTemplate | None:
        query = (
            select(CourseTemplate)
            .where(CourseTemplate.id == course_template_id)
            .options(
                selectinload(CourseTemplate.sections)
                .selectinload(CourseSectionTemplate.units)
                .selectinload(CourseUnitTemplate.levels)
            )
        )
        res = await self.db.execute(query)
        return res.scalars().first()

    async def _create_standard_levels_for_unit(self, unit_template: CourseUnitTemplate) -> list[CourseLevelTemplate]:
        levels: list[CourseLevelTemplate] = []
        levels.append(
            CourseLevelTemplate(
                unit_template_id=unit_template.id,
                order=1,
                type="lesson",
                total_steps=5,
            )
        )
        levels.append(
            CourseLevelTemplate(
                unit_template_id=unit_template.id,
                order=2,
                type="lesson",
                total_steps=5,
            )
        )
        levels.append(
            CourseLevelTemplate(
                unit_template_id=unit_template.id,
                order=3,
                type="practice",
                total_steps=10,
            )
        )
        levels.append(
            CourseLevelTemplate(
                unit_template_id=unit_template.id,
                order=4,
                type="trophy",
                total_steps=15,
            )
        )
        self.db.add_all(levels)
        await self.db.flush()
        return levels

    async def generate_course_for_user(
        self,
        user: User,
        interests: list[str] | None = None,
        theme: str | None = None,
        level: str = "A1",
        regenerate: bool = True,
    ) -> Enrollment:
        interests = interests or []

        if regenerate:
            # Архивируем предыдущие записи курса (историю сохраняем)
            existing = await self.db.execute(
                select(Enrollment).where(Enrollment.user_id == user.id).where(Enrollment.status == "active")
            )
            for enr in existing.scalars().all():
                enr.status = "archived"
                self.db.add(enr)
            await self.db.commit()

        interests_str = ", ".join(interests) if interests else "General"
        theme_str = str(theme).strip() if theme else interests_str
        ai_data = await ai_service.generate_course_path(
            target_language=user.target_language,
            native_language=user.native_language,
            level=level,
            interests=interests_str,
            theme=theme_str,
            db=self.db,
        )
        sections_data = ai_data.get("sections", [])

        course = CourseTemplate(
            slug=_slugify(f"{user.id}_{user.target_language}_{level}_{theme_str}"),
            created_by_user_id=user.id,
            target_language=user.target_language,
            theme=theme_str,
            cefr_level=level,
            version=1,
            is_active=True,
            interests=interests,
        )
        self.db.add(course)
        await self.db.flush()

        first_level_template_id: uuid.UUID | None = None

        for sec in sections_data:
            section = CourseSectionTemplate(
                course_template_id=course.id,
                order=sec.get("order", 1),
                title=sec.get("title", "Section"),
                description=sec.get("description", ""),
            )
            self.db.add(section)
            await self.db.flush()

            for unit_data in sec.get("units", []) or []:
                unit = CourseUnitTemplate(
                    section_template_id=section.id,
                    order=unit_data.get("order", 1),
                    topic=unit_data.get("topic", "Topic"),
                    description=unit_data.get("description", ""),
                    icon=unit_data.get("icon", "📚"),
                )
                self.db.add(unit)
                await self.db.flush()

                created_levels = await self._create_standard_levels_for_unit(unit)
                if first_level_template_id is None and created_levels:
                    first_level_template_id = created_levels[0].id

        enrollment = Enrollment(user_id=user.id, course_template_id=course.id, status="active")
        self.db.add(enrollment)
        await self.db.flush()

        # Создаём строки прогресса для всех шаблонов уровней
        course_full = await self.get_course_template_full(course.id)
        assert course_full is not None

        progress_rows: list[UserLevelProgress] = []
        for section in course_full.sections:
            for unit in section.units:
                for lvl in unit.levels:
                    status = ProgressStatus.LOCKED.value
                    if first_level_template_id is not None and lvl.id == first_level_template_id:
                        status = ProgressStatus.IN_PROGRESS.value
                    progress_rows.append(
                        UserLevelProgress(
                            enrollment_id=enrollment.id,
                            level_template_id=lvl.id,
                            status=status,
                            stars=0,
                        )
                    )

        self.db.add_all(progress_rows)
        await self.db.commit()
        await self.db.refresh(enrollment)
        return enrollment

    async def get_active_course_view(self, user: User) -> dict[str, Any] | None:
        enrollment = await self.get_active_enrollment(user.id)
        if not enrollment:
            return None

        course = await self.get_course_template_full(enrollment.course_template_id)
        if not course:
            return None

        progress_res = await self.db.execute(
            select(UserLevelProgress).where(UserLevelProgress.enrollment_id == enrollment.id)
        )
        progresses = progress_res.scalars().all()
        progress_by_level = {p.level_template_id: p for p in progresses}

        sections_out: list[dict[str, Any]] = []
        for sec in course.sections:
            units_out: list[dict[str, Any]] = []
            for unit in sec.units:
                levels_out: list[dict[str, Any]] = []
                for lvl in unit.levels:
                    p = progress_by_level.get(lvl.id)
                    levels_out.append(
                        {
                            "id": lvl.id,
                            "order": lvl.order,
                            "type": lvl.type,
                            "total_steps": lvl.total_steps,
                            "status": (p.status if p else ProgressStatus.LOCKED.value),
                            "stars": (p.stars if p else 0),
                        }
                    )
                units_out.append(
                    {
                        "id": unit.id,
                        "order": unit.order,
                        "topic": unit.topic,
                        "description": unit.description,
                        "icon": unit.icon,
                        "levels": levels_out,
                    }
                )
            sections_out.append(
                {
                    "id": sec.id,
                    "order": sec.order,
                    "title": sec.title,
                    "description": sec.description,
                    "units": units_out,
                }
            )

        return {
            "enrollment_id": enrollment.id,
            "course_template_id": course.id,
            "target_language": course.target_language,
            "theme": course.theme,
            "cefr_level": course.cefr_level,
            "sections": sections_out,
        }

    async def update_progress(
        self,
        user: User,
        level_template_id: uuid.UUID,
        status: Optional[str] = None,
        stars: Optional[int] = None,
        xp_gained: Optional[int] = None,
    ) -> dict[str, Any] | None:
        enrollment = await self.get_active_enrollment(user.id)
        if not enrollment:
            return None

        res = await self.db.execute(
            select(UserLevelProgress)
            .where(UserLevelProgress.enrollment_id == enrollment.id)
            .where(UserLevelProgress.level_template_id == level_template_id)
        )
        progress = res.scalars().first()
        if not progress:
            return None

        if status is not None:
            progress.status = status
        if stars is not None:
            progress.stars = stars

        self.db.add(progress)

        # Track attempt (best-effort): store a row for analytics/audit.
        attempt = UserLevelAttempt(
            enrollment_id=enrollment.id,
            level_template_id=level_template_id,
            progress_id=progress.id,
            finished_at=(datetime.utcnow() if status == ProgressStatus.COMPLETED.value else None),
            stars=stars,
            xp_gained=xp_gained,
        )
        self.db.add(attempt)

        # XP via event bus (reuse existing listener)
        if status == ProgressStatus.COMPLETED.value and xp_gained:
            event = LevelCompletedEvent(
                user_id=user.id,
                level_id=level_template_id,
                xp_earned=xp_gained,
                stars=stars or 0,
            )
            await event_bus.publish(event, self.db)
            await self.db.refresh(user)

        next_unlocked = False
        if status == ProgressStatus.COMPLETED.value:
            # Unlock next level in same unit
            lvl_res = await self.db.execute(select(CourseLevelTemplate).where(CourseLevelTemplate.id == level_template_id))
            lvl = lvl_res.scalars().first()
            if lvl:
                next_lvl_res = await self.db.execute(
                    select(CourseLevelTemplate)
                    .where(CourseLevelTemplate.unit_template_id == lvl.unit_template_id)
                    .where(CourseLevelTemplate.order == lvl.order + 1)
                )
                next_lvl = next_lvl_res.scalars().first()
                if not next_lvl:
                    # Если последний уровень в уните то разблокируем следующий унит
                    unit_res = await self.db.execute(
                        select(CourseUnitTemplate).where(CourseUnitTemplate.id == lvl.unit_template_id)
                    )
                    unit = unit_res.scalars().first()

                    next_unit = None
                    if unit is not None:
                        next_unit_res = await self.db.execute(
                            select(CourseUnitTemplate)
                            .where(CourseUnitTemplate.section_template_id == unit.section_template_id)
                            .where(CourseUnitTemplate.order == unit.order + 1)
                        )
                        next_unit = next_unit_res.scalars().first()

                        if next_unit is None:
                            sec_res = await self.db.execute(
                                select(CourseSectionTemplate).where(
                                    CourseSectionTemplate.id == unit.section_template_id
                                )
                            )
                            sec = sec_res.scalars().first()
                            if sec is not None:
                                next_sec_res = await self.db.execute(
                                    select(CourseSectionTemplate)
                                    .where(CourseSectionTemplate.course_template_id == sec.course_template_id)
                                    .where(CourseSectionTemplate.order == sec.order + 1)
                                )
                                next_sec = next_sec_res.scalars().first()
                                if next_sec is not None:
                                    next_unit_res = await self.db.execute(
                                        select(CourseUnitTemplate)
                                        .where(CourseUnitTemplate.section_template_id == next_sec.id)
                                        .order_by(CourseUnitTemplate.order)
                                        .limit(1)
                                    )
                                    next_unit = next_unit_res.scalars().first()

                    if next_unit is not None:
                        next_lvl_res = await self.db.execute(
                            select(CourseLevelTemplate)
                            .where(CourseLevelTemplate.unit_template_id == next_unit.id)
                            .where(CourseLevelTemplate.type == 'lesson')
                            .order_by(CourseLevelTemplate.order)
                            .limit(1)
                        )
                        next_lvl = next_lvl_res.scalars().first()

                if next_lvl:
                    next_prog_res = await self.db.execute(
                        select(UserLevelProgress)
                        .where(UserLevelProgress.enrollment_id == enrollment.id)
                        .where(UserLevelProgress.level_template_id == next_lvl.id)
                    )
                    next_prog = next_prog_res.scalars().first()
                    if next_prog and next_prog.status == ProgressStatus.LOCKED.value:
                        next_prog.status = ProgressStatus.IN_PROGRESS.value
                        self.db.add(next_prog)
                        next_unlocked = True

        await self.db.commit()
        return {
            "status": "success",
            "level_template_id": str(level_template_id),
            "new_status": progress.status,
            "user_total_xp": user.xp,
            "next_level_unlocked": next_unlocked,
        }
