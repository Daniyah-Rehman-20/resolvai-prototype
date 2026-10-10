# Browser voice support

This implementation records turn-based browser conversations: accept consent, record
a question, upload it, receive a real transcript and persisted support reply, and
optionally hear the reply using browser speech synthesis. It is not a telephone/PSTN
service, full-duplex realtime call, or verified bank integration.

## Configuration

| Variable | Default |
| --- | --- |
| `VOICE_TRANSCRIPTION_API_KEY` | Unset; server-only provider credential |
| `VOICE_TRANSCRIPTION_BASE_URL` | `https://api.openai.com/v1` (HTTPS required) |
| `VOICE_TRANSCRIPTION_MODEL` | `gpt-4o-mini-transcribe` |
| `VOICE_STORAGE_DIR` | `./data/private-recordings` |
| `VOICE_MAX_UPLOAD_BYTES` | 10485760 (10 MiB; maximum 24 MiB) |
| `VOICE_RETENTION_DAYS` | 7 (range 1–90) |

Missing credentials return 503; provider failure returns sanitized errors. There is
no canned transcript fallback. Implementation follows the official [transcription
API](https://developers.openai.com/api/reference/resources/audio/subresources/transcriptions/methods/create)
and [speech-to-text guide](https://developers.openai.com/api/docs/guides/speech-to-text)
(checked 2026-10-09).

## Authenticated API

Create a conversation with `channel: "voice"` and `recording_consent: true`.
All requests require the user's bearer token:

- `POST /support/conversations/{id}/audio`: multipart `file` and `consent=true`.
- `GET /support/conversations/{id}/recordings`: retained metadata.
- `GET /support/conversations/{id}/recordings/{recording_id}`: download audio.
- `DELETE /support/conversations/{id}/recordings/{recording_id}`: erase audio.

Uploads return `transcript`, `recording`, and the standard support intake response
(`conversation_id`, `message`, `queries`). Ownership is checked before provider calls
or recording access. Consent must exist on the conversation and accompany each upload.
Failed transcription stores no recording; a failed support turn removes its recording.
Audio deletion does not erase already saved messages/queries; apply a separate
conversation data retention policy.

## Operations and privacy

Storage uses server-generated UUIDs, private directories (0700), files (0600), and
metadata sidecars. Never serve this directory as static assets. Downloads expire and
use `Cache-Control: private, no-store`. Schedule `python -m app.services.voice` hourly
with the same environment/volume to erase expired files and interrupted-write orphan
audio. The command must be scheduled by the operator; expiry is also enforced on access.
Use an encrypted persistent volume and restrict backups; file permissions are not
encryption. Configure backup and transcription-provider retention separately.

Multiple replicas require private object storage with database metadata or a suitable
shared private volume. Configure ingress body limits to bound uploads before multipart
parsing/spooling, rate limits, and client recording duration limits. The application
also checks MIME types and upload size while reading the file.

Before microphone capture, disclose recording, automated transcription, external AI
processing, purpose, retention, and deletion controls. Do not request PINs, OTPs,
passwords, full card numbers, or CVV. Raw audio may contain sensitive information that
text redaction cannot remove. Microphone access requires HTTPS except on localhost.
Browser speech synthesis may use OS/browser services; review that privacy behavior.

An optional Twilio adapter adds inbound telephone recording turns; see OPERATIONS.md.
It still requires a separately provisioned number, credentials, a public TLS callback
endpoint, a running recording worker, live call testing and applicable telecom/privacy
review. Full-duplex streaming and human transfer remain future work. This implementation creates no public phone number,
provider account, legal approval, or bank credentials.
