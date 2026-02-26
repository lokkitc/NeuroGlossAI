import re
import math
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import EntityNotFoundException, ServiceException
from app.features.common.db import begin_if_needed
from app.features.rooms.models import RoomParticipant
from app.features.chat.models import ChatSession, ChatTurn, ChatSessionSummary, ModerationEvent
from app.features.memory.models import MemoryItem
from app.features.characters.repository import CharacterRepository
from app.features.rooms.repository import RoomRepository, RoomParticipantRepository
from app.features.chat.repository import (
    ChatSessionRepository,
    ChatTurnRepository,
    ChatSummaryRepository,
    ModerationEventRepository,
)
from app.features.memory.repository import MemoryRepository
from app.features.ai.ai_service import ai_service
from app.features.chat_learning.service import ChatLearningService
from app.core.config import settings
from app.utils.prompt_templates import CHAT_SESSION_SUMMARY_TEMPLATE

logger = logging.getLogger(__name__)


_SELF_HARM_RE = re.compile(r"(suicide|kill myself|self-harm|end my life)", re.IGNORECASE)
_ILLEGAL_RE = re.compile(r"(buy drugs|make a bomb|credit card fraud|hack password)", re.IGNORECASE)


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.sessions = ChatSessionRepository(db)
        self.turns = ChatTurnRepository(db)
        self.memories = MemoryRepository(db)
        self.summaries = ChatSummaryRepository(db)
        self.moderation = ModerationEventRepository(db)
        self.characters = CharacterRepository(db)
        self.rooms = RoomRepository(db)
        self.room_participants = RoomParticipantRepository(db)

    async def list_sessions(self, *, owner_user_id, skip: int = 0, limit: int = 50):
        return await self.sessions.list_for_owner(owner_user_id, skip=skip, limit=limit)

    async def get_session_for_owner(self, *, session_id, owner_user_id):
        sess = await self.sessions.get_full(session_id)
        if not sess or sess.owner_user_id != owner_user_id:
            raise EntityNotFoundException("ChatSession", session_id)
        return sess

    async def create_session(self, *, owner_user_id, character_id=None, room_id=None, title: str = "") -> ChatSession:
        if bool(character_id) == bool(room_id):
            raise ServiceException("Provide exactly one of character_id or room_id")

        if character_id:
            ch = await self.characters.get(character_id)
            if not ch:
                raise EntityNotFoundException("Character", character_id)
        if room_id:
            room = await self.rooms.get_full(room_id)
            if not room:
                raise EntityNotFoundException("Room", room_id)

        sess = ChatSession(
            owner_user_id=owner_user_id,
            character_id=character_id,
            room_id=room_id,
            title=title or "",
        )
        async with begin_if_needed(self.db):
            await self.sessions.create(sess)

        await self.db.refresh(sess)
        return sess

    async def _score_memory(self, memory: MemoryItem, query: str) -> float:
                                                                                        
        q = (query or "").lower().strip()
        if not q:
            return 0.0
        text = f"{memory.title} {memory.content}".lower()
        return 1.0 if any(t in text for t in set(re.findall(r"[a-zа-я0-9_]{3,}", q))) else 0.0

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        if not isinstance(text, str):
            text = str(text or "")
        text = text.lower()
                                                         
        tokens = re.findall(r"[a-zа-я0-9_]{2,}", text)
        return tokens

    @classmethod
    def _bm25_rank(cls, *, query: str, docs: list[tuple[MemoryItem, str]], k1: float = 1.2, b: float = 0.75):
        q_tokens = cls._tokenize(query)
        if not q_tokens:
            return []
                              
        df: dict[str, int] = {}
        doc_tfs: list[dict[str, int]] = []
        doc_lens: list[int] = []

        for _, text in docs:
            toks = cls._tokenize(text)
            doc_lens.append(len(toks) or 1)
            tf: dict[str, int] = {}
            for t in toks:
                tf[t] = tf.get(t, 0) + 1
            doc_tfs.append(tf)
            for t in set(toks):
                df[t] = df.get(t, 0) + 1

        N = len(docs)
        avgdl = (sum(doc_lens) / N) if N else 1.0

        def idf(t: str) -> float:
            n = df.get(t, 0)
                                                  
            return math.log(1.0 + (N - n + 0.5) / (n + 0.5))

        scored: list[tuple[float, MemoryItem]] = []
        for i, (mem, _) in enumerate(docs):
            tf = doc_tfs[i]
            dl = float(doc_lens[i])
            score = 0.0
            for t in q_tokens:
                f = float(tf.get(t, 0))
                if f <= 0:
                    continue
                denom = f + k1 * (1.0 - b + b * (dl / avgdl))
                score += idf(t) * (f * (k1 + 1.0) / denom)
                                         
            score += 0.15 * float(getattr(mem, "importance", 0) or 0)
            if score > 0:
                scored.append((score, mem))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored

    async def _select_relevant_memories(
        self,
        *,
        owner_user_id,
        query: str,
        character_id=None,
        room_id=None,
        limit: int = 12,
    ) -> list[MemoryItem]:
        candidates = await self.memories.list_candidates(owner_user_id, character_id=character_id, room_id=room_id, limit=250)
        docs: list[tuple[MemoryItem, str]] = []
        for m in candidates:
            docs.append((m, f"{m.title} {m.content}"))
        ranked = self._bm25_rank(query=query, docs=docs)
        return [m for _, m in ranked[:limit]]

    @staticmethod
    def _speaker_key(name: str) -> str:
        return (name or "").strip().lower()

    async def _maybe_summarize(self, session: ChatSession) -> ChatSessionSummary | None:
        recent = await self.turns.list_recent(session.id, limit=120)
        if not recent:
            return None

        max_index = max(t.turn_index for t in recent)
        if max_index - int(getattr(session, "last_summary_at_turn", 0) or 0) < 30:
            return None

        latest = await self.summaries.get_latest(session.id)
        previous_summary = latest.content if latest else ""

        history_lines: list[str] = []
        for t in recent:
            if t.turn_index <= int(getattr(session, "last_summary_at_turn", 0) or 0):
                continue
            role = t.role
            name = "USER" if role == "user" else ("ASSISTANT" if role in {"assistant", "director"} else role.upper())
            if t.character_id:
                name = f"CHAR({t.character_id})"
            history_lines.append(f"{name}: {t.content}")

        prompt = CHAT_SESSION_SUMMARY_TEMPLATE.format(
            previous_summary=previous_summary,
            dialogue="\n".join(history_lines[-120:]),
        )

        summary_text = await ai_service.provider.generate_text(prompt)
        row = ChatSessionSummary(session_id=session.id, up_to_turn_index=max_index, content=summary_text)
        async with begin_if_needed(self.db):
            await self.summaries.create(row)
            session.last_summary_at_turn = max_index
            self.db.add(session)
        return row

    async def _moderate(self, *, owner_user_id, session_id, turn_id, content: str) -> None:
        decision = "allow"
        event_type = "precheck"
        details: dict[str, Any] = {}

        if _SELF_HARM_RE.search(content or ""):
            decision = "block"
            details["reason"] = "self_harm"
        elif _ILLEGAL_RE.search(content or ""):
            decision = "block"
            details["reason"] = "illegal"

        evt = ModerationEvent(
            owner_user_id=owner_user_id,
            session_id=session_id,
            turn_id=turn_id,
            event_type=event_type,
            decision=decision,
            details=details or None,
        )
        async with begin_if_needed(self.db):
            await self.moderation.create(evt)

        if decision == "block":
            raise ServiceException("Message blocked by safety policy")

    async def _build_messages_for_llm(
        self,
        *,
        session: ChatSession,
        user_message: str,
    ):
                                                                                   
        recent = await self.turns.list_recent(session.id, limit=80)
        pinned = await self.memories.list_pinned(
            session.owner_user_id,
            character_id=session.character_id,
            room_id=session.room_id,
            limit=50,
        )
        relevant = await self._select_relevant_memories(
            owner_user_id=session.owner_user_id,
            query=user_message,
            character_id=session.character_id,
            room_id=session.room_id,
            limit=12,
        )
        latest_summary = await self.summaries.get_latest(session.id)

        system_parts: list[str] = []

                                  
        room_participants_by_name: dict[str, RoomParticipant] = {}

        temperature: float | None = None

        if session.character_id:
            ch = await self.characters.get(session.character_id)
            if not ch:
                raise EntityNotFoundException("Character", session.character_id)
            system_parts.append(ch.system_prompt or "")
            if ch.style_prompt:
                system_parts.append(ch.style_prompt)

            if getattr(ch, "greeting", None):
                system_parts.append(f"GREETING (use as initial tone, do not repeat verbatim every time):\n{ch.greeting}")

            cs = getattr(ch, "chat_settings", None)
            if isinstance(cs, dict):
                t = cs.get("temperature")
                try:
                    if t is not None:
                        temperature = float(t)
                        if temperature < 0.0:
                            temperature = 0.0
                        if temperature > 2.0:
                            temperature = 2.0
                except Exception:
                    temperature = None
        else:
            room = await self.rooms.get_full(session.room_id)
            if not room:
                raise EntityNotFoundException("Room", session.room_id)
                                                             
            system_parts.append(
                "You are a multi-character roleplay director. Keep continuity, avoid repetition, and choose EXACTLY ONE character to speak per turn. "
                "You MUST output ONLY valid JSON with keys: speaker, message. No markdown. No extra keys."
            )
            parts: list[RoomParticipant] = list(getattr(room, "participants", []) or [])
            parts.sort(key=lambda p: (-(p.priority or 0), str(p.id)))
            for p in parts:
                ch = p.character
                if not ch:
                    continue
                room_participants_by_name[self._speaker_key(ch.display_name)] = p
                system_parts.append(
                    f"CHARACTER {ch.display_name}: {ch.description}\nSYSTEM_PROMPT: {ch.system_prompt}"
                )
            system_parts.append(
                "Output JSON format:\n{\n  \"speaker\": \"<one of the CHARACTER names above>\",\n  \"message\": \"...\"\n}"
            )

        if pinned:
            system_parts.append("PINNED MEMORY (always true):\n" + "\n".join([f"- {m.title}: {m.content}" for m in pinned]))

        if latest_summary and (latest_summary.content or "").strip():
            system_parts.append("SESSION SUMMARY:\n" + latest_summary.content.strip())

        if relevant:
            system_parts.append(
                "RELEVANT MEMORY:\n" + "\n".join([f"- {m.title}: {m.content}" for m in relevant])
            )

        system_prompt = "\n\n".join([p for p in system_parts if (p or "").strip()])

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        for t in recent:
            if t.role == "user":
                messages.append({"role": "user", "content": t.content})
            elif t.role in {"assistant", "director"}:
                messages.append({"role": "assistant", "content": t.content})
            else:
                messages.append({"role": "assistant", "content": t.content})

        messages.append({"role": "user", "content": user_message})
        return messages, (pinned + relevant), room_participants_by_name, temperature

    async def generate_turn(self, *, owner_user_id, session_id, user_message: str) -> dict[str, Any]:
        session = await self.sessions.get(session_id)
        if not session or session.owner_user_id != owner_user_id:
            raise EntityNotFoundException("ChatSession", session_id)

                                                                                                          
        last_integrity_error: Exception | None = None
        for _ in range(3):
            try:
                                   
                next_idx = await self.sessions.next_turn_index(session_id)
                user_turn = ChatTurn(session_id=session_id, turn_index=next_idx, role="user", content=user_message)
                async with begin_if_needed(self.db):
                    await self.turns.create(user_turn)

                await self._moderate(owner_user_id=owner_user_id, session_id=session_id, turn_id=user_turn.id, content=user_message)

                messages, used_mem, room_map, temperature = await self._build_messages_for_llm(
                    session=session,
                    user_message=user_message,
                )

                assistant_turns: list[ChatTurn] = []
                next_idx2 = next_idx + 1

                if session.character_id:
                    assistant_text = await ai_service.generate_character_chat_turn(
                        db=self.db,
                        messages=messages,
                        temperature=temperature,
                    )
                    assistant_turn = ChatTurn(
                        session_id=session_id,
                        turn_index=next_idx2,
                        role="assistant",
                        character_id=session.character_id,
                        content=assistant_text,
                    )
                    async with begin_if_needed(self.db):
                        await self.turns.create(assistant_turn)
                    assistant_turns.append(assistant_turn)
                else:
                                                             
                    data = await ai_service.generate_room_chat_turn_json(
                        db=self.db,
                        messages=messages,
                        temperature=temperature,
                    )
                    speaker = str(data.get("speaker") or "").strip()
                    message = str(data.get("message") or "").strip()
                    if not speaker or not message:
                        raise ServiceException("Room response invalid: missing speaker/message")

                    rp = room_map.get(self._speaker_key(speaker))
                    character_id = getattr(rp, "character_id", None) if rp else None

                    assistant_turn = ChatTurn(
                        session_id=session_id,
                        turn_index=next_idx2,
                        role="assistant",
                        character_id=character_id,
                        content=message,
                        meta={"speaker": speaker},
                    )
                    async with begin_if_needed(self.db):
                        await self.turns.create(assistant_turn)
                    assistant_turns.append(assistant_turn)

                await self.db.refresh(user_turn)
                for t in assistant_turns:
                    await self.db.refresh(t)

                                                                                            
                try:
                    if bool(getattr(settings, "CHAT_LEARNING_ENABLED", True)):
                        every = int(getattr(settings, "CHAT_LEARNING_EVERY_USER_TURNS", 10) or 10)
                        window = int(getattr(settings, "CHAT_LEARNING_TURN_WINDOW", 80) or 80)
                        every = max(1, min(every, 50))
                        window = max(10, min(window, 120))

                        last_at = int(getattr(session, "last_learning_lesson_at_turn", 0) or 0)
                                                                                                      
                        if (user_turn.turn_index - last_at) >= (every * 2):
                            await ChatLearningService(self.db).generate_lesson_for_session(
                                owner_user_id=owner_user_id,
                                chat_session_id=session_id,
                                turn_window=window,
                                generation_mode="balanced",
                            )
                except Exception:
                    pass

                                 
                try:
                    await self._maybe_summarize(session)
                except Exception:
                    pass

                return {
                    "session": session,
                    "user_turn": user_turn,
                    "assistant_turns": assistant_turns,
                    "memory_used": used_mem,
                }

            except IntegrityError as e:
                last_integrity_error = e
            except Exception as e:
                last_integrity_error = e

                if isinstance(e, (EntityNotFoundException, ServiceException)):
                    raise

                logger.exception(
                    "Unhandled error while generating chat turn (session_id=%s)",
                    str(session_id),
                )
                raise ServiceException("Failed to generate chat turn")

        if last_integrity_error is not None:
            raise ServiceException("Failed to write turn")
        raise ServiceException("Failed to generate turn")
