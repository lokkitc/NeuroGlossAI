"""Провайдер модели «Грок».

Отвечает за:
- вызовы чат‑завершений
- получение ответа в формате джейсон (в т.ч. запасной режим при ошибке строгого режима)
"""

import json
import asyncio
from groq import AsyncGroq
from app.core.config import settings
from app.core.ai.base import LLMProvider
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class GroqProvider(LLMProvider):
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        self.api_key = settings.GROQ_API_KEY
        if not self.api_key:
            # Для unit‑тестов мы часто мокируем клиент и не нуждаемся в реальном ключе.
            # В проде запросы всё равно упадут, если ключ неверный, но warning оставляем явным.
            logger.warning("GROQ_API_KEY is not set.")
        self.client = AsyncGroq(api_key=self.api_key or "DUMMY")
        
        self.model = model
        logger.debug("Selected Groq model: %s", self.model)

    async def _ensure_client(self):
        if not self.client:
            raise ValueError("Groq client is not initialized. Check GROQ_API_KEY.")

    async def generate_json(self, prompt: str, *, temperature: float | None = None) -> Dict[str, Any]:
        await self._ensure_client()
        
        # Убедитесь, что модель знает, что она должна выдавать джейсон
        if "JSON" not in prompt:
             prompt += "\n\nIMPORTANT: Output ONLY valid JSON."

        def _extract_json_object(text: str) -> str:
            # Пытаемся извлечь первый джейсон‑объект из ответа модели.
            # Это запасной режим для случаев, когда строгий режим не сработал.
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise ValueError("No JSON object found in response")
            return text[start : end + 1]

        timeout = float(getattr(settings, "AI_REQUEST_TIMEOUT_SECONDS", 30) or 30)
        # Groq SDK may internally retry with backoff on 429. If we wrap it with a strict wait_for(timeout)
        # we can cancel the request mid-retry. Give a larger total wall-clock window.
        total_timeout = max(timeout, timeout * 4.0)
        max_chars = int(getattr(settings, "AI_MAX_RESPONSE_CHARS", 200000) or 200000)

        try:
            chat_completion = await asyncio.wait_for(
                self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model=self.model,
                    response_format={"type": "json_object"},
                    **({"temperature": float(temperature)} if temperature is not None else {}),
                ),
                timeout=total_timeout,
            )
            content = chat_completion.choices[0].message.content
            logger.debug("Groq JSON response received")
            if content and len(content) > max_chars:
                raise ValueError("Groq response too large")
            return json.loads(content)
        except Exception as e:
            message = str(e)
            # Грок иногда отклоняет строгий режим с 400 json_validate_failed.
            # Запасной режим: просим модель без response_format и извлекаем джейсон из текста.
            is_json_validate_failed = (
                "json_validate_failed" in message
                or ("error code: 400" in message.lower() and "json" in message.lower())
            )

            if not is_json_validate_failed:
                logger.exception("Groq API JSON Error")
                raise

            logger.warning("Groq strict JSON mode failed, retrying without response_format")
            chat_completion = await asyncio.wait_for(
                self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt + "\n\nIMPORTANT: Output ONLY valid JSON.",
                        }
                    ],
                    model=self.model,
                    **({"temperature": float(temperature)} if temperature is not None else {}),
                ),
                timeout=total_timeout,
            )
            content = chat_completion.choices[0].message.content
            if content and len(content) > max_chars:
                raise ValueError("Groq response too large")
            extracted = _extract_json_object(content)
            return json.loads(extracted)

    async def generate_text(self, prompt: str, *, temperature: float | None = None) -> str:
        await self._ensure_client()
        timeout = float(getattr(settings, "AI_REQUEST_TIMEOUT_SECONDS", 30) or 30)
        total_timeout = max(timeout, timeout * 4.0)
        max_chars = int(getattr(settings, "AI_MAX_RESPONSE_CHARS", 200000) or 200000)
        try:
            chat_completion = await asyncio.wait_for(
                self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model=self.model,
                    **({"temperature": float(temperature)} if temperature is not None else {}),
                ),
                timeout=total_timeout,
            )
            content = chat_completion.choices[0].message.content
            if content and len(content) > max_chars:
                return content[:max_chars]
            return content
        except Exception as e:
            logger.exception("Groq API Text Error")
            raise e

    async def generate_chat(self, messages: List[Dict[str, str]], *, temperature: float | None = None) -> str:
        await self._ensure_client()
        timeout = float(getattr(settings, "AI_REQUEST_TIMEOUT_SECONDS", 30) or 30)
        total_timeout = max(timeout, timeout * 4.0)
        max_chars = int(getattr(settings, "AI_MAX_RESPONSE_CHARS", 200000) or 200000)
        try:
            chat_completion = await asyncio.wait_for(
                self.client.chat.completions.create(
                    messages=messages,
                    model=self.model,
                    **({"temperature": float(temperature)} if temperature is not None else {}),
                ),
                timeout=total_timeout,
            )
            content = chat_completion.choices[0].message.content
            logger.debug("Groq chat response received")
            if content and len(content) > max_chars:
                return content[:max_chars]
            return content
        except Exception as e:
            logger.exception("Groq API Chat Error")
            raise e
