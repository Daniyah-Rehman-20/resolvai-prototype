# PayResolve AI — Build Notes

This is the short, interview-friendly explanation of how the prototype is being hardened. It intentionally stays practical rather than documenting every line of code.

## 1. What the project does
- PayResolve AI investigates synthetic payment failures across bank, gateway, merchant and order states.
- It gathers evidence, retrieves policy context, recommends a safe next action and creates human approval requests for sensitive simulated actions.
- It never moves real money. Refunds/reversals remain simulated.

## 2. Existing prototype
- Frontend: Next.js + TypeScript.
- Backend: FastAPI + Pydantic + SQLAlchemy.
- Local database: SQLite; PostgreSQL is the production target.
- AI workflow: deterministic investigation logic plus local policy retrieval.
- Infrastructure scaffolding: Redis, RabbitMQ, Celery and Qdrant in Docker Compose.

## 3. Production hardening — foundation
- Created a dedicated `production-hardening` branch so the working demo is not changed directly.
- Authentication is now required for protected payment APIs.
- Added role hierarchy: viewer -> analyst -> approver -> admin.
- Transaction/investigation reads require a viewer; starting investigations requires analyst; approval decisions require approver.
- Audit events use the authenticated demo user instead of a hard-coded reviewer.
- Approval decisions acquire database row locks before state changes, reducing double-approval races on PostgreSQL.
- Removed automatic `Base.metadata.create_all()` from API startup. Schema changes must go through Alembic.
- Hardened CORS/header configuration and disabled interactive API docs in production mode.
- Added basic security tests for missing authentication and insufficient roles.
- Connected the current frontend to the protected demo API through a temporary demo identity bridge.

## 4. Why these changes come first
- AI quality is not useful if an unauthorized caller can approve an action.
- Payment-like actions must be safe against retries and concurrent reviewers.
- Database migrations must be explicit and repeatable before deployment.
- Security and correctness form the base for RAG, LangGraph and distributed workers.

## 5. Important demo-vs-production distinction
- The current bearer token + demo role headers are only a portfolio/demo authentication bridge.
- Real deployment should use an identity provider/OIDC JWT validation; clients must never be allowed to choose their own role.
- SQLite is fine for local learning, but concurrency-sensitive deployment should use PostgreSQL.

## 6. Next engineering stages
- Complete Alembic schema migrations and PostgreSQL constraints.
- Add Redis idempotency and distributed rate limiting.
- Build real document ingestion with Celery/RabbitMQ.
- Replace lexical retrieval with BM25 + embeddings + Qdrant + RRF + reranking.
- Move investigation orchestration into a persistent LangGraph workflow with human interrupt/resume.
- Add structured logs, metrics, tracing and dependency-aware readiness checks.
- Expand unit, integration, concurrency and failure tests.
- Harden Docker/CI and add an Azure-ready deployment path.

## 7. Interview explanation
- Start simple: "The prototype proved the payment-investigation flow."
- Then: "I hardened authorization, database lifecycle and approval concurrency before increasing AI complexity."
- Then: "The next layer adds distributed idempotency/rate limiting, hybrid RAG, durable agent orchestration and async ingestion."
- Finish with: "Sensitive actions remain deterministic, auditable, human-approved and simulated."
