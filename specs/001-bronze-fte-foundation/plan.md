# Implementation Plan: Bronze Tier AI FTE Foundation

**Branch**: `001-bronze-fte-foundation` | **Date**: 2026-02-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-bronze-fte-foundation/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a Bronze Tier AI FTE Foundation implementing the Perception → Reasoning → Action architecture. The system consists of: (1) a file system watcher that monitors Inbox/ and creates structured action files in Needs_Action/, (2) Obsidian vault files (Dashboard.md, Company_Handbook.md) providing operational visibility and rules, (3) three Claude Code agent skills for inbox processing, dashboard updates, and status reporting, and (4) comprehensive audit logging in structured JSON format. All components follow the constitution v1.0.0 requirements for security, observability, and human oversight.

## Technical Context

**Language/Version**: Python 3.12+ (compatible with CPython 3.13)
**Primary Dependencies**: `watchdog>=4.0.0` (file system monitoring), `python-dotenv>=1.0.0` (environment configuration)
**Storage**: File-based (Obsidian vault markdown files, JSON logs)
**Testing**: `pytest>=8.0.0` for unit tests
**Target Platform**: Linux/WSL2, macOS, Windows (cross-platform)
**Project Type**: Single project (Python package)
**Performance Goals**: < 10 second file detection latency, < 2 minute dashboard generation
**Constraints**: No external API dependencies, local-first, file-based coordination only
**Scale/Scope**: Single-user Bronze Tier (1 watcher, 3 skills, local vault)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Section II: Development & Project Structure Governance

- ✅ **Directory Structure**: Vault folders (Inbox/, Needs_Action/, Logs/, etc.) align with constitution Section II
- ✅ **File Operations**: Watchers create files in Needs_Action/, skills move to Done/ — no deletions
- ✅ **Separation**: Core logic in `src/watchers/`, logs in vault `Logs/`, secrets in `.env` (gitignored)

### Section III: Spec-Driven Development Enforcement

- ✅ **Spec First**: Feature spec completed and validated before planning
- ✅ **Testable**: All 14 FRs have acceptance scenarios in spec
- ✅ **Drift Detection**: `/sp.analyze` will verify implementation matches spec

### Section IV: Claude Code Skill Usage Policy

- ✅ **Skills Mandatory**: All AI functionality (process-inbox, update-dashboard, vault-report) implemented as skills in `.claude/skills/`
- ✅ **Skill Logging**: Each skill logs invocations to vault Logs/

### Section V: Security & Secret Handling

- ✅ **No Secrets**: Bronze Tier has no external APIs, no credentials needed
- ✅ **.gitignore**: Already created, excludes `.env`, `.venv/`, `*.key`, `credentials.json`
- ✅ **Environment Variables**: `.env` for VAULT_PATH, check intervals (not secrets in Bronze)

### Section VI: External Integrations & MCP Enforcement

- ⚠️ **Deferred to Silver**: Bronze Tier has no external integrations (no email MCP, no payment MCP)
- ✅ **File System Only**: Watcher uses Python `watchdog` library (not an external API)

### Section VII: Observability, Audit Logging & Transparency

- ✅ **Structured Logs**: All actions logged to `Logs/YYYY-MM-DD.json` with required fields (timestamp, action_id, action_type, actor, target, parameters, result)
- ✅ **90-Day Retention**: Constitution requires minimum 90 days (implementation will support this)
- ✅ **Dashboard**: Dashboard.md shows red flags, queue counts, recent activity per constitution Section XI

### Section VIII: Graceful Degradation & Error Recovery

- ✅ **Error Handling**: BaseWatcher has try/except around check cycle, logs errors
- ✅ **Auto-Create Directories**: FR-014 requires auto-creation of Inbox/, Needs_Action/, Logs/
- ✅ **Safe Shutdown**: Watcher handles SIGINT/SIGTERM gracefully

### Section IX: Ethics & Responsible Automation

- ✅ **No Autonomous Actions**: Bronze Tier watchers only detect and create action files; skills require explicit invocation
- ✅ **HITL Ready**: Company_Handbook.md defines thresholds; Pending_Approval/ folder exists

