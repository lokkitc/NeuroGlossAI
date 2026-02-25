import pytest
from httpx import AsyncClient

from app.services.ai_service import ai_service
from tests.mocks import MockLLMProvider


ai_service.provider = MockLLMProvider()


async def _register_and_login(async_client: AsyncClient, *, username: str, email: str, password: str) -> str:
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert reg.status_code == 200, reg.text

    login = await async_client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


@pytest.mark.asyncio
async def test_chat_first_generates_grounded_lesson_and_course(async_client: AsyncClient):
    token = await _register_and_login(
        async_client,
        username="chatuser",
        email="chatuser@example.com",
        password="password12345",
    )
    headers = {"Authorization": f"Bearer {token}"}

                        
    ch = await async_client.post(
        "/api/v1/characters/me",
        headers=headers,
        json={
            "slug": "buddy",
            "display_name": "Buddy",
            "description": "A friendly buddy",
            "system_prompt": "You are Buddy.",
            "style_prompt": "",
            "is_public": False,
            "is_nsfw": False,
            "settings": {},
        },
    )
    assert ch.status_code == 200, ch.text
    character_id = ch.json()["id"]

                         
    sess = await async_client.post(
        "/api/v1/chat/sessions",
        headers=headers,
        json={"character_id": character_id, "title": "My Session"},
    )
    assert sess.status_code == 200, sess.text
    session_id = sess.json()["id"]

                                                                                        
    user_lines = [
        "I bought an apple.",
        "I need coffee.",
        "I like music.",
        "This book is good.",
        "We walked in the park.",
        "See you tomorrow.",
        "I bought an apple.",
        "I need coffee.",
        "I like music.",
        "See you tomorrow.",
    ]

    for line in user_lines:
        turn = await async_client.post(
            f"/api/v1/chat/sessions/{session_id}/turn",
            headers=headers,
            json={"content": line},
        )
        assert turn.status_code == 200, turn.text

                                                                                                                  
    gen = await async_client.post(
        f"/api/v1/chat/sessions/{session_id}/learning/lessons",
        headers=headers,
        json={"turn_window": 40, "generation_mode": "balanced"},
    )
    assert gen.status_code == 200, gen.text
    lesson = gen.json()

    assert lesson["chat_session_id"] == session_id
    assert lesson["source_turn_to"] >= lesson["source_turn_from"]
    assert lesson["quality_status"] == "ok"

                        
    lst = await async_client.get(
        f"/api/v1/chat/sessions/{session_id}/learning/lessons",
        headers=headers,
    )
    assert lst.status_code == 200, lst.text
    assert len(lst.json()) >= 1


@pytest.mark.asyncio
async def test_chat_learning_rejects_ungrounded_output(async_client: AsyncClient, monkeypatch):
    token = await _register_and_login(
        async_client,
        username="baduser",
        email="baduser@example.com",
        password="password12345",
    )
    headers = {"Authorization": f"Bearer {token}"}

                        
    ch = await async_client.post(
        "/api/v1/characters/me",
        headers=headers,
        json={
            "slug": "buddy2",
            "display_name": "Buddy2",
            "description": "A friendly buddy",
            "system_prompt": "You are Buddy.",
            "style_prompt": "",
            "is_public": False,
            "is_nsfw": False,
            "settings": {},
        },
    )
    assert ch.status_code == 200, ch.text
    character_id = ch.json()["id"]

    sess = await async_client.post(
        "/api/v1/chat/sessions",
        headers=headers,
        json={"character_id": character_id, "title": "Bad Session"},
    )
    assert sess.status_code == 200, sess.text
    session_id = sess.json()["id"]

                                                                      
    await async_client.post(
        f"/api/v1/chat/sessions/{session_id}/turn",
        headers=headers,
        json={"content": "Hello there."},
    )

    class BadProvider(MockLLMProvider):
        async def generate_json(self, prompt: str):
            if "Create a mini-lesson from the following chat" in prompt:
                return {
                    "title": "Bad",
                    "topic": "Bad",
                    "text": "Bad",
                    "vocabulary": [
                        {
                            "phrase": "invented",
                            "meaning": "придумано",
                            "source_quote": "THIS WAS NEVER IN CHAT",
                            "example_quote": "THIS WAS NEVER IN CHAT",
                        }
                    ],
                    "exercises": [
                        {
                            "type": "fill_blank",
                            "sentence_source": "THIS WAS NEVER IN CHAT",
                            "targets": ["invented"],
                            "sentence": "__",
                            "correct": "invented",
                        }
                    ],
                }
            return await super().generate_json(prompt)

    monkeypatch.setattr(ai_service, "provider", BadProvider())

    gen = await async_client.post(
        f"/api/v1/chat/sessions/{session_id}/learning/lessons",
        headers=headers,
        json={"turn_window": 40, "generation_mode": "balanced"},
    )

                                       
    assert gen.status_code == 503, gen.text
