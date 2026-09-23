# PayResolve AI multi-agent delivery board

This repository uses role boundaries rather than duplicate implementations.

- [x] Orchestrator: contracts, sequencing, integration
- [x] Platform: config, exceptions, correlation/CORS/security headers
- [x] Data/DB: SQLAlchemy schema, migration scaffold, 30+ synthetic transactions
- [x] API: health, transactions, investigations, approvals, disputes, documents, analytics, chat
- [x] GenAI/RAG: synthetic policy KB, deterministic local retrieval, citation IDs, evaluation dataset/script
- [x] Agentic: transaction/RAG/resolution stages, deterministic risk/approval gate, mock actions, MCP registry scaffold
- [x] Infra/Async: Docker services, Celery/RabbitMQ wiring, Redis-compatible config
- [x] Security: demo RBAC helper, file limits, approval gate, no real payment actions
- [x] QA: risk/RAG/health tests and demo scenarios
- [x] DevOps: Dockerfile, compose, CI
- [x] Docs: README + contracts

Remaining production-grade extensions are documented in README; local demo fallbacks remain the default.
