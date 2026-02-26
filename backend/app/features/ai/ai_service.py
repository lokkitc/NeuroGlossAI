"""Сервис работы с моделью.

Содержит:
- генерацию уроков (2 шага: основа -> упражнения)
- валидацию/нормализацию результата
- починку ответа по ошибкам валидации
- кэш ответов и фоллбэки по моделям
"""

import json
import asyncio
import logging
import random
import re
import hashlib
import time
from typing import Any, Literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.core.config import settings
from app.core.ai.base import LLMProvider
from app.core.ai.groq_provider import GroqProvider
from app.features.ai.repository import AIIOpsRepository
from app.features.topic_retrieval.service import TopicRetrievalService
from app.utils.prompt_templates import (
    LESSON_SYSTEM_TEMPLATE,
    LESSON_TEXT_ONLY_TEMPLATE,
    VOCAB_FROM_TEXT_TEMPLATE,
    LESSON_TEXT_VOCAB_TEMPLATE,
    LESSON_EXERCISES_TEMPLATE,
    VOCAB_EXERCISES_TEMPLATE,
    TEXT_EXERCISES_TEMPLATE,
    LESSON_PLAN_TEMPLATE,
    LESSON_REVIEW_TEMPLATE,
    EXERCISES_REVIEW_TEMPLATE,
    ROLEPLAY_SYSTEM_TEMPLATE,
    PATH_GENERATION_TEMPLATE,
    ROOM_CHAT_TURN_JSON_TEMPLATE,
)
from app.core.exceptions import ServiceException

logger = logging.getLogger(__name__)


GenerationMode = Literal["fast", "balanced", "strict"]


