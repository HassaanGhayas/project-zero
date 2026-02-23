# Implementation Plan: Plan Generation Skill

**Feature**: 004-plan-generation
**Date**: 2026-02-18
**Status**: Approved

---

## Architecture

### Skill Definition

`.claude/skills/generate-plan/SKILL.md` — invocable as `/generate-plan "description"`

The skill:
1. Slugifies the description → feature name
2. Creates `specs/<slug>/` directory
3. Invokes `/sp.specify` with description → `specs/<slug>/spec.md`
4. Invokes `/sp.plan` → `specs/<slug>/plan.md`
5. Invokes `/sp.tasks` → `specs/<slug>/tasks.md`
6. Writes review action file → `Pending_Approval/FILE_plan-<slug>.md`

### Auto-Trigger Integration

In `src/watchers/inbox_watcher.py`, after action file creation:

```python
score = _complexity_score(action_file)
if score >= 3:
    _trigger_plan_generation(action_file.task_description)
```

`_complexity_score()` is a pure function (easily unit-tested).

---

## Skill File Structure

```
.claude/skills/generate-plan/
└── SKILL.md
```

SKILL.md frontmatter:
```yaml
name: generate-plan
description: Orchestrate SDD loop for a task description
color: blue
```

---

## Review Action File Format

```yaml
---
type: plan_review
feature: <slug>
status: pending
complexity_score: <n>
created: <ISO timestamp>
triggered_by: manual | auto
spec_path: specs/<slug>/spec.md
plan_path: specs/<slug>/plan.md
tasks_path: specs/<slug>/tasks.md
---

## Plan Review

Feature: **<slug>**
Generated from: <source description>

Review the artifacts at the paths above and set `status: approved` to proceed with implementation.
```

---

## Components

### `.claude/skills/generate-plan/SKILL.md`

Skill that sequences sp.specify → sp.plan → sp.tasks and writes the review action file.

### `src/utils/complexity_scorer.py`

```python
def complexity_score(text: str) -> int:
    """Score a task description for SDD loop trigger."""
```

Pure function, no side effects, fully unit-testable.

### Inbox Watcher Integration

`src/watchers/inbox_watcher.py` — add post-processing hook:

```python
from src.utils.complexity_scorer import complexity_score

score = complexity_score(action.description)
action.complexity_score = score
if score >= 3:
    invoke_plan_generation(action.description)
```

---

## Testing Strategy

- `tests/test_complexity_scorer.py` — unit tests for all scoring rules
- `tests/test_generate_plan_skill.py` — mock sp.specify/plan/tasks invocations
- Verify correct slug generation, directory creation, action file format
- Emergency stop test coverage mandatory
