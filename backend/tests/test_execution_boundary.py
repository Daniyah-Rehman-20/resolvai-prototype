from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from app.services import approvals


async def test_production_approval_cannot_claim_payment_execution(monkeypatch):
    async def lookup(*args, **kwargs):
        return SimpleNamespace(status="PENDING")
    monkeypatch.setattr(approvals, "get_approval", lookup)
    monkeypatch.setattr(approvals.settings, "app_env", "production")
    with pytest.raises(HTTPException) as exc:
        await approvals.decide(None, "approval", "APPROVED", "Reviewed", "staff")
    assert exc.value.status_code == 503
    assert "No financial action" in exc.value.detail
