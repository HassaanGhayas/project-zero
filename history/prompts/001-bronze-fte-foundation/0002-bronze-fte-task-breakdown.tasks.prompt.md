---
id: 0002
title: Bronze FTE Task Breakdown
stage: tasks
date: 2026-02-07
surface: agent
model: claude-opus-4-6
feature: 001-bronze-fte-foundation
branch: 001-bronze-fte-foundation
user: hasss
command: /sp.tasks
labels: ["tasks", "bronze-tier", "implementation", "user-stories", "dependencies"]
links:
  spec: specs/001-bronze-fte-foundation/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-bronze-fte-foundation/tasks.md
tests:
  - Phase 8 includes 9 test tasks (T047-T055)
---

## Prompt

Yes, let us begin with the task generation

(User approved proceeding with /sp.tasks after Phase 0 research and Phase 1 design artifacts were completed)

## Response snapshot

Generated comprehensive task breakdown with 62 atomic, dependency-ordered tasks organized by user story priority (P1 → P5):

**Task Organization**:
- **Phase 1: Setup** (6 tasks) - Environment configuration, vault structure verification, dependencies
- **Phase 2: Foundational** (4 tasks) - Core watcher infrastructure (BaseWatcher, utils, logging) that ALL user stories depend on
- **Phase 3: US1 - File Detection (P1)** 🎯 MVP (9 tasks) - FileSystemWatcher implementation, YAML frontmatter, NDJSON logging, emergency stop
- **Phase 4: US2 - Dashboard (P2)** (8 tasks) - update-dashboard skill, vault scanning, red flags detection
- **Phase 5: US5 - Handbook (P5)** (3 tasks) - Company_Handbook.md template with Bronze Tier rules (moved before US3 since US3 reads it)
- **Phase 6: US3 - Inbox Processing (P3)** (10 tasks) - process-inbox skill, auto-approve logic, handbook integration
- **Phase 7: US4 - Status Report (P4)** (6 tasks) - vault-report skill, read-only console output
- **Phase 8: Testing** (9 tasks) - Unit tests, E2E test, edge case validation
- **Phase 9: Documentation** (7 tasks) - README updates, constitution compliance audit

**Key Features**:
- Each task follows strict checklist format: `- [ ] [ID] [P?] [Story?] Description with file path`
- 23 tasks marked [P] for parallel execution (different files, no dependencies)
- Dependency graph showing user story completion order (US1 → US2/US5 → US3 → US4)
- MVP defined as Phase 3 (US1) - demonstrates core perception capability
- Independent test criteria for each user story
- Parallel execution examples per phase
- Constitution compliance verification (13 sections explicitly addressed)

**MVP Deliverables**: File system watcher running, action files created with YAML frontmatter, audit logging, emergency stop mechanism

## Outcome

- ✅ Impact: Complete implementation roadmap. 62 atomic tasks with clear dependencies. Each user story independently testable. MVP scope clearly defined (US1 only).
- 🧪 Tests: 9 test tasks in Phase 8 (unit tests for watcher, action file generator, logger, emergency stop, E2E flow)
- 📁 Files: tasks.md with 9 phases, dependency graph, parallel execution guide
- 🔁 Next prompts: /sp.implement to execute tasks in order, or manual implementation starting with Phase 1-3 (MVP)
- 🧠 Reflection: Task organization by user story enables incremental delivery. US1 (file detection) is truly MVP - proves perception works. US3 (inbox processing) correctly depends on US1, US2, US5. Parallel opportunities identified (23 tasks). Constitution compliance explicitly verified in tasks.

## Evaluation notes (flywheel)

- Failure modes observed: None. Task generation followed user story priorities from spec.md perfectly.
- Graders run and results (PASS/FAIL): Format validation PASS (all 62 tasks follow checklist format with IDs, story labels, file paths), Dependency graph validated (no circular dependencies), MVP scope appropriate (US1 = 9 tasks = 8-12 hours)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Execute MVP tasks (T001-T019) first to prove file detection works, then iterate on remaining user stories based on learnings
