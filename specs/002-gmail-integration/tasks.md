# Tasks: Gmail Integration for AI Employee

**Feature Branch**: `002-gmail-integration`
**Input**: Design documents from `/specs/002-gmail-integration/`
**Prerequisites**: plan.md, spec.md (4 user stories: P1-P4)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- All paths reference `/home/hasss/projects/project-zero/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Gmail API infrastructure

- [X] T001 Add Gmail API dependencies to pyproject.toml (google-auth ^2.28.0, google-auth-oauthlib ^1.2.0, google-api-python-client ^2.118.0)
- [X] T002 Run uv sync to install new dependencies
- [X] T003 [P] Create scripts/ directory in project root
- [X] T004 [P] Create config/ directory in project root for known_contacts.yaml
- [X] T005 [P] Add Gmail environment variables to .env.example (GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH, GMAIL_CHECK_INTERVAL)

**Checkpoint**: Basic project structure ready for Gmail integration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Gmail infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create scripts/setup_gmail_oauth.py for OAuth2 authentication flow
- [X] T007 Create known_contacts.yaml template in config/known_contacts.yaml with structure (email, name, category, priority_override)
- [X] T008 Update AI_Employee_Vault/Company_Handbook.md with Gmail-specific approval rules (email section with auto-approve criteria and known contacts whitelist reference)
- [X] T009 Create src/mcp/gmail_server.py MCP server with archive_email and mark_as_read tool stubs
- [X] T010 Register Gmail MCP server via claude mcp add command (registered in ~/.claude.json)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Email Detection and Action File Creation (Priority: P1) 🎯 MVP

**Goal**: Gmail emails are automatically detected and converted into action files in Obsidian vault within 5 minutes

**Independent Test**: Send a test email to configured Gmail account and verify action file appears in `AI_Employee_Vault/Needs_Action/` within 5 minutes containing email metadata (sender, subject, snippet) with status: pending

### Implementation for User Story 1

- [X] T011 [P] [US1] Create src/watchers/gmail_watcher.py extending BaseWatcher class with __init__, check_for_updates, and create_action_file methods
- [X] T012 [US1] Implement Gmail API client initialization in gmail_watcher.py with OAuth2 credentials loading from .env
- [X] T013 [US1] Implement check_for_updates() method to poll Gmail API every 120 seconds with query "is:unread is:important label:inbox"
- [X] T014 [US1] Implement message ID tracking with _processed_message_ids set to prevent duplicates across watcher restarts
- [X] T015 [US1] Implement create_action_file() method to generate markdown action files with YAML frontmatter (type: email, gmail_message_id, sender, subject, snippet, status: pending, priority, received timestamp)
- [X] T016 [US1] Add exponential backoff logic for Gmail API rate limit errors (HTTP 429) - double check_interval up to max 3600 seconds
- [X] T017 [US1] Add NDJSON audit logging for email_detected events with full context (sender, subject, message_id)
- [X] T018 [US1] Integrate gmail_watcher into src/watchers/run_all_watchers.py orchestrator (instantiate GmailWatcher and add to watchers list)
- [X] T019 [US1] Add graceful error handling for OAuth token expiration with clear re-authentication instructions in logs

**Checkpoint**: At this point, User Story 1 should be fully functional - emails detected and converted to action files

---

## Phase 4: User Story 2 - Email Action Approval via Obsidian (Priority: P2)

**Goal**: Users can approve email actions by editing YAML status fields in Obsidian, with files moving to Approved/ folder within 2 seconds

**Independent Test**: Manually edit an action file's YAML frontmatter (change status: pending to status: approved), save the file, and verify within 2 seconds that the file moves to Approved/ folder

**Note**: This user story reuses existing Bronze Tier infrastructure (status_field_watcher.py and folder-based approval workflow). No new implementation required - validation only.

### Implementation for User Story 2

- [ ] T020 [US2] Verify status_field_watcher.py detects YAML status changes in email action files (type: email)
- [ ] T021 [US2] Test file movement from Needs_Action/ to Approved/ when status changed to "approved"
- [ ] T022 [US2] Test file movement from Needs_Action/ to Rejected/ when status changed to "rejected"
- [ ] T023 [US2] Verify EMERGENCY_STOP.md detection prevents file movement when emergency stop is active
- [ ] T024 [US2] Verify audit logging for file_moved events includes email-specific metadata (gmail_message_id, sender)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - email detection + approval workflow

---

## Phase 5: User Story 3 - Email Execution via MCP Servers (Priority: P3)

**Goal**: Approved email actions (archive, mark as read) are executed via Gmail MCP server and confirmed within 5 seconds

**Independent Test**: Approve an email action file, wait 5 seconds, and verify: (1) confirmation file created in In_Progress/ showing execution result, (2) audit log contains email_executed entry, (3) actual Gmail message is archived/marked as read when checked via Gmail UI

### Implementation for User Story 3

- [ ] T025 [P] [US3] Implement archive_email tool in src/mcp/gmail_server.py (accepts message_id, calls Gmail API users().messages().modify() to remove INBOX label)
- [ ] T026 [P] [US3] Implement mark_as_read tool in src/mcp/gmail_server.py (accepts message_id, calls Gmail API users().messages().modify() to remove UNREAD label)
- [ ] T027 [US3] Add error handling to MCP tools with structured error responses (NOT_FOUND, AUTH_ERROR, RATE_LIMIT, NETWORK_ERROR, PERMISSION_DENIED)
- [ ] T028 [US3] Implement idempotency for archive_email and mark_as_read tools (return success if already archived/read)
- [ ] T029 [US3] Add NDJSON audit logging to MCP tools for all Gmail API calls with result status
- [ ] T030 [US3] Update src/watchers/approved_watcher.py to detect email action files (type: email) in Approved/ folder
- [ ] T031 [US3] Implement _execute_email_action() method in approved_watcher.py to call Gmail MCP server with gmail_message_id
- [ ] T032 [US3] Add confirmation file generation in In_Progress/ after email execution with result, timestamp, Gmail API response
- [ ] T033 [US3] Add audit logging for email_executed events with MCP server response and execution status

**Checkpoint**: At this point, all core user stories (1-3) should be functional - full email workflow from detection to execution

---

## Phase 6: User Story 4 - Email Approval Rules Enforcement (Priority: P4)

**Goal**: Email approval rules (known contacts whitelist, attachment requirements, financial keywords) are enforced automatically to determine priority levels

**Independent Test**: Send emails from both known and unknown contacts, with and without attachments, and verify that action files are created with appropriate priority levels and suggested actions based on Company Handbook rules

### Implementation for User Story 4

- [ ] T034 [P] [US4] Populate config/known_contacts.yaml with sample known contacts (email, name, category: client/newsletter/internal/vendor, priority_override: medium/low)
- [ ] T035 [P] [US4] Add financial_keywords array to config/known_contacts.yaml (payment, invoice, billing, transaction, refund, subscription)
- [ ] T036 [US4] Create src/watchers/email_categorizer.py module with determine_priority() function
- [ ] T037 [US4] Implement known_contacts.yaml loading and parsing in email_categorizer.py with fallback to empty whitelist if file missing
- [ ] T038 [US4] Implement priority determination logic: high (unknown sender OR has_attachments OR financial_keywords match), medium (known sender + no attachments), low (newsletters/automated)
- [ ] T039 [US4] Integrate email_categorizer into gmail_watcher.py create_action_file() method to set priority field
- [ ] T040 [US4] Add attachment detection to gmail_watcher.py (check message payload for attachments, set has_attachments and attachment_count fields)
- [ ] T041 [US4] Add financial keyword detection to gmail_watcher.py (scan subject + snippet for keywords, set category: financial if match)
- [ ] T042 [US4] Generate priority-appropriate suggested actions in action file markdown body based on categorization results

**Checkpoint**: All user stories complete - full Gmail integration with intelligent prioritization

---

## Phase 7: Testing & Validation

**Purpose**: Comprehensive testing of all user stories and edge cases

- [ ] T043 [P] Create tests/test_gmail_watcher.py with mock Gmail API responses testing email detection, duplicate prevention, rate limit handling
- [ ] T044 [P] Create tests/test_gmail_mcp_server.py testing archive_email and mark_as_read tools with mock Gmail API
- [ ] T045 [P] Create tests/test_email_categorizer.py testing priority determination logic with various email scenarios
- [ ] T046 [P] Create tests/integration/test_gmail_e2e.py testing complete workflow (detection → approval → execution)
- [ ] T047 Run full test suite with uv run pytest tests/ -v and verify all Gmail tests pass
- [ ] T048 Manual E2E test: Send test email, verify action file creation, approve, verify execution, check Gmail for archived message
- [ ] T049 Test exponential backoff behavior by simulating rate limit errors (verify check_interval doubles up to 3600s max)
- [ ] T050 Test OAuth token expiration handling (verify watcher pauses and logs clear re-authentication instructions)

**Checkpoint**: All tests passing, Gmail integration validated end-to-end

---

## Phase 8: Documentation & Polish

**Purpose**: User-facing documentation and code quality improvements

- [ ] T051 [P] Create docs/GMAIL_SETUP.md with step-by-step OAuth2 setup instructions (Google Cloud Console, credentials.json, token.json)
- [ ] T052 [P] Update README.md with Gmail integration section (prerequisites, configuration, usage)
- [ ] T053 [P] Document known_contacts.yaml schema and usage examples in docs/
- [ ] T054 [P] Add inline code comments to gmail_watcher.py explaining Gmail API query syntax and rate limit strategy
- [ ] T055 [P] Update AI_Employee_Vault/Dashboard.md template to include Gmail watcher status row
- [ ] T056 Run Black formatter on all new Python files (src/watchers/gmail_watcher.py, src/mcp/gmail_server.py, src/watchers/email_categorizer.py)
- [ ] T057 Verify all NDJSON audit log entries are correctly formatted with complete context
- [ ] T058 Final constitution compliance check: verify sections IV, V, VII, IX, XII requirements met

**Checkpoint**: Feature complete, documented, and ready for production use

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase - Core capability (email detection)
- **User Story 2 (Phase 4)**: Depends on User Story 1 - Reuses Bronze Tier approval infrastructure
- **User Story 3 (Phase 5)**: Depends on User Stories 1 & 2 - Executes approved email actions
- **User Story 4 (Phase 6)**: Depends on User Story 1 - Enhances email detection with prioritization
- **Testing (Phase 7)**: Depends on all user stories being implemented
- **Documentation (Phase 8)**: Can run in parallel with Testing

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories ✅ INDEPENDENTLY TESTABLE
- **User Story 2 (P2)**: Depends on User Story 1 (needs email action files to exist) - Reuses existing Bronze Tier watchers ✅ INDEPENDENTLY TESTABLE
- **User Story 3 (P3)**: Depends on User Story 1 & 2 (needs detection + approval workflow) ✅ INDEPENDENTLY TESTABLE
- **User Story 4 (P4)**: Depends on User Story 1 (enhances email detection) - Can work in parallel with US2 & US3 ✅ INDEPENDENTLY TESTABLE

### Within Each User Story

- User Story 1: Gmail API client → check_for_updates → create_action_file → rate limiting → audit logging → orchestrator integration
- User Story 2: Validation only (no new implementation, reuses Bronze Tier)
- User Story 3: MCP tools (parallel) → approved_watcher integration → confirmation files → audit logging
- User Story 4: Config file → categorizer module → priority logic → integration with gmail_watcher

### Parallel Opportunities

**Phase 1 (Setup)**: T003, T004, T005 can run in parallel (different files)

**Phase 2 (Foundational)**: T006, T007, T009 can run in parallel (different files). T008 depends on T007. T010 depends on T009.

**Phase 3 (User Story 1)**: T011 must complete first (creates class), then T012-T019 can proceed sequentially (all modify same file)

**Phase 5 (User Story 3)**: T025, T026 can run in parallel (different MCP tools). T027-T029 modify same tools (sequential). T030-T033 modify approved_watcher (sequential).

**Phase 6 (User Story 4)**: T034, T035 can run in parallel (same file but independent sections). T036 must complete first, then T037-T042 modify categorizer/watcher sequentially.

**Phase 7 (Testing)**: T043, T044, T045, T046 can run in parallel (different test files). T047-T050 are sequential (run tests, then manual validation).

**Phase 8 (Documentation)**: T051, T052, T053, T054, T055, T056 can all run in parallel (different files)

---

## Parallel Example: Phase 1 Setup

```bash
# Launch all setup tasks together:
Task T003: "Create scripts/ directory in project root"
Task T004: "Create config/ directory in project root"
Task T005: "Add Gmail environment variables to .env.example"
```

## Parallel Example: Phase 7 Testing

```bash
# Launch all test file creation together:
Task T043: "Create tests/test_gmail_watcher.py"
Task T044: "Create tests/test_gmail_mcp_server.py"
Task T045: "Create tests/test_email_categorizer.py"
Task T046: "Create tests/integration/test_gmail_e2e.py"
```

## Parallel Example: Phase 8 Documentation

```bash
# Launch all documentation tasks together:
Task T051: "Create docs/GMAIL_SETUP.md"
Task T052: "Update README.md with Gmail section"
Task T053: "Document known_contacts.yaml schema"
Task T054: "Add inline comments to gmail_watcher.py"
Task T055: "Update Dashboard.md template"
Task T056: "Run Black formatter on new files"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (5 tasks, ~10 minutes)
2. Complete Phase 2: Foundational (5 tasks, ~30 minutes)
3. Complete Phase 3: User Story 1 (9 tasks, ~2 hours)
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Send test email
   - Verify action file created in Needs_Action/ within 5 minutes
   - Verify YAML frontmatter correct (type: email, gmail_message_id, sender, subject, status: pending)
   - Verify audit log entry for email_detected
