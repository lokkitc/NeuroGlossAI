"""E2E сценарий: регистрация -> логин -> генерация курса -> прогресс -> урок -> SRS -> roleplay.

Тест использует мок провайдера LLM, чтобы сделать поведение детерминированным.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.services.ai_service import ai_service
from tests.mocks import MockLLMProvider
from app.core.config import settings


pytestmark = pytest.mark.skipif(
    not (
        getattr(settings, "ENABLE_LEGACY_PATH", False)
        and getattr(settings, "ENABLE_LEGACY_LESSONS", False)
        and getattr(settings, "ENABLE_LEGACY_VOCABULARY", False)
        and getattr(settings, "ENABLE_LEGACY_ROLEPLAY", False)
    ),
    reason="Legacy endpoints are disabled by feature flags",
)

# Для тестового окружения делаем упор на моки, чтобы не зависеть от наличия переменных окружения.

# Переопределяем провайдера глобально для этого модуля.
# Важно: это работает, потому что `ai_service` — singleton-экземпляр в приложении.
ai_service.provider = MockLLMProvider()

@pytest.mark.asyncio
async def test_full_user_journey(async_client: AsyncClient):
    # 1. Регистрация
    reg_response = await async_client.post("/api/v1/auth/register", json={
        "username": "TestHero",
        "email": "hero@mlbb.com",
        "password": "securepassword123"
    })
    assert reg_response.status_code == 200
    data = reg_response.json()
    assert data["username"] == "TestHero"
    user_id = data["id"]

    # 2. Логин
    login_response = await async_client.post("/api/v1/auth/login", data={
        "username": "TestHero",
        "password": "securepassword123"
    })
    assert login_response.status_code == 200
    token_data = login_response.json()
    access_token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 3. Генерация курса по интересам
    path_response = await async_client.post(
        "/api/v1/path/generate",
        json={"interests": ["Mobile Legends", "Esports"], "level": "A1", "regenerate": True},
        headers=headers
    )
    # Диагностика ответа при ошибке
    if path_response.status_code != 200:
        print(f"\n[ERROR] Path Generation Failed: {path_response.text}")    
    assert path_response.status_code == 200
    path_data = path_response.json()

    # Проверяем структуру
    assert "sections" in path_data
    assert len(path_data["sections"]) > 0
    section = path_data["sections"][0]
    assert section["title"] == "Mobile Legends Basics"
    assert len(section["units"]) > 0

    unit = section["units"][0]
    assert unit["topic"] == "Laning Phase"
    
    # Проверяем, что уровни созданы (стандартно 4 уровня)
    assert len(unit["levels"]) == 4
    level_1 = unit["levels"][0]
    assert level_1["type"] == "lesson"
    assert level_1["status"] == "in_progress"  # Первый должен быть разблокирован
    
    level_2 = unit["levels"][1]
    assert level_2["status"] == "locked"

    # 4. Обновление прогресса (завершаем уровень 1)
    progress_response = await async_client.patch(
        "/api/v1/path/progress",
        json={
            "level_template_id": level_1["id"],
            "status": "completed",
            "stars": 3,
            "xp_gained": 50
        },
        headers=headers
    )
    assert progress_response.status_code == 200
    prog_data = progress_response.json()
    assert prog_data["new_status"] == "completed"
    
    # Примечание: user_total_xp обновляется через слушателя событий.
    # Так как EventBus.publish() ждёт обработчики (для простоты реализации), XP должен обновиться сразу.
    assert prog_data["user_total_xp"] == 50
    assert prog_data["next_level_unlocked"] == True

    # 5. Проверяем, что следующий уровень разблокирован
    # Можно проверить БД напрямую, но проще заново запросить курс.
    path_response_2 = await async_client.get("/api/v1/path/", headers=headers)
    path_data_2 = path_response_2.json()
    level_2_updated = path_data_2["sections"][0]["units"][0]["levels"][1]
    assert level_2_updated["status"] == "in_progress"

    # 6. Генерация урока
    lesson_response = await async_client.post(
        "/api/v1/lessons/generate",
        json={"level_template_id": level_2_updated["id"], "topic": "Ganking Strategy", "level": "A1"},
        headers=headers
    )
    # Диагностика ответа при ошибке
    if lesson_response.status_code != 200:
        print(f"\n[ERROR] Lesson Generation Failed: {lesson_response.text}")
    assert lesson_response.status_code == 200
    lesson_data = lesson_response.json()
    
    # В тесте используется мок: внутри `generate_lesson()` вызывается `provider.generate_json(prompt)`.
    # Мок отличает генерацию path по маркеру в prompt, иначе отдаёт дефолтный урок.

    # Для наглядности логируем, что пришло
    print(f"\n[DEBUG] Lesson Data Content: {lesson_data.get('content_text')}")

    assert "content_text" in lesson_data
    assert len(lesson_data["vocabulary_items"]) > 0
    vocab_id = lesson_data["vocabulary_items"][0]["id"]

    # 7. Повторение словаря (SRS)
    # Сразу после создания слово не обязано быть "к повторению", но мы проверяем ручной review по id.
    review_response = await async_client.post(
        "/api/v1/vocabulary/review",
        json={"vocabulary_id": vocab_id, "rating": 5},  # Идеальная оценка
        headers=headers
    )
    assert review_response.status_code == 200
    review_data = review_response.json()
    assert review_data["new_level"] == 1  # Уровень вырос с 0 до 1
    
    # 8. Roleplay
    roleplay_response = await async_client.post(
        "/api/v1/roleplay/chat",
        json={
            "scenario": "Meeting a pro player",
            "role": "Layla",
            "message": "Hi Layla!",
            "history": [],
            "target_language": "Kazakh",
            "level": "A1"
        },
        headers=headers
    )
    assert roleplay_response.status_code == 200
    chat_data = roleplay_response.json()
    assert "Layla" in chat_data["response"]

    print("\n[SUCCESS] All E2E scenarios passed successfully!")
