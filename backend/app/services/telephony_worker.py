"""Run separately: python -m app.services.telephony_worker. PostgreSQL durable queue."""
import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.telephony import PhoneRecording, PhoneCall
from app.models.support import SupportConversation
from app.services import telephony, voice
from app.services.support import intake_message

async def process_one(db):
    job = await db.scalar(select(PhoneRecording).where(PhoneRecording.status == 'queued').order_by(PhoneRecording.created_at).with_for_update(skip_locked=True).limit(1))
    if not job: return False
    job_id = job.recording_sid
    metadata = None
    config = voice.configuration()
    call = await db.get(PhoneCall, job.call_sid)
    conversation = await db.get(SupportConversation, call.conversation_id) if call and call.conversation_id else None
    if not conversation or not conversation.recording_consent or conversation.owner_id != call.owner_id:
        job.status = 'failed'
        await db.commit()
        return True
    conversation_id = conversation.id
    try:
        data = await telephony.download_recording(telephony.require_config(), job.recording_sid)
        transcript = await voice.transcribe(data, 'audio/wav', config)
        metadata = voice.save_recording(config, conversation.id, data, 'audio/wav')
        # intake_message commits these changes and messages atomically. A crash after
        # commit cannot create duplicate queries on queue retry.
        job.status = 'done'
        job.response = 'Your query was saved. Review the response in the application.'
        result = await intake_message(db, conversation, transcript)
        job.response = result['message']['content']
        await db.commit()
    except Exception:
        await db.rollback()
        persisted = await db.get(PhoneRecording, job_id)
        if persisted and persisted.status != 'done':
            if metadata: voice.delete_recording(config, conversation_id, metadata['id'])
            persisted.status = 'failed'
            await db.commit()
    return True

async def main():
    telephony.require_config()
    while True:
        async with SessionLocal() as db:
            worked = await process_one(db)
        if not worked: await asyncio.sleep(2)

if __name__ == '__main__': asyncio.run(main())
