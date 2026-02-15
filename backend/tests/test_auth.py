"""Интеграционные тесты аутентификации.

Проверяем регистрацию, логин и экспорт данных пользователя.
"""

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(async_client: AsyncClient):
    response = await async_client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "strongpassword123",
        "username": "testuser"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_login_user(async_client: AsyncClient):
    # 1. Регистрация
    await async_client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "password": "strongpassword123",
        "username": "loginuser"
    })

    # 2. Логин
    response = await async_client.post("/api/v1/auth/login", data={
        "username": "loginuser",  # Аутентифицируемся по username, а не по email
        "password": "strongpassword123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_export_user_data(async_client: AsyncClient):
    # 1. Регистрация
    await async_client.post("/api/v1/auth/register", json={
        "email": "export@example.com",
        "password": "strongpassword123",
        "username": "exportuser"
    })

    # 2. Логин
    token_resp = await async_client.post("/api/v1/auth/login", data={
        "username": "exportuser",
        "password": "strongpassword123"
    })
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]

    # 3. Экспорт
    export_resp = await async_client.get(
        "/api/v1/users/me/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert export_resp.status_code == 200
    payload = export_resp.json()
    assert "user" in payload
    assert "lessons" in payload
    assert "path" in payload
    assert "streaks" in payload
