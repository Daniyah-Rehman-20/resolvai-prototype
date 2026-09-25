from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def auth(role: str):
    return {
        "Authorization": f"Bearer {settings.auth_demo_token}",
        "X-Demo-Role": role,
        "X-Demo-User": "test-user",
    }

def test_transactions_require_authentication():
    response = client.get("/transactions")
    assert response.status_code == 401

def test_viewer_cannot_start_investigation():
    response = client.post(
        "/investigations",
        headers=auth("viewer"),
        json={"transaction_id": "TXN-10021", "question": "What happened?"},
    )
    assert response.status_code == 403

def test_analyst_cannot_approve():
    response = client.post(
        "/approvals/APR-does-not-matter/approve",
        headers=auth("analyst"),
        json={"note": "test"},
    )
    assert response.status_code == 403
