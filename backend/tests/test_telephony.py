from datetime import datetime, timedelta, timezone
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.api.routes.telephony import router
from app.core.security import Principal, current_principal
from app.db.base import Base
from app.db.session import get_db
from app.models.telephony import PhoneCall, PhoneRecording
from app.models.support import SupportConversation, SupportMessage
from app.services import telephony, voice
from app.services.telephony_worker import process_one

ACCOUNT = 'AC' + 'a' * 32
CALL = 'CA' + 'b' * 32
RECORDING = 'RE' + 'c' * 32

@pytest.fixture
async def phone(monkeypatch, tmp_path):
    config = telephony.TelephonySettings(enabled=True, account_sid=ACCOUNT, auth_token='test', public_base_url='https://phone.example', phone_number='+15555550123')
    monkeypatch.setattr(telephony, 'configuration', lambda: config)
    monkeypatch.setattr(voice, 'configuration', lambda: voice.VoiceSettings(storage_dir=tmp_path, transcription_api_key='test'))
    monkeypatch.delenv('SUPPORT_AI_API_KEY', raising=False)
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    app = FastAPI()
    app.include_router(router)
    async def db():
        async with sessions() as session: yield session
    app.dependency_overrides[get_db] = db
    app.dependency_overrides[current_principal] = lambda: Principal('alice', 'customer')
    async with AsyncClient(transport=ASGITransport(app=app), base_url='https://phone.example') as client:
        yield client, sessions, config
    await engine.dispose()

async def hook(client, config, path, **values):
    form = {'AccountSid': ACCOUNT, 'CallSid': CALL, **values}
    sig = telephony.signature(config.public_base_url + '/telephony/' + path, form.items(), 'test')
    return await client.post('/telephony/' + path, data=form, headers={'X-Twilio-Signature': sig})

async def link(client, config):
    code = (await client.post('/telephony/connection-code', json={'consent': True})).json()['code']
    assert 'Press 1' in (await hook(client, config, 'connect', Digits=code)).text
    return code

async def test_signature_and_consent_and_replay(phone):
    client, sessions, config = phone
    assert (await client.post('/telephony/inbound', data={'CallSid': CALL})).status_code == 403
    assert (await client.post('/telephony/connection-code', json={'consent': False})).status_code == 422
    code = await link(client, config)
    assert 'Invalid or expired' in (await hook(client, config, 'connect', Digits=code, CallSid='CA'+'d'*32)).text
    callback = dict(RecordingSid=RECORDING, RecordingStatus='completed', RecordingUrl=telephony.recording_url(config, RECORDING))
    assert (await hook(client, config, 'recording', **callback)).status_code == 403
    assert '<Record ' in (await hook(client, config, 'consent', Digits='1')).text
    assert '<Record ' not in (await hook(client, config, 'consent', Digits='1')).text
    assert (await hook(client, config, 'recording', **callback)).status_code == 204
    assert (await hook(client, config, 'recording', **callback)).status_code == 204
    async with sessions() as db:
        assert await db.scalar(select(func.count()).select_from(PhoneRecording)) == 1
        assert await db.scalar(select(func.count()).select_from(SupportConversation)) == 1
        call = await db.get(PhoneCall, CALL)
        conversation = await db.get(SupportConversation, call.conversation_id)
        assert conversation.owner_id == 'alice' and conversation.recording_consent
    assert (await hook(client, config, 'recording', **{**callback, 'RecordingUrl': 'https://evil.example/audio'})).status_code == 422
    other = 'RE'+'d'*32
    assert (await hook(client, config, 'recording', **{**callback, 'RecordingSid': other, 'RecordingUrl': telephony.recording_url(config, other)})).status_code == 409

async def test_worker_persists_once_and_poll_timeout(phone, monkeypatch):
    client, sessions, config = phone
    await link(client, config)
    await hook(client, config, 'consent', Digits='1')
    async with sessions() as db:
        call = await db.get(PhoneCall, CALL)
        call.created_at = datetime.now(timezone.utc) - timedelta(minutes=3)
        await db.commit()
    assert '<Hangup' in (await hook(client, config, 'poll')).text
    # Callback still accepted after live-call waiting has timed out.
    await hook(client, config, 'recording', RecordingSid=RECORDING, RecordingStatus='completed', RecordingUrl=telephony.recording_url(config, RECORDING))
    async def download(*args): return b'RIFF0000WAVEaudio'
    async def transcribe(*args): return 'My UPI payment failed. PIN 9876'
    monkeypatch.setattr(telephony, 'download_recording', download)
    monkeypatch.setattr(voice, 'transcribe', transcribe)
    async with sessions() as db:
        assert await process_one(db)
        assert not await process_one(db)
        assert (await db.get(PhoneRecording, RECORDING)).status == 'done'
        messages = list((await db.scalars(select(SupportMessage))).all())
        assert len(messages) == 2 and all('9876' not in m.content for m in messages)
        call = await db.get(PhoneCall, CALL)
        assert len(voice.list_recordings(voice.configuration(), call.conversation_id)) == 1
    assert '<Hangup' in (await hook(client, config, 'poll')).text

async def test_worker_failure_is_durable(phone, monkeypatch):
    client, sessions, config = phone
    await link(client, config)
    await hook(client, config, 'consent', Digits='1')
    await hook(client, config, 'recording', RecordingSid=RECORDING, RecordingStatus='completed', RecordingUrl=telephony.recording_url(config, RECORDING))
    async def failure(*args): raise RuntimeError('private provider error')
    monkeypatch.setattr(telephony, 'download_recording', failure)
    async with sessions() as db:
        assert await process_one(db)
        assert (await db.get(PhoneRecording, RECORDING)).status == 'failed'
        assert await db.scalar(select(func.count()).select_from(SupportMessage)) == 0
    assert 'private provider' not in (await hook(client, config, 'poll')).text

async def test_tampered_signed_payload_rejected(phone):
    client, _, config = phone
    form = {'AccountSid': ACCOUNT, 'CallSid': CALL, 'Digits': '1111111111'}
    signature = telephony.signature(config.public_base_url + '/telephony/connect', form.items(), 'test')
    form['Digits'] = '2222222222'
    response = await client.post('/telephony/connect', data=form, headers={'X-Twilio-Signature': signature})
    assert response.status_code == 403

async def test_expired_call_rejects_provider_replay(phone):
    client, sessions, config = phone
    await link(client, config)
    await hook(client, config, 'consent', Digits='1')
    async with sessions() as db:
        call = await db.get(PhoneCall, CALL)
        call.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        await db.commit()
    assert (await hook(client, config, 'recording', RecordingSid=RECORDING,
        RecordingStatus='completed', RecordingUrl=telephony.recording_url(config, RECORDING))).status_code == 403
