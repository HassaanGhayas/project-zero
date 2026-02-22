#!/usr/bin/env bash
# scripts/install_cron.sh
# Installs cron jobs from config/schedule.yaml. Idempotent.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if ! command -v uv &>/dev/null; then
  echo "ERROR: uv required" >&2
  exit 1
fi

# Parse schedule.yaml and emit cron lines using Python
CRON_LINES=$(cd "$PROJECT_ROOT" && uv run python3 - <<'PYEOF'
import yaml
config = yaml.safe_load(open("config/schedule.yaml"))
import os
project_root = os.getcwd()
for job in config["jobs"]:
    print(f"{job['cron']} cd {project_root} && bash {project_root}/{job['script']} # project-zero:{job['name']}")
PYEOF
)

# Current crontab (ignore error if empty)
CURRENT_CRON=$(crontab -l 2>/dev/null || true)

ADDED=0
while IFS= read -r line; do
  JOB_NAME=$(echo "$line" | grep -oP '(?<=project-zero:)\S+' || true)
  if echo "$CURRENT_CRON" | grep -qF "project-zero:$JOB_NAME"; then
    echo "  [skip] $JOB_NAME already installed"
  else
    CURRENT_CRON="${CURRENT_CRON}"$'\n'"${line}"
    echo "  [add]  $JOB_NAME"
    ADDED=$((ADDED + 1))
  fi
done <<< "$CRON_LINES"

if [ "$ADDED" -gt 0 ]; then
  echo "$CURRENT_CRON" | crontab -
  echo "Installed $ADDED job(s)."
else
  echo "All jobs already installed — nothing changed."
fi