5. Deploy/demo if ready - **MVP DELIVERED** ✅

**MVP Value**: Users can see emails in Obsidian without switching to Gmail. Emails are surfaced as action files for review.

### Incremental Delivery

1. **Foundation** (Phase 1-2): Setup + OAuth + MCP registration → ~40 minutes
2. **MVP** (Phase 3): Email Detection → Test independently → Deploy/Demo (User Story 1) ✅
3. **Approval** (Phase 4): Email Approval Workflow → Test independently → Deploy/Demo (User Stories 1+2) ✅
4. **Execution** (Phase 5): Email Action Execution → Test independently → Deploy/Demo (User Stories 1-3) ✅
5. **Intelligence** (Phase 6): Priority Categorization → Test independently → Deploy/Demo (All 4 User Stories) ✅
6. **Quality** (Phase 7-8): Tests + Documentation → Production Ready 🚀

Each increment adds value without breaking previous functionality.

### Sequential Implementation (Single Developer)

**Estimated Timeline**: ~12-16 hours total

- Week 1, Day 1 Morning: Phase 1-2 (Setup + Foundational) - 1 hour
- Week 1, Day 1 Afternoon: Phase 3 (User Story 1 - Email Detection) - 3 hours
- Week 1, Day 2 Morning: Phase 4 (User Story 2 - Approval) - 1 hour
- Week 1, Day 2 Afternoon: Phase 5 (User Story 3 - Execution) - 3 hours
- Week 1, Day 3 Morning: Phase 6 (User Story 4 - Prioritization) - 2 hours
- Week 1, Day 3 Afternoon: Phase 7 (Testing) - 2 hours
- Week 1, Day 4 Morning: Phase 8 (Documentation + Polish) - 1 hour

