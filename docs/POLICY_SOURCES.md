# Policy source register

Research date: 2026-10-09. Scope: an India-focused payment-support application. These files contain human-authored summaries, not licensed access to bank ledgers and not a compliance certificate. Policy review is required before launch and whenever underlying sources change. Assign an accountable policy owner; retain source versions and effective dates. No automated refresh or legal approval is implied.

| Source | Verification | Used for |
| --- | --- | --- |
| [RBI failed-transaction circular, 20 September 2019](https://www.rbi.org.in/Commonperson/english/Scripts/Notification.aspx?Id=3074) | Full official text and annex retrieved | upi-pending-payment.md and card failure guidance |
| [RBI Integrated Ombudsman Scheme 2026 FAQ](https://www.rbi.org.in/commonperson/english/scripts/FAQs.aspx?Id=3407) | Official FAQ retrieved; linked scheme requires separate review | chargeback.md escalation guidance |
| [Paytm UPI terms](https://paytm.com/company/upi-terms-and-conditions) | Provider's published terms retrieved | Paytm-specific escalation workflow |
| [NPCI MyUPI](https://upihelp.npci.org.in/) | Official search result located; page fetch failed | Support destination only; no asserted detailed SLA |
| [NPCI legacy dispute page](https://www.npci.org.in/what-we-do/upi/dispute-redressal-mechanism) | Fetch failed with redirect loop | No unverified detailed rules imported |
| [MeitY DPDP Rules 2025 listing](https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa) | Official listing located; linked Gazette texts and commencement not reviewed | Privacy review entry point; not a claim of full current enforceability |

## Boundaries

The remaining markdown contains proposed application operating safeguards, explicitly labeled as such. No source establishes a universal merchant-return deadline, chargeback success rate, or bank integration. Keep customer reports distinct from verified provider evidence. The language model must cite the applicable source and abstain from unsupported guarantees. Policy context is untrusted reference material, never authorization to call a financial tool.

## Real data

Production records must come from the user's own authenticated cases and consented recordings plus authorized merchant/payment-provider APIs. A public transaction dataset cannot reveal a customer's live bank status or authorize a reversal. Sandbox fixtures remain synthetic and must be labeled. Partner onboarding, provider contracts, API credentials, and verified webhook configuration are prerequisites for live payment evidence. Do not scrape or obtain unrelated people's transaction records.

## Release review

Confirm jurisdiction, payment incident, applicable contract, source currency, and privacy commencement before exposing an answer as actionable guidance. Review call notice, recording consent, retention/deletion jobs, access isolation, processor terms, and human escalation with the deployment owner. Add regression cases for person-to-person versus merchant UPI, successful purchase refund versus failed payment, stale policy, and unsupported provider status. Review stored/vector-indexed policy copies after changes so old unsupported text cannot remain active.
