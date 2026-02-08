---
id: 001
title: AI FTE Constitution Creation
stage: constitution
date: 2026-02-07
surface: agent
model: claude-opus-4-6
feature: none
branch: master
user: hasss
command: /sp.constitution
labels: ["constitution", "governance", "ai-fte", "spec-driven-development"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
  - history/prompts/constitution/001-ai-fte-constitution-creation.constitution.prompt.md
  - AI_Employee_Vault/Plans/ (directory created)
  - AI_Employee_Vault/Pending_Approval/ (directory created)
  - AI_Employee_Vault/Approved/ (directory created)
  - AI_Employee_Vault/Rejected/ (directory created)
  - AI_Employee_Vault/In_Progress/ (directory created)
  - AI_Employee_Vault/Logs/ (directory created)
  - AI_Employee_Vault/Briefings/ (directory created)
  - AI_Employee_Vault/Accounting/ (directory created)
  - AI_Employee_Vault/Invoices/ (directory created)
  - specs/ (directory created)
  - history/prompts/constitution/ (directory created)
  - history/prompts/general/ (directory created)
  - history/adr/ (directory created)
  - src/watchers/ (directory created)
  - src/orchestrator/ (directory created)
  - src/mcp/ (directory created)
  - tests/ (directory created)
  - config/ (directory created)
  - docs/ (directory created)
tests:
  - N/A (constitution document, no code tests)
---

## Prompt

/sp.constitution

Generate a formal AI Employee Constitution for an FTE built using Spec-Driven Development (SpecifyPlus). The constitution must reference and be based on the hackathon document at /documents/doc.md. It must cover 13 mandatory sections: Identity & Scope, Development & Project Structure Governance, Spec-Driven Development Enforcement, Claude Code Skill Usage Policy, Security & Secret Handling (Zero-Trust), External Integrations & MCP Enforcement, Observability/Audit Logging & Transparency, Graceful Degradation & Error Recovery, Ethics & Responsible Automation, Transparency Principles, Human Oversight & Accountability Tiers, Human-in-the-Loop Enforcement, and Non-Negotiable Rules. The constitution serves as a governing contract, technical specification, behavioral safety system, and human-accountability framework.

## Response snapshot

Created the AI FTE Constitution v1.0.0 at `.specify/memory/constitution.md`. The document covers all 13 required sections derived from the hackathon document at `/documents/doc.md`. Key elements include:

- **Identity & Scope:** Defines the AI FTE role, authority boundaries, non-goals, and explicit human accountability
- **Project Structure:** Full directory tree for vault, specs, history, source, and separation of concerns
- **SDD Enforcement:** Spec-first workflow with drift detection and implementation gating
- **Skill Policy:** Mandatory usage rules with logging requirements for all skill invocations
- **Zero-Trust Security:** Five absolute rules for secret handling, mandatory redaction, least-privilege scoping
- **MCP Enforcement:** All external integrations must use MCP servers; direct API calls prohibited
- **Observability:** Structured JSON logging with complete action visibility and 90-day retention
- **Graceful Degradation:** Error categories with recovery strategies, safe-mode protocol, idempotent retries
- **Ethics:** Hard constraints on autonomous action in emotional, legal, medical, financial, and irreversible contexts
- **Transparency:** AI disclosure in communications, opt-out mechanisms, audit trail accessibility
- **Oversight Tiers:** Daily (2 min), Weekly (15 min), Monthly (1 hr), Quarterly schedules with specific requirements
- **HITL Enforcement:** File-based approval gates, auto-approve thresholds, confidence scoring, kill-switch mechanism
- **Non-Negotiable Rules:** 8 absolute rules that override all other considerations

Also created all required project directories per the constitution's directory structure specification. Validated template compatibility (plan, spec, tasks templates are aligned).

## Outcome

- Impact: Major — Established the governing constitution for the entire AI FTE project
- Tests: N/A (governance document, not code)
- Files: constitution.md written; 19 directories created to match constitutional structure
- Next prompts: Populate Company_Handbook.md with operational rules; create first feature spec; set up .gitignore with secret exclusions
- Reflection: The constitution is comprehensive and implementation-ready. All 13 sections from the prompt are addressed with enforceable, testable rules grounded in the hackathon document.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Manual validation PASS — all 13 sections present, no unresolved placeholders, dates ISO format, version line matches report
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Validate constitution enforcement by implementing the first feature spec and checking all gates fire correctly
