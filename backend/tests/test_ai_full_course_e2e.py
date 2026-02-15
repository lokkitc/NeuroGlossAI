"""E2E тест полного курса с реальными AI вызовами.

Запускается вручную через переменные окружения (см. docstring теста).
"""

import os
import uuid
import asyncio

import pytest
import httpx


def _env_flag(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "y", "on"}


@pytest.mark.asyncio
async def test_ai_generate_full_course_e2e():
    """E2E тест, который реально вызывает AI и подготавливает курс в БД через HTTP API.

    Включается только вручную:
      - RUN_AI_TESTS=1
      - GROQ_API_KEY должен быть выставлен (используется backend'ом)
      - backend должен быть запущен (по умолчанию http://localhost:8000)

    Параметры:
      - BACKEND_URL (default: http://localhost:8000)
      - COURSE_INTERESTS (default: "Travel,Music")
      - COURSE_TOPICS_LIMIT (default: 0 -> без лимита)
      - COURSE_SLEEP_SECONDS (default: 13)  # чтобы не упереться в limiter 5/minute
    """

    if not _env_flag("RUN_AI_TESTS"):
        pytest.skip("Установите RUN_AI_TESTS=1, чтобы запустить AI E2E тесты")

    # Этот ключ должен быть в окружении backend'а (например docker-compose env),
    # но проверку здесь делаем как дополнительный guardrail.
    if not os.getenv("GROQ_API_KEY"):
        pytest.skip("GROQ_API_KEY не задан в окружении")

    base_url = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
    interests_env = os.getenv("COURSE_INTERESTS", "Travel,Music")
    interests = [x.strip() for x in interests_env.split(",") if x.strip()]

    topics_limit = int(os.getenv("COURSE_TOPICS_LIMIT", "0"))
    sleep_seconds = float(os.getenv("COURSE_SLEEP_SECONDS", "13"))

    username = f"ai_course_{uuid.uuid4().hex[:10]}"
    email = f"{username}@example.com"
    password = "strongpassword123"

    async with httpx.AsyncClient(base_url=base_url, timeout=300.0) as client:
        # 1) Регистрация
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "username": username},
        )
        assert reg.status_code == 200, reg.text

        # 2) Логин
        token_resp = await client.post(
            "/api/v1/auth/login",
            data={"username": username, "password": password},
        )
        assert token_resp.status_code == 200, token_resp.text
        token = token_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3) Генерация курса (AI)
        path_gen = await client.post(
            "/api/v1/path/generate",
            json={"interests": interests},
            headers=headers,
        )
        assert path_gen.status_code == 200, path_gen.text
        path_data = path_gen.json()
        assert isinstance(path_data, list)
        assert len(path_data) > 0

        # 4) Собираем темы из unit'ов
        topics: list[str] = []
        for section in path_data:
            for unit in section.get("units", []) or []:
                topic = unit.get("topic")
                if topic:
                    topics.append(str(topic))

        assert len(topics) > 0

        if topics_limit > 0:
            topics = topics[:topics_limit]

        # 5) Генерируем уроки по темам (AI)
        # Эндпойнт ограничен 5/мин, поэтому между вызовами делаем паузу.
        for i, topic in enumerate(topics):
            lesson_resp = await client.post(
                "/api/v1/lessons/generate",
                json={"topic": topic, "level": "A1"},
                headers=headers,
            )
            assert lesson_resp.status_code == 200, lesson_resp.text

            if i < len(topics) - 1 and sleep_seconds > 0:
                await asyncio.sleep(sleep_seconds)

        # 6) Экспорт и sanity-check наличия артефактов курса
        export_resp = await client.get("/api/v1/users/me/export", headers=headers)
        assert export_resp.status_code == 200, export_resp.text
        exported = export_resp.json()

        assert "user" in exported
        assert "path" in exported
        assert "lessons" in exported

        # Должно быть не меньше сгенерированных уроков
        assert len(exported["lessons"]) >= len(topics)
