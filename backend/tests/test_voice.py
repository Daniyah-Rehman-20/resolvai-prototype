from datetime import datetime, timedelta, timezone
from io import BytesIO
import json
from uuid import uuid4
import httpx
import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers
from app.services import voice


def configuration(tmp_path, **overrides):
    return voice.VoiceSettings(storage_dir=tmp_path / "recordings", **overrides)


def upload(data=b"test audio", mime="audio/webm"):
    return UploadFile(BytesIO(data), filename="untrusted.webm", headers=Headers({"content-type": mime}))


@pytest.mark.asyncio
async def test_upload_limits_and_types(tmp_path):
    config = configuration(tmp_path, max_upload_bytes=1024)
    for data, mime, status in [(b"x" * 1025, "audio/webm", 413), (b"x", "text/html", 415), (b"", "audio/webm", 422)]:
        with pytest.raises(HTTPException) as error:
            await voice.read_audio(upload(data, mime), config)
        assert error.value.status_code == status
    valid_webm = b"\x1a\x45\xdf\xa3audio"
    assert await voice.read_audio(upload(valid_webm, "audio/webm;codecs=opus"), config) == (valid_webm, "audio/webm")
    with pytest.raises(HTTPException) as error:
        await voice.read_audio(upload(b"<html>not audio</html>"), config)
    assert error.value.status_code == 415


@pytest.mark.asyncio
async def test_missing_provider_fails_closed(tmp_path):
    with pytest.raises(HTTPException) as error:
        await voice.transcribe(b"audio", "audio/webm", configuration(tmp_path, transcription_api_key=""))
    assert error.value.status_code == 503


@pytest.mark.asyncio
async def test_provider_request_and_failure_are_real_and_sanitized(tmp_path, monkeypatch):
    original_client = httpx.AsyncClient
    def handler(request):
        assert request.url == "https://api.openai.com/v1/audio/transcriptions"
        assert request.headers["authorization"] == "Bearer test-secret"
        assert b"gpt-4o-mini-transcribe" in request.content
        assert b"audio-bytes" in request.content
        return httpx.Response(200, json={"text": " Money was debited but payment failed "})
    monkeypatch.setattr(voice.httpx, "AsyncClient", lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs))
    config = configuration(tmp_path, transcription_api_key="test-secret")
    assert await voice.transcribe(b"audio-bytes", "audio/webm", config) == "Money was debited but payment failed"
    def unavailable(request):
        return httpx.Response(401, json={"error": "secret provider details"})
    monkeypatch.setattr(voice.httpx, "AsyncClient", lambda **kwargs: original_client(transport=httpx.MockTransport(unavailable), **kwargs))
    with pytest.raises(HTTPException) as error:
        await voice.transcribe(b"audio", "audio/webm", config)
    assert error.value.status_code == 502
    assert "secret" not in error.value.detail


def test_private_storage_expiry_and_delete(tmp_path):
    config = configuration(tmp_path)
    conversation = uuid4()
    metadata = voice.save_recording(config, conversation, b"voice payload", "audio/webm")
    loaded, path = voice.load_recording(config, conversation, metadata["id"])
    assert loaded == metadata and path.read_bytes() == b"voice payload"
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700
    assert voice.list_recordings(config, conversation) == [metadata]
    assert voice.list_recordings(config, uuid4()) == []
    metadata["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    path.with_suffix(".json").write_text(json.dumps(metadata))
    assert voice.purge_expired(config) == 1 and not path.exists()
    with pytest.raises(HTTPException) as error:
        voice.load_recording(config, conversation, metadata["id"])
    assert error.value.status_code == 404


def test_storage_rejects_path_traversal(tmp_path):
    with pytest.raises(ValueError):
        voice.recording_directory(configuration(tmp_path), "../../other-user")
