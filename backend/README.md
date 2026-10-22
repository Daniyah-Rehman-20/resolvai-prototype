# PayResolve AI API

FastAPI, SQLAlchemy and Alembic backend for persistent customer support intake, staff query review and consented voice/telephone intake. Real authentication and support persistence do not imply live payment verification: no bank connection or real refund is implemented.

Use the [root README](../README.md) for the PostgreSQL/Redis Compose stack and [operations runbook](../docs/OPERATIONS.md) for retention, backup, deployment and launch gaps.

## Local development

Python 3.12+ is required. From this directory:

```bash
python -m venv .venv
# Linux/macOS:
. .venv/bin/activate
# Windows PowerShell instead: .venv\Scripts\Activate.ps1
pip install -e '.[dev]'
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

This uses SQLite for local development. Run Redis locally, or keep `APP_ENV=development` for the limited in-process rate-limit fallback. Production requires Redis. Interactive API docs are at `/docs` in development and disabled in production.

Create customer accounts through `POST /auth/register` or the frontend `/support` page. Provision staff using `python -m scripts.create_staff analyst@example.com --role analyst`. Authentication uses persisted accounts and revocable sessions; staff roles are provisioned server-side. Synthetic payment fixtures and demo identity headers are not supported.

## Core contracts

| Endpoint | Purpose |
| --- | --- |
| `POST /auth/register`, `POST /auth/login` | Issue a database-backed bearer session |
| `GET /auth/me`, `POST /auth/logout` | Read identity / revoke session |
| `GET/POST /support/conversations` | List own conversations / create conversation |
| `GET /support/conversations/{id}` | Read own persisted messages and queries |
| `POST /support/conversations/{id}/messages` | Submit text, extract intake queries and reply |
| `POST /support/conversations/{id}/audio` | Transcribe consented recording and submit intake |
| `GET /support/queue`, `PATCH /support/queries/{id}` | Staff review, without financial action |
| `GET /health`, `GET /health/ready` | Liveness / database and Redis readiness |

See [voice details](../docs/VOICE.md) for recording list/download/delete APIs and provider configuration. Provider credentials stay server-side. Without optional AI credentials, text uses labeled guided intake; voice transcription requires configured provider credentials.

## Database compatibility

Historical payment-table metadata is isolated in `app/db/legacy_schema.py` for Alembic compatibility, preserving existing databases. They are not exposed by payment-investigation or financial-action APIs. Do not rewrite applied migrations or drop existing tables as part of this source cleanup. New installations do not seed payment records.

## Verification

```bash
ruff check app tests
pytest -q
```

CI separately migrates PostgreSQL and exercises the actual API application against PostgreSQL/Redis. Unit tests and mocked provider tests do not replace a real microphone/provider end-to-end test. See [implementation tasks](../docs/IMPLEMENTATION_PLAN.md) for work remaining before public launch.
