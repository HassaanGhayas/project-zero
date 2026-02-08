# Tasks: Bronze Tier AI FTE Foundation

**Feature Branch**: `001-bronze-fte-foundation`
**Input**: Design documents from `/specs/001-bronze-fte-foundation/`
**Prerequisites**: ✅ plan.md, ✅ spec.md, ✅ research.md, ✅ data-model.md, ✅ contracts/

**Organization**: Tasks are grouped by user story (P1 → P5) to enable independent implementation and testing.

---

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1-US5) this task belongs to
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, environment configuration, and vault structure

- [X] T001 Verify vault folder structure exists at AI_Employee_Vault/ (Inbox/, Needs_Action/, Plans/, Pending_Approval/, Approved/, Rejected/, In_Progress/, Done/, Logs/, Briefings/, Accounting/, Invoices/)
- [X] T002 Create missing vault folders if they don't exist using mkdir -p
- [X] T003 [P] Verify .env configuration with VAULT_PATH, INBOX_WATCH_PATH, WATCHER_CHECK_INTERVAL, DRY_RUN, DEV_MODE
- [X] T004 [P] Verify Python dependencies installed (watchdog>=4.0.0, python-dotenv>=1.0.0, pytest>=8.0.0)
- [X] T005 [P] Create tests/__init__.py for test package initialization
- [X] T006 [P] Create README.md in repository root with quickstart instructions

**Checkpoint**: Environment configured, vault structure ready, dependencies installed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core watcher infrastructure and logging utilities that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Create src/watchers/__init__.py with package exports
- [X] T008 Create src/watchers/base_watcher.py with BaseWatcher abstract class (check_interval, vault_path, needs_action, logger, abstract methods: check_for_updates, create_action_file, run method with error handling)
- [X] T009 [P] Create src/watchers/utils.py with helper functions (create_yaml_frontmatter, write_ndjson_log, load_env_config, ensure_directory_exists)
- [X] T010 [P] Create src/watchers/logger_config.py with logging setup (console + file handlers, structured format)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - File Drop Detection and Action Creation (Priority: P1) 🎯 MVP

**Goal**: Watcher detects files dropped in Inbox/ and creates structured action files in Needs_Action/ with YAML frontmatter

**Independent Test**: Drop any file into AI_Employee_Vault/Inbox/ and verify that a corresponding .md action file appears in Needs_Action/ within 10 seconds with correct YAML frontmatter (type, original_name, size, file_type, category, received, priority, status: pending)

**Why MVP**: This is the minimum viable perception layer. Without this, the AI Employee cannot sense its environment.

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement file categorization logic in src/watchers/categorizer.py (map file extensions to categories per FR-003: document, text, data, image, email, unknown)
- [X] T012 [P] [US1] Implement YAML frontmatter generator in src/watchers/action_file_generator.py (8 required fields: type, original_name, size, file_type, category, received ISO8601, priority, status)
- [X] T013 [US1] Implement FileSystemWatcher class in src/watchers/filesystem_watcher.py extending watchdog.events.FileSystemEventHandler (on_created method, ignore hidden files and .tmp files per FR-011)
- [X] T014 [US1] Implement watcher Observer setup in src/watchers/filesystem_watcher.py (start Observer, watch Inbox/, handle SIGINT/SIGTERM gracefully per FR-013)
- [X] T015 [US1] Implement action file creation logic in src/watchers/filesystem_watcher.py (write to Needs_Action/ with format: FILE_{original_name}.md, prevent duplicates per FR-012)
- [X] T016 [US1] Implement NDJSON audit logging in src/watchers/filesystem_watcher.py (log to Logs/YYYY-MM-DD.json with required fields: timestamp, action_id, action_type, actor, target, parameters, result per FR-004)
- [X] T017 [US1] Implement EMERGENCY_STOP.md check in src/watchers/filesystem_watcher.py (check before each cycle per FR-005, log warning if detected)
- [X] T018 [US1] Create CLI entry point in src/watchers/run_watcher.py (argparse for config, load .env, start watcher, handle graceful shutdown)
- [X] T019 [US1] Implement auto-create directories in src/watchers/filesystem_watcher.py startup (create Inbox/, Needs_Action/, Logs/ if missing per FR-014)

**Checkpoint**: File drop detection complete - files dropped in Inbox/ automatically create action files in Needs_Action/ with full audit logging

---

## Phase 4: User Story 2 - Vault Dashboard and Operational Visibility (Priority: P2)

**Goal**: Dashboard.md shows current vault state at a glance (queue counts, recent activity, red flags, system status)

**Independent Test**: Open Dashboard.md in Obsidian and verify it shows accurate folder counts, recent activity from logs, and any active alerts — all matching actual vault state

