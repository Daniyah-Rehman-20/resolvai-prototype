"""Authenticated, consent-gated browser voice turns. Not a PSTN gateway."""
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal, current_principal
from app.db.session import get_db
from app.services.support import intake_message, owned_conversation, redact_sensitive
from app.services import voice

router = APIRouter(prefix="/support/conversations", tags=["voice"])


@router.post("/{conversation_id}/audio")
async def upload_audio(
    conversation_id: UUID,
    file: UploadFile = File(...),
    consent: bool = Form(False),
    principal: Principal = Depends(current_principal),
    db: AsyncSession = Depends(get_db),
):
    conversation = await owned_conversation(db, str(conversation_id), principal.subject)
    if not consent or not conversation.recording_consent:
        raise HTTPException(403, "Explicit recording and transcription consent is required")
    config = voice.configuration()
    if not config.transcription_api_key.get_secret_value():
        raise HTTPException(503, "Voice transcription is not configured; please use chat")
    try:
        data, mime = await voice.read_audio(file, config)
    finally:
        await file.close()
    transcript = await voice.transcribe(data, mime, config)
    metadata = voice.save_recording(config, conversation_id, data, mime)
    try:
        result = await intake_message(db, conversation, transcript)
    except BaseException:
        voice.delete_recording(config, conversation_id, metadata["id"])
        raise
    return {**result, "transcript": redact_sensitive(transcript), "recording": metadata}


@router.get("/{conversation_id}/recordings")
async def recordings(conversation_id: UUID, principal: Principal = Depends(current_principal), db: AsyncSession = Depends(get_db)):
    await owned_conversation(db, str(conversation_id), principal.subject)
    return {"recordings": voice.list_recordings(voice.configuration(), conversation_id)}


@router.get("/{conversation_id}/recordings/{recording_id}")
async def download_recording(conversation_id: UUID, recording_id: UUID, principal: Principal = Depends(current_principal), db: AsyncSession = Depends(get_db)):
    await owned_conversation(db, str(conversation_id), principal.subject)
    metadata, path = voice.load_recording(voice.configuration(), conversation_id, recording_id)
    return FileResponse(path, media_type=metadata["content_type"], filename=f"recording.{voice.MIME_EXTENSIONS[metadata['content_type']]}", headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


@router.delete("/{conversation_id}/recordings/{recording_id}", status_code=204)
async def remove_recording(conversation_id: UUID, recording_id: UUID, principal: Principal = Depends(current_principal), db: AsyncSession = Depends(get_db)):
    await owned_conversation(db, str(conversation_id), principal.subject)
    config = voice.configuration()
    voice.load_recording(config, conversation_id, recording_id)
    voice.delete_recording(config, conversation_id, recording_id)
    return Response(status_code=204)
