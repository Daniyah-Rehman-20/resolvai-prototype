"""Twilio security boundary and bounded provider recording retrieval."""
import base64
import hashlib
import hmac
import re
from urllib.parse import urlsplit
import httpx
from fastapi import HTTPException, Request
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.services import voice

class TelephonySettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_prefix='TELEPHONY_', extra='ignore')
    enabled: bool = False
    account_sid: str = ''
    auth_token: SecretStr = SecretStr('')
    public_base_url: str = ''
    phone_number: str = ''

def configuration():
    return TelephonySettings()

def configured(config):
    url = urlsplit(config.public_base_url)
    return bool(config.enabled and re.fullmatch(r'AC[0-9a-fA-F]{32}', config.account_sid)
        and config.auth_token.get_secret_value() and url.scheme == 'https' and url.netloc
        and not url.username and not url.query and not url.fragment and not url.path
        and config.phone_number and voice.configuration().transcription_api_key.get_secret_value())

def require_config():
    config = configuration()
    if not configured(config):
        raise HTTPException(503, 'Phone support is not configured; please use chat')
    return config

def digest(code, config):
    return hmac.new(config.auth_token.get_secret_value().encode(), code.encode(), hashlib.sha256).hexdigest()

def signature(url, pairs, token):
    values = {}
    for key, value in pairs:
        values.setdefault(key, set()).add(value)
    payload = url + ''.join(key + value for key in sorted(values) for value in sorted(values[key]))
    return base64.b64encode(hmac.new(token.encode(), payload.encode(), hashlib.sha1).digest()).decode()

async def verified_form(request: Request):
    config = require_config()
    if request.url.query or request.headers.get('content-type', '').split(';')[0] != 'application/x-www-form-urlencoded':
        raise HTTPException(403, 'Invalid provider request')
    data = await request.body()
    if len(data) > 16384:
        raise HTTPException(413, 'Provider request too large')
    form = await request.form()
    pairs = list(form.multi_items())
    if any(not isinstance(value, str) for _, value in pairs):
        raise HTTPException(403, 'Invalid provider request')
    expected = signature(config.public_base_url + request.url.path, pairs, config.auth_token.get_secret_value())
    if not hmac.compare_digest(expected, request.headers.get('X-Twilio-Signature', '')) or form.get('AccountSid') != config.account_sid:
        raise HTTPException(403, 'Invalid provider signature')
    if len(pairs) != len(dict(pairs)) or not re.fullmatch(r'CA[0-9a-fA-F]{32}', form.get('CallSid', '')):
        raise HTTPException(403, 'Invalid provider request')
    return dict(pairs)

def recording_url(config, sid):
    if not re.fullmatch(r'RE[0-9a-fA-F]{32}', sid):
        raise HTTPException(422, 'Invalid recording identifier')
    return f'https://api.twilio.com/2010-04-01/Accounts/{config.account_sid}/Recordings/{sid}'

async def download_recording(config, sid):
    # Construct from validated identifiers; NEVER follow a webhook-provided URL.
    url = recording_url(config, sid) + '.wav'
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
            async with client.stream('GET', url, auth=(config.account_sid, config.auth_token.get_secret_value())) as response:
                response.raise_for_status()
                chunks, size = [], 0
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > voice.configuration().max_upload_bytes:
                        raise HTTPException(413, 'Recording exceeds limit')
                    chunks.append(chunk)
        data = b''.join(chunks)
        if not data.startswith(b'RIFF') or data[8:12] != b'WAVE':
            raise HTTPException(415, 'Invalid recording audio')
        return data
    except httpx.HTTPError as exc:
        raise HTTPException(502, 'Recording provider unavailable') from exc
