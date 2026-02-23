---
id: "0011"
title: LinkedIn Watcher Code Review
stage: green
date: 2026-02-19
surface: agent
model: claude-sonnet-4-6
feature: 002-gmail-integration
branch: 002-gmail-integration
user: hasss
command: code-review
labels: ["code-review","linkedin","watcher","quality"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - src/watchers/linkedin_watcher.py
  - tests/test_linkedin_watcher.py
tests:
  - tests/test_linkedin_watcher.py (7/7 passed)
---

## Prompt

Review code quality for Task 3: LinkedIn Watcher

WHAT_WAS_IMPLEMENTED: LinkedInWatcher extending BaseWatcher. Polls Pending_Approval/ for approved linkedin_post action files, publishes via LinkedInServer, moves to Done/, writes NDJSON audit log. Emergency stop check. Duplicate guard. 7 tests all passing.

PLAN_OR_REQUIREMENTS: Task 3 from /home/hasss/projects/project-zero/docs/plans/2026-02-18-phase3-linkedin-plan-generation.md

BASE_SHA: 33c6a3f
HEAD_SHA: cd2e84a

DESCRIPTION: LinkedIn watcher with approval workflow, audit logging, emergency stop, and duplicate prevention.

Files to review:
- /home/hasss/projects/project-zero/src/watchers/linkedin_watcher.py
- /home/hasss/projects/project-zero/tests/test_linkedin_watcher.py

## Response snapshot

Plan alignment: Faithful to Task 3 spec. The only structural deviation is the addition of a `create_action_file` stub (not in the plan sample) — a justified addition to satisfy the abstract base class contract.

Issues found:

IMPORTANT (4):
1. `_log_audit` does not guard against a missing `Logs/` directory — will raise FileNotFoundError at runtime if directory absent.
2. If `_log_audit` raises after a successful publish, the exception is caught by the outer publish-failure handler, producing a false-failure audit entry and leaving the file in Pending_Approval/ for re-processing — potential duplicate LinkedIn post.
3. `_parse_action_file` uses `str.split("---", 2)` which can truncate frontmatter if the post body contains `---`.
4. `linkedin_server` parameter has no type annotation — violates project constitution and AGENTS.md mandate.

SUGGESTIONS (4):
5. `_is_emergency_stop` duplicates identical logic across all watchers — belongs in BaseWatcher.
6. Audit-log-on-failure path (_log_audit called with "linkedin_post_failed") is not tested.
7. `test_skips_non_linkedin_files` naming is imprecise — it tests the glob boundary, not type filtering.
8. `create_action_file` stub drops the type annotation from the parent signature.

All 7 tests pass. No regressions in the broader suite attributable to this change.

## Outcome

- Impact: Task 3 implementation is functionally correct and plan-aligned. Two actionable reliability issues identified (missing Logs/ guard and audit-failure masking) that could produce duplicate LinkedIn posts under failure conditions in production.
- Tests: 7/7 pass. Audit-on-failure branch not covered.
- Files: src/watchers/linkedin_watcher.py, tests/test_linkedin_watcher.py reviewed.
- Next prompts: Fix Issues 1 and 2 (Logs/ mkdir guard + decouple rename from audit write). Add type annotation for linkedin_server parameter. Add test for audit-on-failure path.
- Reflection: Implementation faithfully follows the plan. The two Important issues are not blockers for the test suite but are production reliability concerns. The missing type annotation is a quick fix. The _parse_action_file issue is systemic across watchers.

## Evaluation notes (flywheel)

- Failure modes observed: Missing directory guard in audit writer; audit failure masking publish outcome.
- Graders run and results (PASS/FAIL): uv run pytest tests/test_linkedin_watcher.py -v — 7 PASSED
- Prompt variant (if applicable): code-review role
- Next experiment: Add _log_audit to a try/except that does not affect file rename; add logs_dir.mkdir guard.
