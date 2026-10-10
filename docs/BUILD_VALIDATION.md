# Customer support implementation validation

Validated 2026-10-10. This records executed checks, not production certification.

## Passed

- Backend: 38 pytest tests, including account/session lifecycle, server-side roles, cross-customer isolation, consent, private recordings, provider failure behavior, signed phone callbacks, replay protection, durable phone jobs and rejection of removed demo/payment endpoints.
- Backend Ruff checks.
- Frontend TypeScript, ESLint and optimized Next.js build (only home, support, not-found and icon routes).
- Fresh SQLite migrations through `0004_telephony`; Alembic metadata check reports no drift.
- Full ASGI application against a migrated SQLite database: register two accounts, create conversation, save chat, extract two concerns, retrieve persisted history, reject other customer's access, reject customer staff-queue access, show disabled unconfigured phone capability, and revoke session on logout. Authentication and database dependencies were real, not overridden.
- Docker/CI YAML syntax was checked. CI includes a PostgreSQL/Redis integration job.

## Not verified here

- PostgreSQL/Redis containers are unavailable locally. GitHub CI passed for the preceding support implementation, including its PostgreSQL/Redis integration job. The cleanup is checked again by the PR pipeline before merge; consult the GitHub check results for that commit. Production load and concurrency remain unverified.
- Browser visual/microphone behavior: Playwright's browser download failed with truncated archives. Static build and source review do not replace device/browser testing.
- Real AI/transcription and Twilio calls: external credentials and an inbound number are absent. Provider calls are mocked in automated tests. Phone mode is one recorded turn per call, not full-duplex conversation.
- Live gateway/bank data, financial execution, public hosting, TLS, email recovery/verification and staff MFA remain launch work. Payment execution endpoints have been removed; the application does not claim to execute financial actions.

See IMPLEMENTATION_PLAN.md and OPERATIONS.md for the remaining launch tasks. Text redaction is heuristic; original audio is not redacted. Apply retention and privacy controls to both application and provider copies.

## Demo-code cleanup

Removed synthetic dashboards, sample payment data, simulated refund/investigation APIs, the shared demo-token login path, obsolete agent/RAG/worker scaffolding, screenshots and evaluation fixtures. Historical payment table definitions are isolated in `app/db/legacy_schema.py` and loaded only by Alembic to preserve schema compatibility; no stored tables are dropped. Real support audit records remain in the application.
