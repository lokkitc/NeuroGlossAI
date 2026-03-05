import uuid
from typing import Any, Awaitable, Callable

import pytest


RequestBuilder = Callable[[], Awaitable[dict[str, Any]]]


@pytest.mark.asyncio
async def test_openapi_full_run_executes_every_endpoint(
    client,
    user_auth_headers,
    admin_auth_headers,
    monkeypatch,
):
    # Mock external integrations.
    from app.features.uploads import service as uploads_service
    from app.features.ai import ai_service as ai_mod

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

    async def _fake_generate_character_chat_turn_json(*, db, messages, temperature=None):
        return {"action": "*waves*", "dialogue": "Hello"}

    monkeypatch.setattr(uploads_service.UploadService, "upload_image_file", _fake_upload_image_file, raising=True)
    monkeypatch.setattr(
        ai_mod.ai_service,
        "generate_character_chat_turn_json",
        _fake_generate_character_chat_turn_json,
        raising=True,
    )

    # Discover OpenAPI endpoints.
    r = await client.get("/api/v1/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    paths: dict[str, Any] = (schema or {}).get("paths", {})

    # Cache: create baseline resources once.
    cache: dict[str, Any] = {}

    async def _me_id(headers) -> str:
        if "me_id" in cache and headers is user_auth_headers:
            return cache["me_id"]
        rr = await client.get("/api/v1/auth/me", headers=headers)
        assert rr.status_code == 200, rr.text
        uid = rr.json().get("id")
        assert uid
        if headers is user_auth_headers:
            cache["me_id"] = uid
        return uid

    async def _ensure_character_id() -> str:
        if "character_id" in cache:
            return cache["character_id"]
        rr = await client.post(
            "/api/v1/characters/me",
            json={
                "slug": "fullrun_char",
                "display_name": "FullRun",
                "description": "d",
                "system_prompt": "You are test",
                "is_public": False,
                "is_nsfw": False,
            },
            headers=user_auth_headers,
        )
        assert rr.status_code == 200, rr.text
        cid = rr.json().get("id")
        assert cid
        cache["character_id"] = cid
        return cid

    async def _ensure_room_id() -> str:
        if "room_id" in cache:
            return cache["room_id"]
        cid = await _ensure_character_id()
        rr = await client.post(
            "/api/v1/rooms/me",
            json={
                "title": "Room",
                "description": "d",
                "is_public": False,
                "is_nsfw": False,
                "participant_character_ids": [cid],
            },
            headers=user_auth_headers,
        )
        assert rr.status_code == 200, rr.text
        rid = rr.json().get("id")
        assert rid
        cache["room_id"] = rid
        return rid

    async def _ensure_chat_session_id() -> str:
        if "chat_session_id" in cache:
            return cache["chat_session_id"]
        cid = await _ensure_character_id()
        rr = await client.post(
            "/api/v1/chat/sessions",
            json={"character_id": cid, "room_id": None, "title": ""},
            headers=user_auth_headers,
        )
        assert rr.status_code == 200, rr.text
        sid = rr.json().get("id")
        assert sid
        cache["chat_session_id"] = sid
        return sid

    async def _ensure_memory_id() -> str:
        if "memory_id" in cache:
            return cache["memory_id"]
        rr = await client.post(
            "/api/v1/memory/me",
            json={"title": "t", "content": "c", "importance": 1, "is_pinned": False},
            headers=user_auth_headers,
        )
        assert rr.status_code == 200, rr.text
        mid = rr.json().get("id")
        assert mid
        cache["memory_id"] = mid
        return mid

    async def _ensure_post_id() -> str:
        if "post_id" in cache:
            return cache["post_id"]
        rr = await client.post(
            "/api/v1/posts/me",
            json={"title": "t", "content": "c", "character_id": None, "media": None, "is_public": False},
            headers=user_auth_headers,
        )
        assert rr.status_code == 200, rr.text
        pid = rr.json().get("id")
        assert pid
        cache["post_id"] = pid
        return pid

    async def _ensure_theme_id() -> str:
        if "theme_id" in cache:
            return cache["theme_id"]
        rr = await client.post(
            "/api/v1/themes/me",
            json={
                "theme_type": "ui",
                "slug": "fullrun",
                "display_name": "FullRun",
                "description": "d",
                "is_public": False,
                "light_tokens": {"bg": "#000"},
                "dark_tokens": {"bg": "#111"},
            },
            headers=user_auth_headers,
        )
        assert rr.status_code == 200, rr.text
        tid = rr.json().get("id")
        assert tid
        cache["theme_id"] = tid
        return tid

    async def _ensure_upload_public_id() -> str:
        if "upload_public_id" in cache:
            return cache["upload_public_id"]
        files = {"image": ("x.png", b"123", "image/png")}
        rr = await client.post("/api/v1/uploads/image", files=files, headers=user_auth_headers)
        assert rr.status_code == 200, rr.text
        pid = rr.json().get("public_id")
        assert pid
        cache["upload_public_id"] = pid
        return pid

    async def _ensure_user_has_pro() -> None:
        if cache.get("has_pro"):
            return
        uid = await _me_id(user_auth_headers)
        rr = await client.post(
            "/api/v1/subscriptions/admin/set",
            json={"user_id": uid, "tier": "pro", "expires_at": None},
            headers=admin_auth_headers,
        )
        assert rr.status_code == 200, rr.text
        cache["has_pro"] = True

    # Build per operation request.
    async def build_request(method: str, path: str) -> dict[str, Any]:
        method_u = method.upper()

        if path == "/api/v1/auth/register" and method_u == "POST":
            u = f"u_{uuid.uuid4().hex[:8]}"
            return {
                "method": method_u,
                "url": path,
                "json": {"username": u, "email": f"{u}@example.com", "password": "password123"},
                "headers": {"X-Session-Id": "test", "X-Device-Id": "test"},
                "expect": {200},
            }

        if path == "/api/v1/auth/login" and method_u == "POST":
            # Ensure a dedicated user exists.
            u = f"login_{uuid.uuid4().hex[:8]}"
            rr = await client.post(
                "/api/v1/auth/register",
                json={"username": u, "email": f"{u}@example.com", "password": "password123"},
                headers={"X-Session-Id": "test", "X-Device-Id": "test"},
            )
            assert rr.status_code == 200, rr.text
            return {
                "method": method_u,
                "url": path,
                "data": {"username": u, "password": "password123"},
                "headers": {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-Session-Id": "test",
                    "X-Device-Id": "test",
                },
                "expect": {200},
            }

        if path == "/api/v1/auth/refresh" and method_u == "POST":
            # Use existing logged-in user from fixture by logging in again quickly.
            u = f"refresh_{uuid.uuid4().hex[:8]}"
            rr = await client.post(
                "/api/v1/auth/register",
                json={"username": u, "email": f"{u}@example.com", "password": "password123"},
                headers={"X-Session-Id": "test", "X-Device-Id": "test"},
            )
            assert rr.status_code == 200, rr.text
            tok = await client.post(
                "/api/v1/auth/login",
                data={"username": u, "password": "password123"},
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-Session-Id": "test",
                    "X-Device-Id": "test",
                },
            )
            assert tok.status_code == 200, tok.text
            refresh_token = tok.json().get("refresh_token")
            assert refresh_token
            return {
                "method": method_u,
                "url": path,
                "json": {"refresh_token": refresh_token},
                "headers": {"X-Session-Id": "test", "X-Device-Id": "test"},
                "expect": {200},
            }

        if path == "/api/v1/auth/logout" and method_u == "POST":
            u = f"logout_{uuid.uuid4().hex[:8]}"
            rr = await client.post(
                "/api/v1/auth/register",
                json={"username": u, "email": f"{u}@example.com", "password": "password123"},
                headers={"X-Session-Id": "test", "X-Device-Id": "test"},
            )
            assert rr.status_code == 200, rr.text
            tok = await client.post(
                "/api/v1/auth/login",
                data={"username": u, "password": "password123"},
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-Session-Id": "test",
                    "X-Device-Id": "test",
                },
            )
            assert tok.status_code == 200, tok.text
            refresh_token = tok.json().get("refresh_token")
            assert refresh_token
            return {
                "method": method_u,
                "url": path,
                "json": {"refresh_token": refresh_token},
                "headers": {"X-Session-Id": "test", "X-Device-Id": "test"},
                "expect": {200},
            }

        if path == "/api/v1/auth/logout-all" and method_u == "POST":
            return {"method": method_u, "url": path, "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/auth/refresh/cleanup" and method_u == "POST":
            return {"method": method_u, "url": path, "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/auth/me" and method_u == "GET":
            return {"method": method_u, "url": path, "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/users/me" and method_u == "PATCH":
            return {
                "method": method_u,
                "url": path,
                "json": {"preferred_name": "Tester"},
                "headers": user_auth_headers,
                "expect": {200},
            }

        if path == "/api/v1/users/me/languages" and method_u == "PUT":
            return {
                "method": method_u,
                "url": path,
                "json": {"native_language": "ru", "target_language": "en"},
                "headers": user_auth_headers,
                "expect": {200},
            }

        if path == "/api/v1/users/me/export" and method_u == "GET":
            await _ensure_user_has_pro()
            return {"method": method_u, "url": path, "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/public/users" and method_u == "GET":
            return {"method": method_u, "url": path, "expect": {200}}

        if path == "/api/v1/public/users/by-username/{username}" and method_u == "GET":
            # Create user so it exists.
            me = await client.get("/api/v1/auth/me", headers=user_auth_headers)
            assert me.status_code == 200
            username = me.json().get("username") or "user1"
            return {"method": method_u, "url": f"/api/v1/public/users/by-username/{username}", "expect": {200}}

        if path == "/api/v1/characters/me" and method_u == "GET":
            return {"method": method_u, "url": path, "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/characters/me" and method_u == "POST":
            # Create an extra character.
            return {
                "method": method_u,
                "url": path,
                "json": {
                    "slug": f"c_{uuid.uuid4().hex[:6]}",
                    "display_name": "C",
                    "description": "d",
                    "system_prompt": "You are test",
                    "is_public": False,
                    "is_nsfw": False,
                },
                "headers": user_auth_headers,
                "expect": {200},
            }

        if path == "/api/v1/characters/me/{character_id}" and method_u == "PATCH":
            cid = await _ensure_character_id()
            return {
                "method": method_u,
                "url": f"/api/v1/characters/me/{cid}",
                "json": {"description": "d2"},
                "headers": user_auth_headers,
                "expect": {200},
            }

        if path == "/api/v1/characters/me/{character_id}" and method_u == "DELETE":
            # Create a throwaway character to delete.
            rr = await client.post(
                "/api/v1/characters/me",
                json={
                    "slug": f"del_{uuid.uuid4().hex[:6]}",
                    "display_name": "D",
                    "description": "d",
                    "system_prompt": "You are test",
                    "is_public": False,
                    "is_nsfw": False,
                },
                headers=user_auth_headers,
            )
            assert rr.status_code == 200
            cid = rr.json().get("id")
            return {"method": method_u, "url": f"/api/v1/characters/me/{cid}", "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/characters/public" and method_u == "GET":
            return {"method": method_u, "url": path, "expect": {200}}

        if path == "/api/v1/characters/public/{character_id}" and method_u == "GET":
            cid = await _ensure_character_id()
            return {"method": method_u, "url": f"/api/v1/characters/public/{cid}", "expect": {200}}

        if path == "/api/v1/rooms/me" and method_u == "GET":
            return {"method": method_u, "url": path, "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/rooms/me" and method_u == "POST":
            cid = await _ensure_character_id()
            return {
                "method": method_u,
                "url": path,
                "json": {
                    "title": f"R_{uuid.uuid4().hex[:6]}",
                    "description": "d",
                    "is_public": False,
                    "is_nsfw": False,
                    "participant_character_ids": [cid],
                },
                "headers": user_auth_headers,
                "expect": {200},
            }

        if path == "/api/v1/rooms/me/{room_id}" and method_u == "GET":
            rid = await _ensure_room_id()
            return {"method": method_u, "url": f"/api/v1/rooms/me/{rid}", "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/rooms/me/{room_id}" and method_u == "PATCH":
            rid = await _ensure_room_id()
            return {
                "method": method_u,
                "url": f"/api/v1/rooms/me/{rid}",
                "json": {"title": "Room2"},
                "headers": user_auth_headers,
                "expect": {200},
            }

        if path == "/api/v1/rooms/me/{room_id}" and method_u == "DELETE":
            # Create throwaway room.
            cid = await _ensure_character_id()
            rr = await client.post(
                "/api/v1/rooms/me",
                json={
                    "title": f"RD_{uuid.uuid4().hex[:6]}",
                    "description": "d",
                    "is_public": False,
                    "is_nsfw": False,
                    "participant_character_ids": [cid],
                },
                headers=user_auth_headers,
            )
            assert rr.status_code == 200
            rid = rr.json().get("id")
            return {"method": method_u, "url": f"/api/v1/rooms/me/{rid}", "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/chat/sessions" and method_u == "GET":
            return {"method": method_u, "url": path, "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/chat/sessions" and method_u == "POST":
            cid = await _ensure_character_id()
            return {
                "method": method_u,
                "url": path,
                "json": {"character_id": cid, "room_id": None, "title": ""},
                "headers": user_auth_headers,
                "expect": {200},
            }

        if path == "/api/v1/chat/sessions/{session_id}" and method_u == "GET":
            sid = await _ensure_chat_session_id()
            return {"method": method_u, "url": f"/api/v1/chat/sessions/{sid}", "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/chat/sessions/{session_id}/turn" and method_u == "POST":
            sid = await _ensure_chat_session_id()
            return {
                "method": method_u,
                "url": f"/api/v1/chat/sessions/{sid}/turn",
                "json": {"content": "hi"},
                "headers": user_auth_headers,
                "expect": {200},
            }

        if path == "/api/v1/memory/me" and method_u == "GET":
            return {"method": method_u, "url": path, "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/memory/me" and method_u == "POST":
            return {
                "method": method_u,
                "url": path,
                "json": {"title": f"t_{uuid.uuid4().hex[:6]}", "content": "c", "importance": 1, "is_pinned": False},
                "headers": user_auth_headers,
                "expect": {200},
            }

        if path == "/api/v1/memory/me/{memory_id}" and method_u == "PATCH":
            mid = await _ensure_memory_id()
            return {
                "method": method_u,
                "url": f"/api/v1/memory/me/{mid}",
                "json": {"title": "t2"},
                "headers": user_auth_headers,
                "expect": {200},
            }

        if path == "/api/v1/memory/me/{memory_id}" and method_u == "DELETE":
            # Create throwaway memory.
            rr = await client.post(
                "/api/v1/memory/me",
                json={"title": "del", "content": "c", "importance": 1, "is_pinned": False},
                headers=user_auth_headers,
            )
            assert rr.status_code == 200
            mid = rr.json().get("id")
            return {"method": method_u, "url": f"/api/v1/memory/me/{mid}", "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/uploads/image" and method_u == "POST":
            files = {"image": ("x.png", b"123", "image/png")}
            return {"method": method_u, "url": path, "files": files, "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/uploads/presign" and method_u == "GET":
            pid = await _ensure_upload_public_id()
            return {
                "method": method_u,
                "url": path,
                "params": {"public_id": pid},
                "headers": user_auth_headers,
                "expect": {200},
            }

        if path == "/api/v1/posts/public" and method_u == "GET":
            return {"method": method_u, "url": path, "expect": {200}}

        if path == "/api/v1/posts/public/by-user/{username}" and method_u == "GET":
            me = await client.get("/api/v1/auth/me", headers=user_auth_headers)
            assert me.status_code == 200
            username = me.json().get("username")
            return {"method": method_u, "url": f"/api/v1/posts/public/by-user/{username}", "expect": {200}}

        if path == "/api/v1/posts/public/by-character/{character_id}" and method_u == "GET":
            cid = await _ensure_character_id()
            return {"method": method_u, "url": f"/api/v1/posts/public/by-character/{cid}", "expect": {200}}

        if path == "/api/v1/posts/me" and method_u == "GET":
            return {"method": method_u, "url": path, "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/posts/me" and method_u == "POST":
            return {
                "method": method_u,
                "url": path,
                "json": {"title": "t", "content": "c", "character_id": None, "media": None, "is_public": False},
                "headers": user_auth_headers,
                "expect": {200},
            }

        if path == "/api/v1/posts/me/{post_id}" and method_u == "DELETE":
            rr = await client.post(
                "/api/v1/posts/me",
                json={"title": "del", "content": "c", "character_id": None, "media": None, "is_public": False},
                headers=user_auth_headers,
            )
            assert rr.status_code == 200
            pid = rr.json().get("id")
            return {"method": method_u, "url": f"/api/v1/posts/me/{pid}", "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/posts/me/{post_id}/share" and method_u == "POST":
            pid = await _ensure_post_id()
            return {
                "method": method_u,
                "url": f"/api/v1/posts/me/{pid}/share",
                "json": {"is_public": True},
                "headers": user_auth_headers,
                "expect": {200},
            }

        if path == "/api/v1/posts/{post_id}/like" and method_u == "POST":
            pid = await _ensure_post_id()
            return {"method": method_u, "url": f"/api/v1/posts/{pid}/like", "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/posts/{post_id}/like" and method_u == "DELETE":
            pid = await _ensure_post_id()
            # Ensure liked first.
            await client.post(f"/api/v1/posts/{pid}/like", headers=user_auth_headers)
            return {"method": method_u, "url": f"/api/v1/posts/{pid}/like", "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/themes/available" and method_u == "GET":
            return {"method": method_u, "url": path, "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/themes/me" and method_u == "POST":
            return {
                "method": method_u,
                "url": path,
                "json": {
                    "theme_type": "ui",
                    "slug": f"t_{uuid.uuid4().hex[:6]}",
                    "display_name": "T",
                    "description": "d",
                    "is_public": False,
                    "light_tokens": {"bg": "#000"},
                    "dark_tokens": {"bg": "#111"},
                },
                "headers": user_auth_headers,
                "expect": {200},
            }

        if path == "/api/v1/themes/me/select" and method_u == "POST":
            tid = await _ensure_theme_id()
            return {"method": method_u, "url": path, "json": {"theme_id": tid}, "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/themes/characters/{character_id}/select-chat" and method_u == "POST":
            tid = await _ensure_theme_id()
            cid = await _ensure_character_id()
            return {
                "method": method_u,
                "url": f"/api/v1/themes/characters/{cid}/select-chat",
                "json": {"theme_id": tid},
                "headers": user_auth_headers,
                "expect": {200},
            }

        if path == "/api/v1/subscriptions/me" and method_u == "GET":
            return {"method": method_u, "url": path, "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/subscriptions/cancel" and method_u == "POST":
            await _ensure_user_has_pro()
            return {"method": method_u, "url": path, "json": {"cancel_now": True}, "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/subscriptions/history" and method_u == "GET":
            await _ensure_user_has_pro()
            return {"method": method_u, "url": path, "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/subscriptions/admin/history/{user_id}" and method_u == "GET":
            await _ensure_user_has_pro()
            uid = await _me_id(user_auth_headers)
            return {"method": method_u, "url": f"/api/v1/subscriptions/admin/history/{uid}", "headers": admin_auth_headers, "expect": {200}}

        if path == "/api/v1/subscriptions/admin/set" and method_u == "POST":
            uid = await _me_id(user_auth_headers)
            return {
                "method": method_u,
                "url": path,
                "json": {"user_id": uid, "tier": "plus", "expires_at": None},
                "headers": admin_auth_headers,
                "expect": {200},
            }

        if path == "/api/v1/achievements/" and method_u == "GET":
            return {"method": method_u, "url": path, "expect": {200}}

        if path == "/api/v1/achievements/me" and method_u == "GET":
            return {"method": method_u, "url": path, "headers": user_auth_headers, "expect": {200}}

        if path == "/api/v1/achievements/admin/award" and method_u == "POST":
            uid = await _me_id(user_auth_headers)
            return {
                "method": method_u,
                "url": path,
                "json": {"user_id": uid, "slug": "perfectionist_3stars", "context": {}},
                "headers": admin_auth_headers,
                "expect": {200, 400, 404},
            }

        raise AssertionError(f"No request mapping for {method_u} {path}")

    # Execute every OpenAPI operation.
    failures: list[str] = []

    for path, item in sorted(paths.items(), key=lambda x: x[0]):
        if not path.startswith("/api/v1/"):
            continue
        methods = {m.lower(): v for m, v in (item or {}).items() if m.lower() in {"get", "post", "put", "patch", "delete"}}
        for method in sorted(methods.keys()):
            req = await build_request(method, path)
            http_method = req["method"].lower()
            url = req["url"]
            expect = req.get("expect", {200})
            kwargs = {k: v for k, v in req.items() if k not in {"method", "url", "expect"}}

            rr = await client.request(http_method, url, **kwargs)

            if rr.status_code not in expect:
                failures.append(f"{http_method.upper()} {path} -> {rr.status_code} expected {sorted(expect)} body={rr.text}")

    assert not failures, "\n".join(failures)
