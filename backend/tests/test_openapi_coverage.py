import pytest


# Guardrail: if you add a new API path, this test will fail until you add it here
# (and preferably add a smoke test for it).
COVERED_API_PATHS: set[str] = {
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/auth/logout",
    "/api/v1/auth/logout-all",
    "/api/v1/auth/refresh/cleanup",
    "/api/v1/auth/me",

    "/api/v1/users/me/export",
    "/api/v1/users/me/languages",
    "/api/v1/users/me",

    "/api/v1/public/users",
    "/api/v1/public/users/by-username/{username}",

    "/api/v1/characters/me",
    "/api/v1/characters/me/{character_id}",
    "/api/v1/characters/public",
    "/api/v1/characters/public/{character_id}",

    "/api/v1/rooms/me",
    "/api/v1/rooms/me/{room_id}",

    "/api/v1/chat/sessions",
    "/api/v1/chat/sessions/{session_id}",
    "/api/v1/chat/sessions/{session_id}/turn",

    "/api/v1/memory/me",
    "/api/v1/memory/me/{memory_id}",

    "/api/v1/uploads/image",
    "/api/v1/uploads/presign",

    "/api/v1/posts/public",
    "/api/v1/posts/public/by-user/{username}",
    "/api/v1/posts/public/by-character/{character_id}",
    "/api/v1/posts/me",
    "/api/v1/posts/me/{post_id}",
    "/api/v1/posts/me/{post_id}/share",
    "/api/v1/posts/{post_id}/like",

    "/api/v1/themes/available",
    "/api/v1/themes/me",
    "/api/v1/themes/me/select",
    "/api/v1/themes/characters/{character_id}/select-chat",

    "/api/v1/subscriptions/me",
    "/api/v1/subscriptions/cancel",
    "/api/v1/subscriptions/history",
    "/api/v1/subscriptions/admin/history/{user_id}",
    "/api/v1/subscriptions/admin/set",

    "/api/v1/achievements/",
    "/api/v1/achievements/me",
    "/api/v1/achievements/admin/award",
}


@pytest.mark.asyncio
async def test_openapi_paths_are_accounted_for(client):
    r = await client.get("/api/v1/openapi.json")
    assert r.status_code == 200
    schema = r.json()

    paths = set((schema or {}).get("paths", {}).keys())

    # Only enforce our public API under /api/v1.
    api_paths = {p for p in paths if p.startswith("/api/v1/")}

    missing = sorted(api_paths - COVERED_API_PATHS)
    assert not missing, f"Missing coverage entries for API paths: {missing}"
