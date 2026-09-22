# Frontend verification

Verified against the local production build on 22 September 2026.

## Build checks

- ESLint: passed.
- TypeScript: passed.
- Next.js production build: passed (all declared routes generated or available dynamically).
- Git whitespace check: passed.

## Browser workflow checks

- Dashboard rendering and desktop screenshot review.
- Transaction search, detail navigation, and mismatch display.
- Simulated investigation completion and saved trace.
- Approval confirmation disabled without a note.
- Cancel leaves approval state unchanged.
- Approve records the decision and audit event; state survives refresh.
- Request more information and reject update their respective states.
- Document upload simulation reaches Ready and Indexed.
- Dispute status update persists.
- Dark-mode preference is applied.
- Simulated investigation failure and disable-and-retry recovery.
- All primary routes render without browser runtime exceptions.
- Demo reset restores pending approval fixtures.
- All ten screen types fit a 390px-wide mobile viewport without page-level horizontal overflow (wide tables scroll inside their containers).
- Mobile navigation opens and closes after selecting a destination.

Representative desktop, mobile, and dark-mode screenshots are included in this folder. These checks cover the mock frontend, not a backend, real AI model, payment provider, multi-user concurrency, or a formal accessibility certification.
