"""Тесты провайдера GroqProvider.

Проверяем JSON режим и базовую генерацию текста с мокнутым AsyncGroq.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.core.ai.groq_provider import GroqProvider

@pytest.fixture
def mock_groq_client():
    with patch("app.core.ai.groq_provider.AsyncGroq") as MockClient:
        # Подготовка мок-экземпляра клиента
        client_instance = AsyncMock()
        MockClient.return_value = client_instance
        yield client_instance

@pytest.mark.asyncio
async def test_groq_generate_json(mock_groq_client):
    """
    Проверяем, что GroqProvider корректно обрабатывает запросы генерации JSON.
    """
    # 1. Подготовка мок-ответа
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"key": "value", "number": 42}'))
    ]
    mock_groq_client.chat.completions.create.return_value = mock_response

    # 2. Инициализация провайдера
    provider = GroqProvider()
    
    # 3. Вызов метода
    result = await provider.generate_json("Test prompt")
    
    # 4. Проверка
    assert result == {"key": "value", "number": 42}
    mock_groq_client.chat.completions.create.assert_called_once()
    
    # Проверяем, что включён strict JSON режим
    call_kwargs = mock_groq_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["response_format"] == {"type": "json_object"}

@pytest.mark.asyncio
async def test_groq_generate_text(mock_groq_client):
    """
    Проверяем базовую генерацию текста.
    """
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="Hello World"))
    ]
    mock_groq_client.chat.completions.create.return_value = mock_response

    provider = GroqProvider()
    result = await provider.generate_text("Say hello")
    
    assert result == "Hello World"
