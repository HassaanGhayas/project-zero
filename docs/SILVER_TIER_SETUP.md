# Silver Tier Setup Guide

This guide covers setting up the Silver Tier AI FTE: Gmail integration, LinkedIn integration,
plan generation, and scheduling & orchestration.

## Prerequisites

- Bronze Tier complete (see `docs/SETUP.md`)
- `.env` configured with all required keys (see `.env.example`)
- `uv sync --all-extras` completed

## 1. Gmail Integration

1. Run OAuth flow: `uv run python src/api/gmail_oauth.py`
2. Token saved to `config/gmail_token.json`
3. Set `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET` in `.env`

## 2. LinkedIn Integration

See `docs/LINKEDIN_SETUP.md` for full OAuth2 flow.

Quick start:
```bash
uv run python src/api/linkedin_oauth.py
```

## 3. Starting Watchers

**With supervisor (recommended — auto-restarts on crash):**
```bash
uv run python -m src.monitors.supervisor
```

**Without supervisor (manual restart):**
```bash
uv run python -m src.watchers.run_all_watchers
```

## 4. Installing Scheduled Tasks

Install cron jobs for daily vault reports and weekly dashboard resets:

```bash
bash scripts/install_cron.sh
```

Verify installation:
```bash
crontab -l | grep project-zero
```

Remove all scheduled tasks:
```bash
bash scripts/uninstall_cron.sh
```

## 5. Schedule Configuration

Edit `config/schedule.yaml` to change timing or add jobs, then re-run `install_cron.sh`.

## 6. Emergency Stop

Touch the emergency stop file to halt all watchers and the supervisor:

```bash
touch AI_Employee_Vault/EMERGENCY_STOP.md
```

Remove it to allow restart:

```bash
rm AI_Employee_Vault/EMERGENCY_STOP.md
uv run python -m src.monitors.supervisor
```

## 7. Health Monitoring

The supervisor writes `AI_Employee_Vault/supervisor_state.json` continuously.
The Dashboard.md includes a "🤖 Process Health" section when this file exists.

Refresh the dashboard:

```bash
# Run the update-dashboard skill via Claude Code
```

## 8. Running Tests

```bash
uv run pytest tests/ -v
```
