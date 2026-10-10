"""Private recording storage and real, server-side speech transcription."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import httpx
from fastapi import HTTPException, UploadFile
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class VoiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="VOICE_", extra="ignore")
    storage_dir: Path = Path("./data/private-recordings")
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, ge=1024, le=24 * 1024 * 1024)
    retention_days: int = Field(default=7, ge=1, le=90)
    transcription_api_key: SecretStr = SecretStr("")
    transcription_base_url: str = "https://api.openai.com/v1"
    transcription_model: str = "gpt-4o-mini-transcribe"


MIME_EXTENSIONS = {
    "audio/webm": "webm", "audio/ogg": "ogg", "audio/wav": "wav",
    "audio/x-wav": "wav", "audio/mpeg": "mp3", "audio/mp4": "mp4",
    "audio/flac": "flac",
}


def configuration() -> VoiceSettings:
    return VoiceSettings()


async def read_audio(file: UploadFile, config: VoiceSettings) -> tuple[bytes, str]:
    mime = (file.content_type or "").split(";", 1)[0].lower().strip()
    if mime not in MIME_EXTENSIONS:
        raise HTTPException(415, "Unsupported audio type; use WebM, Ogg, WAV, MP3, MP4, or FLAC")
    parts = []
    total = 0
    while chunk := await file.read(64 * 1024):
        total += len(chunk)
        if total > config.max_upload_bytes:
            raise HTTPException(413, "Recording exceeds the upload limit")
        parts.append(chunk)
    if not total:
        raise HTTPException(422, "Recording is empty")
    data = b"".join(parts)
    # Reject obvious MIME spoofing before forwarding to the speech provider.
    # Container signatures are not a substitute for the provider's audio decoder.
    valid = {
        "webm": data.startswith(b"\x1a\x45\xdf\xa3"),
        "ogg": data.startswith(b"OggS"),
        "wav": data.startswith(b"RIFF") and data[8:12] == b"WAVE",
        "mp3": data.startswith(b"ID3") or (len(data) >= 2 and data[0] == 0xff and data[1] & 0xe0 == 0xe0),
        "mp4": len(data) >= 12 and data[4:8] == b"ftyp",
        "flac": data.startswith(b"fLaC"),
    }[MIME_EXTENSIONS[mime]]
    if not valid:
        raise HTTPException(415, "Recording bytes do not match the declared audio type")
    return data, mime


async def transcribe(data: bytes, mime: str, config: VoiceSettings) -> str:
    key = config.transcription_api_key.get_secret_value()
    if not key:
        raise HTTPException(503, "Voice transcription is not configured; please use chat")
    url = config.transcription_base_url.rstrip("/") + "/audio/transcriptions"
    if not url.startswith("https://"):
        raise HTTPException(503, "Transcription provider must use HTTPS")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(90, connect=10), follow_redirects=False) as client:
            response = await client.post(
                url, headers={"Authorization": f"Bearer {key}"},
                files={"file": (f"recording.{MIME_EXTENSIONS[mime]}", data, mime)},
                data={"model": config.transcription_model, "response_format": "json"},
            )
            response.raise_for_status()
            text = response.json().get("text", "")
    except (httpx.HTTPError, ValueError, AttributeError) as exc:
        raise HTTPException(502, "Transcription provider unavailable; please retry or use chat") from exc
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(422, "No speech detected; please retry or type your query")
    if len(text) > 8000:
        raise HTTPException(422, "Transcript is too long; record a shorter message")
    return text.strip()


def recording_directory(config: VoiceSettings, conversation_id: str | UUID) -> Path:
    return config.storage_dir / str(UUID(str(conversation_id)))


def save_recording(config: VoiceSettings, conversation_id: str | UUID, data: bytes, mime: str) -> dict:
    directory = recording_directory(config, conversation_id)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(config.storage_dir, 0o700)
    os.chmod(directory, 0o700)
    record_id = str(uuid4())
    now = datetime.now(timezone.utc)
    metadata = {
        "id": record_id, "content_type": mime, "size_bytes": len(data),
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(days=config.retention_days)).isoformat(),
    }
    audio_path = directory / f"{record_id}.audio"
    meta_path = directory / f"{record_id}.json"
    try:
        for path, payload in ((audio_path, data), (meta_path, json.dumps(metadata).encode())):
            with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "wb") as output:
                output.write(payload)
    except Exception:
        audio_path.unlink(missing_ok=True)
        meta_path.unlink(missing_ok=True)
        raise
    return metadata


def delete_recording(config: VoiceSettings, conversation_id: str | UUID, recording_id: str | UUID) -> None:
    directory = recording_directory(config, conversation_id)
    record_id = str(UUID(str(recording_id)))
    (directory / f"{record_id}.audio").unlink(missing_ok=True)
    (directory / f"{record_id}.json").unlink(missing_ok=True)


def load_recording(config: VoiceSettings, conversation_id: str | UUID, recording_id: str | UUID) -> tuple[dict, Path]:
    directory = recording_directory(config, conversation_id)
    record_id = str(UUID(str(recording_id)))
    try:
        metadata = json.loads((directory / f"{record_id}.json").read_text())
        expiry = datetime.fromisoformat(metadata["expires_at"])
    except (OSError, ValueError, KeyError):
        raise HTTPException(404, "Recording not found")
    path = directory / f"{record_id}.audio"
    if expiry <= datetime.now(timezone.utc):
        delete_recording(config, conversation_id, recording_id)
        raise HTTPException(404, "Recording expired")
    if not path.is_file():
        raise HTTPException(404, "Recording not found")
    return metadata, path


def list_recordings(config: VoiceSettings, conversation_id: str | UUID) -> list[dict]:
    result = []
    for path in recording_directory(config, conversation_id).glob("*.json"):
        try:
            result.append(load_recording(config, conversation_id, UUID(path.stem))[0])
        except (HTTPException, ValueError):
            continue
    return sorted(result, key=lambda item: item["created_at"])


def purge_expired(config: VoiceSettings) -> int:
    """Run periodically, also removing audio left behind by an interrupted write."""
    removed = 0
    now = datetime.now(timezone.utc)
    for path in config.storage_dir.glob("*/*.audio"):
        try:
            conversation_id, record_id = UUID(path.parent.name), UUID(path.stem)
            metadata_path = path.with_suffix(".json")
            if metadata_path.exists():
                expired = datetime.fromisoformat(json.loads(metadata_path.read_text())["expires_at"]) <= now
            else:
                expired = now.timestamp() - path.stat().st_mtime > 3600
            if expired:
                delete_recording(config, conversation_id, record_id)
                removed += 1
        except (ValueError, KeyError, OSError):
            continue
    return removed


if __name__ == "__main__":
    print(f"Deleted {purge_expired(configuration())} expired recordings")
