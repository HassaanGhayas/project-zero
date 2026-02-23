---
id: "0013"
title: Complexity Scorer Code Review
stage: green
date: 2026-02-19
surface: agent
model: claude-sonnet-4-6
feature: 002-gmail-integration
branch: 002-gmail-integration
user: hasss
command: code-review (manual invocation)
labels: ["code-review","complexity-scorer","utilities","testing","task-4"]
links:
  spec: specs/003-linkedin-integration/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - src/utils/complexity_scorer.py
  - tests/test_complexity_scorer.py
tests:
  - tests/test_complexity_scorer.py (7 tests, all PASSED)
---

## Prompt

Review code quality for Task 4: Complexity Scorer Utility

WHAT_WAS_IMPLEMENTED: Pure utility function complexity_score(text: str) -> int that scores task descriptions for SDD auto-trigger (score >= 3 = trigger). Four additive criteria: word count, API keywords, step keywords, stakeholder keywords. 7 tests all passing.

PLAN_OR_REQUIREMENTS: Task 4 from /home/hasss/projects/project-zero/docs/plans/2026-02-18-phase3-linkedin-plan-generation.md

BASE_SHA: 5f7093a
HEAD_SHA: 5bb2e3b

DESCRIPTION: Complexity scorer utility — pure function, no side effects, regex-based.

Files to review:
- /home/hasss/projects/project-zero/src/utils/complexity_scorer.py
- /home/hasss/projects/project-zero/tests/test_complexity_scorer.py

## Response snapshot

Full plan alignment confirmed. All three deliverables (src/utils/__init__.py, src/utils/complexity_scorer.py, tests/test_complexity_scorer.py) are present and match the plan exactly. All 7 tests pass.

Issues found:

IMPORTANT - Silent failure on non-string input: text.split() raises AttributeError if None is passed. Since the scorer will be called from a watcher reading YAML frontmatter, a missing description field would become an unhandled exception rather than returning 0. A None guard is needed at the top of the function.

IMPORTANT - Test assertions use >= 1 instead of == 1 for criterion-isolation tests: test_long_text_adds_one, test_api_mention_adds_one, test_multiple_steps_adds_one, test_multiple_stakeholders_adds_one all assert >= 1. The input text in each case contains no other matching keywords, so the score is exactly 1 in each case — but using >= 1 weakens the regression-detection value. Using == 1 would make each test a precise assertion for its specific criterion.

Suggestions:
- Boundary value at exactly 200 words is untested (threshold is > 200 strict).
- _STAKEHOLDER_PATTERN includes very common words (system, service, database) that may over-trigger.
- src/utils/__init__.py could re-export complexity_score for more ergonomic imports.

## Outcome

- Impact: Task 4 implementation is correct and complete; two test-quality issues and one production-robustness gap identified.
- Tests: 7/7 PASSED; no regressions introduced.
- Files: src/utils/complexity_scorer.py (35 lines), tests/test_complexity_scorer.py (35 lines), src/utils/__init__.py (empty).
- Next prompts: Address None guard and test assertion precision before Task 5 integration wires the scorer into the watcher.
- Reflection: Implementation is a clean minimal diff matching the plan. The pure-function constraint and compiled-regex pattern are both correct choices. Test suite covers the happy path well but leaves criterion boundaries imprecise.

## Evaluation notes (flywheel)

- Failure modes observed: Test assertions use >= rather than == for single-criterion tests; None input not guarded.
- Graders run and results (PASS/FAIL): uv run pytest tests/test_complexity_scorer.py -v — 7 PASSED
- Prompt variant (if applicable): null
- Next experiment: Add None guard + change 4 criterion tests from >= 1 to == 1 and verify all still pass.
