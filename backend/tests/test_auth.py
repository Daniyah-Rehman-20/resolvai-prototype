from datetime import datetime, timedelta, timezone

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes.auth import router
from app.core.config import Settings, settings
from app.core.security import current_principal, require
from app.db.base import Base
from app.db.session import get_db
from app.models.auth import AuthSession, User
from app.services.auth import token_digest, verify_password


@pytest.fixture
async def auth_app(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "auth_demo_enabled", False)
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/auth.db")
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: User.__table__.create(c))
        await conn.run_sync(lambda c: AuthSession.__table__.create(c))
    app = FastAPI()
    app.include_router(router)

    async def database():
        async with sessions() as db:
            yield db
    app.dependency_overrides[get_db] = database

    @app.get("/staff", dependencies=[Depends(require("viewer"))])
    async def staff():
        return {"ok": True}

    yield TestClient(app), sessions
    await engine.dispose()


def register(client, email="user@example.com"):
    response = client.post("/auth/register", json={"email": email, "password": "Strong passphrase 123!"})
    assert response.status_code == 201, response.text
    return response.json()


async def test_persistent_sessions_login_logout_and_password_hash(auth_app):
    client, sessions = auth_app
    result = register(client)
    token = result["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert result["user"]["role"] == "customer"
    assert client.get("/auth/me", headers=headers).json() == result["user"]
    async with sessions() as db:
        user = await db.get(User, result["user"]["id"])
        assert user.password_hash != "Strong passphrase 123!"
        assert verify_password("Strong passphrase 123!", user.password_hash)
        assert await db.get(AuthSession, token_digest(token)) is not None
        assert await db.get(AuthSession, token) is None
    login = client.post("/auth/login", json={"email": "USER@example.com", "password": "Strong passphrase 123!"})
    assert login.status_code == 200
    assert login.json()["access_token"] != token
    assert client.post("/auth/logout", headers=headers).status_code == 204
    assert client.get("/auth/me", headers=headers).status_code == 401


async def test_customer_headers_cannot_impersonate_staff(auth_app):
    client, _ = auth_app
    result = register(client)
    headers = {"Authorization": f"Bearer {result['access_token']}",
               "X-Demo-Role": "admin", "X-Demo-User": "another-user"}
    assert client.get("/auth/me", headers=headers).json()["id"] == result["user"]["id"]
    assert client.get("/staff", headers=headers).status_code == 403
    payload = {"email": "admin@example.com", "password": "Strong passphrase 123!", "role": "admin"}
    assert client.post("/auth/register", json=payload).status_code == 422


async def test_expired_and_invalid_session(auth_app):
    client, sessions = auth_app
    result = register(client)
    token = result["access_token"]
    async with sessions() as db:
        session = await db.get(AuthSession, token_digest(token))
        session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        await db.commit()
    for bearer in [token, token + "tampered", settings.auth_demo_token]:
        assert client.get("/auth/me", headers={"Authorization": f"Bearer {bearer}"}).status_code == 401


async def test_generic_credentials_errors_and_unique_email(auth_app):
    client, _ = auth_app
    register(client)
    bad = client.post("/auth/login", json={"email": "user@example.com", "password": "bad"})
    missing = client.post("/auth/login", json={"email": "absent@example.com", "password": "bad"})
    assert bad.status_code == missing.status_code == 401
    assert bad.json() == missing.json()
    duplicate = client.post("/auth/register", json={"email": " USER@example.com ", "password": "Strong passphrase 123!"})
    assert duplicate.status_code == 409
    assert client.post("/auth/register", json={"email": "new@example.com", "password": "short"}).status_code == 422


def test_production_demo_guard():
    with pytest.raises(ValueError, match="Demo authentication"):
        Settings(app_env="production", auth_demo_enabled=True)
    assert Settings(app_env="production", auth_demo_enabled=False).auth_demo_enabled is False
