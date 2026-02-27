from __future__ import annotations

from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import NeuroGlossException
from app.features.common.db import begin_if_needed
from app.features.users.models import User
from app.features.users.schemas import UserUpdateLanguages, UserUpdate
from app.features.user_progress.models import Streak, Enrollment, UserLevelProgress, UserLevelAttempt
from app.features.lessons.models import GeneratedLesson, GeneratedVocabularyItem
from app.features.srs.models import LessonLexeme, UserLexeme
from app.features.course.models import CourseTemplate, CourseSectionTemplate, CourseUnitTemplate


def _normalize_storageapi_url(value: Any) -> Any:
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    url = value.strip()
    if not url:
        return None
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        host = parsed.netloc
        if not host.endswith("storageapi.dev"):
            return url
        parts = host.split(".")
        if len(parts) < 3:
            return url
        bucket = parts[0]
        base_host = ".".join(parts[1:])
        path = parsed.path or ""
        if not path.startswith("/"):
            path = f"/{path}"
        if path.startswith(f"/{bucket}/"):
            return url
        fixed = f"{parsed.scheme or 'https'}://{base_host}/{bucket}{path}"
        if parsed.query:
            fixed = f"{fixed}?{parsed.query}"
        return fixed
    except Exception:
        return url


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_languages(self, *, current_user: User, languages: UserUpdateLanguages) -> User:
        async with begin_if_needed(self.db):
            current_user.target_language = languages.target_language
            current_user.native_language = languages.native_language
            self.db.add(current_user)

        await self.db.refresh(current_user)
        return current_user

    async def export_user_data(self, *, current_user: User) -> dict[str, Any]:
        if not settings.ENABLE_USER_EXPORT:
            raise NeuroGlossException(status_code=404, code="not_found", detail="Not Found")

        streaks_result = await self.db.execute(select(Streak).where(Streak.user_id == current_user.id))
        streaks = streaks_result.scalars().all()

        enrollments_result = await self.db.execute(
            select(Enrollment)
            .where(Enrollment.user_id == current_user.id)
            .order_by(Enrollment.created_at.desc())
        )
        enrollments = enrollments_result.scalars().all()

        enrollment_ids = [e.id for e in enrollments]
        course_template_ids = [e.course_template_id for e in enrollments]

        templates = []
        if course_template_ids:
            templates_result = await self.db.execute(
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
            progresses_result = await self.db.execute(
                select(UserLevelProgress).where(UserLevelProgress.enrollment_id.in_(enrollment_ids))
            )
            progresses = progresses_result.scalars().all()

        generated_lessons = []
        if enrollment_ids:
            generated_lessons_result = await self.db.execute(
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

    async def reset_progress(self, *, current_user: User) -> User:
        async with begin_if_needed(self.db):
            enrollments = await self.db.execute(select(Enrollment).where(Enrollment.user_id == current_user.id))
            enrollments = enrollments.scalars().all()
            enrollment_ids = [e.id for e in enrollments]

            if enrollment_ids:
                glessons = await self.db.execute(
                    select(GeneratedLesson).where(GeneratedLesson.enrollment_id.in_(enrollment_ids))
                )
                glessons = glessons.scalars().all()
                glesson_ids = [l.id for l in glessons]

                if glesson_ids:
                    await self.db.execute(delete(LessonLexeme).where(LessonLexeme.generated_lesson_id.in_(glesson_ids)))
                    await self.db.execute(
                        delete(GeneratedVocabularyItem).where(GeneratedVocabularyItem.generated_lesson_id.in_(glesson_ids))
                    )
                    await self.db.execute(delete(GeneratedLesson).where(GeneratedLesson.id.in_(glesson_ids)))

                await self.db.execute(delete(UserLexeme).where(UserLexeme.enrollment_id.in_(enrollment_ids)))

                await self.db.execute(delete(UserLevelAttempt).where(UserLevelAttempt.enrollment_id.in_(enrollment_ids)))
                await self.db.execute(delete(UserLevelProgress).where(UserLevelProgress.enrollment_id.in_(enrollment_ids)))
                await self.db.execute(delete(Enrollment).where(Enrollment.id.in_(enrollment_ids)))

            current_user.language_levels = {}
            self.db.add(current_user)

        await self.db.refresh(current_user)
        return current_user

    async def update_me(self, *, current_user: User, body: UserUpdate) -> User:
        update_data = body.model_dump(exclude_unset=True)

        if "avatar_url" in update_data:
            update_data["avatar_url"] = _normalize_storageapi_url(update_data.get("avatar_url"))
        if "thumbnail_url" in update_data:
            update_data["thumbnail_url"] = _normalize_storageapi_url(update_data.get("thumbnail_url"))
        if "banner_url" in update_data:
            update_data["banner_url"] = _normalize_storageapi_url(update_data.get("banner_url"))

        async with begin_if_needed(self.db):
            for field, value in update_data.items():
                if hasattr(current_user, field):
                    setattr(current_user, field, value)
            self.db.add(current_user)

        await self.db.refresh(current_user)
        return current_user
