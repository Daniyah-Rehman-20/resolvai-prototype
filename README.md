# PayResolve AI

A payment-failure support application with a Next.js frontend, FastAPI API and PostgreSQL persistence. Customers can register, discuss failed transactions, record a browser voice message with consent, and review the queries captured from their conversation. Staff access is separately provisioned.

This change implements an application foundation, not a claim of production certification or live bank connectivity. Browser voice is **record → transcribe → reply**. An optional Twilio adapter supports incoming telephone recording turns after number/credentials/TLS configuration; neither channel implements full-duplex real-time calls. The application captures customer-provided concerns and provides guidance; it cannot verify a bank balance, confirm settlement or issue a refund.

## Start the full application

Prerequisites: Docker Engine and Docker Compose v2.20+.

```bash
cp .env.example .env
# Edit .env: replace POSTGRES_PASSWORD with a random URL-safe password.
# Optional: set SUPPORT_AI_API_KEY and VOICE_TRANSCRIPTION_API_KEY.
docker compose up --build -d
```

Open **http://localhost:3000/support**, register a customer account, and start a chat. Without an AI key, intake uses an explicitly identified deterministic response; without a transcription key, transcription reports unavailable. No provider response or transcript is fabricated. AI and transcription calls can incur provider charges.

The stack binds browser/API ports to loopback only. PostgreSQL and Redis have no host-exposed ports. Migrations run before the API starts; a database is created without demo accounts or payment fixtures. PostgreSQL records and private recordings use named volumes and survive ordinary container restarts. Do not use `docker compose down -v` unless you intend to erase those volumes.

Create a staff account interactively:

```bash
docker compose exec api python -m scripts.create_staff analyst@example.com --role analyst
```

The command prompts for a password. Available staff roles: `viewer`, `analyst`, `approver`, `admin`. Customer signup never selects a staff role.

## Implemented scope

| Area | Behavior |
| --- | --- |
| Identity | Database-backed users, password hashing, expiring/revocable bearer sessions, server-side roles and interactive staff provisioning |
| Customer chat | Owner-scoped persisted conversations, messages and extracted queries; user statements are unverified claims |
| Voice | Explicit recording consent, private audio storage, bounded upload, provider transcription and support intake |
| Guidance | Payment-policy guidance and optional AI replies; no automatic money movement |
| Deployment | PostgreSQL/Redis Compose stack, database migrations, health checks, persistent volumes, non-root containers and CI |
| Staff review | Authenticated query queue and status updates, without financial actions |

For optional telephone calls, follow [telephone setup](docs/TELEPHONY.md) and the worker instructions in [operations](docs/OPERATIONS.md). Live call testing requires your provider account.

See [build validation](docs/BUILD_VALIDATION.md) for executed checks and unverified deployment/provider boundaries. No payment-execution endpoint is provided.

See [implementation tasks](docs/IMPLEMENTATION_PLAN.md), [operations](docs/OPERATIONS.md), and the policy research documents in `docs/` for scope and launch gates.

## Develop without Docker

Use Node.js 22 and Python 3.12+. Start Redis locally for the production-style limiter, or use `APP_ENV=development` for the bounded in-process fallback.

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

In another terminal at the repository root:

```bash
npm ci
npm run dev
```

`backend/.env.example` uses SQLite for convenient local work only; Compose uses PostgreSQL. Set `NEXT_PUBLIC_API_URL` in the root `.env` if your API is not at `http://localhost:8000`. Never place provider credentials in `NEXT_PUBLIC_*` variables.

```bash
npm run lint
npm run typecheck
npm run build
cd backend
ruff check app tests
pytest -q
```

## Repository scope

The prototype payment dashboard, synthetic transaction seed, demo identity bridge, simulated investigations/refunds, and obsolete screenshots have been removed. Customer support, policy references, consented voice intake and optional incoming telephone recording remain. Historical database tables and migrations are retained for existing database compatibility; this cleanup does not drop data or rewrite applied migrations.

## Before public launch

Supply provider credentials and a TLS domain, configure recording retention, test backups and recovery, verify account recovery/email verification/MFA needs, complete privacy and payment-policy review, and integrate a contracted bank/payment gateway with authenticated signed events. Genuine transaction data must come from an authorized provider or consented account integration, never a scraped database. See the operations guide for the full checklist and the distinction between persisted customer intake and verified payment status.
