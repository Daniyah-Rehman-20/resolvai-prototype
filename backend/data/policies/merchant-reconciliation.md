# Merchant reconciliation
Reviewed: 2026-10-09. Type: product operating guidance.

Maintain separate customer-reported, gateway, bank, merchant-order, and settlement states with source timestamps. Missing order confirmation does not prove gateway failure. Match immutable provider references; verify webhook authenticity and replay protection before treating provider events as evidence. Re-query the authorized provider before any financial action.

If bank debit, gateway capture, and order state disagree, investigate the mismatch and avoid duplicate refunds. The merchant's settlement schedule is contract-specific and is not established by this knowledge base. Treat unconnected data sources as unavailable, not as success or failure. Escalate unresolved mismatches to an authorized operator with an evidence timeline.