**Critical Path**: Setup → Foundational → US1 → US2 → US3 → US4 → Testing → Documentation

### Parallel Team Strategy (3 Developers)

**Estimated Timeline**: ~6-8 hours total

**Day 1 Morning** (1 hour) - All developers together:
- Complete Phase 1-2 (Setup + Foundational) together to establish foundation

**Day 1 Afternoon** (3 hours) - Parallel work begins:
- Developer A: Phase 3 (User Story 1 - Email Detection)
- Developer B: Phase 2 completion + prepare Phase 5 MCP stubs (User Story 3 foundation)
- Developer C: Phase 6 (User Story 4 - Categorization, can work independently with mocks)

**Day 2 Morning** (2 hours) - Integration:
- Developer A: Phase 4 (User Story 2 - Approval validation, depends on US1)
- Developer B: Phase 5 (User Story 3 - Execution, now that US1 complete)
- Developer C: Integrate US4 categorizer with US1 gmail_watcher

**Day 2 Afternoon** (2 hours) - Quality:
- Developer A: Phase 7 testing (T043, T044)
- Developer B: Phase 7 testing (T045, T046)
- Developer C: Phase 8 documentation (T051-T055)

**Day 3 Morning** (1 hour) - Final validation:
- All: Run E2E tests, manual validation, final polish

