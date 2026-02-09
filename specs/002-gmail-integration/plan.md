# Implementation Plan: Gmail Integration for AI Employee

**Branch**: `002-gmail-integration` | **Date**: 2026-02-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-gmail-integration/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Extend AI Employee Bronze Tier foundation with Gmail integration for automated email monitoring and action execution. This adds Gmail watcher (polls Gmail API for unread messages), action file generation in Obsidian vault, and email execution via MCP server (archive, mark as read). Integrates with existing Bronze Tier approval workflow (YAML status field editing) and maintains constitutional compliance (HITL, audit logging, emergency stop).

**Primary Requirement**: Automate Gmail monitoring so users can review/approve email actions through Obsidian without switching to Gmail.

**Technical Approach**: Extend existing BaseWatcher pattern from Bronze Tier with Gmail API client. Reuse action file generator, status field watcher, and approved watcher. Add Gmail MCP server for execution.

## Technical Context

**Language/Version**: Python 3.12+ (matches Bronze Tier)
**Primary Dependencies**:
- Bronze Tier: BaseWatcher, action_file_generator, logger_config, utils (existing)
- New: google-auth ^2.28.0, google-auth-oauthlib ^1.2.0, google-api-python-client ^2.118.0
- Existing: watchdog >=4.0.0, python-dotenv >=1.0.0, pytest >=8.0.0, pyyaml ==6.0.3
**Storage**: Filesystem (AI_Employee_Vault markdown files + NDJSON audit logs)
**Testing**: pytest with mock Gmail API responses
**Target Platform**: Linux/macOS/Windows+WSL (matches Bronze Tier)
**Project Type**: Single project (Python watcher service)
**Performance Goals**:
- Email detection within 5 minutes (95th percentile)
- Approval response within 2 seconds (99th percentile)
- MCP execution within 5 seconds (95th percentile)
**Constraints**:
- Gmail API quota: 10,000 queries/day, 250 queries/user/second (free tier)
- Default poll interval: 120 seconds (2-minute checks = 720/day, 8% of quota = safe margin)
- Must not block existing Bronze Tier watchers
- OAuth token management (refresh on expiry)
**Scale/Scope**:
- Single Gmail account
- ~50-100 emails/day expected volume
- 4 watchers running concurrently (filesystem, status_field, approved, gmail)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
