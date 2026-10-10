# Payment data and call recording safeguards
Reviewed: 2026-10-09. Type: product safeguards and deployment requirements; not a legal certification.

## Application requirements
Never request or retain bank passwords, CVV, PIN, UPI PIN, or OTP. Minimize account/card details; prefer masked references. Disclose the AI identity, recording, transcription, processing purpose, relevant service providers, retention period, and contact route before recording. Obtain affirmative recording consent; refusal must allow chat or a non-recorded route. Store consent timestamp and notice version. Separate consent for recording from permission for financial actions.

Restrict recording/transcript access to the owner and authorized support roles. Encrypt stored media, avoid public recording URLs, redact secrets from logs, and define deletion including provider copies and backups. Retention must be explicitly configured and reviewed; do not invent a mandatory universal retention duration. Confirm processor contracts, hosting region, incident handling, and legal applicability before handling live customer calls. These are intended controls, not evidence that every control has been implemented.

## Official privacy source and verification limit
MeitY lists the Digital Personal Data Protection Rules 2025, corrigendum, and enforcement timeline: https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa
The official listing was located on 2026-10-09, but its linked Gazette documents and provision-specific commencement were not verified in this review. Do not assert that all provisions are already effective, that consent alone ensures compliance, or that a particular call-recording rule applies universally. Obtain deployment-specific review of the current notifications and applicable telecom/payment obligations.
