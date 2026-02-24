import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import re

from app.core.exceptions import EntityNotFoundException, ServiceException
from app.models.chat import ChatSession
from app.models.chat_learning import ChatLearningLesson
from app.models.user import User
from app.models.progress import UserLevelProgress, ProgressStatus
from app.models.course_template import CourseTemplate, CourseSectionTemplate, CourseUnitTemplate, CourseLevelTemplate
from app.models.enrollment import Enrollment
from app.repositories.chat import ChatSessionRepository, ChatTurnRepository
from app.repositories.chat_learning import ChatLearningLessonRepository
from app.repositories.generated_lesson import GeneratedLessonRepository
from app.services.factories import GeneratedLessonFactory
from app.features.ai.ai_service import ai_service


class ChatLearningService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.sessions = ChatSessionRepository(db)
        self.turns = ChatTurnRepository(db)
        self.lessons = ChatLearningLessonRepository(db)

    async def generate_lesson_for_session(
        self,
        *,
        owner_user_id,
        chat_session_id,
        turn_window: int = 40,
        generation_mode: str = "balanced",
    ) -> ChatLearningLesson:
        sess = await self.sessions.get(chat_session_id)
        if not sess or sess.owner_user_id != owner_user_id:
            raise EntityNotFoundException("ChatSession", chat_session_id)

        window = max(10, min(int(turn_window or 40), 120))
        recent = await self.turns.list_recent(chat_session_id, limit=window)
        if not recent:
            raise ServiceException("No turns in session")

        source_from = min(t.turn_index for t in recent)
        source_to = max(t.turn_index for t in recent)

        # Serialize dialogue into a compact transcript with speaker hints.
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

        def _contains_quote(q: str) -> bool:
            q = str(q or "").strip()
            if not q:
                return False
            # Must be exact substring, case-sensitive by default; also try loose match.
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

                # Enforce grounding: phrase and quotes must exist in transcript.
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

            # Exercises must reference exact chat substrings.
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

                # Optional: targets should be a subset of phrases.
                targets = ex.get("targets")
                if isinstance(targets, list):
                    allowed = {v["phrase"] for v in vocab_out}
                    targets = [str(t).strip() for t in targets if str(t).strip() in allowed]
                    ex["targets"] = targets

                ex_out.append(ex)

            # If we don't have enough grounded material, skip lesson.
            if len(vocab_out) < 6:
                return None

            out: dict[str, Any] = {
                "title": str(data.get("title") or "Chat Lesson"),
                "topic": str(data.get("topic") or ""),
                # 'text' may be synthetic explanation, but must be based on the chat.
                "text": str(data.get("text") or ""),
                "vocabulary": vocab_out,
                "exercises": ex_out,
            }
            return out

        prompt = (
            "Create a mini-lesson from the following chat. Focus ONLY on vocabulary/phrases that appeared in the chat. "
            "Do not correct the user, do not grade. Keep it fun and grounded in the conversation. "
            "CRITICAL: Do NOT invent phrases, examples, or facts that are not present in the chat. "
            "Every vocabulary item MUST include an exact quote from the chat where it appears. "
            "Every exercise MUST include an exact sentence_source substring copied from the chat. "
            "Output ONLY valid JSON with keys: title, topic, text, vocabulary, exercises.\n\n"
            "JSON schema:\n"
            "{\n"
            "  \"title\": string,\n"
            "  \"topic\": string,\n"
            "  \"text\": string,\n"
            "  \"vocabulary\": [\n"
            "    {\"phrase\": string, \"meaning\": string, \"source_quote\": string, \"example_quote\": string}\n"
            "  ],\n"
            "  \"exercises\": [\n"
            "    {\"type\": \"quiz\"|\"match\"|\"fill_blank\"|\"scramble\", \"sentence_source\": string, \"targets\": [string], ...}\n"
            "  ]\n"
            "}\n\n"
            "Rules:\n"
            "- vocabulary items must be phrases or words that appeared verbatim in the chat\n"
            "- 6-10 vocabulary items\n"
            "- source_quote and example_quote MUST be exact substrings from the chat\n"
            "- exercises must be solvable using only the chat and the vocabulary list\n"
            "- sentence_source MUST be an exact substring from the chat\n\n"
            "CHAT:\n"
            + "\n".join(lines)
        )

        raw = await ai_service.generate_chat_learning_lesson_json(
            db=self.db,
            prompt=prompt,
            generation_mode=generation_mode,
        )

        data = _sanitize_lesson_json(raw)
        if data is None:
            raise ServiceException("Insufficient grounded material in chat to create a lesson")

        # Ensure this chat session has its own course/enrollment/active level.
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

        await self.lessons.create(row, commit=False)

        # update cadence state
        sess.last_learning_lesson_at_turn = int(source_to)

        # --- Course-from-chat integration: upsert GeneratedLesson and advance dynamic progress ---
        if not sess.enrollment_id or not sess.active_level_template_id:
            raise ServiceException("Chat session is missing enrollment/active level")

        enrollment_id = sess.enrollment_id
        level_template_id = sess.active_level_template_id

        # Convert grounded chat lesson JSON into legacy lesson schema expected by GeneratedLessonFactory
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

        # Load enrollment row
        enr_res = await self.db.execute(select(Enrollment).where(Enrollment.id == enrollment_id))
        enrollment = enr_res.scalars().first()
        if enrollment is None:
            raise ServiceException("Enrollment not found for chat session")

        gen_repo = GeneratedLessonRepository(self.db)
        existing = await gen_repo.get_by_enrollment_and_level(enrollment_id, level_template_id)
        if existing is not None:
            await gen_repo.delete(existing.id, commit=False)
            await self.db.flush()

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

        # Advance progress inside this session's course: complete current level and create next level.
        await self._advance_dynamic_progress(enrollment_id=enrollment_id, completed_level_template_id=level_template_id, session=sess)

        self.db.add(sess)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def _ensure_course_for_session(self, session: ChatSession) -> None:
        if getattr(session, "enrollment_id", None) and getattr(session, "active_level_template_id", None):
            return

        user_res = await self.db.execute(select(User).where(User.id == session.owner_user_id))
        user = user_res.scalars().first()
        if user is None:
            raise ServiceException("User not found")

        # Create a dedicated course template for this chat session (no AI path generation).
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
    ) -> None:
        # Mark current progress as completed
        prog_res = await self.db.execute(
            select(UserLevelProgress)
            .where(UserLevelProgress.enrollment_id == enrollment_id)
            .where(UserLevelProgress.level_template_id == completed_level_template_id)
        )
        prog = prog_res.scalars().first()
        if prog is not None:
            prog.status = ProgressStatus.COMPLETED.value
            self.db.add(prog)

        # Create next level inside same unit
        lvl_res = await self.db.execute(select(CourseLevelTemplate).where(CourseLevelTemplate.id == completed_level_template_id))
        lvl = lvl_res.scalars().first()
        if lvl is None:
            return

        max_res = await self.db.execute(
            select(func.max(CourseLevelTemplate.order)).where(CourseLevelTemplate.unit_template_id == lvl.unit_template_id)
        )
        max_order = max_res.scalar() or 1
        next_level = CourseLevelTemplate(
            unit_template_id=lvl.unit_template_id,
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
