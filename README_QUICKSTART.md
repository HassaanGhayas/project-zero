# 🚀 AI Employee - Quick Start

**Status**: Silver Tier Phase 1 MVP Complete (42/50 tasks)

## What This Is

AI-powered digital assistant that monitors Gmail, approves emails via Obsidian, and archives automatically. Local-first, no cloud dependencies.

## 5-Minute Setup

```bash
# 1. Clone & install
git clone <repo>
cd project-zero
uv sync

# 2. Create .env
cp .env.example .env
# Edit: VAULT_PATH, GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH

# 3. Setup Gmail OAuth
uv run python scripts/setup_gmail_oauth.py

# 4. Start watchers
uv run -m src.watchers.run_all_watchers
```

## The Workflow

```
Email arrives (Gmail)
  ↓ [120s polling]
Action file created (Needs_Action/)
  ↓ [user edits YAML status in Obsidian]
File moves to Approved/
  ↓ [MCP executes]
Email archived in Gmail
  ↓ [confirmation created]
In_Progress/ → Done/
```

## Key Files

| File | Purpose |
|------|---------|
| `src/watchers/gmail_watcher.py` | Detects emails |
| `src/watchers/status_field_watcher.py` | Approves workflow |
| `src/watchers/approved_watcher.py` | Executes actions |
| `src/mcp/gmail_server.py` | Gmail API interface |
| `config/known_contacts.yaml` | Contact whitelist |
| `.env.example` | Required environment variables |

## Environment Variables

```bash
GMAIL_CREDENTIALS_PATH=/path/to/credentials.json  # OAuth2 file
GMAIL_TOKEN_PATH=/path/to/token.json              # Token storage
GMAIL_CHECK_INTERVAL=120                          # Polling seconds
VAULT_PATH=/path/to/AI_Employee_Vault             # Root directory
```

## Test It

See `MANUAL_E2E_TEST_GUIDE.md` for step-by-step validation.

## Architecture

- **4 Watchers**: Filesystem, Gmail, Status Field, Approved
- **2 MCP Servers**: Playwright (Bronze), Gmail (Silver)
- **Storage**: Local YAML + NDJSON logs
- **Auth**: OAuth2 (refresh automatic)

## Status

✅ **Implemented**: Email detection, approval workflow, MCP execution, categorization
⏳ **Remaining**: Documentation, edge-case testing
📊 **Tests**: 71/93 passing (76%), E2E validated

## Docs

- **MANUAL_E2E_TEST_GUIDE.md** - Complete testing walkthrough
- **documents/doc.md** - Full architecture guide
- **CONSTITUTION_COMPLIANCE.md** - Requirements checklist
- **specs/** - Detailed feature specifications

## Help

```bash
# Check watcher status
tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json

# View sample action file
cat AI_Employee_Vault/Needs_Action/*.md | head -30

# Run tests
uv run pytest tests/ -v

# Re-authenticate Gmail
uv run python scripts/setup_gmail_oauth.py
```

---

**Ready? Run:**
```bash
uv run -m src.watchers.run_all_watchers
```

Then open Obsidian and watch emails flow in!