### Section X: Transparency Principles

- ✅ **Audit Trail**: All watcher and skill actions logged
- ✅ **Dashboard Visibility**: Dashboard.md provides human-readable summary

### Section XI: Human Oversight & Accountability Tiers

- ✅ **Daily Check (2 min)**: Dashboard.md + vault-report skill support this
- ✅ **Red Flags**: Dashboard.md has red flags section at top
- ✅ **Queue Counts**: Dashboard.md shows all folder counts

### Section XII: Human-in-the-Loop Enforcement

- ✅ **Emergency Stop**: FR-005 requires checking for EMERGENCY_STOP.md before each cycle
- ✅ **Approval Folders**: Pending_Approval/, Approved/, Rejected/ exist per constitution

### Section XIII: Non-Negotiable Rules

- ✅ **Safety First**: No irreversible actions in Bronze (only file creation/moves)
- ✅ **Transparency**: All actions logged
- ✅ **Specs Govern**: This plan follows approved spec
- ✅ **Constitution Supersedes**: All design decisions checked against constitution above

**Gate Result:** ✅ PASS — All applicable constitution requirements met for Bronze Tier

## Project Structure

### Documentation (this feature)

```text
specs/001-bronze-fte-foundation/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (next)
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── checklists/
│   └── requirements.md  # Spec quality checklist (completed)
└── contracts/           # Phase 1 output (skills API contracts)
```

### Source Code (repository root)

```text
project-root/
├── src/
│   ├── __init__.py
│   ├── watchers/
│   │   ├── __init__.py
│   │   ├── base_watcher.py          # Abstract base class
│   │   ├── filesystem_watcher.py    # File system watcher implementation
│   │   └── run_watcher.py           # CLI entry point
│   ├── orchestrator/                # Reserved for Silver Tier
│   └── mcp/                         # Reserved for Silver Tier
├── tests/
│   ├── __init__.py
│   ├── test_filesystem_watcher.py   # Watcher unit tests
│   └── e2e_test_flow.sh             # End-to-end integration test
├── .claude/
│   ├── commands/                    # Existing SDD commands
│   └── skills/                      # NEW: Agent skills (Phase 1)
│       ├── process-inbox.md
│       ├── update-dashboard.md
│       └── vault-report.md
├── AI_Employee_Vault/
│   ├── Dashboard.md                 # Populated in Phase 1
│   ├── Company_Handbook.md          # Populated in Phase 1
│   ├── Inbox/                       # Monitored by watcher
│   ├── Needs_Action/                # Action files created here
│   ├── Plans/
│   ├── Pending_Approval/
│   ├── Approved/
│   ├── Rejected/
│   ├── In_Progress/
│   ├── Done/                        # Completed items
│   ├── Logs/                        # Audit logs (YYYY-MM-DD.json)
│   ├── Briefings/
│   ├── Accounting/
│   └── Invoices/
├── .env                             # Local config (gitignored)
├── .env.example                     # Template (committed)
├── .gitignore                       # Excludes secrets
├── pyproject.toml                   # Python project config
└── README.md                        # To be created
```

**Structure Decision:** Single Python project structure chosen because Bronze Tier is a monolithic watcher + skills system with no separate backend/frontend or microservices.

## Complexity Tracking

> **No complexity violations.** Bronze Tier follows the simplest viable architecture: single Python project, file-based coordination, no external APIs, no process management (manual start).

---

## Phase 0: Research

Research tasks to resolve before Phase 1 design:

### Research Task 1: Watchdog Library Best Practices

**Question:** What is the recommended pattern for using Python `watchdog` library for event-driven file monitoring vs polling?

**Research Approach:**
- Review watchdog documentation for Observer pattern
- Compare `FileSystemEventHandler` (event-driven) vs periodic `check_for_updates()` (polling)
- Determine best practice for Bronze Tier use case (Inbox/ monitoring)

**Decision Needed:** Event-driven (Observer) vs polling (while loop with sleep)

### Research Task 2: YAML Frontmatter Standard

