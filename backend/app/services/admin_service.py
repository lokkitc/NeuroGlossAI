from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import EntityNotFoundException
from app.models.enrollment import Enrollment
from app.models.user import User
from app.repositories.admin_user import AdminUserRepository
from app.repositories.admin_generated_lesson import AdminGeneratedLessonRepository
from app.services.learning_service import LearningService


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users_repo = AdminUserRepository(db)
        self.lessons_repo = AdminGeneratedLessonRepository(db)
        self.learning_service = LearningService(db)

    async def list_users(self, *, skip: int = 0, limit: int = 50) -> list[dict]:
        users = await self.users_repo.list_users(skip=skip, limit=limit)
        return [
            {
                "id": str(u.id),
                "username": u.username,
                "email": u.email,
                "is_admin": bool(getattr(u, "is_admin", False)),
                "xp": getattr(u, "xp", 0),
                "native_language": getattr(u, "native_language", None),
                "target_language": getattr(u, "target_language", None),
                "created_at": (u.created_at.isoformat() if getattr(u, "created_at", None) else None),
            }
            for u in users
        ]

    async def set_user_admin(self, *, user_id: UUID, is_admin: bool) -> dict:
        user = await self.users_repo.get_by_id(user_id=user_id)
        if user is None:
            raise EntityNotFoundException(entity_name="User", entity_id=str(user_id))
        user.is_admin = bool(is_admin)
        await self.db.commit()
        await self.db.refresh(user)
        return {"id": str(user.id), "is_admin": bool(user.is_admin)}

    async def list_generated_lessons(self, *, skip: int = 0, limit: int = 50) -> list[dict]:
        lessons = await self.lessons_repo.list_lessons(skip=skip, limit=limit)
        return [
            {
                "id": str(l.id),
                "enrollment_id": str(l.enrollment_id),
                "level_template_id": str(l.level_template_id),
                "topic_snapshot": l.topic_snapshot,
                "quality_status": l.quality_status,
                "repair_count": l.repair_count,
                "created_at": (l.created_at.isoformat() if getattr(l, "created_at", None) else None),
            }
            for l in lessons
        ]

    async def get_generated_lesson(self, *, lesson_id: UUID) -> dict:
        lesson = await self.lessons_repo.get_by_id(lesson_id=lesson_id)
        if lesson is None:
            raise EntityNotFoundException(entity_name="GeneratedLesson", entity_id=str(lesson_id))

        return {
            "id": str(lesson.id),
            "enrollment_id": str(lesson.enrollment_id),
            "level_template_id": str(lesson.level_template_id),
            "topic_snapshot": lesson.topic_snapshot,
            "prompt_version": lesson.prompt_version,
            "provider": lesson.provider,
            "model": lesson.model,
            "quality_status": lesson.quality_status,
            "repair_count": lesson.repair_count,
            "validation_errors": lesson.validation_errors,
            "input_context": lesson.input_context,
            "raw_model_output": lesson.raw_model_output,
            "content_text": lesson.content_text,
            "exercises": lesson.exercises,
            "created_at": (lesson.created_at.isoformat() if getattr(lesson, "created_at", None) else None),
        }

    async def _get_user_for_lesson(self, *, lesson_enrollment_id: UUID) -> User:
        enr_res = await self.db.execute(select(Enrollment).where(Enrollment.id == lesson_enrollment_id))
        enrollment = enr_res.scalars().first()
        if enrollment is None:
            raise EntityNotFoundException(entity_name="Enrollment", entity_id=str(lesson_enrollment_id))

        user_res = await self.db.execute(select(User).where(User.id == enrollment.user_id))
        user = user_res.scalars().first()
        if user is None:
            raise EntityNotFoundException(entity_name="User", entity_id=str(enrollment.user_id))

        return user

    async def regen_exercises(self, *, lesson_id: UUID, generation_mode: str) -> dict:
        lesson = await self.lessons_repo.get_by_id(lesson_id=lesson_id)
        if lesson is None:
            raise EntityNotFoundException(entity_name="GeneratedLesson", entity_id=str(lesson_id))

        user = await self._get_user_for_lesson(lesson_enrollment_id=lesson.enrollment_id)
        out = await self.learning_service.regenerate_exercises_only(
            lesson=lesson,
            user=user,
            generation_mode=str(generation_mode or "strict"),
        )
        return {"id": str(out.id), "quality_status": out.quality_status}

    async def purge_all_except_users(self, *, confirm: str) -> dict:
        if str(getattr(settings, "ENV", "development")) == "production":
            raise ValueError("Purge is disabled in production")

        if str(confirm or "") != "DELETE_ALL_EXCEPT_USERS":
            raise ValueError("Invalid confirmation")

        # Очищаем все таблицы, кроме пользователей и версии базы данных
        tables = [
            "ai_generation_events",
            "llm_cache_entries",
            "lesson_lexemes",
            "user_lexemes",
            "lexemes",
            "generated_vocabulary_items",
            "generated_lessons",
            "user_level_attempts",
            "user_level_progress",
            "enrollments",
            "course_level_templates",
            "course_unit_templates",
            "course_section_templates",
            "course_templates",
            "refresh_tokens",
            "streaks",
        ]

        bind = self.db.get_bind()
        dialect_name = getattr(getattr(bind, "dialect", None), "name", "") if bind is not None else ""
        if dialect_name != "postgresql":
            raise ValueError("Purge is only implemented for PostgreSQL")

        sql = "TRUNCATE TABLE " + ", ".join(tables) + " RESTART IDENTITY CASCADE"
        await self.db.execute(text(sql))
        await self.db.commit()
        return {"status": "ok", "truncated": tables}

    async def regen_core(self, *, lesson_id: UUID, level: str, generation_mode: str) -> dict:
        lesson = await self.lessons_repo.get_by_id(lesson_id=lesson_id)
        if lesson is None:
            raise EntityNotFoundException(entity_name="GeneratedLesson", entity_id=str(lesson_id))

        user = await self._get_user_for_lesson(lesson_enrollment_id=lesson.enrollment_id)
        out = await self.learning_service.regenerate_core_only(
            lesson=lesson,
            user=user,
            level=str(level or "A1"),
            generation_mode=str(generation_mode or "strict"),
        )
        return {"id": str(out.id), "quality_status": out.quality_status}
