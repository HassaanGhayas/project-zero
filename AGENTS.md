# Agent Preferences — AI FTE Project

## Project Capabilities

**AI Full-Time Employee (Bronze Tier)** - Autonomous digital employee that:
- Monitors file drops in Inbox/ and generates structured action files
- Processes documents according to Company_Handbook.md rules
- Routes items automatically (Done/) or for approval (Pending_Approval/)
- Provides real-time visibility via Dashboard and status reports
- Maintains comprehensive audit logs of all actions

## Architecture Pattern

**Perception → Reasoning → Action**
- Watchers detect events (file drops, emails, calendar changes)
- Claude Code reasons via skills (process-inbox, update-dashboard, vault-report)
- Actions execute within vault structure (file moves, status updates, logs)

## Technology Stack

- **Language**: Python 3.12+ (watchdog for file monitoring)
- **Agent Platform**: Claude Code CLI with skills-based reasoning
- **Knowledge Base**: Obsidian vault (markdown files, YAML frontmatter)
- **Logging**: NDJSON append-only audit logs
- **Package Manager**: uv

## Code Style Preferences

### Commits
- **Format**: `<type>: <description>` (e.g., "feat: add emergency stop check")
- **Types**: feat, fix, refactor, test, docs, chore
- **Co-author**: Always include `Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>`

### Python Conventions
- MUST use type hints for function signatures
- MUST use pathlib.Path for file operations (not os.path)
- MUST use logging (not print statements)
- Prefer dataclasses for structured data
- Follow PEP 8 with 88-character line length (Black formatter style)

### Markdown Conventions
- YAML frontmatter for all action files (8 required fields)
- Emoji section headers for readability (🚨, 📊, ✅)
- ISO 8601 timestamps (YYYY-MM-DDTHH:MM:SSZ)
- Keep lines under 100 characters for readability

## Development Workflow

**Spec-Driven Development (SDD)**:
1. Spec first (`/sp.specify`)
2. Plan architecture (`/sp.plan`)
3. Break into tasks (`/sp.tasks`)
4. Implement (`/sp.implement`)
5. Test and validate

## Constitution Compliance

All code MUST comply with 13 constitutional sections:
- Emergency stop mechanism required
- Secrets in .env (never committed)
- Human-in-the-loop for uncertain actions
- Comprehensive audit logging
- 2-minute daily oversight capability

See `.specify/memory/constitution.md` for full requirements.

## Testing Requirements

- Unit tests for all core modules (pytest)
- Emergency stop test coverage mandatory
- E2E bash scripts for workflow validation
- Target: 85%+ test coverage

## Key Commands

```bash
# Start watcher
source .venv/bin/activate
python src/watchers/run_watcher.py

# Run tests
uv run pytest tests/ -v

# Install dependencies
uv sync --all-extras

# Emergency halt
touch AI_Employee_Vault/EMERGENCY_STOP.md
```

## Gotchas

- **File naming**: Action files MUST use `FILE_{original_name}.md` format
- **Log format**: NDJSON only (one JSON object per line, no arrays)
- **Emergency stop**: Check BEFORE every file operation, not after
- **Signal handling**: SIGINT/SIGTERM required for graceful shutdown
- **Duplicate prevention**: Check for existing action files before creating new ones
- **Hidden files**: Ignore files starting with `.` or ending with `.tmp`

## Silver Tier Roadmap

Next phase will add:
- Gmail watcher via MCP
- Calendar integration
- Process management (PM2)
- Enhanced dashboard with charts