class AIService:
    def __init__(self, db: AsyncSession | None = None, provider: LLMProvider | None = None):
        self.provider = provider or self._select_provider()
        self.topic_retrieval = TopicRetrievalService()
        self.db = db

    @staticmethod
    def _provider_info(provider: LLMProvider) -> tuple[str | None, str | None]:
        provider_name = type(provider).__name__ if provider else None
        model_name = getattr(provider, "model", None) if provider else None
        return provider_name, (str(model_name) if model_name is not None else None)

    async def _log_chat_event(
        self,
        *,
        db: AsyncSession | None,
        operation: str,
        latency_ms: int | None,
        error_codes: list[str] | None = None,
        quality_status: str | None = None,
        generation_mode: str | None = None,
    ) -> None:
        if db is None:
            return
        try:
            repo = AIIOpsRepository(db)
            provider_name, model_name = self._provider_info(self.provider)
            await repo.create_event(
                enrollment_id=None,
                generated_lesson_id=None,
                operation=operation,
                provider=provider_name,
                model=model_name,
                generation_mode=generation_mode,
                latency_ms=latency_ms,
                repair_count=None,
                quality_status=quality_status,
                error_codes=error_codes,
            )
        except Exception:
                                       
            return

    async def generate_character_chat_turn(
        self,
        *,
        db: AsyncSession | None,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        generation_mode: str = "deep",
    ) -> str:
        started = time.monotonic()
        try:
            text = await self.provider.generate_chat(messages, temperature=temperature)
            latency_ms = int((time.monotonic() - started) * 1000)
            await self._log_chat_event(
                db=db,
                operation="chat_turn",
                latency_ms=latency_ms,
                quality_status="ok",
                generation_mode=generation_mode,
            )
            return text
        except Exception as e:
            latency_ms = int((time.monotonic() - started) * 1000)
            await self._log_chat_event(
                db=db,
                operation="chat_turn",
                latency_ms=latency_ms,
                quality_status="error",
                generation_mode=generation_mode,
                error_codes=["provider_error"],
            )
            raise ServiceException(f"AI provider error: {str(e)}")

    async def generate_chat_learning_lesson_json(
        self,
        *,
        db: AsyncSession | None,
        prompt: str,
        generation_mode: str = "balanced",
    ) -> dict[str, Any]:
        started = time.monotonic()
        try:
            data = await self.provider.generate_json(prompt)
            latency_ms = int((time.monotonic() - started) * 1000)
            await self._log_chat_event(
                db=db,
                operation="chat_lesson",
                latency_ms=latency_ms,
                quality_status="ok",
                generation_mode=generation_mode,
            )
            return data
        except Exception as e:
            latency_ms = int((time.monotonic() - started) * 1000)
            await self._log_chat_event(
                db=db,
                operation="chat_lesson",
                latency_ms=latency_ms,
                quality_status="error",
                generation_mode=generation_mode,
                error_codes=["provider_error"],
            )
            raise ServiceException(f"AI provider error: {str(e)}")

    async def generate_room_chat_turn_json(
        self,
        *,
        db: AsyncSession | None,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        generation_mode: str = "deep",
    ) -> dict[str, Any]:
        started = time.monotonic()
        try:
                                                                    
                                                                                                            
            transcript_lines: list[str] = []
            for m in messages:
                role = (m.get("role") or "").strip().lower()
                content = m.get("content", "") or ""
                if not content.strip():
                    continue
                if role == "system":
                    transcript_lines.append("[SYSTEM]\n" + content.strip())
                elif role == "user":
                    transcript_lines.append("[USER] " + content.strip())
                else:
                    transcript_lines.append("[ASSISTANT] " + content.strip())

            prompt = ROOM_CHAT_TURN_JSON_TEMPLATE.format(transcript="\n\n".join(transcript_lines))

            data = await self.provider.generate_json(prompt, temperature=temperature)
            latency_ms = int((time.monotonic() - started) * 1000)
            await self._log_chat_event(
                db=db,
                operation="room_turn",
                latency_ms=latency_ms,
                quality_status="ok",
                generation_mode=generation_mode,
            )
            return data
        except Exception as e:
            latency_ms = int((time.monotonic() - started) * 1000)
            await self._log_chat_event(
                db=db,
                operation="room_turn",
                latency_ms=latency_ms,
                quality_status="error",
                generation_mode=generation_mode,
                error_codes=["provider_error"],
            )
            raise ServiceException(f"AI provider error: {str(e)}")

                                                              
    _circuit_state: dict[tuple[str, str], dict[str, float]] = {}

    @classmethod
    def _circuit_key(cls, provider: LLMProvider) -> tuple[str, str]:
        provider_name = type(provider).__name__
        model_name = getattr(provider, "model", None) or ""
        return provider_name, str(model_name)

    @classmethod
    def _is_circuit_open(cls, provider: LLMProvider) -> bool:
        key = cls._circuit_key(provider)
        st = cls._circuit_state.get(key)
        if not st:
            return False
        opened_until = float(st.get("opened_until", 0.0) or 0.0)
        return opened_until > time.monotonic()

    @classmethod
    def _record_circuit_failure(cls, provider: LLMProvider) -> None:
        threshold = int(getattr(settings, "AI_CIRCUIT_BREAKER_FAIL_THRESHOLD", 3) or 3)
        open_seconds = int(getattr(settings, "AI_CIRCUIT_BREAKER_OPEN_SECONDS", 60) or 60)

        key = cls._circuit_key(provider)
        st = cls._circuit_state.get(key) or {"fail_count": 0.0, "opened_until": 0.0}
        st["fail_count"] = float(st.get("fail_count", 0.0) or 0.0) + 1.0
        if st["fail_count"] >= float(threshold):
            st["opened_until"] = time.monotonic() + float(open_seconds)
        cls._circuit_state[key] = st

    @classmethod
    def _record_circuit_success(cls, provider: LLMProvider) -> None:
        key = cls._circuit_key(provider)
        if key in cls._circuit_state:
            cls._circuit_state[key] = {"fail_count": 0.0, "opened_until": 0.0}

    def _provider_candidates(self) -> list[LLMProvider]:
                                                           
        if isinstance(self.provider, GroqProvider):
            primary_model = getattr(self.provider, "model", None) or ""
            models = [str(primary_model)] if primary_model else []
            for m in (getattr(settings, "GROQ_FALLBACK_MODELS", None) or []):
                if str(m) not in models:
                    models.append(str(m))
            if not models:
                models = ["llama-3.3-70b-versatile"]
            return [GroqProvider(model=m) for m in models]

        return [self.provider]

    @staticmethod
    def _select_provider() -> LLMProvider:
                                                 
                                                                                             
        models = list(getattr(settings, "GROQ_FALLBACK_MODELS", None) or [])
        primary = str(models[0]) if models else "llama-3.3-70b-versatile"
        return GroqProvider(model=primary)

    @staticmethod
    def _compute_prompt_hash(prompt: str, *, provider: str | None, model: str | None) -> str:
        payload = f"{provider or ''}|{model or ''}|{prompt}".encode("utf-8", errors="ignore")
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _truncate_prompt(prompt: str) -> str:
        max_chars = int(getattr(settings, "AI_MAX_PROMPT_CHARS", 20000) or 20000)
        if not isinstance(prompt, str):
            prompt = str(prompt)
        if max_chars > 0 and len(prompt) > max_chars:
            return prompt[:max_chars]
        return prompt

    @staticmethod
    def _is_garbage_text(text: str) -> bool:
        lowered = text.lower()
        return any(
            token in lowered
            for token in [
                "error code",
                "rate limit",
                "rate_limit",
                "traceback",
                "sqlalchemy",
            ]
        )

    @staticmethod
    def _expected_script_for_language(language: str) -> str | None:
                                                                                             
                                                        
        lang = (language or "").strip().lower()
        if not lang:
            return None

    @staticmethod
    def _sanitize_scrambled_parts(parts) -> list[str] | None:
        if parts is None:
            return None
        if isinstance(parts, list) and all(isinstance(p, str) and p.strip() for p in parts):
            return [p.strip() for p in parts if p.strip()]
        if isinstance(parts, str) and parts.strip():
                                                                                      
            chunks = [c.strip() for c in parts.replace("|", " ").split() if c.strip()]
            return chunks if chunks else None
        return None

                                                                       
        if lang in {"russian", "kazakh", "ukrainian", "bulgarian", "belarusian", "serbian"}:
            return "cyrillic"

                            
        if lang in {"english", "spanish", "french", "german", "italian", "portuguese", "turkish", "indonesian", "malay", "vietnamese", "dutch"}:
            return "latin"

                                
        if lang in {"arabic", "persian", "urdu"}:
            return "arabic"

                                                    
        if lang in {"chinese", "mandarin"}:
            return "han"
        if lang in {"japanese"}:
            return "japanese"
        if lang in {"korean"}:
            return "hangul"

                                 
        if lang in {"hindi"}:
            return "devanagari"

        return None

    @staticmethod
    def _script_char_regex(script: str) -> str:
        if script == "cyrillic":
            return r"[\u0400-\u04FF]"
        if script == "latin":
            return r"[A-Za-z]"
        if script == "arabic":
            return r"[\u0600-\u06FF\u0750-\u077F]"
        if script == "han":
            return r"[\u4E00-\u9FFF]"
        if script == "hangul":
            return r"[\uAC00-\uD7AF]"
        if script == "japanese":
            return r"[\u3040-\u30FF\u4E00-\u9FFF]"
        if script == "devanagari":
            return r"[\u0900-\u097F]"
        return r"$^"                         

    @classmethod
    def _count_script_letters(cls, text: str, script: str) -> int:
        if not text or not script:
            return 0
        return len(re.findall(cls._script_char_regex(script), text))

    @classmethod
    def _script_ratio(cls, text: str, expected_script: str) -> float:
        if not text or not expected_script:
            return 0.0
        exp = cls._count_script_letters(text, expected_script)
                                                                                          
        total = len(re.findall(r"[A-Za-z\u0400-\u04FF\u0600-\u06FF\u0750-\u077F\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF\u0900-\u097F]", text))
        if total == 0:
            return 0.0
        return exp / total

    def _looks_like_language_mix(self, text: str, target_language: str) -> bool:
                                                                           
        if not text:
            return True

        expected = self._expected_script_for_language(target_language)
        if expected is None:
                                                                                  
            if re.search(r"[\u0600-\u06FF\u0750-\u077F\u4E00-\u9FFF]", text):
                return True
            return False

        ratio = self._script_ratio(text, expected)
                                                                                   
        if ratio < 0.80:
            return True

                                                                                             
        if expected != "latin" and re.search(r"(?:\b[a-z]{2,}\b\s*){3,}", text, re.IGNORECASE):
            return True

        return False

    def _translation_matches_native_language(self, translation: str, native_language: str) -> bool:
        expected = self._expected_script_for_language(native_language)
        if expected is None:
            return bool((translation or "").strip())

        return self._count_script_letters(translation or "", expected) >= 1

    @staticmethod
    def _normalize_fill_blank_sentence(sentence: str) -> str:
        if not isinstance(sentence, str):
            return sentence
                                                                                     
        normalized = re.sub(r"_{3,}", "___", sentence)
        return normalized

    @staticmethod
    def _maybe_normalize_cyrillic_confusables(text: str, *, target_language: str) -> str:
        if not isinstance(text, str) or not text:
            return text

        expected = AIService._expected_script_for_language(target_language)
        if expected != "cyrillic":
            return text

                                                                                                   
        ratio = AIService._script_ratio(text, "cyrillic")
        if ratio < 0.70:
            return text

                                                                        
                                                                    
        mapping = str.maketrans(
            {
                "A": "А",
                "a": "а",
                "B": "В",
                "E": "Е",
                "e": "е",
                "K": "К",
                "k": "к",
                "M": "М",
                "H": "Н",
                "h": "һ",
                "O": "О",
                "o": "о",
                "P": "Р",
                "p": "р",
                "C": "С",
                "c": "с",
                "T": "Т",
                "y": "у",
                "X": "Х",
                "x": "х",
                "s": "с",
                "S": "С",
            }
        )
        return text.translate(mapping)

    def _normalize_lesson_json_inplace(self, data: dict) -> None:
                                                                                            
        if not isinstance(data, dict):
            return

        exercises = data.get("exercises")
        if not isinstance(exercises, list):
            return

        for ex in exercises:
            if not isinstance(ex, dict):
                continue
            if ex.get("type") == "fill_blank" and isinstance(ex.get("sentence"), str):
                ex["sentence"] = self._normalize_fill_blank_sentence(ex["sentence"])

    def _validate_exercises(self, exercises: list[dict], *, target_language: str) -> list[dict]:
        errors: list[dict] = []

        if not exercises:
            return [
                {
                    "code": "exercises_invalid",
                    "field": "exercises",
                    "reason": "missing_or_empty",
                    "message": "Exercises list is missing or empty",
                }
            ]

        for idx, ex in enumerate(exercises):
            if not isinstance(ex, dict):
                errors.append(
                    {
                        "code": "exercise_invalid",
                        "field": f"exercises[{idx}]",
                        "reason": "not_object",
                        "message": "Exercise item is not an object",
                    }
                )
                continue

            ex_type = ex.get("type")
            if not isinstance(ex_type, str) or not ex_type.strip():
                errors.append(
                    {
                        "code": "exercise_invalid",
                        "field": f"exercises[{idx}].type",
                        "reason": "missing",
                        "message": "Exercise missing 'type'",
                    }
                )
                continue

            if ex_type == "quiz":
                q = ex.get("question")
                if not isinstance(q, str) or not q.strip():
                    errors.append(
                        {
                            "code": "exercise_invalid",
                            "field": f"exercises[{idx}].question",
                            "reason": "missing",
                            "message": "Quiz missing 'question'",
                        }
                    )
                else:
                    q_norm = self._maybe_normalize_cyrillic_confusables(q, target_language=target_language)
                    ex["question"] = q_norm
                    if self._looks_like_language_mix(q_norm, target_language):
                        errors.append(
                            {
                                "code": "exercise_invalid",
                                "field": f"exercises[{idx}].question",
                                "reason": "language_mix",
                                "message": "Quiz question language is invalid",
                            }
                        )

                options = ex.get("options")
                if not isinstance(options, list) or len(options) < 3:
                    errors.append(
                        {
                            "code": "exercise_invalid",
                            "field": f"exercises[{idx}].options",
                            "reason": "invalid",
                            "message": "Quiz has invalid 'options'",
                        }
                    )
                else:
                    for j, opt in enumerate(options):
                        if not isinstance(opt, str) or not opt.strip():
                            errors.append(
                                {
                                    "code": "exercise_invalid",
                                    "field": f"exercises[{idx}].options[{j}]",
                                    "reason": "missing",
                                    "message": "Quiz option is invalid",
                                }
                            )
                            continue
                        opt_norm = self._maybe_normalize_cyrillic_confusables(opt, target_language=target_language)
                        options[j] = opt_norm
                        if self._looks_like_language_mix(opt_norm, target_language):
                            errors.append(
                                {
                                    "code": "exercise_invalid",
                                    "field": f"exercises[{idx}].options[{j}]",
                                    "reason": "language_mix",
                                    "message": "Quiz option language is invalid",
                                }
                            )

                ci = ex.get("correct_index")
                if not isinstance(ci, int) or not isinstance(options, list) or not (0 <= ci < len(options)):
                    errors.append(
                        {
                            "code": "exercise_invalid",
                            "field": f"exercises[{idx}].correct_index",
                            "reason": "invalid",
                            "message": "Quiz has invalid 'correct_index'",
                        }
                    )

            elif ex_type == "match":
                pairs = ex.get("pairs")
                if not isinstance(pairs, list) or len(pairs) < 3:
                    errors.append(
                        {
                            "code": "exercise_invalid",
                            "field": f"exercises[{idx}].pairs",
                            "reason": "invalid",
                            "message": "Match has invalid 'pairs'",
                        }
                    )
                else:
                    for j, p in enumerate(pairs):
                        if not isinstance(p, dict) or not isinstance(p.get("left"), str) or not isinstance(p.get("right"), str):
                            errors.append(
                                {
                                    "code": "exercise_invalid",
                                    "field": f"exercises[{idx}].pairs[{j}]",
                                    "reason": "invalid",
                                    "message": "Match pair is invalid",
                                }
                            )

            elif ex_type == "true_false":
                st = ex.get("statement")
                if not isinstance(st, str) or not st.strip():
                    errors.append(
                        {
                            "code": "exercise_invalid",
                            "field": f"exercises[{idx}].statement",
                            "reason": "missing",
                            "message": "true_false missing 'statement'",
                        }
                    )
                else:
                    st_norm = self._maybe_normalize_cyrillic_confusables(st, target_language=target_language)
                    ex["statement"] = st_norm
                    if self._looks_like_language_mix(st_norm, target_language):
                        errors.append(
                            {
                                "code": "exercise_invalid",
                                "field": f"exercises[{idx}].statement",
                                "reason": "language_mix",
                                "message": "true_false statement language is invalid",
                            }
                        )
                if not isinstance(ex.get("is_true"), bool):
                    errors.append(
                        {
                            "code": "exercise_invalid",
                            "field": f"exercises[{idx}].is_true",
                            "reason": "missing",
                            "message": "true_false missing 'is_true'",
                        }
                    )

            elif ex_type == "fill_blank":
                sentence = ex.get("sentence")
                correct = ex.get("correct_word")
                blank_index = ex.get("blank_index")
                full_sentence_native = ex.get("full_sentence_native")
                
                if not isinstance(sentence, str):
                    errors.append(
                        {
                            "code": "exercise_invalid",
                            "field": f"exercises[{idx}].sentence",
                            "reason": "invalid",
                            "message": "fill_blank has invalid 'sentence'",
                        }
                    )
                else:
                    sentence = self._normalize_fill_blank_sentence(sentence)
                    sentence = self._maybe_normalize_cyrillic_confusables(sentence, target_language=target_language)
                    if "___" not in sentence:
                        errors.append(
                            {
                                "code": "exercise_invalid",
                                "field": f"exercises[{idx}].sentence",
                                "reason": "placeholder_missing",
                                "message": "fill_blank sentence missing ___ placeholder",
                            }
                        )
                    elif self._looks_like_language_mix(sentence.replace("___", ""), target_language):
                        errors.append(
                            {
                                "code": "exercise_invalid",
                                "field": f"exercises[{idx}].sentence",
                                "reason": "language_mix",
                                "message": "fill_blank sentence language is invalid",
                            }
                        )

                    ex["sentence"] = sentence

                if not isinstance(correct, str) or not correct.strip() or len(correct.split()) > 2:
                    errors.append(
                        {
                            "code": "exercise_invalid",
                            "field": f"exercises[{idx}].correct_word",
                            "reason": "invalid",
                            "message": "fill_blank has invalid 'correct_word'",
                        }
                    )
                
                                                 
                if blank_index is not None and not isinstance(blank_index, int):
                    errors.append(
                        {
                            "code": "exercise_invalid",
                            "field": f"exercises[{idx}].blank_index",
                            "reason": "invalid",
                            "message": "fill_blank has invalid 'blank_index'",
                        }
                    )
                
                                                                           
                if full_sentence_native is not None and not isinstance(full_sentence_native, str):
                    errors.append(
                        {
                            "code": "exercise_invalid",
                            "field": f"exercises[{idx}].full_sentence_native",
                            "reason": "invalid",
                            "message": "fill_blank has invalid 'full_sentence_native'",
                        }
                    )

            elif ex_type == "scramble":
                parts = ex.get("scrambled_parts")
                correct_sentence = ex.get("correct_sentence")
                if not isinstance(parts, list) or len(parts) < 3:
                    errors.append(
                        {
                            "code": "exercise_invalid",
                            "field": f"exercises[{idx}].scrambled_parts",
                            "reason": "invalid",
                            "message": "scramble has invalid 'scrambled_parts'",
                        }
                    )
                if not isinstance(correct_sentence, str) or not correct_sentence.strip():
                    errors.append(
                        {
                            "code": "exercise_invalid",
                            "field": f"exercises[{idx}].correct_sentence",
                            "reason": "missing",
                            "message": "scramble missing 'correct_sentence'",
                        }
                    )
                else:
                    cs_norm = self._maybe_normalize_cyrillic_confusables(correct_sentence, target_language=target_language)
                    ex["correct_sentence"] = cs_norm
                    if self._looks_like_language_mix(cs_norm, target_language):
                        errors.append(
                            {
                                "code": "exercise_invalid",
                                "field": f"exercises[{idx}].correct_sentence",
                                "reason": "language_mix",
                                "message": "scramble sentence language is invalid",
                            }
                        )

            else:
                errors.append(
                    {
                        "code": "exercise_invalid",
                        "field": f"exercises[{idx}].type",
                        "reason": "unsupported_type",
                        "message": f"Unsupported exercise type: {ex_type}",
                    }
                )

        return errors

    @staticmethod
    def _sanitize_match_pairs(pairs) -> list[dict] | None:
                                                                          
                                            
        if pairs is None:
            return None

                         
        if isinstance(pairs, list) and all(
            isinstance(p, dict) and isinstance(p.get("left"), str) and isinstance(p.get("right"), str) for p in pairs
        ):
            return pairs

                                                         
        if isinstance(pairs, list) and all(isinstance(p, dict) for p in pairs):
            out: list[dict] = []
            for p in pairs:
                if not isinstance(p, dict):
                    continue
                left = p.get("left")
                right = p.get("right")
                if not isinstance(left, str) or not isinstance(right, str):
                                             
                    cand = [
                        (p.get("word"), p.get("translation")),
                        (p.get("term"), p.get("definition")),
                        (p.get("question"), p.get("answer")),
                    ]
                    left = None
                    right = None
                    for l, r in cand:
                        if isinstance(l, str) and isinstance(r, str):
                            left, right = l, r
                            break

                                                            
                    if left is None or right is None:
                        string_values = [v for v in p.values() if isinstance(v, str)]
                        if len(string_values) >= 2:
                            left, right = string_values[0], string_values[1]

                if isinstance(left, str) and isinstance(right, str):
                    out.append({"left": left, "right": right})

            return out

                               
        if isinstance(pairs, list) and all(isinstance(p, (list, tuple)) and len(p) == 2 for p in pairs):
            out: list[dict] = []
            for left, right in pairs:
                if isinstance(left, str) and isinstance(right, str):
                    out.append({"left": left, "right": right})
            return out

                               
        if isinstance(pairs, dict):
            out = []
            for k, v in pairs.items():
                if isinstance(k, str) and isinstance(v, str):
                    out.append({"left": k, "right": v})
            return out

                                                      
        if isinstance(pairs, dict) and isinstance(pairs.get("left"), list) and isinstance(pairs.get("right"), list):
            lefts = pairs.get("left")
            rights = pairs.get("right")
            out = []
            for l, r in zip(lefts, rights):
                if isinstance(l, str) and isinstance(r, str):
                    out.append({"left": l, "right": r})
            return out

        return None

    def _sanitize_exercises_container(self, exercises_container: dict | None) -> dict | None:
        if not isinstance(exercises_container, dict):
            return exercises_container

        exercises = exercises_container.get("exercises")
        if not isinstance(exercises, list):
            return exercises_container

        sanitized: list[dict] = []
        for ex in exercises:
            if not isinstance(ex, dict):
                continue
            if ex.get("type") == "match":
                fixed = self._sanitize_match_pairs(ex.get("pairs"))
                if fixed is None:
                                                                                            
                    continue
                ex = {**ex, "pairs": fixed}
            elif ex.get("type") == "fill_blank":
                cw = ex.get("correct_word")
                if not isinstance(cw, str) or not cw.strip():
                                                                                    
                    continue
            elif ex.get("type") == "scramble":
                sp = self._sanitize_scrambled_parts(ex.get("scrambled_parts"))
                if sp is None or len(sp) < 2:
                    continue
                ex = {**ex, "scrambled_parts": sp}
            sanitized.append(ex)

        return {**exercises_container, "exercises": sanitized}

    @staticmethod
    def _is_game_role_topic(topic: str) -> bool:
        t = (topic or "").lower()
        if not t.strip():
            return False
        markers = [
            "mobile legends",
            "moba",
            "mlbb",
            "мобла",
            "мобле",
            "моблу",
            "мобла",
            "mobile",
            "легенд",
            "marksman",
            "fighter",
            "tank",
            "mage",
            "support",
            "assassin",
            "hero",
            "heroes",
        ]

        if any(m in t for m in markers):
            return True

                                                                 
        role_words = [
            "роль",
            "рөл",
            "позиция",
            "позициясы",
        ]
        marksman_words = [
            "марк",
            "марка",
            "стрелок",
            "мерген",
            "атқыш",
            "gold lane",
            "голд лейн",
            "голд",
            "лейн",
            "лайн",
        ]
        fighter_words = [
            "файтер",
            "бойцов",
            "бойца",
            "жекпе-жек",
            "жауынгер",
            "жойғыш",
            "exp lane",
            "эксп лейн",
            "эксп",
        ]

        if any(w in t for w in role_words) and (any(w in t for w in marksman_words) or any(w in t for w in fighter_words)):
            return True

        return False

    @staticmethod
    def _has_game_context(text: str) -> bool:
        s = (text or "").lower()
        if not s.strip():
            return False
                                                                                        
        markers = [
            "ойын",
            "матч",
            "команда",
            "карта",
            "рөл",
            "роль",
            "лайн",
            "лейн",
            "голд",
            "эксп",
            "джангл",
            "лес",
            "крип",
            "миньон",
            "вышка",
            "башня",
            "фарма",
            "фарм",
            "предмет",
            "итем",
            "скилл",
            "ульт",
            "кейіпкер",
            "герой",
            "шабуыл",
            "қорған",
            "skill",
            "item",
            "lane",
        ]
        return any(m in s for m in markers)

    @staticmethod
    def _vocab_words_from_list(vocabulary: list[dict] | None) -> set[str]:
        words: set[str] = set()
        for it in vocabulary or []:
            if not isinstance(it, dict):
                continue
            w = it.get("word")
            if isinstance(w, str) and w.strip():
                words.add(w.strip())
        return words

    def _validate_exercise_traceability(
        self,
        exercises: list[dict] | None,
        *,
        vocab_words: set[str],
    ) -> list[dict]:
        errs: list[dict] = []
        if not exercises:
            return errs

        for idx, ex in enumerate(exercises):
            if not isinstance(ex, dict):
                continue

            ex_type = ex.get("type")
            if not isinstance(ex_type, str) or not ex_type.strip():
                continue

                                                                 
            expected_source = "vocab" if ex_type in {"quiz", "match"} else "text"

            src = ex.get("source")
            if not isinstance(src, str) or not src.strip():
                errs.append(
                    {
                        "code": "exercise_trace_missing",
                        "field": f"exercises[{idx}].source",
                        "reason": "missing",
                        "message": "Exercise missing source traceability field",
                    }
                )
            elif src != expected_source:
                errs.append(
                    {
                        "code": "exercise_trace_invalid",
                        "field": f"exercises[{idx}].source",
                        "reason": "wrong_source",
                        "message": f"Exercise source must be '{expected_source}'",
                    }
                )

            targets = ex.get("targets")
            if not isinstance(targets, list) or not targets:
                errs.append(
                    {
                        "code": "exercise_trace_missing",
                        "field": f"exercises[{idx}].targets",
                        "reason": "missing",
                        "message": "Exercise missing targets traceability field",
                    }
                )
                continue

            for j, t in enumerate(targets):
                if not isinstance(t, str) or not t.strip():
                    errs.append(
                        {
                            "code": "exercise_trace_invalid",
                            "field": f"exercises[{idx}].targets[{j}]",
                            "reason": "invalid",
                            "message": "Target must be a non-empty string",
                        }
                    )
                    continue
                if t.strip() not in vocab_words:
                    errs.append(
                        {
                            "code": "exercise_trace_invalid",
                            "field": f"exercises[{idx}].targets[{j}]",
                            "reason": "not_in_vocab",
                            "message": "Target is not present in lesson vocabulary",
                        }
                    )

        return errs

    def _validate_sentence_source(
        self,
        exercises: list[dict] | None,
        *,
        lesson_text: str,
    ) -> list[dict]:
        errors: list[dict] = []
        if not exercises or not isinstance(lesson_text, str) or not lesson_text.strip():
            return errors

        text = lesson_text
        for idx, ex in enumerate(exercises):
            if not isinstance(ex, dict):
                continue
            ex_type = ex.get("type")
            if ex_type not in {"true_false", "fill_blank", "scramble"}:
                continue

            ss = ex.get("sentence_source")
            if not isinstance(ss, str) or not ss.strip():
                errors.append(
                    {
                        "code": "exercise_sentence_source_missing",
                        "field": f"exercises[{idx}].sentence_source",
                        "reason": "missing",
                        "message": "Text-based exercise missing sentence_source",
                    }
                )
                continue

                                                                 
            if ss not in text:
                errors.append(
                    {
                        "code": "exercise_sentence_source_invalid",
                        "field": f"exercises[{idx}].sentence_source",
                        "reason": "not_in_text",
                        "message": "sentence_source must be an exact substring of the lesson text",
                    }
                )

        return errors

    def _collect_text_and_vocab_errors(self, data: dict, *, target_language: str, native_language: str) -> list[dict]:
        if not isinstance(data, dict):
            return [
                {
                    "code": "invalid_json",
                    "field": "$",
                    "reason": "not_object",
                    "message": "Lesson response is not a JSON object",
                }
            ]

        text = data.get("text")
        vocab = data.get("vocabulary")

        errors: list[dict] = []

        if not isinstance(text, str) or not text.strip():
            errors.append({"code": "missing_text", "field": "text", "reason": "missing", "message": "Missing lesson text"})
        else:
            text_norm = self._maybe_normalize_cyrillic_confusables(text, target_language=target_language)
            data["text"] = text_norm

            if self._is_garbage_text(text_norm):
                errors.append({"code": "garbage_text", "field": "text", "reason": "garbage", "message": "Text looks like error output"})
            if self._looks_like_language_mix(text_norm, target_language):
                errors.append({"code": "text_language_invalid", "field": "text", "reason": "language_mix", "message": "Text language invalid"})

        if not isinstance(vocab, list) or len(vocab) < 4:
            errors.append({"code": "vocabulary_invalid", "field": "vocabulary", "reason": "missing_or_small", "message": "Vocabulary is missing or too small"})
            vocab = []

                                       
        for i, item in enumerate(vocab):
            if not isinstance(item, dict):
                errors.append({"code": "vocabulary_item_invalid", "field": f"vocabulary[{i}]", "reason": "not_object", "message": "Vocabulary item invalid"})
                continue

            word = item.get("word")
            if not isinstance(word, str) or not word.strip():
                errors.append({"code": "vocabulary_word_missing", "field": f"vocabulary[{i}].word", "reason": "missing", "message": "Word missing"})
            else:
                w_norm = self._maybe_normalize_cyrillic_confusables(word.strip(), target_language=target_language)
                item["word"] = w_norm
                if len(w_norm) > 40:
                    errors.append({"code": "vocabulary_word_invalid", "field": f"vocabulary[{i}].word", "reason": "too_long", "message": "Word too long"})

            tr = item.get("translation")
            if not isinstance(tr, str) or not tr.strip():
                errors.append({"code": "vocabulary_translation_missing", "field": f"vocabulary[{i}].translation", "reason": "missing", "message": "Translation missing"})
            else:
                tr_s = tr.strip()
                if len(tr_s) > 80:
                    errors.append({"code": "vocabulary_translation_invalid", "field": f"vocabulary[{i}].translation", "reason": "too_long", "message": "Translation too long"})
                if not self._translation_matches_native_language(tr_s, native_language):
                    errors.append({"code": "translation_language_invalid", "field": f"vocabulary[{i}].translation", "reason": "wrong_script", "message": "Translation not in native language script"})
                                                                                                                           
                                                                                                                             
                target_script = self._expected_script_for_language(target_language)
                native_script = self._expected_script_for_language(native_language)
                if target_script and native_script and target_script != native_script:
                    if self._count_script_letters(tr_s, target_script) >= 2:
                        errors.append({"code": "translation_contains_target_script", "field": f"vocabulary[{i}].translation", "reason": "contains_target", "message": "Translation contains target-language script"})

            ctx = item.get("context")
            if not isinstance(ctx, str) or not ctx.strip():
                errors.append({"code": "vocabulary_context_missing", "field": f"vocabulary[{i}].context", "reason": "missing", "message": "Context missing"})
            else:
                ctx_norm = self._maybe_normalize_cyrillic_confusables(ctx.strip(), target_language=target_language)
                item["context"] = ctx_norm
                if self._looks_like_language_mix(ctx_norm, target_language):
                    errors.append({"code": "context_language_invalid", "field": f"vocabulary[{i}].context", "reason": "language_mix", "message": "Context language invalid"})

        return errors

    def _validate_lesson_json(self, data: dict, *, target_language: str, native_language: str) -> list[dict]:
                                                                          
        self._normalize_lesson_json_inplace(data)

        errors = self._collect_text_and_vocab_errors(
            data,
            target_language=target_language,
            native_language=native_language,
        )

        exercises = data.get("exercises")
        if not isinstance(exercises, list) or len(exercises) < 3:
            errors.append({"code": "exercises_invalid", "field": "exercises", "reason": "missing_or_small", "message": "Exercises missing/too small"})
        else:
            errors.extend(self._validate_exercises(exercises, target_language=target_language))

        return errors

    def _validate_text_and_vocab(self, data: dict, *, target_language: str, native_language: str) -> list[dict]:
        return self._collect_text_and_vocab_errors(
            data,
            target_language=target_language,
            native_language=native_language,
        )

    async def _fix_json_with_patch(
        self,
        *,
        invalid_json: dict,
        errors: list[str],
        instruction: str,
        db: AsyncSession | None = None,
        strict_multistep: bool = False,
    ) -> dict:
        payload = json.dumps(invalid_json, ensure_ascii=False)
        prompt = (
            instruction
            + "\n\nINVALID_JSON:\n"
            + payload
            + "\n\nVALIDATION_ERRORS:\n"
            + "- "
            + "\n- ".join(errors or ["unknown"])
            + "\n\nRULES:\n"
            + "- Return corrected JSON ONLY.\n"
            + "- Keep the SAME top-level structure and keys; only edit values and add missing required fields.\n"
            + "- Do NOT add any commentary or markdown.\n"
        )
        prompt = self._truncate_prompt(prompt)
        return await self._generate_json_with_retries(
            prompt,
            max_attempts=3,
            db=db,
            use_cache=True,
            temperature=float(getattr(settings, "AI_TEMPERATURE_REPAIR", 0.1) or 0.1),
        )

    @staticmethod
    def _errors_to_patch_lines(errors: list[dict]) -> list[str]:
        lines: list[str] = []
        for e in errors or []:
            if not isinstance(e, dict):
                continue
            code = e.get("code")
            field = e.get("field")
            reason = e.get("reason")
            msg = e.get("message")
            parts = [str(p) for p in [code, field, reason, msg] if p]
            if parts:
                lines.append(" | ".join(parts))
        return lines or ["unknown"]

    def _build_course_context_suffix(
        self,
        *,
        topic: str | None = None,
        verified_topic_context: str | None = None,
        prior_topics: list[str] | None,
        used_words: list[str] | None,
        opening_sentences: list[str] | None = None,
        recent_exercise_types: list[str] | None = None,
        target_language: str,
        native_language: str,
    ) -> str:
        prior_topics = prior_topics or []
        used_words = used_words or []
        opening_sentences = opening_sentences or []
        recent_exercise_types = recent_exercise_types or []

                                      
        prior_topics = prior_topics[:30]
        used_words = used_words[:80]
        opening_sentences = opening_sentences[:10]
        recent_exercise_types = recent_exercise_types[:30]

        suffix = (
            "\n\nCOURSE MEMORY / ANTI-REPETITION RULES:\n"
            f"- The course target language is {target_language}. The ONLY language allowed in the lesson text is {target_language}.\n"
            f"- The ONLY language allowed in 'translation' fields is {native_language}.\n"
            "- Do NOT start the lesson with generic filler like 'I like this game' unless it is essential. Start directly on the topic.\n"
        )

        if topic and str(topic).strip():
            suffix += f"- Current unit topic: {str(topic).strip()}\n"

        if verified_topic_context and str(verified_topic_context).strip():
            suffix += "- VERIFIED TOPIC CONTEXT (from web sources, use as ground truth; if missing details, do NOT invent):\n"
            suffix += "  " + "\n  ".join(str(verified_topic_context).strip().splitlines()) + "\n"

        if prior_topics:
            suffix += "- Topics already covered (do NOT repeat the same scenarios/examples):\n"
            suffix += "  - " + "\n  - ".join(prior_topics) + "\n"

        if used_words:
            suffix += "- Words already used in previous lessons (avoid repeating them as vocabulary targets):\n"
            suffix += "  - " + ", ".join(used_words) + "\n"

        if opening_sentences:
            suffix += "- Recent lesson openings (avoid starting the lesson with the same first sentence/structure):\n"
            suffix += "  - " + "\n  - ".join([s.replace("\n", " ").strip() for s in opening_sentences if str(s).strip()][:10]) + "\n"

        if recent_exercise_types:
            suffix += "- Recent exercise types used (vary the pattern, avoid repeating the exact same sequence):\n"
            suffix += "  - " + ", ".join([str(t).strip() for t in recent_exercise_types if str(t).strip()][:30]) + "\n"

        suffix += "- Ensure this lesson introduces NEW vocabulary and NEW examples compared to prior lessons.\n"
        return suffix

    @staticmethod
    def _issues_to_patch_lines(issues: list[dict]) -> list[str]:
        lines: list[str] = []
        for it in issues or []:
            if not isinstance(it, dict):
                continue
            code = it.get("code")
            field = it.get("field")
            why = it.get("why")
            hint = it.get("fix_hint")
            parts = [str(p) for p in [code, field, why, hint] if p]
            if parts:
                lines.append(" | ".join(parts))
        return lines or ["unknown"]

    async def _strict_plan(
        self,
        *,
        topic: str,
        target_language: str,
        native_language: str,
        level: str,
        interests: str,
        prior_topics: list[str] | None,
        used_words: list[str] | None,
        db: AsyncSession | None,
    ) -> dict:
        prompt = LESSON_PLAN_TEMPLATE.format(
            target_language=target_language,
            native_language=native_language,
            level=level,
            topic=topic,
            interests=interests,
            prior_topics="\n".join([f"- {t}" for t in (prior_topics or [])[:30]]) or "- none",
            used_words=", ".join((used_words or [])[:80]) or "none",
        )
        return await self._generate_json_with_retries(prompt, max_attempts=4, db=db, use_cache=False)

    async def _strict_review_and_fix_core(
        self,
        *,
        lesson_core: dict,
        topic: str,
        target_language: str,
        native_language: str,
        level: str,
        db: AsyncSession | None,
    ) -> tuple[dict, list[dict]]:
        review_prompt = LESSON_REVIEW_TEMPLATE.format(
            target_language=target_language,
            native_language=native_language,
            topic=topic,
            level=level,
        ) + "\n\nLESSON_JSON:\n" + json.dumps(lesson_core, ensure_ascii=False)
        review = await self._generate_json_with_retries(review_prompt, max_attempts=3, db=db, use_cache=False)
        issues = review.get("issues") if isinstance(review, dict) else None
        issues_list: list[dict] = list(issues) if isinstance(issues, list) else []
        if not issues_list:
            return lesson_core, []

        fixed = await self._fix_json_with_patch(
            invalid_json=lesson_core,
            errors=self._issues_to_patch_lines(issues_list),
            instruction=(
                f"You previously generated lesson JSON for {target_language}/{native_language} but it needs improvements. "
                f"Fix the SAME JSON." 
            ),
            db=db,
        )
        return fixed, issues_list

    async def _strict_review_and_fix_exercises(
        self,
        *,
        exercises_container: dict,
        target_language: str,
        native_language: str,
        topic: str,
        text: str,
        vocab_pairs: str,
        db: AsyncSession | None,
    ) -> tuple[dict, list[dict]]:
        review_prompt = EXERCISES_REVIEW_TEMPLATE.format(
            target_language=target_language,
            native_language=native_language,
            topic=topic,
        )
        review_prompt += "\n\nTEXT:\n" + str(text or "")
        review_prompt += "\n\nVOCAB_PAIRS:\n" + str(vocab_pairs or "")
        review_prompt += "\n\nEXERCISES_JSON:\n" + json.dumps(exercises_container, ensure_ascii=False)
        review = await self._generate_json_with_retries(review_prompt, max_attempts=3, db=db, use_cache=False)
        issues = review.get("issues") if isinstance(review, dict) else None
        issues_list: list[dict] = list(issues) if isinstance(issues, list) else []
        if not issues_list:
            return exercises_container, []

        fixed = await self._fix_json_with_patch(
            invalid_json=exercises_container,
            errors=self._issues_to_patch_lines(issues_list),
            instruction=(
                f"You previously generated ONLY exercises JSON for a {target_language} lesson. Fix ONLY the exercises JSON." 
            ),
            db=db,
        )
        return fixed, issues_list

    @staticmethod
    def _extract_retry_after_seconds(error_message: str) -> float | None:
                                                                                            
        match = re.search(
            r"try again in\s+(?:(?P<minutes>[0-9]+)m)?(?P<seconds>[0-9]+(?:\.[0-9]+)?)s",
            error_message,
            re.IGNORECASE,
        )
        if match:
            try:
                minutes = float(match.group("minutes")) if match.group("minutes") else 0.0
                seconds = float(match.group("seconds"))
                return minutes * 60.0 + seconds
            except ValueError:
                return None
        return None

    async def _generate_json_with_retries(
        self,
        prompt: str,
        *,
        max_attempts: int = 5,
        db: AsyncSession | None = None,
        use_cache: bool = True,
        temperature: float | None = None,
    ) -> dict:
        last_exc: Exception | None = None
        prompt = self._truncate_prompt(prompt)
        candidates = self._provider_candidates()

        for candidate in candidates:
            if self._is_circuit_open(candidate):
                continue

            provider_name = type(candidate).__name__ if candidate else None
            model_name = getattr(candidate, "model", None) if candidate else None

            prompt_hash = None
            if use_cache and db is not None:
                try:
                    prompt_hash = self._compute_prompt_hash(prompt, provider=provider_name, model=model_name)
                    repo = AIIOpsRepository(db)
                    cached = await repo.get_cache_by_hash(prompt_hash)
                    if cached is not None and isinstance(getattr(cached, "response_json", None), dict):
                        return dict(cached.response_json)
                except Exception:
                    prompt_hash = None

            for attempt in range(1, max_attempts + 1):
                try:
                    result = await candidate.generate_json(prompt, temperature=temperature)
                    self._record_circuit_success(candidate)

                    if use_cache and db is not None and prompt_hash is not None and isinstance(result, dict):
                        try:
                            repo = AIIOpsRepository(db)
                            await repo.create_cache_entry(
                                prompt_hash=prompt_hash,
                                prompt=prompt,
                                response_json=result,
                                provider=provider_name,
                                model=model_name,
                            )
                        except IntegrityError:
                            pass
                        except Exception:
                            pass

                    return result
                except Exception as e:
                    last_exc = e
                    message = str(e)
                    retry_after = self._extract_retry_after_seconds(message)

                    is_rate_limit = "429" in message or "rate limit" in message.lower() or "rate_limit" in message.lower()
                    is_transient = is_rate_limit or any(
                        token in message.lower()
                        for token in [
                            "timeout",
                            "timed out",
                            "temporar",
                            "service unavailable",
                            "503",
                            "connection",
                            "network",
                        ]
                    )

                    if is_transient:
                        self._record_circuit_failure(candidate)

                                                                                                               
                                                                                              
                    if is_rate_limit and retry_after is not None and retry_after >= 120.0:
                        raise ServiceException(
                            f"Provider retry requested retry_after_seconds={int(retry_after)}"
                        )

                    if attempt >= max_attempts or not is_transient:
                        break

                                                                                                                
                    if retry_after is None:
                        retry_after = min(30.0, (2 ** (attempt - 1))) + random.random()

                    logger.warning(
                        "AI transient error, retrying. provider=%s model=%s attempt=%s/%s sleep=%.2fs error=%s",
                        provider_name,
                        model_name,
                        attempt,
                        max_attempts,
                        retry_after,
                        message,
                    )
                    await asyncio.sleep(retry_after)

                                                                                                

        raise ServiceException(f"AI generation failed: {str(last_exc) if last_exc else 'unknown error'}")

    async def generate_lesson(
        self,
        topic: str,
        target_language: str,
        native_language: str,
        level: str,
        interests: list[str] = None,
        prior_topics: list[str] | None = None,
        used_words: list[str] | None = None,
        opening_sentences: list[str] | None = None,
        recent_exercise_types: list[str] | None = None,
        generation_mode: GenerationMode = "balanced",
        db: AsyncSession | None = None,
    ) -> dict:
        if not settings.AI_ENABLED:
            raise ServiceException("AI is disabled")

        mode: GenerationMode = generation_mode if generation_mode in {"fast", "balanced", "strict"} else "balanced"
        ex_repairs_max = 0 if mode == "fast" else (2 if mode == "balanced" else 4)
        max_ai_attempts = 3 if mode == "fast" else (5 if mode == "balanced" else 7)

        provider_name = type(self.provider).__name__ if getattr(self, "provider", None) else None
        model_name = getattr(self.provider, "model", None) if getattr(self, "provider", None) else None

                                                                                       
        if mode == "strict":
            lesson_core = await self.generate_text_vocab_only(
                topic=topic,
                target_language=target_language,
                native_language=native_language,
                level=level,
                interests=interests,
                prior_topics=prior_topics,
                used_words=used_words,
                opening_sentences=opening_sentences,
                recent_exercise_types=recent_exercise_types,
                generation_mode=mode,
                db=db,
                strict_multistep=True,
            )
        else:
            lesson_core = await self.generate_text_vocab_only(
                topic=topic,
                target_language=target_language,
                native_language=native_language,
                level=level,
                interests=interests,
                prior_topics=prior_topics,
                used_words=used_words,
                opening_sentences=opening_sentences,
                recent_exercise_types=recent_exercise_types,
                generation_mode=mode,
                db=db,
                strict_multistep=False,
            )

        meta_core = lesson_core.get("_meta") if isinstance(lesson_core, dict) else None
        validation_errors: list[dict] = (
            list(meta_core.get("validation_errors")) if isinstance(meta_core, dict) and isinstance(meta_core.get("validation_errors"), list) else []
        )
        repair_count = int(meta_core.get("repair_count") or 0) if isinstance(meta_core, dict) else 0

        text = str(lesson_core.get("text") or "")
        vocab_list = lesson_core.get("vocabulary") or []
        vocab_pairs = "\n".join(
            f"- {str(it.get('word','')).strip()} -> {str(it.get('translation','')).strip()}" for it in vocab_list if isinstance(it, dict)
        )

        exercises_container: dict
        vocab_words = self._vocab_words_from_list(vocab_list)

        if mode == "strict":
                                                       
            ex_vocab = await self.generate_exercises_vocab_only(
                vocabulary=vocab_list,
                target_language=target_language,
                native_language=native_language,
                topic=topic,
                db=db,
            )
            ex_text = await self.generate_exercises_text_only(
                text=text,
                vocabulary=vocab_list,
                target_language=target_language,
                native_language=native_language,
                topic=topic,
                db=db,
            )
            exercises_container = {
                "exercises": list(ex_vocab.get("exercises") or []) + list(ex_text.get("exercises") or [])
            }
        else:
                                    
            prompt_ex = LESSON_EXERCISES_TEMPLATE.format(
                topic=topic,
                target_language=target_language,
                native_language=native_language,
                text=text,
                vocab_pairs=vocab_pairs,
            )
            exercises_container = await self._generate_json_with_retries(
                prompt_ex,
                max_attempts=max_ai_attempts,
                db=db,
                use_cache=True,
            )

        exercises_attempts = 0
        quality_status = "ok"

                                                                                             
        exercises_container = self._sanitize_exercises_container(exercises_container)

        for _ in range(0, ex_repairs_max + 1):
            exercises_attempts += 1

                                                                            
            exercises_container = self._sanitize_exercises_container(exercises_container)
            exercises = exercises_container.get("exercises") if isinstance(exercises_container, dict) else None
            errs = self._validate_exercises(exercises, target_language=target_language)
            if not errs:
                break

            validation_errors.extend(errs)
            if (exercises_attempts - 1) >= ex_repairs_max:
                break

            logger.warning("AI exercises validation failed, attempting JSON fix: %s", errs)
            exercises_container = await self._fix_json_with_patch(
                invalid_json=exercises_container,
                errors=self._errors_to_patch_lines(errs),
                instruction=(
                    f"You previously generated ONLY exercises JSON for a {target_language} lesson. Fix ONLY the exercises JSON." 
                ),
                db=db,
            )

            exercises_container = self._sanitize_exercises_container(exercises_container)

                                                                               
        if mode == "strict" and isinstance(exercises_container, dict):
            exercises = exercises_container.get("exercises") if isinstance(exercises_container, dict) else None
            trace_errs = self._validate_exercise_traceability(exercises, vocab_words=vocab_words)
            if trace_errs:
                validation_errors.extend(trace_errs)

                exercises_container = await self._fix_json_with_patch(
                    invalid_json=exercises_container,
                    errors=self._errors_to_patch_lines(trace_errs),
                    instruction=(
                        f"You previously generated ONLY exercises JSON for a {target_language} lesson. "
                        f"Add/repair traceability fields: source (must match exercise type: quiz/match=vocab, others=text) "
                        f"and targets (each must be from the lesson vocabulary)."
                    ),
                    db=db,
                )

                                                                                      
            exercises = exercises_container.get("exercises") if isinstance(exercises_container, dict) else None
            ss_errs = self._validate_sentence_source(exercises, lesson_text=text)
            if ss_errs:
                validation_errors.extend(ss_errs)
                exercises_container = await self._fix_json_with_patch(
                    invalid_json=exercises_container,
                    errors=self._errors_to_patch_lines(ss_errs),
                    instruction=(
                        f"You previously generated ONLY exercises JSON for a {target_language} lesson. "
                        f"For every text-based exercise (true_false/fill_blank/scramble) set sentence_source to an EXACT substring from the provided lesson text."
                    ),
                    db=db,
                )

                                                                                                                  
        if mode == "strict" and isinstance(exercises_container, dict):
            try:
                reviewed_ex, ex_issues = await self._strict_review_and_fix_exercises(
                    exercises_container=exercises_container,
                    target_language=target_language,
                    native_language=native_language,
                    topic=topic,
                    text=text,
                    vocab_pairs=vocab_pairs,
                    db=db,
                )
                if isinstance(reviewed_ex, dict):
                    exercises_container = reviewed_ex
                if ex_issues:
                    validation_errors.extend(
                        [
                            {
                                "code": (it.get("code") or "exercise_review_issue"),
                                "field": (it.get("field") or "exercises"),
                                "reason": "review",
                                "message": (it.get("why") or ""),
                            }
                            for it in (ex_issues or [])
                            if isinstance(it, dict)
                        ]
                    )
            except Exception:
                pass

        if self._validate_exercises(
            exercises_container.get("exercises") if isinstance(exercises_container, dict) else None,
            target_language=target_language,
        ):
                                                                           
            exercises_container = {"exercises": []}
            quality_status = "needs_review"

        out = {
            "text": text,
            "vocabulary": vocab_list,
            "exercises": exercises_container.get("exercises", []) if isinstance(exercises_container, dict) else [],
            "_meta": {
                "generation_mode": mode,
                "repair_count": repair_count,
                "exercise_attempts": exercises_attempts,
                "validation_errors": validation_errors,
                "provider": provider_name,
                "model": model_name,
                "quality_status": quality_status,
            },
        }

                                                                                                        
        if mode == "balanced":
            too_many_errors = len(validation_errors) >= 6
            if quality_status == "needs_review" or too_many_errors:
                try:
                    strict_out = await self.generate_lesson(
                        topic=topic,
                        target_language=target_language,
                        native_language=native_language,
                        level=level,
                        interests=interests,
                        prior_topics=prior_topics,
                        used_words=used_words,
                        opening_sentences=opening_sentences,
                        recent_exercise_types=recent_exercise_types,
                        generation_mode="strict",
                        db=db,
                    )
                    return strict_out
                except Exception:
                    return out

        return out

    async def generate_text_only(
        self,
        *,
        topic: str,
        target_language: str,
        native_language: str,
        level: str,
        interests: str,
        prior_topics: list[str] | None,
        used_words: list[str] | None,
        opening_sentences: list[str] | None,
        recent_exercise_types: list[str] | None,
        db: AsyncSession | None,
    ) -> dict:
        base_suffix = self._build_course_context_suffix(
            topic=topic,
            prior_topics=prior_topics,
            used_words=used_words,
            opening_sentences=opening_sentences,
            recent_exercise_types=recent_exercise_types,
            target_language=target_language,
            native_language=native_language,
        )
        prompt = LESSON_TEXT_ONLY_TEMPLATE.format(
            target_language=target_language,
            native_language=native_language,
            topic=topic,
            level=level,
            interests=interests,
        ) + base_suffix
        return await self._generate_json_with_retries(
            prompt,
            max_attempts=6,
            db=db,
            use_cache=True,
            temperature=float(getattr(settings, "AI_TEMPERATURE_TEXT", 0.6) or 0.6),
        )

    async def extract_vocab_from_text(
        self,
        *,
        text: str,
        target_language: str,
        native_language: str,
        level: str,
        db: AsyncSession | None,
    ) -> dict:
        prompt = VOCAB_FROM_TEXT_TEMPLATE.format(
            target_language=target_language,
            native_language=native_language,
            level=level,
            text=str(text or ""),
        )
        return await self._generate_json_with_retries(
            prompt,
            max_attempts=6,
            db=db,
            use_cache=True,
            temperature=float(getattr(settings, "AI_TEMPERATURE_JSON", 0.2) or 0.2),
        )

    async def generate_exercises_vocab_only(
        self,
        *,
        vocabulary: list[dict],
        target_language: str,
        native_language: str,
        topic: str,
        db: AsyncSession | None,
    ) -> dict:
        vocab_pairs = "\n".join(
            f"- {str(it.get('word','')).strip()} -> {str(it.get('translation','')).strip()}"
            for it in (vocabulary or [])
            if isinstance(it, dict)
        )
        prompt = VOCAB_EXERCISES_TEMPLATE.format(
            target_language=target_language,
            native_language=native_language,
            topic=topic,
            vocab_pairs=vocab_pairs,
        )
        prompt = self._truncate_prompt(prompt)
        return await self._generate_json_with_retries(
            prompt,
            max_attempts=6,
            db=db,
            use_cache=True,
            temperature=float(getattr(settings, "AI_TEMPERATURE_JSON", 0.2) or 0.2),
        )

    async def generate_exercises_text_only(
        self,
        *,
        text: str,
        vocabulary: list[dict],
        target_language: str,
        native_language: str,
        topic: str,
        db: AsyncSession | None,
    ) -> dict:
        vocab_pairs = "\n".join(
            f"- {str(it.get('word','')).strip()} -> {str(it.get('translation','')).strip()}"
            for it in (vocabulary or [])
            if isinstance(it, dict)
        )
        prompt = TEXT_EXERCISES_TEMPLATE.format(
            target_language=target_language,
            native_language=native_language,
            topic=topic,
            text=str(text or ""),
            vocab_pairs=vocab_pairs,
        )
        prompt = self._truncate_prompt(prompt)
        return await self._generate_json_with_retries(
            prompt,
            max_attempts=6,
            db=db,
            use_cache=True,
            temperature=float(getattr(settings, "AI_TEMPERATURE_JSON", 0.2) or 0.2),
        )

    async def generate_text_vocab_only(
        self,
        *,
        topic: str,
        target_language: str,
        native_language: str,
        level: str,
        interests: list[str] | None = None,
        prior_topics: list[str] | None = None,
        used_words: list[str] | None = None,
        opening_sentences: list[str] | None = None,
        recent_exercise_types: list[str] | None = None,
        generation_mode: GenerationMode = "balanced",
        db: AsyncSession | None = None,
        strict_multistep: bool = False,
    ) -> dict:
        if not settings.AI_ENABLED:
            raise ServiceException("AI is disabled")

        mode: GenerationMode = generation_mode if generation_mode in {"fast", "balanced", "strict"} else "balanced"
        core_repairs_max = 0 if mode == "fast" else (2 if mode == "balanced" else 4)
        max_ai_attempts = 3 if mode == "fast" else (5 if mode == "balanced" else 7)

        interests_str = ", ".join(interests) if interests else "General Topics"

        provider_name = type(self.provider).__name__ if getattr(self, "provider", None) else None
        model_name = getattr(self.provider, "model", None) if getattr(self, "provider", None) else None

        verified = None
        try:
            r = await self.topic_retrieval.retrieve(topic)
            verified = r.to_prompt_block() if r is not None else None
        except Exception:
            verified = None

        base_suffix = self._build_course_context_suffix(
            topic=topic,
            verified_topic_context=verified,
            prior_topics=prior_topics,
            used_words=used_words,
            opening_sentences=opening_sentences,
            recent_exercise_types=recent_exercise_types,
            target_language=target_language,
            native_language=native_language,
        )

        plan_payload = None
        if mode == "strict":
            try:
                plan_payload = await self._strict_plan(
                    topic=topic,
                    target_language=target_language,
                    native_language=native_language,
                    level=level,
                    interests=interests_str,
                    prior_topics=prior_topics,
                    used_words=used_words,
                    db=db,
                )
            except Exception:
                plan_payload = None

        prompt_text_vocab = LESSON_TEXT_VOCAB_TEMPLATE.format(
            target_language=target_language,
            native_language=native_language,
            topic=topic,
            level=level,
            interests=interests_str,
        ) + base_suffix

        if isinstance(plan_payload, dict) and plan_payload:
            prompt_text_vocab += "\n\nLESSON_PLAN_JSON (follow this plan):\n" + json.dumps(plan_payload, ensure_ascii=False)

                                                                           
        if mode == "strict" and strict_multistep:
            text_payload = await self.generate_text_only(
                topic=topic,
                target_language=target_language,
                native_language=native_language,
                level=level,
                interests=interests_str,
                prior_topics=prior_topics,
                used_words=used_words,
                opening_sentences=opening_sentences,
                recent_exercise_types=recent_exercise_types,
                db=db,
            )
            text_val = str(text_payload.get("text") or "") if isinstance(text_payload, dict) else ""
            vocab_payload = await self.extract_vocab_from_text(
                text=text_val,
                target_language=target_language,
                native_language=native_language,
                level=level,
                db=db,
            )
            lesson_core = {
                "text": text_val,
                "vocabulary": (vocab_payload.get("vocabulary") if isinstance(vocab_payload, dict) else []) or [],
            }
        else:
            lesson_core = await self._generate_json_with_retries(
                prompt_text_vocab,
                max_attempts=max_ai_attempts,
                db=db,
                use_cache=True,
            )
        validation_errors: list[dict] = []
        repair_count = 0

        for _ in range(0, core_repairs_max + 1):
            errs = self._validate_text_and_vocab(
                lesson_core,
                target_language=target_language,
                native_language=native_language,
            )

                                                                          
            if mode == "strict" and self._is_game_role_topic(topic):
                txt = str(lesson_core.get("text") or "") if isinstance(lesson_core, dict) else ""
                if not self._has_game_context(txt):
                    errs = list(errs) + [
                        {
                            "code": "topic_not_game_context",
                            "field": "text",
                            "reason": "topic_relevance",
                            "message": "Topic indicates a MOBA game/roles, but the text lacks game context (match/team/roles/map/items).",
                        }
                    ]

            if not errs:
                break
            validation_errors.extend(errs)
            if repair_count >= core_repairs_max:
                break
            logger.warning("AI lesson core validation failed, attempting JSON fix: %s", errs)
            repair_count += 1
            lesson_core = await self._fix_json_with_patch(
                invalid_json=lesson_core,
                errors=self._errors_to_patch_lines(errs),
                instruction=(
                    f"You previously generated lesson JSON for {target_language}/{native_language} but it failed validation. "
                    f"Fix the SAME JSON. If the topic is about a MOBA game / Mobile Legends roles (marksman/fighter/etc.), rewrite the text to be explicitly about the video game (match, team, roles, map, items), not real-life warriors." 
                ),
                db=db,
            )

        core_final_errs = self._validate_text_and_vocab(
            lesson_core,
            target_language=target_language,
            native_language=native_language,
        )
        if core_final_errs:
            validation_errors.extend(core_final_errs)
            raise ServiceException("AI lesson core failed validation")

        if mode == "strict":
            try:
                reviewed, review_issues = await self._strict_review_and_fix_core(
                    lesson_core=lesson_core,
                    topic=topic,
                    target_language=target_language,
                    native_language=native_language,
                    level=level,
                    db=db,
                )
                if isinstance(reviewed, dict):
                    lesson_core = reviewed
                    if review_issues:
                        validation_errors.extend(
                            [
                                {
                                    "code": (it.get("code") or "review_issue"),
                                    "field": (it.get("field") or "review"),
                                    "reason": "review",
                                    "message": (it.get("why") or ""),
                                }
                                for it in (review_issues or [])
                                if isinstance(it, dict)
                            ]
                        )
                        repair_count += 1
            except Exception:
                pass

        return {
            "text": str(lesson_core.get("text") or "") if isinstance(lesson_core, dict) else "",
            "vocabulary": lesson_core.get("vocabulary", []) if isinstance(lesson_core, dict) else [],
            "_meta": {
                "generation_mode": mode,
                "repair_count": repair_count,
                "validation_errors": validation_errors,
                "provider": provider_name,
                "model": model_name,
            },
        }

    async def generate_exercises_only(
        self,
        *,
        topic: str,
        text: str,
        vocabulary: list[dict],
        target_language: str,
        native_language: str,
        generation_mode: GenerationMode = "balanced",
        db: AsyncSession | None = None,
    ) -> dict:
        if not settings.AI_ENABLED:
            raise ServiceException("AI is disabled")

        mode: GenerationMode = generation_mode if generation_mode in {"fast", "balanced", "strict"} else "balanced"
        ex_repairs_max = 0 if mode == "fast" else (2 if mode == "balanced" else 4)
        max_ai_attempts = 3 if mode == "fast" else (5 if mode == "balanced" else 7)

        provider_name = type(self.provider).__name__ if getattr(self, "provider", None) else None
        model_name = getattr(self.provider, "model", None) if getattr(self, "provider", None) else None

        vocab_pairs = "\n".join(
            f"- {str(it.get('word','')).strip()} -> {str(it.get('translation','')).strip()}"
            for it in (vocabulary or [])
            if isinstance(it, dict)
        )

        prompt_ex = LESSON_EXERCISES_TEMPLATE.format(
            target_language=target_language,
            native_language=native_language,
            topic=topic,
            text=str(text or ""),
            vocab_pairs=vocab_pairs,
        )

        exercises_container = await self._generate_json_with_retries(
            prompt_ex,
            max_attempts=max_ai_attempts,
            db=db,
            use_cache=True,
        )
        validation_errors: list[dict] = []
        exercises_attempts = 0
        quality_status = "ok"

        for _ in range(0, ex_repairs_max + 1):
            exercises_attempts += 1
            exercises = exercises_container.get("exercises") if isinstance(exercises_container, dict) else None
            errs = self._validate_exercises(exercises, target_language=target_language)
            if not errs:
                break

            validation_errors.extend(errs)
            if (exercises_attempts - 1) >= ex_repairs_max:
                break

            logger.warning("AI exercises validation failed, attempting JSON fix: %s", errs)
            exercises_container = await self._fix_json_with_patch(
                invalid_json=exercises_container,
                errors=self._errors_to_patch_lines(errs),
                instruction=(
                    f"You previously generated ONLY exercises JSON for a {target_language} lesson. Fix ONLY the exercises JSON."
                ),
                db=db,
            )

        if self._validate_exercises(
            exercises_container.get("exercises") if isinstance(exercises_container, dict) else None,
            target_language=target_language,
        ):
            exercises_container = {"exercises": []}
            quality_status = "needs_review"

        return {
            "exercises": exercises_container.get("exercises", []) if isinstance(exercises_container, dict) else [],
            "_meta": {
                "generation_mode": mode,
                "exercise_attempts": exercises_attempts,
                "validation_errors": validation_errors,
                "provider": provider_name,
                "model": model_name,
                "quality_status": quality_status,
            },
        }

    async def generate_course_path(
        self,
        target_language: str,
        native_language: str,
        level: str,
        interests: str = "General",
        theme: str | None = None,
        *,
        db: AsyncSession | None = None,
    ) -> dict:
        if not settings.AI_ENABLED:
            raise ServiceException("AI is disabled")

        theme_str = str(theme).strip() if theme else str(interests or "General").strip()
        prompt = PATH_GENERATION_TEMPLATE.format(
            target_language=target_language,
            native_language=native_language,
            level=level,
            theme=theme_str,
            interests=interests,
        )
        prompt = self._truncate_prompt(prompt)

        try:
            return await self._generate_json_with_retries(prompt, db=db, use_cache=True)
        except ServiceException as e:
            logger.warning("Path Generation Failed: %s", str(e))
                                            
            return {
                "sections": [
                    {
                        "order": 1,
                        "title": "Introduction",
                        "description": "Basics",
                        "units": [
                            {"order": 1, "topic": "Greetings", "description": "Hello", "icon": "👋"}
                        ]
                    }
                ]
            }

    async def generate_roleplay_response(self, history: list, scenario: str, role: str, level: str, target_language: str) -> str:
        system_instruction = ROLEPLAY_SYSTEM_TEMPLATE.format(
            scenario=scenario, role=role, level=level, target_language=target_language
        )
        
        messages = [{"role": "system", "content": self._truncate_prompt(system_instruction)}]
        for msg in history[-5:]:
                                                                                 
             role_name = "assistant" if msg['role'] == "bot" else "user"
             messages.append({"role": role_name, "content": self._truncate_prompt(msg['content'])})

        try:
            return await self.provider.generate_chat(messages)
        except Exception as e:
            raise ServiceException(f"AI provider error: {str(e)}")

ai_service = AIService()
