# Operations runbook

## Deployment status and boundaries

The supplied Compose stack is a single-host baseline for testing and a controlled pilot after review. It has not been deployed to a public cloud, certified, or connected to a bank. `/support` persists real customer-provided intake; it does not establish a transaction's bank status. No refund or complaint is submitted to an external institution.

Voice is browser **record, upload, transcribe, reply**. An optional Twilio adapter adds incoming telephone recording turns. Continuous audio streaming, interruption handling and human call transfer remain separate integration tasks. Query extraction is conservative rule-based intake and can miss or combine questions; staff must review it.

## Start and verify

Follow the root README and set a random URL-safe `POSTGRES_PASSWORD` in the root `.env`. Keep `.env` out of source control. Run from the repository root:

```bash
docker compose config --quiet
docker compose up --build -d
docker compose ps
curl --fail http://localhost:8000/health/ready
```

`/health` is process liveness. `/health/ready` requires PostgreSQL and Redis. Readiness does not test provider credentials, schema compatibility, or recording storage. Production API requests fail with 503 if Redis rate limiting is unavailable.

The API image runs `alembic upgrade head` before startup. For multiple replicas, run migration as a single release job, then start API workers; do not let workers race schema changes. Provision staff with the interactive command in README. Registration always creates customers. Verify with two accounts that each sees only their conversations, staff queue returns 403 for customers, and logout invalidates the session.

## Configuration and provider verification

`NEXT_PUBLIC_API_URL` is a browser-facing URL embedded at frontend build time. Changing it requires rebuilding `web`. `CORS_ORIGINS` must match the frontend origin, including scheme and port. Never expose API keys through `NEXT_PUBLIC_*` variables.

`SUPPORT_AI_API_KEY`, `SUPPORT_AI_BASE_URL`, `SUPPORT_AI_MODEL` configure optional replies. `VOICE_TRANSCRIPTION_API_KEY`, `VOICE_TRANSCRIPTION_BASE_URL`, `VOICE_TRANSCRIPTION_MODEL` configure transcription. Provider endpoints must use HTTPS. Configure keys through a server-side secret manager for a hosted deployment. Do not paste keys into chat, tickets or logs.

Without an AI key, saved chat receives a labeled `guided_intake` response. Without a voice key, upload returns 503 and chat remains available. Test paid providers with a short nonsensitive recording, verify real transcript and persisted query output, then delete the recording. Provider outage, invalid credentials and silence must show errors, never simulated transcripts.

For local Python development, provider services load configuration from the backend working directory where supported; explicitly exporting `VOICE_*` variables also works. Compose passes provider variables directly. The examples use PostgreSQL for deployment and SQLite only for local development. A real database does not supply real bank transaction records: an authorized bank/gateway integration is still required.

## Private recordings and retention

Recordings and metadata live in the private `recordings` volume (`VOICE_STORAGE_DIR=/app/recordings`). Never mount it into the public frontend or static file server. The owner-authenticated recording API provides list, download and delete operations; see [VOICE.md](VOICE.md). Keep the underlying volume encrypted and access-controlled; Unix permissions do not encrypt files.

Compose uses `VOICE_RETENTION_DAYS=7` and `VOICE_MAX_UPLOAD_BYTES=10485760` by default. Set overrides in `.env` before startup. Existing recording expiration timestamps do not change when the configured retention period changes. Expiry is checked on access, but automatic deletion requires a scheduled command. Run hourly from a host scheduler, with the repository as working directory:

```bash
docker compose exec -T api python -m app.services.voice
```

Example crontab, replacing the checkout path and ensuring the job account can access Docker:

```cron
17 * * * * cd /srv/payresolve && docker compose exec -T api python -m app.services.voice >> /var/log/payresolve-retention.log 2>&1
```

Alert on command failure and unexpected disk growth. The command removes expired recordings and interrupted-write orphan audio; monitor malformed metadata separately. Deleting audio does not delete saved transcripts, messages or queries. Conversation/account deletion, exports, transcript retention and expired-session cleanup require additional lifecycle work before public launch. Backups and provider-held copies require their own retention policy. Multiple API replicas require a shared private volume or an object-storage implementation with durable metadata.

## Backup and restore

Set retention and encryption for backups outside the application host. A PostgreSQL snapshot and a recordings-volume snapshot must be coordinated; pause writes for a consistent combined backup. Do not include real customer data in CI or development fixtures.

Create a database archive with restrictive local permissions:

```bash
umask 077
docker compose exec -T postgres pg_dump -U payresolve -d payresolve -Fc > payresolve.dump
```

Restore into an **isolated test database**, never overwrite the live database during a drill:

```bash
docker compose exec -T postgres createdb -U payresolve payresolve_restore
docker compose exec -T postgres pg_restore -U payresolve -d payresolve_restore --exit-on-error < payresolve.dump
```

Confirm schema version and sample row counts, start an isolated API against the restored database and copied recordings volume, then verify owner access and retention. Record recovery time and acceptable data loss. Production backup scheduling and recovery targets are operator responsibilities. `docker compose down -v` destroys named volumes; normal `down` or restart does not.

## Release and rollback

Run frontend lint/typecheck/build and backend tests before release. CI additionally starts PostgreSQL and Redis, migrates an empty PostgreSQL database, verifies metadata drift, and exercises registration, persisted chat and owner isolation through the real API application. Unit tests use isolated SQLite fixtures; provider tests use mocks and do not prove real speech-provider or microphone compatibility. CI configuration is not evidence that a hosted run passed.

Record the deployed commit/image identifiers and take a tested backup before schema changes. Deploy only one migration runner. If startup fails, inspect migration and readiness errors without dumping secrets. Roll back application images only when the previous version supports the current schema. Otherwise use an assessed forward fix or restore the pre-release database and recording snapshot together. Do not blindly run Alembic downgrade on customer data.

## Public launch work still required

- Terminate TLS at a reverse proxy; configure trusted forwarded-client addresses so IP rate limits remain meaningful and client-spoofed headers are rejected. Microphone capture needs HTTPS outside localhost.
- Enforce ingress request-body and timeout limits before multipart parsing. Preserve authorization headers and set appropriate frontend microphone policy; do not copy the API's microphone-denial header onto the frontend.
- Add email verification, secure recovery, staff MFA and lifecycle administration. Review browser bearer-token storage and XSS protections.
- Establish notices, consent evidence, deletion/export workflows, provider processing agreements and region-specific policy review. Do not request OTPs, PINs, passwords, CVV or full card numbers. Text redaction is heuristic; raw audio can retain sensitive speech.
- Add PII-safe observability, alerts for database/Redis/provider failures, queue workload ownership, scheduled retention, dependency/image scanning, restore drills and load testing. Pin reviewed dependencies and images for reproducible releases.
- Integrate an authorized payment provider with signed events, idempotency, reconciliation and ownership checks. Keep financial actions behind reviewed staff workflows; support resolution is not settlement confirmation.
- For telephone calling, provision the Twilio number and credentials, verify signed callbacks and actual calls, validate recording/AI consent and disconnect handling, and complete telecom/privacy review. Streaming and human transfer remain unimplemented.

The legacy `render.yaml` is not a complete launch recipe: its ephemeral service storage cannot safely retain recordings. Use an approved persistent private disk and retention scheduler before enabling voice there, and verify the provider's current service plans separately.
