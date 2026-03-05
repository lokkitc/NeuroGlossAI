import pytest


@pytest.mark.asyncio
async def test_health_root(client):
    r = await client.get("/")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_public_endpoints(client):
    r = await client.get("/api/v1/public/users")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_auth_me_requires_token(client):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_users_me_patch_requires_token(client):
    r = await client.patch("/api/v1/users/me", json={"preferred_name": "x"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_users_me_patch_ok(client, user_auth_headers):
    r = await client.patch("/api/v1/users/me", json={"preferred_name": "Tester"}, headers=user_auth_headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_characters_requires_auth(client):
    r = await client.get("/api/v1/characters/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_characters_flow_smoke(client, user_auth_headers):
    r = await client.post(
        "/api/v1/characters/me",
        json={
            "slug": "test",
            "display_name": "Test",
            "description": "d",
            "system_prompt": "You are test",
            "is_public": False,
            "is_nsfw": False,
        },
        headers=user_auth_headers,
    )
    assert r.status_code == 200, r.text
    char = r.json()

    r2 = await client.get("/api/v1/characters/me", headers=user_auth_headers)
    assert r2.status_code == 200

    r3 = await client.patch(
        f"/api/v1/characters/me/{char['id']}",
        json={"description": "d2"},
        headers=user_auth_headers,
    )
    assert r3.status_code == 200


@pytest.mark.asyncio
async def test_rooms_flow_smoke(client, user_auth_headers):
    # Rooms require at least one participant_character_id.
    r0 = await client.post(
        "/api/v1/characters/me",
        json={
            "slug": "room_char",
            "display_name": "RoomChar",
            "description": "d",
            "system_prompt": "You are room char",
            "is_public": False,
            "is_nsfw": False,
        },
        headers=user_auth_headers,
    )
    assert r0.status_code == 200, r0.text
    ch = r0.json()

    r = await client.post(
        "/api/v1/rooms/me",
        json={
            "title": "Room",
            "description": "d",
            "is_public": False,
            "is_nsfw": False,
            "participant_character_ids": [ch["id"]],
        },
        headers=user_auth_headers,
    )
    assert r.status_code == 200, r.text
    room = r.json()

    r2 = await client.get(f"/api/v1/rooms/me/{room['id']}", headers=user_auth_headers)
    assert r2.status_code == 200


@pytest.mark.asyncio
async def test_memory_flow_smoke(client, user_auth_headers):
    r = await client.post(
        "/api/v1/memory/me",
        json={"title": "t", "content": "c", "importance": 1, "is_pinned": False},
        headers=user_auth_headers,
    )
    assert r.status_code == 200, r.text
    mem = r.json()

    r2 = await client.get("/api/v1/memory/me", headers=user_auth_headers)
    assert r2.status_code == 200

    r3 = await client.patch(f"/api/v1/memory/me/{mem['id']}", json={"title": "t2"}, headers=user_auth_headers)
    assert r3.status_code == 200


@pytest.mark.asyncio
async def test_posts_flow_smoke(client, user_auth_headers):
    r = await client.post(
        "/api/v1/posts/me",
        json={"title": "t", "content": "c", "character_id": None, "media": None, "is_public": False},
        headers=user_auth_headers,
    )
    assert r.status_code == 200, r.text
    post = r.json()

    r2 = await client.get("/api/v1/posts/me", headers=user_auth_headers)
    assert r2.status_code == 200

    r3 = await client.post(f"/api/v1/posts/me/{post['id']}/share", json={"is_public": True}, headers=user_auth_headers)
    assert r3.status_code == 200

    r4 = await client.post(f"/api/v1/posts/{post['id']}/like", headers=user_auth_headers)
    assert r4.status_code == 200

    r5 = await client.delete(f"/api/v1/posts/{post['id']}/like", headers=user_auth_headers)
    assert r5.status_code == 200


@pytest.mark.asyncio
async def test_themes_flow_smoke(client, user_auth_headers):
    r = await client.get("/api/v1/themes/available", headers=user_auth_headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_subscriptions_requires_auth(client):
    r = await client.get("/api/v1/subscriptions/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_subscriptions_admin_set_and_history(client, admin_auth_headers, user_tokens):
    # Use admin to grant subscription to the regular user
    from jose import jwt

    token = user_tokens["access_token"]
    payload = jwt.get_unverified_claims(token)
    user_id = payload.get("sub")

    r = await client.post(
        "/api/v1/subscriptions/admin/set",
        json={"user_id": user_id, "tier": "pro", "expires_at": None},
        headers=admin_auth_headers,
    )
    assert r.status_code == 200, r.text

    r2 = await client.get(f"/api/v1/subscriptions/admin/history/{user_id}", headers=admin_auth_headers)
    assert r2.status_code == 200


@pytest.mark.asyncio
async def test_achievements_endpoints(client, user_auth_headers, admin_auth_headers, user_tokens):
    r = await client.get("/api/v1/achievements/")
    assert r.status_code == 200

    r2 = await client.get("/api/v1/achievements/me", headers=user_auth_headers)
    assert r2.status_code == 200

    from jose import jwt

    payload = jwt.get_unverified_claims(user_tokens["access_token"])
    user_id = payload.get("sub")

    r3 = await client.post(
        "/api/v1/achievements/admin/award",
        json={"user_id": user_id, "slug": "perfectionist_3stars", "context": {}},
        headers=admin_auth_headers,
    )
    # Can be 404 if no seed; in that case we just assert it doesn't 500.
    assert r3.status_code in {200, 404, 400}
