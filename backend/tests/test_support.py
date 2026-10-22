import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.api.routes.support import router
from app.core.security import Principal, current_principal
from app.db.base import Base
from app.db.session import get_db
from app.services.support import extract_queries, redact_sensitive


@pytest.fixture
async def support_client(monkeypatch):
    monkeypatch.delenv("SUPPORT_AI_API_KEY", raising=False)
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    app = FastAPI()
    app.include_router(router)
    async def db():
        async with sessions() as session:
            yield session
    app.dependency_overrides[get_db] = db
    app.dependency_overrides[current_principal] = lambda: Principal("alice", "customer")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client, app
    await engine.dispose()


async def test_ownership_and_persistence(support_client):
    client, app = support_client
    response = await client.post("/support/conversations", json={"channel": "chat"})
    assert response.status_code == 201
    cid = response.json()["id"]
    result = await client.post(f"/support/conversations/{cid}/messages",
        json={"content": "My UPI payment of INR 500 failed. OTP 123456 and account 12345678901234"})
    assert result.status_code == 200
    assert result.json()["message"]["mode"] == "guided_intake"
    assert result.json()["queries"][0]["facts"]["verified"] is False
    stored = (await client.get(f"/support/conversations/{cid}")).json()
    assert len(stored["messages"]) == 2
    assert "123456" not in stored["messages"][0]["content"]
    app.dependency_overrides[current_principal] = lambda: Principal("bob", "customer")
    assert (await client.get("/support/conversations")).json() == []
    assert (await client.get(f"/support/conversations/{cid}")).status_code == 404
    assert (await client.post(f"/support/conversations/{cid}/messages", json={"content": "hello"})).status_code == 404


async def test_consent_and_validation(support_client):
    client, _ = support_client
    assert (await client.post("/support/conversations", json={"channel": "voice"})).status_code == 422
    created = await client.post("/support/conversations", json={"channel": "voice", "recording_consent": True})
    assert created.status_code == 201
    assert created.json()["consent_at"]
    cid = created.json()["id"]
    for content in (" ", "a" * 8001):
        assert (await client.post(f"/support/conversations/{cid}/messages", json={"content": content})).status_code == 422


async def test_fraud_triage_is_local(support_client):
    client, _ = support_client
    cid = (await client.post("/support/conversations", json={})).json()["id"]
    result = await client.post(f"/support/conversations/{cid}/messages", json={"content": "This was an unauthorized card payment"})
    assert result.json()["queries"][0]["status"] == "needs_human_review"
    assert "no external complaint" in result.json()["message"]["content"]
    assert (await client.get(f"/support/conversations/{cid}")).json()["status"] == "needs_human_review"


def test_redaction_and_intake_facts():
    assert "9876" not in redact_sensitive("PIN: 9876")
    assert "1234 5678" not in redact_sensitive("card 1234 5678 9012 3456")
    rows = extract_queries("UPI INR 1,250.50 failed? Did merchant receive it?")
    assert len(rows) == 2
    assert rows[0]["facts"]["amount"] == "1250.50"
    assert rows[0]["facts"]["provenance"] == "user_reported"
    many = extract_queries(" ".join(f"Concern {i}?" for i in range(20)))
    assert len(many) == 12
    assert "Concern 19?" in many[-1]["summary"]


async def test_voice_consent_ownership_and_private_recordings(support_client, tmp_path, monkeypatch):
    from app.api.routes.voice import router as voice_router
    from app.services import voice
    client, app = support_client
    app.include_router(voice_router)
    config = voice.VoiceSettings(storage_dir=tmp_path / "private", transcription_api_key="test")
    monkeypatch.setattr(voice, "configuration", lambda: config)
    async def transcription(*args):
        return "My UPI failed. PIN 9876"
    monkeypatch.setattr(voice, "transcribe", transcription)
    cid = (await client.post("/support/conversations", json={"channel": "voice", "recording_consent": True})).json()["id"]
    audio = b"\x1a\x45\xdf\xa3audio"
    url = f"/support/conversations/{cid}"
    assert (await client.post(url + "/audio", files={"file": ("clip.webm", audio, "audio/webm")})).status_code == 403
    result = await client.post(url + "/audio", data={"consent": "true"}, files={"file": ("clip.webm", audio, "audio/webm")})
    assert result.status_code == 200
    assert "9876" not in result.json()["transcript"]
    rid = result.json()["recording"]["id"]
    recording_url = url + f"/recordings/{rid}"
    download = await client.get(recording_url)
    assert download.content == audio
    assert download.headers["cache-control"] == "private, no-store"
    app.dependency_overrides[current_principal] = lambda: Principal("bob", "customer")
    for path in (url + "/recordings", recording_url):
        assert (await client.get(path)).status_code == 404
    assert (await client.delete(recording_url)).status_code == 404
    assert (await client.post(url + "/audio", data={"consent": "true"}, files={"file": ("clip.webm", audio, "audio/webm")})).status_code == 404
    app.dependency_overrides[current_principal] = lambda: Principal("alice", "customer")
    assert (await client.delete(recording_url)).status_code == 204
    assert (await client.get(recording_url)).status_code == 404


async def test_customer_cannot_review_and_staff_review_is_audited(support_client):
    client, app = support_client
    cid = (await client.post("/support/conversations", json={})).json()["id"]
    result = await client.post(f"/support/conversations/{cid}/messages", json={"content": "UPI failed"})
    qid = result.json()["queries"][0]["id"]
    body = {"status": "in_review", "reviewer_note": "Asked customer for masked reference"}
    assert (await client.get("/support/queue")).status_code == 403
    assert (await client.patch(f"/support/queries/{qid}", json=body)).status_code == 403
    app.dependency_overrides[current_principal] = lambda: Principal("agent", "analyst")
    assert (await client.get("/support/queue")).status_code == 200
    reviewed = await client.patch(f"/support/queries/{qid}", json=body)
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "in_review"
    assert reviewed.json()["reviewed_at"]
    from sqlalchemy import select
    from app.models.domain import AuditEvent
    async for db in app.dependency_overrides[get_db]():
        event = await db.scalar(select(AuditEvent).where(AuditEvent.resource_id == qid))
        assert event.actor == "agent" and event.action == "support.query.reviewed"


async def test_ai_uses_curated_sources_and_fails_safely(monkeypatch):
    import httpx
    from app.services import support
    monkeypatch.setenv("SUPPORT_AI_API_KEY", "test-key")
    monkeypatch.setenv("SUPPORT_AI_BASE_URL", "https://provider.example/v1")
    original_client = httpx.AsyncClient
    def handler(request):
        import json
        body = json.loads(request.content)
        system = body["messages"][0]["content"]
        assert "RBI/2019-20/67" in system
        assert "NO access to bank systems" in system
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(200, json={"choices": [{"message": {"content": "Contact your bank. PIN 9876"}}]})
    monkeypatch.setattr(support.httpx, "AsyncClient", lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs))
    answer, mode, sources = await support.generate_answer("My UPI payment is pending", [], False)
    assert mode == "ai_intake" and "9876" not in answer
    assert any(source["url"] and "rbi.org.in" in source["url"] for source in sources)
    monkeypatch.setenv("SUPPORT_AI_BASE_URL", "http://unsafe.example/v1")
    answer, mode, _ = await support.generate_answer("My UPI payment is pending", [], False)
    assert mode == "guided_intake"
