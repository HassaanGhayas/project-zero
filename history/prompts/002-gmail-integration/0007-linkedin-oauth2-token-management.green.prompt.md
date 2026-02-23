---
id: "0007"
title: LinkedIn OAuth2 Token Management
stage: green
date: 2026-02-18
surface: agent
model: claude-sonnet-4-6
feature: 002-gmail-integration
branch: 002-gmail-integration
user: hasss
command: implement Task 1 LinkedIn OAuth2 Token Management
labels: ["linkedin", "oauth2", "token", "tdd", "phase3"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - src/api/linkedin_oauth.py
  - tests/test_linkedin_oauth.py
tests:
  - tests/test_linkedin_oauth.py::test_load_token_returns_dict
  - tests/test_linkedin_oauth.py::test_load_token_raises_if_missing
  - tests/test_linkedin_oauth.py::test_save_token_creates_file
  - tests/test_linkedin_oauth.py::test_is_token_expired_true_for_old_token
  - tests/test_linkedin_oauth.py::test_is_token_expired_false_for_fresh_token
  - tests/test_linkedin_oauth.py::test_refresh_access_token_returns_new_token
---

## Prompt

You are implementing Task 1: LinkedIn OAuth2 Token Management

Files:
- Create: `src/api/linkedin_oauth.py`
- Test: `tests/test_linkedin_oauth.py`

Implement 4 functions (load_token, save_token, is_token_expired, refresh_access_token) following TDD.
Write failing tests first, verify failure, then implement, verify 6 tests pass, commit.

## Response snapshot

TDD cycle completed:

1. Verified `src/api/__init__.py` already exists from Phase 2 WhatsApp work.
2. Wrote 6 tests in `tests/test_linkedin_oauth.py` — confirmed `ModuleNotFoundError` on first run.
3. Implemented `src/api/linkedin_oauth.py` with all 4 typed functions using pathlib.Path and requests.
4. All 6 tests passed on second run.
5. Committed as `feat: add LinkedIn OAuth2 token management` (SHA: e795741).

## Outcome

- Impact: LinkedIn OAuth2 token lifecycle management implemented; foundation for LinkedIn watcher (Task 3) and MCP server (Task 2).
- Tests: 6/6 PASSED (test_load_token_returns_dict, test_load_token_raises_if_missing, test_save_token_creates_file, test_is_token_expired_true_for_old_token, test_is_token_expired_false_for_fresh_token, test_refresh_access_token_returns_new_token)
- Files: Created src/api/linkedin_oauth.py (42 lines) and tests/test_linkedin_oauth.py (43 lines)
- Next prompts: Task 2 (LinkedIn MCP Server), Task 3 (LinkedIn Watcher)
- Reflection: TDD cycle clean; no regressions; no hardcoded secrets; all functions typed.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): pytest 6/6 PASS
- Prompt variant (if applicable): none
- Next experiment: extend refresh_access_token to handle non-200 responses with custom error types
