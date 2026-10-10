# Customer support implementation validation

Validated 2026-10-10. This records executed checks, not production certification.

## Passed

- Backend: 34 pytest tests, including account/session lifecycle, server-side roles, cross-customer isolation, consent, private recordings, provider failure behavior, signed phone callbacks, replay protection, durable phone jobs and blocked production payment execution.
- Backend Ruff checks.
- Frontend TypeScript, ESLint and optimized Next.js build (14 routes).
- Fresh SQLite migrations through `0004_telephony`; Alembic metadata check reports no drift.
- Full ASGI application against a migrated SQLite database: register two accounts, create conversation, save chat, extract two concerns, retrieve persisted history, reject other customer's access, reject customer staff-queue access, show disabled unconfigured phone capability, and revoke session on logout. Authentication and database dependencies were real, not overridden.
- Docker/CI YAML syntax was checked. CI includes a PostgreSQL/Redis integration job.

## Not verified here

- PostgreSQL/Redis containers and production concurrency: Docker/PostgreSQL were unavailable in this workspace. The CI job is configured but has not been run remotely.
- Browser visual/microphone behavior: Playwright's browser download failed with truncated archives. Static build and source review do not replace device/browser testing.
- Real AI/transcription and Twilio calls: external credentials and an inbound number are absent. Provider calls are mocked in automated tests. Phone mode is one recorded turn per call, not full-duplex conversation.
- Live gateway/bank data, financial execution, public hosting, TLS, email recovery/verification and staff MFA remain launch work. Production approvals explicitly fail rather than claiming execution without a provider.

One pre-existing `datetime.utcnow()` deprecation warning remains in the legacy audit model. See IMPLEMENTATION_PLAN.md and OPERATIONS.md for the remaining launch tasks. Text redaction is heuristic; original audio is not redacted. Apply retention and privacy controls to both application and provider copies.
