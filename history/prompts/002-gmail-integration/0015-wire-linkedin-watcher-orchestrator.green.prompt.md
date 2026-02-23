---
id: "0015"
title: Wire LinkedIn Watcher into Orchestrator
stage: green
date: 2026-02-20
surface: agent
model: claude-sonnet-4-6
feature: 002-gmail-integration
branch: 002-gmail-integration
user: hasss
command: implement Task 6 - Wire LinkedIn Watcher into run_all_watchers.py
labels: ["linkedin", "orchestrator", "watcher", "graceful-degradation", "integration"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - src/watchers/run_all_watchers.py
  - .env.example
tests:
  - tests/ (full suite: 119 passed, 19 pre-existing failures, 0 regressions)
---

## Prompt

You are implementing Task 6: Wire LinkedIn Watcher into run_all_watchers.py

## Task Description

**Files:**
- Modify: `src/watchers/run_all_watchers.py`
- Modify: `.env.example`

**Step 1: Add env vars to `.env.example`**

Read the file first, then add this block after the WhatsApp section:

```bash
# LinkedIn Integration (Silver Tier Phase 3)
# Get Client ID/Secret from https://www.linkedin.com/developers/apps
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_TOKEN_PATH=/home/hasss/.linkedin/token.json
LINKEDIN_CHECK_INTERVAL=60
```

**Step 2: Wire into run_all_watchers.py**

Read the file first. Then make these changes:

1. Add imports near the top (after existing watcher imports)
2. Add LinkedIn watcher initialization after the WhatsApp watcher block wrapped in try/except with `linkedin_watcher_available` flag
3. Add to shutdown handler (inside signal_handler function)
4. Add to start block (after whatsapp_watcher.start())
5. Update the docstring at the top to mention LinkedIn

**Step 3: Run existing tests to confirm no regressions**

**Step 4: Commit**

## Response snapshot

Applied all changes to `src/watchers/run_all_watchers.py` and `.env.example`:

1. `.env.example` — Added 4 LinkedIn env vars (CLIENT_ID, CLIENT_SECRET, TOKEN_PATH, CHECK_INTERVAL) after the WhatsApp block.

2. `run_all_watchers.py`:
   - Module docstring updated: "five" → "six", added entry 6 for LinkedIn Watcher.
   - `main()` docstring updated to list LinkedIn watcher with Silver Tier Phase 3 label.
   - Added imports: `from .linkedin_watcher import LinkedInWatcher` and `from src.mcp.linkedin_server import create_server_from_env`.
   - Added watcher block (#6) with try/except + `linkedin_watcher_available` flag for graceful degradation.
   - Added `if linkedin_watcher_available: linkedin_watcher.stop()` in `signal_handler`.
   - Added `if linkedin_watcher_available: linkedin_watcher.start()` with appropriate log messages in start block.

Test results verified: 119 passed, 19 failed (pre-existing, confirmed via git stash baseline check). Zero regressions introduced.

Commit SHA: 4b5214b

## Outcome

- Impact: LinkedIn watcher is now wired into the master orchestrator with full graceful degradation; the orchestrator continues to function normally when LinkedIn credentials are absent.
- Tests: 119 passed, 19 pre-existing failures (unchanged baseline), 0 regressions.
- Files: src/watchers/run_all_watchers.py (modified), .env.example (modified).
- Next prompts: Task 7 (Setup Docs + SDD tasks.md files), Task 8 (Full Test Suite Run + PHR).
- Reflection: The try/except + availability flag pattern cleanly handles missing credentials without breaking the orchestrator startup sequence.

## Evaluation notes (flywheel)

- Failure modes observed: none introduced
- Graders run and results (PASS/FAIL): uv run pytest tests/ -v --ignore=tests/integration --ignore=tests/manual — PASS (same baseline as pre-change)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add LinkedIn watcher section to workflow description in docstring
