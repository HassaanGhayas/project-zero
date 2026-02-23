---
id: "0014"
title: Generate-Plan Skill Implementation
stage: green
date: 2026-02-20
surface: agent
model: claude-sonnet-4-6
feature: 002-gmail-integration
branch: 002-gmail-integration
user: hasss
command: "Task 5: Generate-Plan Skill"
labels: ["skill", "sdd", "generate-plan", "hitl", "automation"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .claude/skills/generate-plan/SKILL.md
tests:
  - "No automated tests — skill files are markdown invoked manually"
---

## Prompt

You are implementing Task 5: Generate-Plan Skill

Files:
- Create: `.claude/skills/generate-plan/SKILL.md`

No automated tests — skill files are markdown invoked manually.

The skill orchestrates the full SDD loop (sp.specify → sp.plan → sp.tasks) for a given task description, then routes a review action file to Pending_Approval/ for HITL approval.

## Response snapshot

Created `.claude/skills/generate-plan/SKILL.md` with:
- YAML frontmatter: name, description (multi-line), color
- Usage instructions with example invocation
- Step-by-step workflow: slugify, SDD loop, write review action file, confirm to user
- Auto-trigger documentation for complexity_score >= 3
- Constitution compliance section (emergency stop, HITL, audit logging)
- Committed as: c9dbb0f feat: add generate-plan skill for SDD auto-loop

## Outcome

- Impact: New skill available in the Claude Code skill registry for orchestrating SDD loops with HITL approval gating
- Tests: No automated tests required; skill is markdown-invoked manually
- Files: .claude/skills/generate-plan/SKILL.md created (82 lines)
- Next prompts: Task 6 (Wire LinkedIn Watcher into Orchestrator), Task 7 (Setup Docs + SDD tasks.md files)
- Reflection: Checked existing skill format across process-inbox, audit-search, and skill-creator before writing to ensure frontmatter and structure consistency

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): file existence verified via ls -la
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null
