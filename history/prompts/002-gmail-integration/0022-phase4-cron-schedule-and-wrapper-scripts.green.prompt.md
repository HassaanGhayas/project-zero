---
id: "0022"
title: Phase 4 Cron Schedule and Wrapper Scripts
stage: green
date: 2026-02-22
surface: agent
model: claude-sonnet-4-6
feature: 002-gmail-integration
branch: 002-gmail-integration
user: hasss
command: implement tasks 4 5 6 phase 4
labels: ["cron", "scheduling", "automation", "phase4", "green"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - config/schedule.yaml
  - scripts/cron_vault_report.sh
  - scripts/cron_dashboard_reset.sh
  - scripts/install_cron.sh
  - scripts/uninstall_cron.sh
tests:
  - "yaml parse check: ['daily_vault_report', 'weekly_dashboard_reset']"
  - "bash -n scripts/cron_vault_report.sh && bash -n scripts/cron_dashboard_reset.sh"
  - "bash -n scripts/install_cron.sh && bash -n scripts/uninstall_cron.sh"
---

## Prompt

You are implementing Tasks 4, 5, and 6 for project-zero Phase 4.

Task 4: Create schedule config — config/schedule.yaml with two cron job definitions.
Task 5: Create cron wrapper scripts — scripts/cron_vault_report.sh and scripts/cron_dashboard_reset.sh.
Task 6: Create install/uninstall cron scripts — scripts/install_cron.sh and scripts/uninstall_cron.sh.

Make three separate commits (one per task), verify each step, and report back with files created, verification outputs, commit SHAs, and any issues found.

## Response snapshot

Implemented all three tasks in order with separate commits:

Task 4: Created config/schedule.yaml with two job definitions (daily_vault_report at 0 8 * * * and weekly_dashboard_reset at 0 9 * * 1). YAML parse check returned ['daily_vault_report', 'weekly_dashboard_reset'] as expected. Committed as 1bdfc39.

Task 5: Created scripts/cron_vault_report.sh and scripts/cron_dashboard_reset.sh. Both use set -euo pipefail, derive PROJECT_ROOT from script location, create Logs/ dir if needed, and append timestamped output to AI_Employee_Vault/Logs/cron.log. Made executable with chmod +x. Bash syntax check passed. Committed as 636efc5.

Task 6: Created scripts/install_cron.sh (idempotent, reads schedule.yaml via Python/yaml, installs only missing entries tagged with project-zero:<name> marker) and scripts/uninstall_cron.sh (removes all project-zero-tagged entries). Made executable. Bash syntax check passed. Committed as c1accd4.

## Outcome

- Impact: Phase 4 scheduling infrastructure in place — cron jobs for daily vault report and weekly dashboard reset can now be installed/uninstalled idempotently via scripts/install_cron.sh and scripts/uninstall_cron.sh, driven by config/schedule.yaml.
- Tests: YAML parse check passed; bash -n syntax checks passed for all four scripts.
- Files: 5 files created across config/ and scripts/.
- Next prompts: Task 7 (update update-dashboard skill), Task 8 (Silver Tier setup docs).
- Reflection: All tasks implemented exactly to spec with no deviations. Scripts directory was created fresh (did not previously exist).

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): YAML parse PASS, bash -n syntax PASS x4
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): run install_cron.sh in a sandbox environment to validate end-to-end crontab installation
