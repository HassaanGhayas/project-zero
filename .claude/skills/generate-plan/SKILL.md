---
name: generate-plan
description: >
  Orchestrate the full SDD loop (sp.specify → sp.plan → sp.tasks) for a given task
  description, then route a review action file to Pending_Approval/ for HITL approval.
color: blue
---

# Generate Plan Skill

Given a task description, this skill:
1. Slugifies the description into a feature name
2. Runs /sp.specify to create specs/<slug>/spec.md
3. Runs /sp.plan to create specs/<slug>/plan.md
4. Runs /sp.tasks to create specs/<slug>/tasks.md
5. Writes a plan review action file to Pending_Approval/

## Usage

```
/generate-plan "Brief description of the task"
```

## Steps

### 1. Slugify the description

Convert the description to a slug: lowercase, spaces → hyphens, strip special chars.
Example: "Build Stripe payment integration" → `build-stripe-payment-integration`

Check if `specs/<slug>/` already exists. If so, append `-2`, `-3`, etc.

### 2. Run SDD loop

Invoke in sequence:
- `/sp.specify` with the task description as input
- `/sp.plan` using the generated spec
- `/sp.tasks` using the generated plan

Each writes to `specs/<slug>/`.

### 3. Write review action file

Create `Pending_Approval/FILE_plan-<slug>.md`:

```yaml
---
type: plan_review
feature: <slug>
status: pending
complexity_score: <n>
created: <ISO timestamp>
triggered_by: manual
spec_path: specs/<slug>/spec.md
plan_path: specs/<slug>/plan.md
tasks_path: specs/<slug>/tasks.md
---

## Plan Review

Feature: **<slug>**

Review the SDD artifacts linked above.
Set `status: approved` to proceed with implementation.
```

### 4. Confirm to user

Report:
- Feature slug created
- Paths to spec/plan/tasks
- Pending_Approval/ action file path

## Auto-Trigger

This skill is also triggered automatically by the inbox watcher when an action file has `complexity_score >= 3`. In that case, `triggered_by` is set to `auto` in the review action file.

## Constitution Compliance

- Emergency stop: Check for EMERGENCY_STOP.md before creating any files
- HITL: All generated plans require status: approved before implementation proceeds
- Audit: Log plan generation to Logs/audit.json
