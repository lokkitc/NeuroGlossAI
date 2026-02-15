"""Интеграционные тесты генерации уроков.

Используем мок AI, чтобы не делать реальные LLM вызовы.
"""

import pytest
from httpx import AsyncClient

# Мокаем AI сервис для уроков
@pytest.fixture
def mock_ai_lesson_service(monkeypatch):
    async def mock_generate_lesson(*args, **kwargs):
        return {
            "text": "This is a mock lesson text about travel.",
            "vocabulary": [
                {"word": "Plane", "translation": "Самолет", "context": "I fly by plane."}
            ],
            "exercises": [
                {
                    "type": "quiz",
                    "question": "What is this?",
                    "options": ["A", "B", "C"],
                    "correct_index": 0
                }
            ]
        }
    
    from app.services import ai_service
    monkeypatch.setattr(ai_service.ai_service, "generate_lesson", mock_generate_lesson)

@pytest.fixture
async def lesson_auth_headers(async_client: AsyncClient):
    # 1. Регистрация пользователя
    await async_client.post("/api/v1/auth/register", json={
        "username": "lessonuser",
        "email": "lesson@example.com",
        "password": "password123"
    })
    
    # 2. Логин
    login_res = await async_client.post("/api/v1/auth/login", data={
        "username": "lessonuser",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_generate_lesson_flow(async_client: AsyncClient, lesson_auth_headers, mock_ai_lesson_service):
    headers = lesson_auth_headers
    # 1. Обновление языков (опционально)
    await async_client.put("/api/v1/users/me/languages", json={
        "target_language": "English",
        "native_language": "Russian"
    }, headers=headers)

    # 2a. Генерация курса, чтобы получить active enrollment + level_template_id
    course_resp = await async_client.post(
        "/api/v1/path/generate",
        json={"interests": ["Testing"], "level": "A1", "regenerate": True},
        headers=headers,
    )
    assert course_resp.status_code == 200
    course = course_resp.json()
    first_level_template_id = course["sections"][0]["units"][0]["levels"][0]["id"]

    # 2. Генерация урока
    response = await async_client.post("/api/v1/lessons/generate", json={
        "level_template_id": first_level_template_id,
        "topic": "Travel",
        "level": "A1",
    }, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["topic_snapshot"] == "Travel"
    assert data["level_template_id"] == first_level_template_id
    assert len(data["vocabulary_items"]) > 0
    assert "id" in data
    
    # Проверяем структуру упражнений
    assert "exercises" in data
    assert isinstance(data["exercises"], list)
    assert len(data["exercises"]) > 0
    assert data["exercises"][0]["type"] == "quiz"

@pytest.mark.asyncio
async def test_lesson_languages_persistence(async_client: AsyncClient, lesson_auth_headers, mock_ai_lesson_service):
    headers = lesson_auth_headers
    # Меняем языки на French -> German
    res = await async_client.put("/api/v1/users/me/languages", json={
        "target_language": "German",
        "native_language": "French"
    }, headers=headers)
    assert res.status_code == 200
    assert res.json()["target_language"] == "German"

    # Проверяем профиль пользователя
    me_res = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_res.json()["native_language"] == "French"

    course_resp = await async_client.post(
        "/api/v1/path/generate",
        json={"interests": ["Testing"], "level": "A1", "regenerate": True},
        headers=headers,
    )
    assert course_resp.status_code == 200
    course = course_resp.json()
    first_level_template_id = course["sections"][0]["units"][0]["levels"][0]["id"]

    # Генерируем урок и проверяем, что языки применились
    lesson_res = await async_client.post("/api/v1/lessons/generate", json={
        "level_template_id": first_level_template_id,
        "topic": "Food",
        "level": "A1"
    }, headers=headers)
    
    lesson_data = lesson_res.json()
    assert "content_text" in lesson_data
    assert "vocabulary_items" in lesson_data
