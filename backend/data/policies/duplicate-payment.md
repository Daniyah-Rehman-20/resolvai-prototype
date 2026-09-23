# Duplicate Payment Policy

Synthetic policy created for the PayResolve AI demonstration.

## Scope
This fictional policy applies only to synthetic demo transactions and mock systems.

## Investigation guidance
Compare bank, gateway, merchant and order states. Preserve evidence, correlation identifiers and timestamps. Never request CVV, PIN, UPI PIN, bank passwords or real financial credentials.

## Resolution guidance
For informational or pending states, prefer wait, recheck, reconciliation or escalation. Any simulated refund, reversal or dispute action must pass deterministic backend risk checks and human approval before mock execution.

## Duplicate detection
Compare transactions sharing the same order, amount, instrument class and nearby timestamps. Any refund or reversal remains simulated and approval-gated.