**Question:** What is the standard format for YAML frontmatter in markdown files for metadata?

**Research Approach:**
- Review Jekyll/Hugo/Obsidian frontmatter conventions
- Determine required fields for action files per FR-002
- Ensure compatibility with Obsidian rendering

**Decision Needed:** YAML structure and required fields for action files

### Research Task 3: JSON Audit Log Schema

**Question:** What is the optimal structure for append-only daily JSON log files?

**Research Approach:**
- Review constitution Section VII log format requirements
- Consider: single JSON object with array of entries vs newline-delimited JSON (NDJSON)
- Evaluate file locking considerations for concurrent writes (deferred to Silver for Bronze)

**Decision Needed:** JSON file structure (array of objects vs NDJSON)

### Research Task 4: Claude Code Skills Discovery

**Question:** How does Claude Code discover and invoke agent skills from `.claude/skills/`?

**Research Approach:**
- Review Claude Code agent skills documentation
- Understand YAML frontmatter requirements (`name`, `description`, `model`, `color`)
- Determine best practices for `<example>` blocks to trigger skills

**Decision Needed:** Skill file structure and example trigger patterns

---

## Phase 1: Design & Contracts

✅ **Status**: Complete (2026-02-07)

### Data Model

See [data-model.md](./data-model.md) - **Generated**

**Contents**:
- Entity 1: Action File (YAML frontmatter schema, 8 required fields, category rules, lifecycle)
- Entity 2: Audit Log Entry (NDJSON format, 10 required fields, action types taxonomy)
- Entity 3: Dashboard (markdown structure, 6 required sections, red flags logic)
- Entity 4: Company Handbook (configuration schema, auto-approve rules, thresholds)
- Data flow diagram showing vault coordination

### API Contracts

See [contracts/](./contracts/) - **Generated**

**Skills documented**:
1. **process-inbox-skill.md**: FR-008 implementation (categorize, apply rules, move files, log actions)
   - Input: Natural language trigger, discovers pending items
   - Output: Processing summary, files moved to Done/ or Pending_Approval/
   - Error handling: Emergency stop, invalid frontmatter, permission errors
   - Test scenarios: Happy path, flagging, emergency stop, mixed batch

2. **update-dashboard-skill.md**: FR-009 implementation (regenerate Dashboard.md)
   - Input: Natural language trigger, scans vault folders and logs
   - Output: Dashboard.md with current state, queue counts, red flags, recent activity
   - Performance: < 2 seconds for typical vault
   - Called by: process-inbox skill, human operator

3. **vault-report-skill.md**: FR-010 implementation (read-only status report)
   - Input: Natural language trigger (e.g., "What's the status?")
   - Output: Console text report, no file modifications
   - Use case: Daily 2-minute check per constitution Section XI
   - Zero side effects: Can be called repeatedly without affecting vault

### Quickstart

See [quickstart.md](./quickstart.md) - **Generated**

**Contents**:
- Prerequisites checklist (Python 3.12+, Claude Code, Obsidian, Git, uv)
- 8-step setup guide (clone, configure, install, verify, start watcher, test flow)
- Complete test scenario: Drop file → Action file created → Process with skill → Verify completion
- Emergency stop test procedure
- Common issues & solutions (5 troubleshooting scenarios)
- Daily operations guide (morning routine, starting/stopping watcher, reviewing logs)
- Constitution compliance checklist

### Agent Context Update

✅ **CLAUDE.md updated** via update-agent-context.sh:
- Added language: Python 3.12+ (compatible with CPython 3.13)
- Added framework: watchdog>=4.0.0 (file system monitoring), python-dotenv>=1.0.0
- Added database: File-based (Obsidian vault markdown files, JSON logs)

---

## Notes

- **Deferred to Silver Tier:** Process management (PM2/supervisord), Gmail watcher, MCP servers, orchestrator automation
- **Bronze Scope:** Manual watcher start, file system monitoring only, local vault only
- **Testing Strategy:** Unit tests for watcher (pytest), E2E test script for drop-file-to-done flow, manual skill testing via Claude Code CLI
