#!/usr/bin/env bash
# scripts/uninstall_cron.sh
# Removes all project-zero cron entries. Idempotent.
set -euo pipefail

MARKER="project-zero"
CURRENT_CRON=$(crontab -l 2>/dev/null || true)
FILTERED=$(echo "$CURRENT_CRON" | grep -v "$MARKER" || true)

if [ "$CURRENT_CRON" = "$FILTERED" ]; then
  echo "No project-zero cron entries found — nothing to remove."
else
  # If nothing remains after filtering, remove the crontab entirely
  STRIPPED=$(echo "$FILTERED" | tr -d '[:space:]')
  if [ -z "$STRIPPED" ]; then
    crontab -r
    echo "Removed all project-zero entries (crontab cleared)."
  else
    echo "$FILTERED" | crontab -
    REMOVED=$(echo "$CURRENT_CRON" | grep -c "$MARKER" || true)
    echo "Removed $REMOVED project-zero cron entry/entries."
  fi
fi
