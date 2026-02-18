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
from app.repositories.ai_ops import AIIOpsRepository
from app.utils.prompt_templates import (
    LESSON_SYSTEM_TEMPLATE,
    LESSON_TEXT_VOCAB_TEMPLATE,
    LESSON_EXERCISES_TEMPLATE,
    ROLEPLAY_SYSTEM_TEMPLATE,
    PATH_GENERATION_TEMPLATE,
)
from app.core.exceptions import ServiceException

logger = logging.getLogger(__name__)


GenerationMode = Literal["fast", "balanced", "strict"]


class AIService:
    def __init__(self, provider: LLMProvider = None):
        self.provider = provider or GroqProvider()

    # Встроенный предохранитель (локальное состояние процесса)
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
        # Пока поддерживаем только фоллбэк по моделям Грок.
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
    def _compute_prompt_hash(prompt: str, *, provider: str | None, model: str | None) -> str:
        payload = f"{provider or ''}|{model or ''}|{prompt}".encode("utf-8", errors="ignore")
        return hashlib.sha256(payload).hexdigest()

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
        # Грубая эвристика: ожидаемая письменность для языка, как он используется в продукте.
        # Должно быть лёгким и без внешних зависимостей.
        lang = (language or "").strip().lower()
        if not lang:
            return None

        # Языки на кириллице (в продукте обычно выдаются на кириллице).
        if lang in {"russian", "kazakh", "ukrainian", "bulgarian", "belarusian", "serbian"}:
            return "cyrillic"

        # Языки на латинице.
        if lang in {"english", "spanish", "french", "german", "italian", "portuguese", "turkish", "indonesian", "malay", "vietnamese", "dutch"}:
            return "latin"

        # Арабская письменность.
        if lang in {"arabic", "persian", "urdu"}:
            return "arabic"

        # Китайская/японская/корейская письменности.
        if lang in {"chinese", "mandarin"}:
            return "han"
        if lang in {"japanese"}:
            return "japanese"
        if lang in {"korean"}:
            return "hangul"

        # Индийские письменности.
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
        return r"$^"  # не матчится ни на что

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
        # В "прочие" буквы включаем латиницу/кириллицу/арабский/хань и т.п. Держим просто.
        total = len(re.findall(r"[A-Za-z\u0400-\u04FF\u0600-\u06FF\u0750-\u077F\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF\u0900-\u097F]", text))
        if total == 0:
            return 0.0
        return exp / total

    def _looks_like_language_mix(self, text: str, target_language: str) -> bool:
        # Грубая проверка по письменности (адаптивно по нескольким языкам).
        if not text:
            return True

        expected = self._expected_script_for_language(target_language)
        if expected is None:
            # Неизвестный язык: отсекаем только явный "мусор" (неожиданные блоки).
            if re.search(r"[\u0600-\u06FF\u0750-\u077F\u4E00-\u9FFF]", text):
                return True
            return False

        ratio = self._script_ratio(text, expected)
        # Разрешаем немного чужой письменности (бренды/имена), но не доминирование.
        if ratio < 0.80:
            return True

        # Если ожидаем не латиницу и видим длинные английские фрагменты — считаем невалидным.
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
        # Канонический плейсхолдер — ___, но модель часто отдаёт много подчёркиваний.
        normalized = re.sub(r"_{3,}", "___", sentence)
        return normalized

    @staticmethod
    def _maybe_normalize_cyrillic_confusables(text: str, *, target_language: str) -> str:
        if not isinstance(text, str) or not text:
            return text

        expected = AIService._expected_script_for_language(target_language)
        if expected != "cyrillic":
            return text

        # Применяем только если текст уже в основном на кириллице, чтобы не ломать латинские уроки.
        ratio = AIService._script_ratio(text, "cyrillic")
        if ratio < 0.70:
            return text

        # Исправляем визуально похожие латинские буквы на кириллические.
        # Консервативно: только самые частые одиночные подмешивания.
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
        # Нормализуем мелкие форматные различия, чтобы не получать лишние падения валидации.
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
                
                # Validate blank_index if present
                if blank_index is not None and not isinstance(blank_index, int):
                    errors.append(
                        {
                            "code": "exercise_invalid",
                            "field": f"exercises[{idx}].blank_index",
                            "reason": "invalid",
                            "message": "fill_blank has invalid 'blank_index'",
                        }
                    )
                
                # Validate full_sentence_native if present (optional field)
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

        # Проверки корректности словаря
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
                # Запрещаем доминирование письменности целевого языка внутри перевода ТОЛЬКО если письменности различаются.
                # Если оба языка используют одну письменность (например, казахский/русский на кириллице), проверка невалидна.
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
        # Нормализация перед валидацией (только несемантические изменения)
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
        return await self._generate_json_with_retries(
            prompt,
            max_attempts=3,
            db=db,
            use_cache=True,
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
        prior_topics: list[str] | None,
        used_words: list[str] | None,
        target_language: str,
        native_language: str,
    ) -> str:
        prior_topics = prior_topics or []
        used_words = used_words or []

        # Ограничиваем размер промпта.
        prior_topics = prior_topics[:30]
        used_words = used_words[:80]

        suffix = (
            "\n\nCOURSE MEMORY / ANTI-REPETITION RULES:\n"
            f"- The course target language is {target_language}. The ONLY language allowed in the lesson text is {target_language}.\n"
            f"- The ONLY language allowed in 'translation' fields is {native_language}.\n"
            "- Do NOT start the lesson with generic filler like 'I like this game' unless it is essential. Start directly on the topic.\n"
        )

        if prior_topics:
            suffix += "- Topics already covered (do NOT repeat the same scenarios/examples):\n"
            suffix += "  - " + "\n  - ".join(prior_topics) + "\n"

        if used_words:
            suffix += "- Words already used in previous lessons (avoid repeating them as vocabulary targets):\n"
            suffix += "  - " + ", ".join(used_words) + "\n"

        suffix += "- Ensure this lesson introduces NEW vocabulary and NEW examples compared to prior lessons.\n"
        return suffix

    @staticmethod
    def _extract_retry_after_seconds(error_message: str) -> float | None:
        # Ошибки Грок часто содержат подсказку, через сколько секунд можно повторить запрос.
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
    ) -> dict:
        last_exc: Exception | None = None
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
                    result = await candidate.generate_json(prompt)
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
                            await db.commit()
                        except IntegrityError:
                            try:
                                await db.rollback()
                            except Exception:
                                pass
                        except Exception:
                            try:
                                await db.rollback()
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

                    # Если провайдер просит ждать много минут (например, из-за дневных лимитов), не спим здесь.
                    # Возвращаемся быстро, чтобы интерфейс отдал информацию о повторе клиенту.
                    if is_rate_limit and retry_after is not None and retry_after >= 120.0:
                        raise ServiceException(
                            f"Provider retry requested retry_after_seconds={int(retry_after)}"
                        )

                    if attempt >= max_attempts or not is_transient:
                        break

                    # Задержка между ретраями: учитываем подсказку сервера, иначе экспонента + случайная добавка
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

            # После исчерпания попыток для кандидата — переходим к следующему провайдеру/модели.

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

        lesson_core = await self.generate_text_vocab_only(
            topic=topic,
            target_language=target_language,
            native_language=native_language,
            level=level,
            interests=interests,
            prior_topics=prior_topics,
            used_words=used_words,
            generation_mode=mode,
            db=db,
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

        # Шаг B: генерируем упражнения на основе основы урока
        prompt_ex = LESSON_EXERCISES_TEMPLATE.format(
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
            # Мягкая деградация: сохраняем основу урока, упражнения очищаем
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
        return out

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
        generation_mode: GenerationMode = "balanced",
        db: AsyncSession | None = None,
    ) -> dict:
        if not settings.AI_ENABLED:
            raise ServiceException("AI is disabled")

        mode: GenerationMode = generation_mode if generation_mode in {"fast", "balanced", "strict"} else "balanced"
        core_repairs_max = 0 if mode == "fast" else (2 if mode == "balanced" else 4)
        max_ai_attempts = 3 if mode == "fast" else (5 if mode == "balanced" else 7)

        interests_str = ", ".join(interests) if interests else "General Topics"

        provider_name = type(self.provider).__name__ if getattr(self, "provider", None) else None
        model_name = getattr(self.provider, "model", None) if getattr(self, "provider", None) else None

        base_suffix = self._build_course_context_suffix(
            prior_topics=prior_topics,
            used_words=used_words,
            target_language=target_language,
            native_language=native_language,
        )

        prompt_text_vocab = LESSON_TEXT_VOCAB_TEMPLATE.format(
            target_language=target_language,
            native_language=native_language,
            topic=topic,
            level=level,
            interests=interests_str,
        ) + base_suffix

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
                    f"Fix the SAME JSON." 
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

        try:
            return await self._generate_json_with_retries(prompt, db=db, use_cache=True)
        except ServiceException as e:
            logger.warning("Path Generation Failed: %s", str(e))
            # Минимальная запасная структура
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
        
        messages = [{"role": "system", "content": system_instruction}]
        for msg in history[-5:]:
             # Маппим роль 'бот' в 'ассистент' для совместимого формата сообщений
             role_name = "assistant" if msg['role'] == "bot" else "user"
             messages.append({"role": role_name, "content": msg['content']})

        try:
            return await self.provider.generate_chat(messages)
        except Exception as e:
            return f"AI Error: {str(e)}"

ai_service = AIService()
