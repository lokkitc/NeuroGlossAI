"""Сервис обучения пользователя.

Отвечает за:
- генерацию уроков (через сервис ИИ) и сохранение сгенерированного контента
- регенерацию основы урока и упражнений
- нормализованный словарь и повторение слов
- запись событий генерации (по возможности)
"""

from datetime import datetime, timedelta
import uuid
import time
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.enrollment import Enrollment
from app.models.generated_content import GeneratedLesson
from app.models.srs import Lexeme, UserLexeme, LessonLexeme
from app.models.generated_content import GeneratedVocabularyItem
from app.schemas.vocabulary import VocabularyReviewRequest
from app.services.ai_service import ai_service, GenerationMode
from app.repositories.ai_ops import AIIOpsRepository
from app.repositories.generated_lesson import GeneratedLessonRepository
from app.repositories.generated_vocabulary import GeneratedVocabularyRepository
from app.repositories.srs import LexemeRepository, UserLexemeRepository, LessonLexemeRepository
from app.services.factories import GeneratedLessonFactory


def _normalize_word(word: str) -> str:
    return (word or "").strip().lower()


def _extract_error_codes(errors: list[dict] | None) -> list[str] | None:
    if not isinstance(errors, list):
        return None
    out: list[str] = []
    for e in errors:
        if isinstance(e, dict) and e.get("code"):
            out.append(str(e.get("code")))
    return out or None

