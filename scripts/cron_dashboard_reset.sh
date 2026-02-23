#!/usr/bin/env bash
# scripts/cron_dashboard_reset.sh
# Runs weekly dashboard regeneration via cron. Logs output to Logs/cron.log.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/AI_Employee_Vault/Logs/cron.log"

mkdir -p "$(dirname "$LOG_FILE")"

{
  echo "--- $(date -u +%Y-%m-%dT%H:%M:%SZ) dashboard_reset ---"
  cd "$PROJECT_ROOT"
  uv run python -m src.skills.update_dashboard
} >> "$LOG_FILE" 2>&1
