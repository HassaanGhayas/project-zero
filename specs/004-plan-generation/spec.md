# Feature Specification: Plan Generation Skill

**Feature Branch**: `002-gmail-integration`
**Created**: 2026-02-18
**Status**: Approved
**Phase**: Silver Tier Phase 3

## Overview

A skill that orchestrates the SDD loop (`/sp.specify` → `/sp.plan` → `/sp.tasks`) when a complex inbox item arrives, generating structured artifacts under `specs/<feature>/` and routing a review action file to `Pending_Approval/` for HITL approval.

---

## User Scenarios & Testing

### User Story 1 — Manual Plan Generation (P1)

As a user, I want to run `/generate-plan "task description"` and get a full SDD artifact set generated automatically, so I can start implementation without manually running three separate commands.

**Acceptance Scenarios:**

1. **Given** I run `/generate-plan "Build X"`, **When** the skill executes, **Then** `specs/<slug>/spec.md`, `specs/<slug>/plan.md`, and `specs/<slug>/tasks.md` are created and a review action file appears in `Pending_Approval/`
2. **Given** the feature slug already exists in `specs/`, **When** the skill runs, **Then** it increments the slug (e.g., `build-x-2`) rather than overwriting

### User Story 2 — Auto-Trigger from Complex Action Files (P2)

As a user, I want the plan generation to trigger automatically when a complex inbox item is processed, so I don't have to manually decide when to invoke the SDD loop.

**Acceptance Scenarios:**

1. **Given** an action file has `complexity_score ≥ 3`, **When** inbox processing runs, **Then** `/generate-plan` is invoked automatically with the action file's task description
2. **Given** an action file has `complexity_score < 3`, **When** inbox processing runs, **Then** the normal inbox workflow runs without triggering plan generation

---

## Complexity Scoring Heuristic

Score +1 for each:
- Task description > 200 words
- Mentions an external API or integration
- Contains multiple distinct steps (keywords: "then", "after", "next", "step")
- Involves multiple stakeholders or systems

Score ≥ 3 → trigger plan generation

---

## Constraints

- Skill wraps existing `/sp.specify`, `/sp.plan`, `/sp.tasks` — no re-implementation
- `specs/<feature>/` must follow existing SDD structure exactly
- Review action file must have `type: plan_review` and `status: pending`
- Emergency stop check before creating any files