class LearningService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.generated_repo = GeneratedLessonRepository(db)
        self.generated_vocab_repo = GeneratedVocabularyRepository(db)
        self.lexeme_repo = LexemeRepository(db)
        self.user_lexeme_repo = UserLexemeRepository(db)
        self.lesson_lexeme_repo = LessonLexemeRepository(db)

    @staticmethod
    def calculate_next_review(current_level: int, is_correct: bool) -> tuple[int, datetime]:
        if not is_correct:
            return 0, datetime.utcnow()
        
        new_level = current_level + 1
        # Простая схема интервальных повторений: 1, 3, 7, 14, 30 дней
        intervals = {
            1: 1,
            2: 3,
            3: 7,
            4: 14, 
            5: 30
        }
        days = intervals.get(new_level, 30)
        next_date = datetime.utcnow() + timedelta(days=days)
        
        return new_level, next_date

    async def create_generated_lesson_from_ai(
        self,
        *,
        enrollment: Enrollment,
        user: User,
        level_template_id: uuid.UUID,
        topic: str,
        level: str,
        prior_topics: list[str] | None = None,
        used_words: list[str] | None = None,
        force_regenerate: bool = False,
        generation_mode: GenerationMode = "balanced",
    ) -> GeneratedLesson:
        existing = await self.generated_repo.get_by_enrollment_and_level(enrollment.id, level_template_id)
        if existing is not None and not force_regenerate:
            return existing

        if existing is not None and force_regenerate:
            await self.generated_repo.delete(existing.id)

        started = time.monotonic()
        ai_data = None
        err: Exception | None = None
        try:
            ai_data = await ai_service.generate_lesson(
                topic=topic,
                target_language=user.target_language,
                native_language=user.native_language,
                level=level,
                interests=user.interests if hasattr(user, "interests") else [],
                prior_topics=prior_topics,
                used_words=used_words,
                generation_mode=generation_mode,
                db=self.db,
            )
        except Exception as e:
            err = e
            raise
        finally:
            try:
                meta = ai_data.get("_meta") if isinstance(ai_data, dict) else None
                repo = AIIOpsRepository(self.db)
                latency_ms = int((time.monotonic() - started) * 1000)
                await repo.create_event(
                    enrollment_id=enrollment.id,
                    generated_lesson_id=None,
                    operation="lesson_generate",
                    provider=(meta.get("provider") if isinstance(meta, dict) else None),
                    model=(meta.get("model") if isinstance(meta, dict) else None),
                    generation_mode=(meta.get("generation_mode") if isinstance(meta, dict) else str(generation_mode)),
                    latency_ms=latency_ms,
                    repair_count=(meta.get("repair_count") if isinstance(meta, dict) else None),
                    quality_status=(meta.get("quality_status") if isinstance(meta, dict) else None),
                    error_codes=_extract_error_codes(meta.get("validation_errors") if isinstance(meta, dict) else None),
                )
                await self.db.commit()
            except Exception:
                try:
                    await self.db.rollback()
                except Exception:
                    pass

        # Сохраняем диагностические поля генерации (по возможности) в сгенерированный урок.
        meta = ai_data.get("_meta") if isinstance(ai_data, dict) else None

        lesson, vocab_items = GeneratedLessonFactory.create_from_ai_response(
            ai_data=ai_data,
            enrollment=enrollment,
            level_template_id=level_template_id,
            topic=topic,
            prompt_version=(
                f"lesson_v2|mode={meta.get('generation_mode')}" if isinstance(meta, dict) and meta.get("generation_mode") else "lesson_v2"
            ),
            input_context={
                "topic": topic,
                "level": level,
                "target_language": user.target_language,
                "native_language": user.native_language,
                "interests": (user.interests if hasattr(user, "interests") else []),
                "prior_topics": prior_topics,
                "used_words": used_words,
                "generation_mode": generation_mode,
            },
            raw_model_output=ai_data,
            validation_errors=(meta.get("validation_errors") if isinstance(meta, dict) else None),
            repair_count=(meta.get("repair_count") if isinstance(meta, dict) else 0),
            provider=(meta.get("provider") if isinstance(meta, dict) else None),
            model=(meta.get("model") if isinstance(meta, dict) else None),
            quality_status=(meta.get("quality_status") if isinstance(meta, dict) else "ok"),
        )
        created = await self.generated_repo.create_with_vocabulary(lesson, vocab_items)
        await self._upsert_srs_from_generated_lesson(
            generated_lesson=created,
            user_id=user.id,
            enrollment_id=enrollment.id,
            target_language=user.target_language,
        )
        return created

    async def regenerate_exercises_only(
        self,
        *,
        lesson: GeneratedLesson,
        user: User,
        generation_mode: GenerationMode = "balanced",
    ) -> GeneratedLesson:
        vocab_payload: list[dict] = []
        for item in getattr(lesson, "vocabulary_items", []) or []:
            vocab_payload.append(
                {
                    "word": getattr(item, "word", None),
                    "translation": getattr(item, "translation", None),
                    "context": getattr(item, "context_sentence", None),
                }
            )

        started = time.monotonic()
        ex_data = None
        try:
            ex_data = await ai_service.generate_exercises_only(
                text=getattr(lesson, "content_text", ""),
                vocabulary=vocab_payload,
                target_language=user.target_language,
                native_language=user.native_language,
                generation_mode=generation_mode,
                db=self.db,
            )
        finally:
            try:
                meta_evt = ex_data.get("_meta") if isinstance(ex_data, dict) else None
                repo = AIIOpsRepository(self.db)
                latency_ms = int((time.monotonic() - started) * 1000)
                await repo.create_event(
                    enrollment_id=lesson.enrollment_id,
                    generated_lesson_id=lesson.id,
                    operation="lesson_regen_exercises",
                    provider=(meta_evt.get("provider") if isinstance(meta_evt, dict) else None),
                    model=(meta_evt.get("model") if isinstance(meta_evt, dict) else None),
                    generation_mode=(meta_evt.get("generation_mode") if isinstance(meta_evt, dict) else str(generation_mode)),
                    latency_ms=latency_ms,
                    repair_count=None,
                    quality_status=(meta_evt.get("quality_status") if isinstance(meta_evt, dict) else None),
                    error_codes=_extract_error_codes(meta_evt.get("validation_errors") if isinstance(meta_evt, dict) else None),
                )
                await self.db.commit()
            except Exception:
                try:
                    await self.db.rollback()
                except Exception:
                    pass

        meta = ex_data.get("_meta") if isinstance(ex_data, dict) else None
        lesson.exercises = ex_data.get("exercises", []) if isinstance(ex_data, dict) else []
        if isinstance(meta, dict) and meta.get("quality_status"):
            lesson.quality_status = str(meta.get("quality_status"))

        # Добавляем диагностические поля
        if isinstance(meta, dict) and meta.get("validation_errors"):
            existing_errs = lesson.validation_errors if isinstance(lesson.validation_errors, list) else []
            lesson.validation_errors = list(existing_errs) + list(meta.get("validation_errors") or [])
        if isinstance(meta, dict) and meta.get("exercise_attempts"):
            lesson.repair_count = int(getattr(lesson, "repair_count", 0) or 0)

        self.db.add(lesson)
        await self.db.commit()
        return await self.generated_repo.get_by_id_and_enrollment(lesson.id, lesson.enrollment_id)

    async def regenerate_core_only(
        self,
        *,
        lesson: GeneratedLesson,
        user: User,
        level: str,
        generation_mode: GenerationMode = "balanced",
    ) -> GeneratedLesson:
        # Перегенерируем только текст + словарь, сохраняя ту же запись урока.
        # Упражнения могут перестать соответствовать тексту, поэтому очищаем их и помечаем как требующие проверки.

        topic = getattr(lesson, "topic_snapshot", None) or "regen_core"

        started = time.monotonic()
        ai_core = None
        try:
            ai_core = await ai_service.generate_lesson(
                topic=topic,
                target_language=user.target_language,
                native_language=user.native_language,
                level=level,
                interests=user.interests if hasattr(user, "interests") else [],
                prior_topics=None,
                used_words=None,
                generation_mode=generation_mode,
                db=self.db,
            )
        finally:
            try:
                meta_evt = ai_core.get("_meta") if isinstance(ai_core, dict) else None
                repo = AIIOpsRepository(self.db)
                latency_ms = int((time.monotonic() - started) * 1000)
                await repo.create_event(
                    enrollment_id=lesson.enrollment_id,
                    generated_lesson_id=lesson.id,
                    operation="lesson_regen_core",
                    provider=(meta_evt.get("provider") if isinstance(meta_evt, dict) else None),
                    model=(meta_evt.get("model") if isinstance(meta_evt, dict) else None),
                    generation_mode=(meta_evt.get("generation_mode") if isinstance(meta_evt, dict) else str(generation_mode)),
                    latency_ms=latency_ms,
                    repair_count=(meta_evt.get("repair_count") if isinstance(meta_evt, dict) else None),
                    quality_status=(meta_evt.get("quality_status") if isinstance(meta_evt, dict) else None),
                    error_codes=_extract_error_codes(meta_evt.get("validation_errors") if isinstance(meta_evt, dict) else None),
                )
                await self.db.commit()
            except Exception:
                try:
                    await self.db.rollback()
                except Exception:
                    pass

        meta = ai_core.get("_meta") if isinstance(ai_core, dict) else None

        # Обновляем core поля
        lesson.content_text = str(ai_core.get("text") or "") if isinstance(ai_core, dict) else ""

        # Заменяем элементы словаря
        existing_items = list(getattr(lesson, "vocabulary_items", []) or [])
        for it in existing_items:
            self.db.delete(it)

        new_items: list[GeneratedVocabularyItem] = []
        for item in (ai_core.get("vocabulary") if isinstance(ai_core, dict) else []) or []:
            if not isinstance(item, dict):
                continue
            new_items.append(
                GeneratedVocabularyItem(
                    generated_lesson_id=lesson.id,
                    word=item.get("word"),
                    translation=item.get("translation"),
                    context_sentence=item.get("context"),
                )
            )

        # Очищаем упражнения и помечаем как требующие проверки; пользователь может вызвать регенерацию упражнений.
        lesson.exercises = []
        lesson.quality_status = "needs_review"

        if isinstance(meta, dict) and meta.get("validation_errors"):
            lesson.validation_errors = meta.get("validation_errors")
        if isinstance(meta, dict) and meta.get("repair_count") is not None:
            lesson.repair_count = int(meta.get("repair_count") or 0)
        if isinstance(meta, dict) and meta.get("provider"):
            lesson.provider = str(meta.get("provider"))
        if isinstance(meta, dict) and meta.get("model"):
            lesson.model = str(meta.get("model"))
        lesson.prompt_version = (
            f"lesson_v2|mode={meta.get('generation_mode')}" if isinstance(meta, dict) and meta.get("generation_mode") else "lesson_v2"
        )

        self.db.add(lesson)
        for it in new_items:
            self.db.add(it)

        await self.db.commit()
        refreshed = await self.generated_repo.get_by_id_and_enrollment(lesson.id, lesson.enrollment_id)

        # Обновляем связи нормализованного словаря (по возможности)
        if refreshed is not None:
            await self._upsert_srs_from_generated_lesson(
                generated_lesson=refreshed,
                user_id=user.id,
                enrollment_id=lesson.enrollment_id,
                target_language=user.target_language,
            )

        return refreshed

    async def _upsert_srs_from_generated_lesson(
        self,
        *,
        generated_lesson: GeneratedLesson,
        user_id: uuid.UUID,
        enrollment_id: uuid.UUID,
        target_language: str,
    ) -> None:
        any_updates = False

        for item in getattr(generated_lesson, "vocabulary_items", []) or []:
            word = getattr(item, "word", None)
            if not word:
                continue

            normalized = _normalize_word(str(word))

            lexeme = await self.lexeme_repo.get_by_lang_and_normalized(
                target_language=target_language,
                normalized=normalized,
            )
            if lexeme is None:
                lexeme = await self.lexeme_repo.create(
                    Lexeme(
                        target_language=target_language,
                        text=str(word),
                        normalized=normalized,
                    ),
                    commit=False,
                )
                any_updates = True

            user_lexeme = await self.user_lexeme_repo.get_by_user_and_lexeme(user_id=user_id, lexeme_id=lexeme.id)
            if user_lexeme is None:
                user_lexeme = await self.user_lexeme_repo.create(
                    UserLexeme(
                        user_id=user_id,
                        enrollment_id=enrollment_id,
                        lexeme_id=lexeme.id,
                        translation_preferred=getattr(item, "translation", None),
                        context_sentence_preferred=getattr(item, "context_sentence", None),
                        mastery_level=getattr(item, "mastery_level", 0) or 0,
                        next_review_at=getattr(item, "next_review_at", None),
                    ),
                    commit=False,
                )
                any_updates = True

            # Связываем строку словаря урока с каноническим идентификатором записи словаря пользователя.
            if getattr(item, "user_lexeme_id", None) != user_lexeme.id:
                item.user_lexeme_id = user_lexeme.id
                self.db.add(item)
                any_updates = True

            existing_link = await self.lesson_lexeme_repo.get_by_lesson_and_lexeme(
                generated_lesson_id=generated_lesson.id,
                lexeme_id=lexeme.id,
            )
            if existing_link is None:
                await self.lesson_lexeme_repo.create(
                    LessonLexeme(
                        generated_lesson_id=generated_lesson.id,
                        lexeme_id=lexeme.id,
                        user_lexeme_id=user_lexeme.id,
                        translation=getattr(item, "translation", None),
                        context_sentence=getattr(item, "context_sentence", None),
                    ),
                    commit=False,
                )
                any_updates = True

        if any_updates:
            await self.db.commit()

    async def get_user_generated_lessons(
        self,
        enrollment_id: uuid.UUID,
        skip: int = 0,
        limit: int = 10,
    ) -> list[GeneratedLesson]:
        return await self.generated_repo.get_by_enrollment(enrollment_id, skip=skip, limit=limit)

    async def get_generated_lesson_by_id(
        self,
        lesson_id: uuid.UUID,
        enrollment_id: uuid.UUID,
    ) -> GeneratedLesson | None:
        return await self.generated_repo.get_by_id_and_enrollment(lesson_id, enrollment_id)

    async def get_daily_review_items(self, user_id: int):
        now = datetime.utcnow()
        items = await self.user_lexeme_repo.get_daily_review(user_id=user_id, now=now)
        out: list[dict] = []
        for ul in items:
            lex = getattr(ul, "lexeme", None)
            out.append(
                {
                    "id": ul.id,
                    "word": (lex.text if lex else ""),
                    "translation": ul.translation_preferred or "",
                    "context_sentence": ul.context_sentence_preferred or "",
                    "mastery_level": ul.mastery_level,
                    "next_review_at": ul.next_review_at,
                }
            )
        return out

    async def process_vocabulary_review(self, user_id: int, review_data: VocabularyReviewRequest) -> dict | None:
        # Принимаем оба варианта:
        # - нормализованный идентификатор записи словаря пользователя
        # - идентификатор сгенерированного словаря, который приходит в ответе урока
        user_lexeme = await self.user_lexeme_repo.get_by_id_and_user(
            user_lexeme_id=review_data.vocabulary_id,
            user_id=user_id,
        )

        if user_lexeme is None:
            gvi: GeneratedVocabularyItem | None = await self.generated_vocab_repo.get_by_id_and_user(
                review_data.vocabulary_id,
                user_id,
            )
            if gvi is None:
                return None

            word = getattr(gvi, "word", None)
            if not word:
                return None

            # Маппинг к нормализованному словарю (по возможности).
            # Язык пользователя здесь недоступен; аккуратно работаем только по сохранённому слову.
            normalized = _normalize_word(str(word))
            lexeme = await self.lexeme_repo.get_by_lang_and_normalized(
                target_language="unknown",
                normalized=normalized,
            )
            if lexeme is None:
                lexeme = await self.lexeme_repo.create(
                    Lexeme(
                        target_language="unknown",
                        text=str(word),
                        normalized=normalized,
                    )
                )

            user_lexeme = await self.user_lexeme_repo.get_by_user_and_lexeme(user_id=user_id, lexeme_id=lexeme.id)
            if user_lexeme is None:
                user_lexeme = await self.user_lexeme_repo.create(
                    UserLexeme(
                        user_id=user_id,
                        enrollment_id=None,
                        lexeme_id=lexeme.id,
                        translation_preferred=getattr(gvi, "translation", None),
                        context_sentence_preferred=getattr(gvi, "context_sentence", None),
                        mastery_level=getattr(gvi, "mastery_level", 0) or 0,
                        next_review_at=getattr(gvi, "next_review_at", None),
                    )
                )

        new_level, next_date = self.calculate_next_review(
            user_lexeme.mastery_level,
            review_data.rating >= 3,
        )

        await self.user_lexeme_repo.update(
            user_lexeme,
            {
                "mastery_level": new_level,
                "next_review_at": next_date,
                "last_reviewed_at": datetime.utcnow(),
            },
        )

        return {"status": "success", "new_level": new_level, "next_review": next_date}

    async def process_roleplay_message(self, scenario: str, role: str, message: str, history: list, target_language: str, level: str) -> str:
        response_text = await ai_service.generate_roleplay_response(
            history=history,
            scenario=scenario,
            role=role,
            level=level,
            target_language=target_language
        )
        return response_text
