#!/usr/bin/env bash
# scripts/cron_vault_report.sh
# Runs daily vault report via cron. Logs output to Logs/cron.log.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/AI_Employee_Vault/Logs/cron.log"

mkdir -p "$(dirname "$LOG_FILE")"

{
  echo "--- $(date -u +%Y-%m-%dT%H:%M:%SZ) vault_report ---"
  cd "$PROJECT_ROOT"
  uv run python -m src.skills.vault_report
} >> "$LOG_FILE" 2>&1
