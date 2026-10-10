"""Consent-gated, signed inbound PSTN flow with durable transcription jobs."""
from datetime import datetime, timedelta, timezone
import secrets
from uuid import uuid4
from xml.etree.ElementTree import Element, SubElement, tostring
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import Principal, current_principal
from app.db.session import get_db
from app.models.support import SupportConversation
from app.models.telephony import PhoneLink, PhoneCall, PhoneRecording
from app.services import telephony as service

router = APIRouter(prefix='/telephony', tags=['telephony'])
def now(): return datetime.now(timezone.utc)
def utc(value): return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value

def xml(message=None, gather=None, record=False, poll=False):
    root = Element('Response')
    if message: SubElement(root, 'Say').text = message
    if gather:
        SubElement(root, 'Gather', input='dtmf', numDigits=str(gather[1]), timeout='15', action='/telephony/' + gather[0], method='POST')
        SubElement(root, 'Hangup')
    elif record:
        SubElement(root, 'Record', action='/telephony/recorded', method='POST', maxLength='60', finishOnKey='#', timeout='5', playBeep='true', recordingStatusCallback='/telephony/recording', recordingStatusCallbackMethod='POST', recordingStatusCallbackEvent='completed')
        SubElement(root, 'Hangup')
    elif poll:
        SubElement(root, 'Pause', length='3')
        SubElement(root, 'Redirect', method='POST').text = '/telephony/poll'
    else: SubElement(root, 'Hangup')
    return Response(tostring(root, encoding='unicode'), media_type='application/xml')

@router.get('/capabilities')
async def capabilities(principal: Principal = Depends(current_principal)):
    config = service.configuration()
    ready = service.configured(config)
    return {'configured': ready, 'phone_number': config.phone_number if ready else None}

class Consent(BaseModel):
    consent: bool = False

@router.post('/connection-code')
async def connection_code(body: Consent, principal: Principal = Depends(current_principal), db: AsyncSession = Depends(get_db)):
    config = service.require_config()
    if not body.consent: raise HTTPException(422, 'Acknowledge phone recording and transcription before requesting a code')
    await db.execute(update(PhoneLink).where(PhoneLink.owner_id == principal.subject).values(used=True))
    code = ''.join(str(secrets.randbelow(10)) for _ in range(10))
    expires = now() + timedelta(minutes=5)
    db.add(PhoneLink(code_hash=service.digest(code, config), owner_id=principal.subject, expires_at=expires))
    await db.commit()
    return {'code': code, 'expires_at': expires, 'phone_number': config.phone_number}

async def active_call(db, form):
    call = await db.scalar(select(PhoneCall).where(PhoneCall.call_sid == form['CallSid']).with_for_update())
    if not call or utc(call.expires_at) <= now(): raise HTTPException(403, 'Call is not linked or has expired')
    return call

@router.post('/inbound')
async def inbound(form=Depends(service.verified_form)):
    return xml('Welcome to PayResolve. Enter your ten digit connection code from the signed in application. Do not share bank credentials.', gather=('connect', 10))

@router.post('/connect')
async def connect(form=Depends(service.verified_form), db: AsyncSession = Depends(get_db)):
    config = service.require_config()
    link = await db.scalar(select(PhoneLink).where(PhoneLink.code_hash == service.digest(form.get('Digits', ''), config)).with_for_update())
    if not link or link.used or utc(link.expires_at) <= now():
        return xml('Invalid or expired code. Request a new code in the application and call again.')
    if await db.get(PhoneCall, form['CallSid']): return xml('This call is already linked. Please call again with a new code.')
    link.used = True
    db.add(PhoneCall(call_sid=form['CallSid'], owner_id=link.owner_id, expires_at=now()+timedelta(minutes=15)))
    await db.commit()
    return xml('This AI support service records your messages and sends audio for transcription. Recordings are saved privately with limited retention. Never state an OTP, PIN, password, or full payment details. Press 1 to consent, or hang up and use chat.', gather=('consent', 1))

@router.post('/consent')
async def consent(form=Depends(service.verified_form), db: AsyncSession = Depends(get_db)):
    call = await active_call(db, form)
    if form.get('Digits') != '1': return xml('Recording was not enabled. Please use chat.')
    if call.conversation_id:
        return xml('This recording turn has already started. Review your query in the application.')
    if not call.conversation_id:
        conversation = SupportConversation(id=str(uuid4()), owner_id=call.owner_id, channel='voice', recording_consent=True, consent_at=now())
        db.add(conversation)
        await db.flush()
        call.conversation_id = conversation.id
        await db.commit()
    return xml('After the beep, explain your transaction issue. Press hash when finished. Hang up at any time.', record=True)

@router.post('/recorded')
async def recorded(form=Depends(service.verified_form), db: AsyncSession = Depends(get_db)):
    call = await active_call(db, form)
    if not call.conversation_id: raise HTTPException(403, 'Recording consent required')
    return xml('Thank you. Please wait while your message is processed.', poll=True)

@router.post('/recording', status_code=204)
async def recording(form=Depends(service.verified_form), db: AsyncSession = Depends(get_db)):
    call = await active_call(db, form)
    if not call.conversation_id: raise HTTPException(403, 'Recording consent required')
    sid = form.get('RecordingSid', '')
    expected = service.recording_url(service.require_config(), sid)
    if form.get('RecordingStatus') != 'completed' or form.get('RecordingUrl') not in {expected, expected+'.wav'}:
        raise HTTPException(422, 'Invalid recording callback')
    existing = await db.scalar(select(PhoneRecording).where(PhoneRecording.call_sid == call.call_sid))
    if existing and existing.recording_sid != sid:
        raise HTTPException(409, 'Only one recording is allowed per call')
    existing = await db.get(PhoneRecording, sid)
    if existing:
        if existing.call_sid != call.call_sid: raise HTTPException(403, 'Recording mismatch')
        return Response(status_code=204)
    db.add(PhoneRecording(recording_sid=sid, call_sid=call.call_sid))
    try: await db.commit()
    except IntegrityError:
        await db.rollback()
        existing = await db.get(PhoneRecording, sid)
        if not existing or existing.call_sid != form['CallSid']:
            raise HTTPException(409, 'Recording identity conflict')
    return Response(status_code=204)

@router.post('/poll')
async def poll(form=Depends(service.verified_form), db: AsyncSession = Depends(get_db)):
    call = await active_call(db, form)
    job = await db.scalar(select(PhoneRecording).where(PhoneRecording.call_sid == call.call_sid).order_by(PhoneRecording.created_at.desc()).limit(1))
    if not job or job.status == 'queued':
        if now() >= utc(call.created_at) + timedelta(minutes=2):
            return xml('Processing is taking longer than expected. Please check your transcript and queries in the application. Goodbye.')
        return xml(poll=True)
    if job.status == 'done':
        # Completed one phone turn; new turns use a fresh code/call. Avoid replaying old answers.
        return xml((job.response or 'Your query was saved. Review it in the application.') + ' Your transcript and queries are available in the application. Thank you.')
    return xml('We could not process the audio. Please use chat or call again. No resolution has been confirmed.')