**Dependencies**: Requires US1 (logs must exist to show recent activity)

### Implementation for User Story 2

- [X] T020 [P] [US2] Create .claude/skills/update-dashboard.md with YAML frontmatter (name, description, model: opus, color, example triggers)
- [X] T021 [US2] Implement dashboard skill instructions in .claude/skills/update-dashboard.md (scan vault folders, read today's log, check EMERGENCY_STOP.md, find stale approvals, generate markdown per data-model.md Entity 3 schema)
- [X] T022 [US2] Create initial Dashboard.md template in AI_Employee_Vault/ with 6 required sections (Red Flags, System Status, Pending Approvals, Recent Activity, Queue Status, Errors)
- [X] T023 [US2] Add dashboard skill logic to scan all workflow folders (Inbox/, Needs_Action/, Plans/, Pending_Approval/, In_Progress/, Done/) and count files
- [X] T024 [US2] Add dashboard skill logic to read Logs/YYYY-MM-DD.json and extract last 10 entries for Recent Activity section
- [X] T025 [US2] Add dashboard skill logic to identify red flags (EMERGENCY_STOP.md exists, Pending_Approval/ items > 24 hours old, error count > 5 in last hour)
- [X] T026 [US2] Add dashboard skill logic to determine watcher status (check for watcher_started log entry within last 10 minutes)
- [X] T027 [US2] Add dashboard skill audit logging (log dashboard_updated action to daily log per FR-004)

**Checkpoint**: Dashboard.md provides real-time vault visibility - operator can do 2-minute daily check per constitution Section XI

---

## Phase 5: User Story 5 - Company Handbook as Rules Engine (Priority: P5)

**Goal**: Company_Handbook.md defines auto-approve thresholds, confidence rules, and AI behavior policies

**Independent Test**: Modify a threshold in Company_Handbook.md, process an action item that crosses the threshold, verify AI behavior changes accordingly

**Dependencies**: None (handbook is configuration only, read by US3)

**Why before US3**: Handbook must exist before inbox processing skill can read it

### Implementation for User Story 5

- [X] T028 [US5] Create Company_Handbook.md template in AI_Employee_Vault/ with 7 required sections per data-model.md Entity 4 (Communication Rules, Auto-Approve Thresholds, Confidence Scoring Rules, Known Contacts, Opt-Out List, Financial Rules, Watcher Rules)
- [X] T029 [US5] Populate Company_Handbook.md with Bronze Tier defaults (auto-process text files < 1MB, require review for documents, flag unknown file types, ignore hidden/temp files)
- [X] T030 [US5] Add version field and last updated timestamp to Company_Handbook.md frontmatter

**Checkpoint**: Company_Handbook.md ready to govern AI behavior with Bronze Tier rules

---

## Phase 6: User Story 3 - AI-Powered Inbox Processing (Priority: P3)

**Goal**: AI reads pending action files, categorizes them, applies handbook rules, moves to Done/ or Pending_Approval/

**Independent Test**: Place action files in Needs_Action/, invoke "Process my inbox" in Claude Code, verify items are categorized, moved to Done/ or Pending_Approval/, and logged

**Dependencies**: Requires US1 (action files must exist), US2 (dashboard for updates), US5 (handbook for rules)

### Implementation for User Story 3

- [X] T031 [P] [US3] Create .claude/skills/process-inbox.md with YAML frontmatter (name, description, model: opus, color, example triggers per contracts/process-inbox-skill.md)
- [X] T032 [US3] Implement precondition validation in process-inbox skill (check vault exists, required folders exist, Company_Handbook.md exists, EMERGENCY_STOP.md does NOT exist per contracts/process-inbox-skill.md)
- [X] T033 [US3] Implement pending item discovery logic in process-inbox skill (list Needs_Action/*.md, filter for status: pending in YAML frontmatter)
- [X] T034 [US3] Implement Company_Handbook.md reader in process-inbox skill (parse auto-approve thresholds, confidence rules, category rules)
- [X] T035 [US3] Implement auto-approve decision tree in process-inbox skill (text files < 1MB → high confidence, documents → medium confidence, unknown → low confidence per contracts/process-inbox-skill.md)
- [X] T036 [US3] Implement file moving logic in process-inbox skill (auto-approved → Done/, flagged → Pending_Approval/, update frontmatter status field)
- [X] T037 [US3] Implement audit logging for inbox processing (log inbox_processed, item_completed, item_flagged actions to daily log)
- [X] T038 [US3] Implement emergency stop check in process-inbox skill (abort if EMERGENCY_STOP.md detected, log emergency_stop action)
- [X] T039 [US3] Implement dashboard update call at end of process-inbox skill (invoke update-dashboard skill after processing completes)
- [X] T040 [US3] Implement processing summary generator in process-inbox skill (total processed, completed count, flagged count, errors count per contracts/process-inbox-skill.md output format)

**Checkpoint**: Inbox processing complete - AI can categorize and route items based on handbook rules with full audit trail

---

## Phase 7: User Story 4 - Quick Vault Status Report (Priority: P4)

**Goal**: Read-only console status report without modifying any files (daily 2-minute check tool)

**Independent Test**: Invoke "What's the status?" in Claude Code, verify concise text report with accurate folder counts and alerts, verify no files modified

**Dependencies**: Requires US1 (logs for recent activity), US2 (vault structure)

### Implementation for User Story 4

- [X] T041 [P] [US4] Create .claude/skills/vault-report.md with YAML frontmatter (name, description, model: haiku, color, example triggers per contracts/vault-report-skill.md)
- [X] T042 [US4] Implement read-only folder counting logic in vault-report skill (count Inbox/, Needs_Action/, Pending_Approval/, Done/ files without modifying)
- [X] T043 [US4] Implement recent activity reader in vault-report skill (read last 3 entries from Logs/YYYY-MM-DD.json)
- [X] T044 [US4] Implement alert detection in vault-report skill (check EMERGENCY_STOP.md, pending approvals > 0)
- [X] T045 [US4] Implement console report formatter in vault-report skill (generate concise text with emoji indicators per contracts/vault-report-skill.md output format)
- [X] T046 [US4] Verify vault-report skill has NO side effects (no file writes, no log entries, console output only per contracts/vault-report-skill.md)

**Checkpoint**: Quick status report complete - operator can check vault state in < 30 seconds without modifying any files

---

## Phase 8: Testing & Validation

**Purpose**: Comprehensive testing of the complete Bronze Tier system

**Note**: Tests were not explicitly requested in spec, but included here for robustness validation

- [X] T047 [P] Create tests/test_filesystem_watcher.py with unit tests (test file categorization, YAML frontmatter generation, action file creation, duplicate prevention, hidden file ignoring)
- [X] T048 [P] Create tests/test_action_file_generator.py with unit tests (test YAML frontmatter schema, ISO 8601 timestamps, category mapping, priority assignment)
- [X] T049 [P] Create tests/test_logger.py with unit tests (test NDJSON format, append-only writes, daily log file creation, required fields validation)
- [X] T050 Create tests/e2e_test_flow.sh bash script (test complete flow: start watcher → drop file → verify action file → stop watcher → verify logs)
- [X] T051 Create tests/test_emergency_stop.py with unit test (create EMERGENCY_STOP.md → verify watcher halts, skill aborts, logs warning)
- [X] T052 Test edge case: watcher started with missing Inbox/ folder (verify auto-creation per FR-014)
- [X] T053 Test edge case: corrupted log file (verify new log created, warning logged)
- [X] T054 Test edge case: invalid YAML frontmatter in action file (verify skill flags as unknown, routes to Pending_Approval/)
- [X] T055 Run full test suite with pytest (pytest tests/ -v --cov=src)

**Checkpoint**: All tests passing, edge cases handled, constitution compliance verified

---

## Phase 9: Documentation & Polish

**Purpose**: Final documentation, README updates, and cross-cutting concerns

- [X] T056 [P] Update README.md with Bronze Tier setup instructions (link to quickstart.md)
- [X] T057 [P] Add architecture diagram to README.md (Perception → Reasoning → Action flow)
- [X] T058 [P] Document CLI usage for run_watcher.py (arguments, environment variables, graceful shutdown)
- [X] T059 [P] Create example .md files in AI_Employee_Vault/Inbox/ for testing (sample.txt, document.pdf placeholders)
- [X] T060 Verify .gitignore excludes .env, .venv/, Logs/*.json, AI_Employee_Vault/Inbox/*, AI_Employee_Vault/Needs_Action/* per constitution Section V
- [X] T061 Run constitution compliance audit (verify all 13 sections met: directory structure, skills-based AI, structured logging, emergency stop, HITL enforcement)
- [X] T062 Perform manual smoke test using quickstart.md instructions (follow all 8 steps, verify complete flow works)

**Checkpoint**: Bronze Tier complete and documented - ready for demo and Silver Tier planning

---

## Dependency Graph (User Story Completion Order)

```
Phase 1: Setup (Foundation)
    ↓
Phase 2: Foundational (Core Infrastructure)
    ↓
Phase 3: US1 (File Detection) ← MVP MILESTONE
    ↓
    ├──→ Phase 4: US2 (Dashboard)
    │         ↓
    ├──→ Phase 5: US5 (Handbook)
    │         ↓
    └──→ Phase 6: US3 (Inbox Processing) ← depends on US1, US2, US5
              ↓
         Phase 7: US4 (Status Report) ← depends on US1, US2
              ↓
         Phase 8: Testing
              ↓
         Phase 9: Documentation
```

**Critical Path**: Setup → Foundational → US1 → US5 → US3 → Testing → Documentation

**Parallel Opportunities**:
- After US1: US2, US4, and US5 can be implemented in parallel
- After Foundation: All setup tasks (T003, T004, T005, T006) can run in parallel
- Testing: Most unit tests (T047-T049, T051) can be written and run in parallel

---

## Parallel Execution Examples

### After Foundation (Phase 2 Complete)

**Can start in parallel**:
- Agent A: US1 implementation (T011-T019)

### After US1 (Phase 3 Complete)

**Can start in parallel**:
- Agent A: US2 implementation (T020-T027) - Dashboard skill
- Agent B: US5 implementation (T028-T030) - Handbook template
- Agent C: US4 implementation (T041-T046) - Status report skill
- Agent D: Unit tests (T047-T049) - Test infrastructure

### After US2 + US5 (Phases 4 & 5 Complete)

**Can start**:
- Agent A: US3 implementation (T031-T040) - Inbox processing skill (depends on US1, US2, US5)

---

## MVP Definition (Minimum Viable Product)

**Bronze Tier MVP = User Story 1 Complete (Phase 3)**

**Deliverables**:
✅ File system watcher running
✅ Files dropped in Inbox/ create action files in Needs_Action/
✅ YAML frontmatter with 8 required fields
✅ Audit logging to Logs/YYYY-MM-DD.json
✅ Emergency stop mechanism (EMERGENCY_STOP.md)
✅ Graceful shutdown handling

**Demo**: Drop test_document.txt into Inbox/ → Action file appears in Needs_Action/ within 10 seconds → Log entry created

**Why this is MVP**: Demonstrates core perception capability. Proves the watcher works. Provides foundation for all other user stories.

---

## Implementation Strategy

1. **Start with MVP** (Phase 3: US1)
   - Get file detection working end-to-end
   - Verify audit logging works
   - Test emergency stop mechanism

2. **Add visibility** (Phase 4: US2 + Phase 7: US4)
   - Dashboard for persistent state
   - Status report for quick checks
   - Both build on US1's logging

3. **Add intelligence** (Phase 5: US5 + Phase 6: US3)
   - Handbook defines rules
   - Inbox processing applies rules
   - Completes Perception → Reasoning → Action loop

4. **Validate & document** (Phase 8 + Phase 9)
   - Comprehensive testing
   - Documentation for handoff

---

## Task Summary

**Total Tasks**: 62
- **Setup**: 6 tasks (T001-T006)
- **Foundation**: 4 tasks (T007-T010)
- **US1 (File Detection)**: 9 tasks (T011-T019)
- **US2 (Dashboard)**: 8 tasks (T020-T027)
- **US5 (Handbook)**: 3 tasks (T028-T030)
- **US3 (Inbox Processing)**: 10 tasks (T031-T040)
- **US4 (Status Report)**: 6 tasks (T041-T046)
- **Testing**: 9 tasks (T047-T055)
- **Documentation**: 7 tasks (T056-T062)

**Parallel Opportunities**: 23 tasks marked [P] can run concurrently

**Estimated Effort**:
- MVP (Setup + Foundation + US1): ~8-12 hours
- Full Bronze Tier: ~20-25 hours
- With testing & documentation: ~30-35 hours

---

## Constitution Compliance Verification

Tasks explicitly address constitution requirements:

- ✅ **Section II** (Directory Structure): T001-T002 create vault folders
- ✅ **Section IV** (Skills-based AI): T020, T031, T041 create skills in .claude/skills/
- ✅ **Section V** (Secret Handling): T003 verifies .env, T060 verifies .gitignore
- ✅ **Section VII** (Audit Logging): T016 implements NDJSON logs, T037 logs all actions
- ✅ **Section VIII** (Error Recovery): T014 graceful shutdown, T052-T054 edge cases
- ✅ **Section XI** (Daily Oversight): T022 Dashboard.md, T041 vault-report skill
- ✅ **Section XII** (HITL Enforcement): T017 EMERGENCY_STOP.md check, T038 skill check
- ✅ **Section XIII** (Constitution Supersedes): T061 constitution compliance audit

---

## Next Steps

1. **Review this task breakdown** with user for approval
2. **Run `/sp.implement`** to execute tasks in dependency order
3. **Monitor progress** via task checkboxes
4. **Test incrementally** after each user story completes
5. **Demo MVP** after Phase 3 (US1) completion

**Ready to begin implementation!** 🚀
