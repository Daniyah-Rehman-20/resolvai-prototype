import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("path", ["/support/conversations", "/support/queue", "/audit", "/telephony/capabilities"])
def test_support_and_staff_endpoints_require_authentication(path):
    assert client.get(path).status_code == 401


@pytest.mark.parametrize("method,path", [
    ("post", "/demo/reset"),
    ("post", "/transactions/use-cases/duplicate-charge"),
    ("get", "/transactions"),
    ("post", "/investigations"),
    ("post", "/approvals/example/approve"),
])
def test_removed_demo_endpoints_cannot_be_invoked(method, path):
    assert getattr(client, method)(path).status_code == 404
