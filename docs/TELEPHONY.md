# Inbound phone support

This is a real provider adapter, disabled until configured. It implements one recorded customer message per inbound call, transcription, durable query intake, and spoken response polling. It is **not** a full-duplex realtime voice agent. No outbound calls are placed. A funded Twilio account, permitted inbound number, HTTPS backend, transcription credentials and running worker are required; no live provider call has been certified by the automated tests.

## Enable

Set backend environment variables:

```dotenv
TELEPHONY_ENABLED=true
TELEPHONY_ACCOUNT_SID=AC...your_account_sid...
TELEPHONY_AUTH_TOKEN=your_secret_from_secret_manager
TELEPHONY_PUBLIC_BASE_URL=https://api.your-domain.example
TELEPHONY_PHONE_NUMBER=+your_twilio_number
VOICE_TRANSCRIPTION_API_KEY=your_transcription_key
```

The public base URL is an HTTPS origin without a path, query or trailing slash. Configure the number's incoming voice webhook to `https://api.your-domain.example/telephony/inbound`, HTTP POST. Preserve request paths and form fields through your reverse proxy; do not rewrite callback URLs or add query parameters. Run `alembic upgrade head`, then run `python -m app.services.telephony_worker` as a separately supervised process with the same PostgreSQL URL, credentials and private voice storage volume as the API. The queue uses PostgreSQL row locks with `SKIP LOCKED`; SQLite tests validate persistence and sequential replay, not production concurrency.

The authenticated application requests `/telephony/connection-code` with `{"consent":true}`. A ten-digit, five-minute, single-use connection code links the inbound caller to that account; the stored code is HMAC hashed and never linked by spoofable caller ID. The caller enters the code, hears the recording/transcription notice and presses 1. Only then is `<Record>` issued. Keep this code private: possession authorizes a call to add a support query to that account.

## Flow and failure behavior

- `connect` consumes the code with a row lock; `consent` locks the call and creates exactly one owner-scoped conversation. Repeated consent does not issue another recording instruction.
- A recording is limited to 60 seconds, terminated with hash or five seconds of silence. Only a signed `completed` recording callback enqueues work; the earlier `action` callback is not proof the audio is ready.
- Provider callbacks use the configured HTTPS URL, every submitted form field, HMAC-SHA1, constant-time signature comparison and matching AccountSid. Query-bearing and duplicate-field callbacks are rejected. Recording downloads use a validated SID under the configured account, bounded bytes and no redirects; callback URLs cannot redirect the downloader.
- At most one recording job exists per call. Duplicate recording callbacks are idempotent. The signed callbacks have no timestamp-based freshness guarantee; single-use linkage, state and expiry provide replay protection for mutations.
- Live waiting stops two minutes after call linkage; callers can check the application later. Signed recording callbacks remain accepted for 15 minutes after linkage, including after the caller hangs up. Later callbacks fail closed. Operator recovery is required for callbacks arriving outside this window.
- The durable worker holds a PostgreSQL row lock until intake commits. Job completion and transcript/query persistence commit together. Crashes before commit leave work queued; processing errors mark the job failed without returning provider error details. A crash after intake commit but before the final response update leaves a generic saved-query response. Filesystem writes cannot be transactionally committed with PostgreSQL; abrupt worker death can leave orphan private files for retention cleanup.
- Phone records use the same ownership checks, redaction, recording access and retention as browser voice. Redaction applies to text, not original recorded audio. Enable Twilio media HTTP Basic Authentication in the provider console so recordings are not publicly retrievable by URL. Verify authenticated retrieval with the deployed account. The provider also holds a recording copy: configure and verify Twilio-side retention/deletion independently. Deleting an application recording does not delete Twilio's copy.

## Operational gates

Verify one live call including hangup-before-callback, no-consent hangup, invalid code, failed transcription, expired code and provider retries before enabling customer access. Verify the number's local regulatory eligibility, recording consent wording, transfer/storage requirements and provider retention with your operator/legal reviewers. Do not treat use of this adapter as compliance certification.

The API's shared IP limiter also covers webhook traffic. Twilio calls share provider IPs and the three-second polling requests can hit the limit under concurrent load. Current configuration is suitable only for low-volume validation; before scaling, implement an independently bounded signed-provider callback limiter and load test it (do not simply expose unauthenticated unlimited webhook endpoints). Deploy worker health/queue-age alerts, recording purge scheduling, PostgreSQL backups, TLS and secret rotation. No automatic bank settlement or refund follows a support call.

## Official provider references

Reviewed 2026-10-10:

- [Twilio request security and signature construction](https://www.twilio.com/docs/usage/security)
- [Record verb: action versus completed recording callback, timeouts and hangup](https://www.twilio.com/docs/voice/twiml/record)
- [Recording resource and provider-side deletion](https://www.twilio.com/docs/voice/api/recording)

Run `pytest tests/test_telephony.py` in the backend environment. These tests use a real temporary SQLite database and mock external transcription/audio calls; they do not place calls or spend provider credit.
