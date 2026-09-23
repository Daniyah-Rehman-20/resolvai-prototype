# PayResolve AI — complete frontend

A Next.js payment-operations workspace for Daniyah Rehman's portfolio. Investigate fictional credit-card, debit-card, UPI, and cash payment issues and review proposed resolutions with human approval.

## Run on your computer

Use Node.js 20.9 or newer (a supported LTS release is recommended).

1. Extract this project into a new folder, or copy its files into your existing repository while keeping your existing `.git` directory.
2. Open the project folder in VS Code and open a terminal there.
3. Run:

```bash
npm ci
npm run dev
```

Open http://localhost:3000. The root opens the dashboard. If that port is occupied, use the alternate URL printed in the terminal. Keep the terminal running and press Ctrl+C to stop it.

For a production build:

```bash
npm run lint
npm run typecheck
npm run build
npm start
```

If PowerShell blocks `npm.ps1`, use Command Prompt from the VS Code terminal dropdown. No API key, database, cloud account, or environment file is required.

## Pages and functionality

| Route                | Features                                                                                                                                                                     |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/dashboard`         | Eight metrics, daily outcome chart, method distribution, issue categories, recent investigations, approval previews, CSV summary export.                                     |
| `/transactions`      | Search by transaction/order/customer, method/status/date filters, sorting, pagination, links to details.                                                                     |
| `/transactions/[id]` | Payment state comparison, mismatch highlighting, customer summary, timeline, investigation findings, policy evidence, agent steps, audit history.                            |
| `/investigator`      | Transaction selection, issue input, sequential simulated agent checks, evidence, policy retrieval, uncertainty, recommendation, review requirement, prior runs, error retry. |
| `/approvals`         | Pending/more-info/approved/rejected views, evidence, policy, reasoning summary, mandatory notes, confirmation, local decision updates and audit events.                      |
| `/disputes`          | Case filters, transaction links, reviewer notes, confirmed case-status updates and audit events.                                                                             |
| `/knowledge`         | Policy search, policy reader, PDF/TXT/Markdown upload simulation, file validation, processing/indexing statuses, retry.                                                      |
| `/agents`            | Run selection, execution path, human handoff, step status/duration/timestamp log.                                                                                            |
| `/analytics`         | Method success/failure rates, failure reasons, dispute/refund rates, AI resolution and human escalation rates, investigation and resolution times.                           |
| `/settings`          | Light/dark mode, notifications, failure simulation, confirmed reset of local demo records.                                                                                   |

The shared shell includes sidebar navigation, global transaction search, notifications, profile/settings menu, mobile navigation, a skip link, and status feedback. Dialogs use native modal semantics and keyboard dismissal. Loading, empty, success, and failure states are included.

## Try an end-to-end workflow

1. Open Transactions, find `TXN-10001`, and open it. Inspect the debit and failed order mismatch.
2. Click **Investigate payment**, then **Start investigation**. Each simulated step completes in order.
3. Read the evidence and uncertainty, then open **Approval Queue**.
4. Click **Approve** on a proposal. Confirm remains disabled until a review note is entered. Cancel to leave the request unchanged, or confirm to save the decision.
5. Open the transaction's **Audit log**. Refresh the page: the decision remains saved in this browser.
6. Upload a small `.txt` document in Knowledge Base. Watch the simulated status change from Processing to Ready.
7. Enable **Simulate a source failure** in Settings and save. A new investigation fails at its evidence-source step; disable/retry from the error panel. Document processing can also fail and be retried after disabling the setting.
8. Switch to dark mode, save, and inspect the pages at mobile width. Reset the demo in Settings when finished.

## Architecture

- `src/app/`: App Router pages, root layout, loading/error/not-found boundaries, favicon.
- `src/components/layout/`: Shared shell and data context.
- `src/components/common/`: Panels, badges, empty/loading states, accessible confirmation modal.
- `src/components/dashboard/`, `transactions/`, `investigator/`, `approvals/`, `knowledge/`, `agents/`: Feature components.
- `src/lib/types/`: Transaction, Customer, PaymentStatus, PaymentMethod, Investigation, AgentStep, ApprovalRequest, PolicyDocument, AuditEvent, Dispute, Settings, AppData.
- `src/lib/mocks/`: Central fictional fixtures and agent-step definitions.
- `src/lib/api/`: Async mock service, persistence, investigations, decisions, uploads, settings, dispute updates.
- `src/lib/utils/`: INR, IST, status labels, and percentage formatting.

Pages/components call the service layer and do not import mock fixtures. Next.js route wrappers pass identifiers to client components. The shared context refreshes after mutations so related views use the same state.

### FastAPI integration

The Next.js workspace now calls the FastAPI backend directly. The frontend service layer uses `NEXT_PUBLIC_API_URL` (default: `http://127.0.0.1:8000`) for transactions, investigations, approvals, disputes, documents, audit history, and demo reset. Theme/notification/failure-simulation preferences remain browser-local because they are UI settings.

Run the backend first:

```bash
cd backend
python -m app.db.seed
python -m uvicorn app.main:app --reload
```

Then, from the repository root in a second terminal:

```bash
npm ci
npm run dev
```

Open http://localhost:3000. The local backend must allow that origin through `CORS_ORIGINS`. For deployment, set `NEXT_PUBLIC_API_URL` to the public FastAPI URL and set backend `CORS_ORIGINS` to the deployed frontend origin.

The integration remains a synthetic payment-operations demo: no real bank, gateway, merchant, refund, or external LLM action is performed. Real production use would still require authentication, authorization, provider integrations, durable infrastructure, stronger audit controls, and production secret management.

## Demo behavior and limits

- All records are fictional. Customer emails use `example.test`; instrument values are masked.
- The 48-transaction cohort is dated 15–21 September 2026. New local activity uses the current timestamp. Dates display in IST.
- Investigations use deterministic rules, not a live LLM. They do not actually contact banks, gateways, or merchants. Uploaded policies do not influence the fixed recommendation rules.
- Refund approval changes a local transaction to `REFUND_PENDING`; it does not pretend that a real refund settled. Dispute approval creates a local case. Escalation approval records the human decision in the audit log.
- Dispute resolution changes case status only, not the financial transaction status.
- Duplicate pending/more-information approval requests are prevented for the same transaction. Decided requests cannot be decided again.
- Uploads store metadata only, not file bytes. Chunk counts and indexing are explicitly simulated. Only PDF/TXT/Markdown files from 1 byte to 10 MB are accepted.
- LocalStorage saves demo state under `payresolve-demo-v2`. It is local to one browser/origin, not shared multi-user storage. Browser privacy settings must allow local storage. Simultaneous multi-tab editing is not supported.
- Simulation traces persist when a run finishes. Closing the browser during a run does not persist an unfinished run. A document stuck Processing after a reload can be retried.
- Analytics derive from current local records. Resolution time covers only completed no-action demo cases; it does not imply real banking resolution performance.
- Reset clears demo edits and restores fixtures after confirmation.

## Push updates to your existing GitHub repository

After copying the project files into your existing checkout (preserving its `.git` folder):

```bash
git add .
git commit -m "Build complete PayResolve AI frontend"
git push
```

Keep `.gitignore`: it excludes dependencies, build output, local environment files, and generated TypeScript artifacts. The ZIP contains source and the dependency lockfile, not `node_modules` or `.next`.
