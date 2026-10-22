import json
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.routes import health
from app.main import app


def test_health():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "payresolve-api"


@pytest.mark.asyncio
@pytest.mark.parametrize("database,redis,status", [(True, True, 200), (False, True, 503), (True, False, 503)])
async def test_readiness_depends_on_database_and_redis(monkeypatch, database, redis, status):
    monkeypatch.setattr(health, "database_ok", AsyncMock(return_value=database))
    monkeypatch.setattr(health, "redis_ok", AsyncMock(return_value=redis))
    response = await health.ready()
    assert response.status_code == status
    assert json.loads(response.body)["dependencies"] == {"database": database, "redis": redis}
