# Duplicate Payment Policy

PayResolve operational policy reference.

## Scope
This policy applies to payment investigation workflows handled within PayResolve.

## Investigation guidance
Compare bank, gateway, merchant and order states. Preserve evidence, correlation identifiers and timestamps. Never request CVV, PIN, UPI PIN, bank passwords or real financial credentials.

## Resolution guidance
For informational or pending states, prefer wait, recheck, reconciliation or escalation. Any refund, reversal, or dispute recommendation must pass deterministic backend risk checks and human approval before an execution request is recorded.

## Duplicate detection
Compare transactions sharing the same order, amount, instrument class and nearby timestamps. Any refund or reversal remains simulated and approval-gated.
