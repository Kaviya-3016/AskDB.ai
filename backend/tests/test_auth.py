import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_flow(client: AsyncClient):
    unique_email = f"test_{uuid.uuid4().hex[:8]}@company.com"

    # Register new analyst
    reg_resp = await client.post(
        "/api/auth/register",
        json={
            "email": unique_email,
            "password": "Password@123",
            "full_name": "Test Analyst",
            "role": "analyst",
        },
    )
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert "access_token" in reg_data
    assert "refresh_token" in reg_data
    assert reg_data["user"]["email"] == unique_email

    # Login
    login_resp = await client.post(
        "/api/auth/login",
        json={
            "email": unique_email,
            "password": "Password@123",
        },
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    token = login_data["access_token"]
    refresh = login_data["refresh_token"]

    # Access /auth/me
    me_resp = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == unique_email

    # Refresh token
    ref_resp = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh},
    )
    assert ref_resp.status_code == 200
    assert "access_token" in ref_resp.json()


@pytest.mark.asyncio
async def test_invalid_login_credentials(client: AsyncClient):
    resp = await client.post(
        "/api/auth/login",
        json={"email": "nonexistent@company.com", "password": "WrongPassword"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_google_auth_config(client: AsyncClient):
    resp = await client.get("/api/auth/google/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "client_id" in data
    assert "enabled" in data


@pytest.mark.asyncio
async def test_google_auth_new_user_registration_and_login(client: AsyncClient):
    google_email = f"google_user_{uuid.uuid4().hex[:8]}@gmail.com"
    user_name = "Google Explorer"

    # 1. First time Google Auth -> Auto Register
    resp1 = await client.post(
        "/api/auth/google",
        json={
            "email": google_email,
            "name": user_name,
            "picture": "https://lh3.googleusercontent.com/a/default-user=s96-c",
            "role": "analyst",
        },
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert "access_token" in data1
    assert "refresh_token" in data1
    assert data1["user"]["email"] == google_email
    assert data1["user"]["full_name"] == user_name
    assert data1["user"]["role"] == "analyst"

    # 2. Verify token works on /auth/me
    token1 = data1["access_token"]
    me_resp = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == google_email

    # 3. Second time Google Auth -> Existing User Login
    resp2 = await client.post(
        "/api/auth/google",
        json={
            "email": google_email,
            "name": user_name,
        },
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["user"]["email"] == google_email
    assert data2["user"]["id"] == data1["user"]["id"]


@pytest.mark.asyncio
async def test_google_auth_missing_email_fails(client: AsyncClient):
    resp = await client.post(
        "/api/auth/google",
        json={},
    )
    assert resp.status_code == 400

