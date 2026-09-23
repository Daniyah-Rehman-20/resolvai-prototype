# PayResolve AI Backend

FastAPI backend for the synthetic **Agentic Payment Investigation & Resolution Platform**. It never transfers real funds and never requests CVV/PIN/UPI PIN. Refunds/reversals are simulated and sensitive actions are approval-gated.

## Architecture
Frontend → FastAPI → SQLAlchemy/Postgres → investigation workflow → local policy retrieval (Qdrant-ready) → deterministic risk gate → human approval → mock action → audit. RabbitMQ/Celery, Redis, Qdrant, Prometheus/Langfuse are optional infrastructure adapters; core local development works without paid credentials.

## Run locally
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
python -m app.db.seed
uvicorn app.main:app --reload
```
Swagger: http://localhost:8000/docs · ReDoc: http://localhost:8000/redoc · Health: http://localhost:8000/health

## Docker
```bash
cp .env.example .env
docker compose up -d --build
docker compose exec api python -m app.db.seed
```

## Demo journeys
1. `POST /investigations` with `TXN-10021`: bank DEBITED + gateway SUCCESS + merchant FAILED → reconciliation evidence.
2. `POST /investigations` with `TXN-10035`: UPI PENDING → wait/recheck policy path; no automatic refund.
3. `TXN-10070` and `TXN-10071`: duplicate pair tied to `ORD-1029`; simulated refund requires approval.

Example:
```json
{"transaction_id":"TXN-10021","question":"₹2,000 was deducted but my order failed. What happened?"}
```

## Tests/evaluation
```bash
pytest -q
python scripts/evaluate_retrieval.py
ruff check app tests
```
Measured in this build sandbox on the 30-question synthetic set using the offline lexical fallback: Recall@1=0.60, Recall@3=0.80, Recall@5=0.80, MRR=0.70. Re-run after enabling BGE/Qdrant/reranking because those results will differ.

## Frontend compatibility
Routes shape transactions and investigations to the existing camelCase TypeScript contracts (`id`, `orderId`, `method`, `bank`, `gateway`, `merchant`, `createdAt`, `requiresApproval`, etc.).

## Credentials / Azure
No credentials are required for the local demo. For deployment, replace the SQLite URL with Azure Database for PostgreSQL, object storage with Azure Blob, and secrets with Key Vault. Qdrant can remain containerized. Ollama/cloud LLMs may be added behind the provider abstraction without changing API contracts.

## Current limitations
The checked-in local retriever is deterministic lexical retrieval so the project runs offline. Qdrant/BGE/reranker dependencies and service slots are provisioned but a production embedding ingestion adapter still needs model download/network access. LangGraph state persistence, full Redis distributed rate limiting/idempotency, Prometheus/Grafana provisioning, and a complete MCP transport server are extension points rather than falsely claimed as verified in this offline build.
