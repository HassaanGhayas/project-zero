---
id: "0023"
title: Update Dashboard Skill Health Section
stage: green
date: 2026-02-22
surface: agent
model: claude-sonnet-4-6
feature: 002-gmail-integration
branch: 002-gmail-integration
user: hasss
command: Task 7 - Update update-dashboard skill for health section
labels: ["skill","dashboard","supervisor","process-health","phase4"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .claude/skills/update-dashboard/SKILL.md
tests:
  - uv run pytest tests/ -v (19 failed pre-existing, 131 passed, 0 regressions)
---

## Prompt

You are implementing Task 7: Update update-dashboard skill for health section.

Modify `.claude/skills/update-dashboard/SKILL.md` to add instructions for reading `supervisor_state.json` and appending a process health table to Dashboard.md.

Steps:
1. Read the current skill file
2. Add health section instructions after the last existing Dashboard section
3. Verify no regressions (uv run pytest tests/ -v)
4. Commit

## Response snapshot

Added two targeted insertions to `/home/hasss/projects/project-zero/.claude/skills/update-dashboard/SKILL.md`:

1. **Step 7.5: Read Supervisor State** — inserted between existing Step 7 (Get Errors) and Step 8 (Generate Dashboard.md). Instructs Claude to read `AI_Employee_Vault/supervisor_state.json` if it exists, parse `status`, `started_at`, `restart_count`, `last_exit_code`, `backoff_seconds`, and map status strings to display emojis. Sets `supervisor_section_available` flag.

2. **Process Health table in Dashboard template** — appended after the `## Errors (Last 24 Hours)` block in the Step 8 markdown template. Includes `## 🤖 Process Health` section with a 4-column table (Component, Status, Since, Restarts). Section is conditionally omitted when `supervisor_section_available` is false.

Verified no regressions: 19 pre-existing failures unchanged, 131 passing unchanged. Committed as `3d1bfe4`.

## Outcome

- Impact: Dashboard skill now surfaces supervisor process health when supervisor_state.json is present; section is silently omitted when supervisor is not running
- Tests: 131 passed, 19 pre-existing failures (unchanged) — no regressions
- Files: .claude/skills/update-dashboard/SKILL.md (36 lines inserted)
- Next prompts: Task 8 - Create Silver Tier setup docs
- Reflection: Minimal-diff approach (two targeted Edit calls) preserved all existing steps and only appended the new step + template section

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): pytest 131 PASS / 19 pre-existing FAIL
- Prompt variant (if applicable): null
- Next experiment: Verify dashboard output visually once supervisor.py is wired and running
