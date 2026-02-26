import re
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.exceptions import EntityNotFoundException, ServiceException
from app.features.chat.models import ChatSession
from app.features.chat_learning.models import ChatLearningLesson
from app.features.users.models import User
from app.features.user_progress.models import UserLevelProgress, ProgressStatus, Enrollment
from app.features.course.models import (
    CourseTemplate,
    CourseSectionTemplate,
    CourseUnitTemplate,
    CourseLevelTemplate,
)
from app.features.chat.repository import ChatSessionRepository, ChatTurnRepository
from app.features.chat_learning.repository import ChatLearningLessonRepository
from app.features.lessons.repository import GeneratedLessonRepository
from app.features.lessons.factories import GeneratedLessonFactory
from app.features.ai.ai_service import ai_service
from app.features.srs.repository import LexemeRepository, UserLexemeRepository, LessonLexemeRepository
from app.features.srs.models import Lexeme, UserLexeme, LessonLexeme
from app.utils.prompt_templates import CHAT_LEARNING_LESSON_TEMPLATE


class ChatLearningService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.sessions = ChatSessionRepository(db)
        self.turns = ChatTurnRepository(db)
        self.lessons = ChatLearningLessonRepository(db)
        self.lexemes = LexemeRepository(db)
        self.user_lexemes = UserLexemeRepository(db)
        self.lesson_lexemes = LessonLexemeRepository(db)

    async def list_lessons_for_session(
        self,
        *,
        owner_user_id,
        chat_session_id,
        skip: int = 0,
        limit: int = 50,
    ):
        sess = await self.sessions.get(chat_session_id)
        if not sess or sess.owner_user_id != owner_user_id:
            raise EntityNotFoundException("ChatSession", chat_session_id)

        return await self.lessons.list_for_session(owner_user_id, chat_session_id, skip=skip, limit=limit)

    @staticmethod
    def _normalize_lexeme(text: str) -> str:
        text = str(text or "").strip().lower()
        text = re.sub(r"\s+", " ", text)
                                               
        text = re.sub(r"[^a-zа-я0-9\-\s]", "", text, flags=re.IGNORECASE)
        return text.strip()

    async def _upsert_srs_for_generated_lesson(
        self,
        *,
        user: User,
        enrollment_id,
        lesson_id,
        vocab_items: list[dict[str, Any]],
        generated_vocab_items,
    ) -> None:
        """Upsert Lexeme/UserLexeme and link to lesson.

        - Uses user.target_language
        - Ensures every generated vocab item gets user_lexeme_id when possible
        """
        target_language = str(getattr(user, "target_language", "") or "").strip() or "Unknown"
        now = datetime.utcnow()

                                               
        gvi_by_phrase: dict[str, Any] = {}
        try:
            for gvi in list(generated_vocab_items or []):
                phrase = str(getattr(gvi, "word", "") or "").strip()
                if phrase:
                    gvi_by_phrase[phrase.lower()] = gvi
        except Exception:
            gvi_by_phrase = {}

        for it in vocab_items:
            if not isinstance(it, dict):
                continue
            phrase = str(it.get("phrase") or "").strip()
            if not phrase:
                continue
            normalized = self._normalize_lexeme(phrase)
            if not normalized:
                continue

            lex: Lexeme | None = await self.lexemes.get_by_lang_and_normalized(
                target_language=target_language,
                normalized=normalized,
            )
            if lex is None:
                lex = Lexeme(target_language=target_language, text=phrase, normalized=normalized)
                self.db.add(lex)
                await self.db.flush()

            ulex: UserLexeme | None = await self.user_lexemes.get_by_user_and_lexeme(user_id=user.id, lexeme_id=lex.id)
            if ulex is None:
                ulex = UserLexeme(
                    user_id=user.id,
                    enrollment_id=enrollment_id,
                    lexeme_id=lex.id,
                    translation_preferred=str(it.get("meaning") or "").strip() or None,
                    context_sentence_preferred=str(it.get("example_quote") or it.get("source_quote") or "").strip() or None,
                    mastery_level=0,
                    next_review_at=now,
                )
                self.db.add(ulex)
                await self.db.flush()
            else:
                                                                    
                updated = False
                if not getattr(ulex, "translation_preferred", None) and str(it.get("meaning") or "").strip():
                    ulex.translation_preferred = str(it.get("meaning") or "").strip()
                    updated = True
                if not getattr(ulex, "context_sentence_preferred", None) and str(
                    it.get("example_quote") or it.get("source_quote") or ""
                ).strip():
                    ulex.context_sentence_preferred = str(it.get("example_quote") or it.get("source_quote") or "").strip()
                    updated = True
                if updated:
                    self.db.add(ulex)

                                    
            existing_link = await self.lesson_lexemes.get_by_lesson_and_lexeme(
                generated_lesson_id=lesson_id,
                lexeme_id=lex.id,
            )
            if existing_link is None:
                link = LessonLexeme(
                    generated_lesson_id=lesson_id,
                    lexeme_id=lex.id,
                    user_lexeme_id=ulex.id,
                    translation=str(it.get("meaning") or "").strip() or None,
                    context_sentence=str(it.get("example_quote") or it.get("source_quote") or "").strip() or None,
                )
                self.db.add(link)

                                                           
            gvi = gvi_by_phrase.get(phrase.lower())
            if gvi is not None:
                try:
                    gvi.user_lexeme_id = ulex.id
                    self.db.add(gvi)
                except Exception:
                    pass

    async def generate_lesson_for_session(
        self,
        *,
        owner_user_id,
        chat_session_id,
        turn_window: int = 80,
        generation_mode: str = "balanced",
    ) -> ChatLearningLesson:
        sess = await self.sessions.get(chat_session_id)
        if not sess or sess.owner_user_id != owner_user_id:
            raise EntityNotFoundException("ChatSession", chat_session_id)

        window = max(10, min(int(turn_window or 80), 120))
        recent = await self.turns.list_recent(chat_session_id, limit=window)
        if not recent:
            raise ServiceException("No turns in session")

        source_from = min(t.turn_index for t in recent)
        source_to = max(t.turn_index for t in recent)

        lines: list[str] = []
        transcript_raw_parts: list[str] = []
        for t in recent:
            role = t.role
            if role == "user":
                content = str(t.content or "")
                lines.append(f"USER: {content}")
                transcript_raw_parts.append(content)
            else:
                speaker = None
                if t.meta and isinstance(t.meta, dict) and t.meta.get("speaker"):
                    speaker = str(t.meta.get("speaker"))
                content = str(t.content or "")
                lines.append(f"ASSISTANT{('(' + speaker + ')') if speaker else ''}: {content}")
                transcript_raw_parts.append(content)

        transcript_text = "\n".join(transcript_raw_parts)

        def _extract_keywords(text: str, *, limit: int = 3) -> list[str]:
            text = str(text or "").lower()
            tokens = re.findall(r"[a-zа-я0-9_]{3,}", text)
            if not tokens:
                return []

            stop = {
                    
                "the",
                "and",
                "but",
                "for",
                "with",
                "you",
                "your",
                "are",
                "was",
                "were",
                "have",
                "has",
                "had",
                "this",
                "that",
                "there",
                "here",
                "what",
                "when",
                "where",
                "why",
                "how",
                "can",
                "could",
                "would",
                "should",
                "just",
                "like",
                "really",
                    
                "это",
                "как",
                "что",
                "тут",
                "там",
                "вот",
                "его",
                "ее",
                "она",
                "они",
                "мы",
                "вы",
                "ты",
                "да",
                "нет",
                "ну",
                "очень",
                "просто",
                "тоже",
                "мне",
                "меня",
                "тебя",
                "твой",
            }

            freq: dict[str, int] = {}
            for t in tokens:
                if t in stop:
                    continue
                freq[t] = freq.get(t, 0) + 1

            ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
            return [w for w, _ in ranked[: max(0, int(limit or 0))]]

        keywords = _extract_keywords(transcript_text, limit=3)
        inferred_topic = ", ".join(keywords) if keywords else ""

        def _contains_quote(q: str) -> bool:
            q = str(q or "").strip()
            if not q:
                return False
            if q in transcript_text:
                return True
            q_norm = re.sub(r"\s+", " ", q).strip().lower()
            t_norm = re.sub(r"\s+", " ", transcript_text).strip().lower()
            return bool(q_norm) and q_norm in t_norm

        def _sanitize_lesson_json(data: dict[str, Any]) -> dict[str, Any] | None:
            if not isinstance(data, dict):
                return None

            vocab_in = data.get("vocabulary")
            if not isinstance(vocab_in, list):
                vocab_in = []

            vocab_out: list[dict[str, Any]] = []
            for it in vocab_in:
                if not isinstance(it, dict):
                    continue
                phrase = str(it.get("phrase") or "").strip()
                source_quote = str(it.get("source_quote") or "").strip()
                example_quote = str(it.get("example_quote") or "").strip()
                meaning = str(it.get("meaning") or "").strip()

                if not phrase or not source_quote:
                    continue
                if not _contains_quote(source_quote):
                    continue
                if phrase not in source_quote and phrase.lower() not in source_quote.lower():
                    continue
                if example_quote and not _contains_quote(example_quote):
                    example_quote = ""

                vocab_out.append(
                    {
                        "phrase": phrase,
                        "meaning": meaning,
                        "source_quote": source_quote,
                        "example_quote": example_quote or source_quote,
                    }
                )

            ex_in = data.get("exercises")
            if not isinstance(ex_in, list):
                ex_in = []
            ex_out: list[dict[str, Any]] = []
            for ex in ex_in:
                if not isinstance(ex, dict):
                    continue
                ex_type = str(ex.get("type") or "").strip()
                if ex_type not in {"quiz", "match", "fill_blank", "scramble"}:
                    continue

                sentence_source = str(ex.get("sentence_source") or "").strip()
                if not sentence_source or not _contains_quote(sentence_source):
                    continue

                targets = ex.get("targets")
                if isinstance(targets, list):
                    allowed = {v["phrase"] for v in vocab_out}
                    targets = [str(t).strip() for t in targets if str(t).strip() in allowed]
                    ex["targets"] = targets

                ex_out.append(ex)

            if len(vocab_out) < 6:
                return None

                                                                                                
            if len(ex_out) < 4:
                ex_out = []

            out: dict[str, Any] = {
                "title": str(data.get("title") or "Chat Lesson"),
                "topic": str(data.get("topic") or ""),
                "text": str(data.get("text") or ""),
                "vocabulary": vocab_out,
                "exercises": ex_out,
            }
            return out

        def _fallback_exercises(*, vocab: list[dict[str, Any]]) -> list[dict[str, Any]]:
            out: list[dict[str, Any]] = []
                         
            for it in vocab[:8]:
                phrase = str(it.get("phrase") or "").strip()
                source_quote = str(it.get("source_quote") or "").strip()
                if not phrase or not source_quote:
                    continue
                if not _contains_quote(source_quote):
                    continue

                                                                         
                idx = source_quote.lower().find(phrase.lower())
                if idx < 0:
                    continue
                sentence = source_quote[:idx] + "___" + source_quote[idx + len(phrase) :]
                out.append(
                    {
                        "type": "fill_blank",
                        "sentence_source": source_quote,
                        "sentence": sentence,
                        "answer": phrase,
                        "targets": [phrase],
                    }
                )

                   
            pairs: list[dict[str, str]] = []
            for it in vocab[:10]:
                phrase = str(it.get("phrase") or "").strip()
                meaning = str(it.get("meaning") or "").strip()
                if phrase and meaning:
                    pairs.append({"left": phrase, "right": meaning})
            if len(pairs) >= 6:
                                                                                          
                anchor = str(vocab[0].get("source_quote") or "").strip() if vocab else ""
                out.append(
                    {
                        "type": "match",
                        "sentence_source": anchor,
                        "pairs": pairs,
                        "targets": [p["left"] for p in pairs],
                    }
                )

            return out

        prompt = CHAT_LEARNING_LESSON_TEMPLATE.format(chat="\n".join(lines))

        raw = await ai_service.generate_chat_learning_lesson_json(
            db=self.db,
            prompt=prompt,
            generation_mode=generation_mode,
        )

        data = _sanitize_lesson_json(raw)
        if data is None:
            raise ServiceException("Insufficient grounded material in chat to create a lesson")

                                                                               
        if not str(data.get("topic") or "").strip() and inferred_topic:
            data["topic"] = inferred_topic
        if not str(data.get("title") or "").strip() and inferred_topic:
            data["title"] = f"Chat Lesson: {inferred_topic}"

        if not isinstance(data.get("exercises"), list) or len(data.get("exercises") or []) < 4:
            data["exercises"] = _fallback_exercises(vocab=list(data.get("vocabulary") or []))

        await self._ensure_course_for_session(sess)

        provider_name, model_name = ai_service._provider_info(ai_service.provider)

        row = ChatLearningLesson(
            owner_user_id=owner_user_id,
            chat_session_id=chat_session_id,
            source_turn_from=source_from,
            source_turn_to=source_to,
            title=str(data.get("title") or "Chat Lesson"),
            topic_snapshot=str(data.get("topic") or "") or None,
            content_text=str(data.get("text") or ""),
            vocabulary=data.get("vocabulary"),
            exercises=data.get("exercises"),
            provider=provider_name,
            model=model_name,
            quality_status="ok",
            raw_model_output=raw,
        )

        async with self.db.begin():
            await self.lessons.create(row)

        sess.last_learning_lesson_at_turn = int(source_to)

        if not sess.enrollment_id or not sess.active_level_template_id:
            raise ServiceException("Chat session is missing enrollment/active level")

        enrollment_id = sess.enrollment_id
        level_template_id = sess.active_level_template_id

        vocab_in = data.get("vocabulary") if isinstance(data, dict) else None
        vocab_out: list[dict] = []
        if isinstance(vocab_in, list):
            for it in vocab_in:
                if not isinstance(it, dict):
                    continue
                phrase = str(it.get("phrase") or "").strip()
                meaning = str(it.get("meaning") or "").strip()
                example = str(it.get("example_quote") or it.get("source_quote") or "").strip()
                if not phrase:
                    continue
                vocab_out.append({"word": phrase, "translation": meaning, "context": example})

        legacy_ai_data = {
            "text": str(data.get("text") or ""),
            "vocabulary": vocab_out,
            "exercises": (data.get("exercises") if isinstance(data, dict) else None) or [],
        }

        enr_res = await self.db.execute(select(Enrollment).where(Enrollment.id == enrollment_id))
        enrollment = enr_res.scalars().first()
        if enrollment is None:
            raise ServiceException("Enrollment not found for chat session")

        gen_repo = GeneratedLessonRepository(self.db)
        existing = await gen_repo.get_by_enrollment_and_level(enrollment_id, level_template_id)
        if existing is not None:
            await gen_repo.delete(existing.id)

        lesson, vocab_items = GeneratedLessonFactory.create_from_ai_response(
            ai_data=legacy_ai_data,
            enrollment=enrollment,
            level_template_id=level_template_id,
            topic=(row.topic_snapshot or row.title or "Chat"),
            prompt_version="chat_learning_v1",
            provider=provider_name,
            model=model_name,
            input_context={
                "chat_session_id": str(chat_session_id),
                "source_turn_from": source_from,
                "source_turn_to": source_to,
            },
            raw_model_output=data,
            validation_errors=None,
            repair_count=0,
            quality_status="ok",
        )
        await gen_repo.create_with_vocabulary(lesson, vocab_items)

                                                                          
        user_res = await self.db.execute(select(User).where(User.id == owner_user_id))
        user = user_res.scalars().first()
        if user is not None:
            await self._upsert_srs_for_generated_lesson(
                user=user,
                enrollment_id=enrollment_id,
                lesson_id=lesson.id,
                vocab_items=list(data.get("vocabulary") or []),
                generated_vocab_items=vocab_items,
            )

        await self._advance_dynamic_progress(
            enrollment_id=enrollment_id,
            completed_level_template_id=level_template_id,
            session=sess,
            next_unit_topic=(row.topic_snapshot or row.title or inferred_topic or "Chat"),
        )

        async with self.db.begin():
            self.db.add(sess)

        await self.db.refresh(row)
        return row

    async def _ensure_course_for_session(self, session: ChatSession) -> None:
        if getattr(session, "enrollment_id", None) and getattr(session, "active_level_template_id", None):
            return

        user_res = await self.db.execute(select(User).where(User.id == session.owner_user_id))
        user = user_res.scalars().first()
        if user is None:
            raise ServiceException("User not found")

        slug = f"chat_session:{session.id}"

        course = CourseTemplate(
            slug=slug,
            created_by_user_id=user.id,
            target_language=user.target_language,
            theme=(session.title or "Chat Session"),
            cefr_level="A1",
            version=1,
            is_active=True,
            interests=(user.interests if hasattr(user, "interests") else []),
        )
        self.db.add(course)
        await self.db.flush()

        section = CourseSectionTemplate(
            course_template_id=course.id,
            order=1,
            title=(session.title or "Session"),
            description="",
        )
        self.db.add(section)
        await self.db.flush()

        unit = CourseUnitTemplate(
            section_template_id=section.id,
            order=1,
            topic=(session.title or "Conversation"),
            description="",
            icon="💬",
        )
        self.db.add(unit)
        await self.db.flush()

        level = CourseLevelTemplate(
            unit_template_id=unit.id,
            order=1,
            type="lesson",
            total_steps=5,
            goal="",
        )
        self.db.add(level)
        await self.db.flush()

        enrollment = Enrollment(user_id=user.id, course_template_id=course.id, status="active")
        self.db.add(enrollment)
        await self.db.flush()

        progress = UserLevelProgress(
            enrollment_id=enrollment.id,
            level_template_id=level.id,
            status=ProgressStatus.IN_PROGRESS.value,
            stars=0,
        )
        self.db.add(progress)
        await self.db.flush()

        session.enrollment_id = enrollment.id
        session.active_level_template_id = level.id
        self.db.add(session)
        await self.db.flush()

    async def _advance_dynamic_progress(
        self,
        *,
        enrollment_id,
        completed_level_template_id,
        session: ChatSession,
        next_unit_topic: str,
    ) -> None:
        prog_res = await self.db.execute(
            select(UserLevelProgress)
            .where(UserLevelProgress.enrollment_id == enrollment_id)
            .where(UserLevelProgress.level_template_id == completed_level_template_id)
        )
        prog = prog_res.scalars().first()
        if prog is not None:
            prog.status = ProgressStatus.COMPLETED.value
            self.db.add(prog)

        lvl_res = await self.db.execute(
            select(CourseLevelTemplate).where(CourseLevelTemplate.id == completed_level_template_id)
        )
        lvl = lvl_res.scalars().first()
        if lvl is None:
            return

                                                                                                    
                                                                                            
        roll_every = 3
        unit_id = lvl.unit_template_id
        count_res = await self.db.execute(
            select(func.count(CourseLevelTemplate.id)).where(CourseLevelTemplate.unit_template_id == unit_id)
        )
        level_count = int(count_res.scalar() or 0)
        should_roll_unit = level_count >= roll_every

        if should_roll_unit:
                                                      
            unit_res = await self.db.execute(select(CourseUnitTemplate).where(CourseUnitTemplate.id == unit_id))
            unit = unit_res.scalars().first()
            if unit is not None:
                max_unit_res = await self.db.execute(
                    select(func.max(CourseUnitTemplate.order)).where(
                        CourseUnitTemplate.section_template_id == unit.section_template_id
                    )
                )
                max_unit_order = int(max_unit_res.scalar() or 1)
                new_unit = CourseUnitTemplate(
                    section_template_id=unit.section_template_id,
                    order=max_unit_order + 1,
                    topic=str(next_unit_topic or "Conversation")[:120],
                    description="",
                    icon="💬",
                )
                self.db.add(new_unit)
                await self.db.flush()
                unit_id = new_unit.id

        max_res = await self.db.execute(
            select(func.max(CourseLevelTemplate.order)).where(
                CourseLevelTemplate.unit_template_id == unit_id
            )
        )
        max_order = max_res.scalar() or 1
        next_level = CourseLevelTemplate(
            unit_template_id=unit_id,
            order=int(max_order) + 1,
            type="lesson",
            total_steps=5,
            goal="",
        )
        self.db.add(next_level)
        await self.db.flush()

        next_prog = UserLevelProgress(
            enrollment_id=enrollment_id,
            level_template_id=next_level.id,
            status=ProgressStatus.IN_PROGRESS.value,
            stars=0,
        )
        self.db.add(next_prog)
        await self.db.flush()

        session.active_level_template_id = next_level.id
        self.db.add(session)
