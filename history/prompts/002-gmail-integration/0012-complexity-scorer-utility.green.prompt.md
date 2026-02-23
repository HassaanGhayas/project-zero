---
id: "0012"
title: Complexity Scorer Utility
stage: green
date: 2026-02-19
surface: agent
model: claude-sonnet-4-6
feature: 002-gmail-integration
branch: 002-gmail-integration
user: hasss
command: implement Task 4 Complexity Scorer Utility
labels: ["complexity-scorer","utils","tdd","regex","sdd-auto-trigger"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - src/utils/__init__.py
  - src/utils/complexity_scorer.py
  - tests/test_complexity_scorer.py
tests:
  - tests/test_complexity_scorer.py::test_short_simple_text_scores_zero
  - tests/test_complexity_scorer.py::test_long_text_adds_one
  - tests/test_complexity_scorer.py::test_api_mention_adds_one
  - tests/test_complexity_scorer.py::test_multiple_steps_adds_one
  - tests/test_complexity_scorer.py::test_multiple_stakeholders_adds_one
  - tests/test_complexity_scorer.py::test_complex_task_scores_three_or_more
  - tests/test_complexity_scorer.py::test_api_keyword_case_insensitive
---

## Prompt

You are implementing Task 4: Complexity Scorer Utility

Files:
- Create: src/utils/__init__.py
- Create: src/utils/complexity_scorer.py
- Test: tests/test_complexity_scorer.py

Step 1: Write the failing tests first, run to confirm ModuleNotFoundError.
Step 2: Create src/utils/ package and implementation using regex patterns for
  word count (>200), API keywords, step keywords, and stakeholder keywords.
  Each matching criterion adds 1 to the score (max 4).
Step 3: Verify 7 tests pass.
Step 4: Commit with conventional commit message.

## Response snapshot

Implemented the complexity scorer following TDD:

1. Wrote tests/test_complexity_scorer.py with 7 tests covering: zero score for
   simple text, long text (+1), API mention (+1), multiple steps (+1), multiple
   stakeholders (+1), complex task scoring >=3, and case-insensitive API matching.

2. Confirmed ModuleNotFoundError (red phase).

3. Created src/utils/__init__.py (empty package marker) and
   src/utils/complexity_scorer.py with three compiled regex patterns:
   - _STEP_PATTERN: first|second|third|then|after that|next|step \d+|finally
   - _API_PATTERN: api|webhook|integration|endpoint|sdk|oauth|rest|graphql|mcp
   - _STAKEHOLDER_PATTERN: team|system|service|frontend|backend|database|stakeholder|coordinate

4. complexity_score(text: str) -> int returns 0-4 based on four criteria.

5. All 7 tests passed in 0.04s.

6. Committed as 5bb2e3b.

## Outcome

- Impact: Pure utility module src/utils/complexity_scorer.py added; will be
  used by inbox watcher to auto-trigger SDD loop when score >= 3.
- Tests: 7/7 passed (0.04s)
- Files: src/utils/__init__.py, src/utils/complexity_scorer.py, tests/test_complexity_scorer.py
- Next prompts: Task 5 (Generate-Plan Skill), Task 6 (Wire LinkedIn Watcher into Orchestrator)
- Reflection: TDD cycle was clean; regex patterns handle case-insensitivity and
  word-boundary matching correctly. Pure function with no side effects.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): pytest 7/7 PASS
- Prompt variant (if applicable): none
- Next experiment: consider adding a weight-based scoring approach for more
  granular thresholds in a future refactor
