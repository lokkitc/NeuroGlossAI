"""Интеграционные тесты эндпойнтов курса (path).

Используем мок AI, чтобы не делать реальные вызовы LLM.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.core.config import settings


pytestmark = pytest.mark.skipif(
    not getattr(settings, "ENABLE_LEGACY_PATH", False),
    reason="Legacy /path endpoints are disabled by feature flag",
)

# Мокаем AI сервис, чтобы во время тестов не делать реальные API/LLM вызовы
@pytest.fixture
def mock_ai_service(monkeypatch):
    async def mock_generate_course_path(*args, **kwargs):
        return {
            "sections": [
                {
                    "order": 1,
                    "title": "Test Section",
                    "description": "Test Description",
                    "units": [
                        {
                            "order": 1,
                            "topic": "Test Topic",
                            "description": "Test Unit Desc",
                            "icon": "🧪"
                        }
                    ]
                }
            ]
        }
    
    from app.services import ai_service
    monkeypatch.setattr(ai_service.ai_service, "generate_course_path", mock_generate_course_path)

@pytest.fixture
async def path_auth_headers(async_client: AsyncClient):
    # 1. Регистрация пользователя
    await async_client.post("/api/v1/auth/register", json={
        "username": "pathuser",
        "email": "path@example.com",
        "password": "password123"
    })
    
    # 2. Логин
    login_res = await async_client.post("/api/v1/auth/login", data={
        "username": "pathuser",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_generate_path(async_client: AsyncClient, db_session: AsyncSession, path_auth_headers, mock_ai_service):
    headers = path_auth_headers  # Уже получено через фикстуру
    # 1. Генерация курса
    response = await async_client.post(
        "/api/v1/path/generate",
        headers=headers,
        json={"interests": ["Testing", "Pytest"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "sections" in data
    assert len(data["sections"]) == 1
    assert data["sections"][0]["title"] == "Test Section"
    assert len(data["sections"][0]["units"]) == 1
    assert data["sections"][0]["units"][0]["topic"] == "Test Topic"
    
    # Проверка БД
    # (Опционально: можно проверить БД напрямую, но для интеграционного теста обычно хватает ответа API)

@pytest.mark.asyncio
async def test_get_path(async_client: AsyncClient, path_auth_headers, mock_ai_service):
    headers = path_auth_headers
    # Предполагаем, что курс уже сгенерирован в предыдущем тесте, либо состояние сохраняется.
    # Строже было бы всегда генерировать заново, но здесь оставляем простую цепочку.
    
    # 1. Генерация (чтобы гарантировать наличие данных)
    await async_client.post(
        "/api/v1/path/generate",
        headers=headers,
        json={"interests": ["Testing"]}
    )
    
    # 2. Получение курса
    response = await async_client.get("/api/v1/path/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "sections" in data
    assert len(data["sections"]) > 0
    assert "units" in data["sections"][0]
    assert "levels" in data["sections"][0]["units"][0]

@pytest.mark.asyncio
async def test_update_progress(async_client: AsyncClient, path_auth_headers, mock_ai_service):
    headers = path_auth_headers
    # 1. Генерация курса
    gen_resp = await async_client.post(
        "/api/v1/path/generate",
        headers=headers,
        json={"interests": ["Testing"]}
    )
    course_data = gen_resp.json()
    first_level_id = course_data["sections"][0]["units"][0]["levels"][0]["id"]
    
    # 2. Обновление прогресса
    update_payload = {
        "level_template_id": first_level_id,
        "status": "completed",
        "stars": 3,
        "xp_gained": 20
    }
    response = await async_client.patch(
        "/api/v1/path/progress",
        headers=headers,
        json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["new_status"] == "completed"
    assert data["next_level_unlocked"] is True  # Должен разблокировать следующий уровень
