# Implementation work and next milestones

## Delegated implementation

Each workstream has one implementation owner. The coordinator integrates interfaces and runs cross-feature checks.

| Agent | Task | Subtasks / artifacts | Acceptance |
| --- | --- | --- | --- |
| Authentication & security | Persisted account identity | User/session models; migration; password hashing; register/login/logout; customer/staff separation; secure staff provisioning; authorization tests | A caller cannot grant itself staff access or read another customer's data |
| Support backend | Persist customer support | Conversation/message/query models; migration; owner checks; query extraction; optional AI responder; explicit fallback; policy context | Restart does not erase intake; unknown bank status remains unknown |
| Voice backend | Record and transcribe | Consent gate; size/type limits; private files; owner-scoped access; external transcription adapter; retention command; failure tests | No recording without consent; no fabricated transcript; customer isolation |
| Telephony integration | Optional incoming phone channel | Twilio webhook verification; account pairing; call consent; durable recording processing; transcript intake | Signed test callbacks pass; live number and provider test remain external |
| Customer frontend | Usable support journey | Registration/login; chat history; query list; microphone recording; upload/transcription; response playback; error/loading states | Customer completes text/voice intake through `/support` |
| Policy research | Ground payment guidance | RBI/NPCI and privacy source research; applicability caveats; source dates; policy source catalog; escalation boundaries | Guidance distinguishes failed transactions from fraud/chargebacks and cites sources |
| Operations | Reproducible deployment | Compose PostgreSQL/Redis; private volumes; migration startup; non-root images; env examples; CI; runbook | Empty install starts without demo seed; data survives restart |
| Coordinator | Integration and verification | API contracts; dependency wiring; authorization review; tests/build; final gaps report | Report exact completed checks and credentials still required |

## Support-only repository cleanup

- Remove the obsolete operations dashboard, synthetic payment seed, demo authentication bridge, simulated investigations/actions, and unused prototype scaffolding.
- Keep authenticated customer chat, query history and staff review, consented browser voice, signed telephone webhooks and durable telephone jobs.
- Keep curated policy summaries and source attribution; remove the repeated synthetic retrieval-evaluation dataset.
- Preserve historical database tables and migration history for upgrade compatibility; do not delete existing customer or payment records.
- Verify the retained application with lint, typecheck, build, backend tests and migration checks; record only executed results in BUILD_VALIDATION.md.

## Next milestone: controlled pilot

1. **Account lifecycle**: add verified email, reset/recovery, admin lifecycle, MFA for staff, session/device view, and abuse controls. Acceptance: recovery cannot bypass verified identity.
2. **Provider integration**: choose payment gateway/bank partner; obtain sandbox merchant credentials; implement signature-verified webhooks, replay protection, idempotent events, reconciliation and ownership mapping. Acceptance: use provider sandbox tests for success, late settlement, duplicate events, and refund failures.
3. **Refund workflow**: enforce staff permissions and dual approval as required; call provider APIs using idempotency keys; reconcile actual outcomes. Acceptance: approval never marks funds settled before provider evidence.
4. **Voice channels**: configure the optional Twilio incoming-call adapter, provision a number and TLS endpoint, run the durable recording worker and test signed callbacks and actual calls. Full-duplex streaming, interruption handling and human transfer remain future work.
5. **Privacy and data lifecycle**: finalize purpose-specific notices, provider data-processing agreements, recording/transcript retention, deletion/export, encryption/key management, and regional hosting decisions. Acceptance: deletion and retention are demonstrated including backups.
6. **Operations**: choose hosting and TLS; secret manager; automated backups plus restore drill; alerts; request/body limits; structured PII-safe logs; cost budgets; load tests. Acceptance: outage and restore exercises meet agreed RPO/RTO.
7. **Policy governance**: assign source owners and review intervals, version source text, have qualified staff approve guidance, and evaluate response accuracy and prompt-injection handling. Acceptance: expired/unverified policy cannot silently become definitive financial guidance.
8. **Launch review**: security review, dependency/image scan, real PostgreSQL end-to-end tests and browser microphone tests on target devices. Acceptance: documented sign-off with unresolved risks and rollback plan.

No external provider account, cloud service, public deployment, real financial record ingestion, or money movement is created by this implementation.