---

## Task Summary

**Total Tasks**: 58
- **Setup (Phase 1)**: 5 tasks
- **Foundational (Phase 2)**: 5 tasks (BLOCKING)
- **User Story 1 (Phase 3)**: 9 tasks - Email Detection 🎯 MVP
- **User Story 2 (Phase 4)**: 5 tasks - Approval Workflow
- **User Story 3 (Phase 5)**: 9 tasks - Email Execution
- **User Story 4 (Phase 6)**: 9 tasks - Priority Categorization
- **Testing (Phase 7)**: 8 tasks
- **Documentation (Phase 8)**: 8 tasks

**Parallel Opportunities**: 18 tasks marked [P] can run in parallel (31% of tasks)

**Independent Test Criteria**:
- **US1**: Send test email → verify action file in Needs_Action/ with correct YAML
- **US2**: Edit action file YAML → verify file moves to Approved/ within 2 seconds
- **US3**: Approve email action → verify Gmail message archived + confirmation file created
- **US4**: Send emails from known/unknown senders → verify correct priority assignment

**Suggested MVP Scope**: Phase 1-3 only (User Story 1) = 19 tasks, ~4 hours, delivers core email detection capability

---

## Notes

- [P] tasks = different files, no dependencies - safe to parallelize
- [Story] label (US1, US2, US3, US4) maps task to specific user story for traceability
- Each user story is independently completable and testable
- No test tasks marked as REQUIRED - tests are comprehensive but optional per SDD guidelines
- User Story 2 reuses existing Bronze Tier infrastructure (status_field_watcher) - validation only
- User Story 4 can be developed in parallel with US2/US3 using mocks
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- OAuth setup (T006) is manual user action - script guides user through browser flow
- Gmail MCP server requires registration in Claude settings (T010) before use
- Known contacts whitelist (T034-T035) provides sample data - users customize for their needs
- Exponential backoff (T016) protects against Gmail API quota exhaustion (10,000 queries/day)
- All NDJSON audit logging follows Bronze Tier format: action_type, actor, target, parameters, result, timestamp
