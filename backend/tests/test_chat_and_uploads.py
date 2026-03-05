import pytest


@pytest.mark.asyncio
async def test_upload_image_mocked(client, user_auth_headers, monkeypatch):
    # Avoid calling real cloud providers.
    from app.features.uploads import service as uploads_service

    async def _fake_upload_image_file(self, image, folder: str):
        return {
            "secure_url": "https://example.com/x.png",
            "public_id": "pid",
            "bytes": 1,
            "width": 1,
            "height": 1,
            "format": "png",
            "resource_type": "image",
        }

    monkeypatch.setattr(uploads_service.UploadService, "upload_image_file", _fake_upload_image_file, raising=True)

    files = {"image": ("x.png", b"123", "image/png")}
    r = await client.post("/api/v1/uploads/image", files=files, headers=user_auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("public_id") == "pid"


@pytest.mark.asyncio
async def test_chat_character_session_and_turn_mocked(client, user_auth_headers, monkeypatch):
    # Mock AI calls used by ChatService.
    from app.features.ai import ai_service as ai_mod

    async def _fake_generate_character_chat_turn_json(*, db, messages, temperature=None):
        return {"action": "*waves*", "dialogue": "Hello"}

    monkeypatch.setattr(ai_mod.ai_service, "generate_character_chat_turn_json", _fake_generate_character_chat_turn_json, raising=True)

    # Create a character
    r = await client.post(
        "/api/v1/characters/me",
        json={
            "slug": "chatty",
            "display_name": "Chatty",
            "description": "d",
            "system_prompt": "You are Chatty",
            "is_public": False,
            "is_nsfw": False,
        },
        headers=user_auth_headers,
    )
    assert r.status_code == 200, r.text
    ch = r.json()

    # Create session
    r2 = await client.post(
        "/api/v1/chat/sessions",
        json={"character_id": ch["id"], "room_id": None, "title": ""},
        headers=user_auth_headers,
    )
    assert r2.status_code == 200, r2.text
    sess = r2.json()

    # Create turn
    r3 = await client.post(
        f"/api/v1/chat/sessions/{sess['id']}/turn",
        json={"content": "hi"},
        headers=user_auth_headers,
    )
    assert r3.status_code == 200, r3.text
    body = r3.json()
    assert body.get("session")
    assert body.get("assistant_turns")
