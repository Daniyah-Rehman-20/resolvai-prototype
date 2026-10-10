from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core import rate_limit
from app.core.config import settings


def request(demo_user="spoof", path="/auth/login"):
    return Request({"type": "http", "method": "POST", "path": path,
                    "headers": [(b"x-demo-user", demo_user.encode())],
                    "client": ("192.0.2.1", 54321), "server": ("test", 80),
                    "scheme": "http", "query_string": b""})


async def test_rate_limit_ignores_spoofed_identity_headers(monkeypatch):
    client = AsyncMock()
    client.eval.return_value = 1
    monkeypatch.setattr(rate_limit, "redis_client", lambda: client)
    await rate_limit.enforce_rate_limit(request("alice"))
    await rate_limit.enforce_rate_limit(request("bob"))
    assert client.eval.call_args_list[0].args[2] == client.eval.call_args_list[1].args[2]
    client.eval.return_value = 11
    with pytest.raises(HTTPException) as exc:
        await rate_limit.enforce_rate_limit(request("new-bypass-name"))
    assert exc.value.status_code == 429


async def test_production_limiter_outage_is_fail_closed(monkeypatch):
    client = AsyncMock()
    client.eval.side_effect = ConnectionError("offline")
    monkeypatch.setattr(rate_limit, "redis_client", lambda: client)
    monkeypatch.setattr(settings, "app_env", "production")
    with pytest.raises(HTTPException) as exc:
        await rate_limit.enforce_rate_limit(request())
    assert exc.value.status_code == 503


async def test_development_limiter_fallback_still_limits(monkeypatch):
    client = AsyncMock()
    client.eval.side_effect = ConnectionError("offline")
    monkeypatch.setattr(rate_limit, "redis_client", lambda: client)
    monkeypatch.setattr(settings, "app_env", "test")
    monkeypatch.setattr(settings, "rate_limit_requests", 2)
    monkeypatch.setattr(rate_limit, "_local_buckets", {})
    await rate_limit.enforce_rate_limit(request())
    await rate_limit.enforce_rate_limit(request())
    with pytest.raises(HTTPException) as exc:
        await rate_limit.enforce_rate_limit(request())
    assert exc.value.status_code == 429
