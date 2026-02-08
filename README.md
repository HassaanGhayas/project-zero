# Project Zero: AI FTE Foundation

**Autonomous Digital Employee powered by Claude Code and Obsidian**

## Overview

Project Zero implements a Bronze Tier AI Full-Time Employee (FTE) that autonomously monitors file drops, processes documents, and maintains an organized vault following the Perception → Reasoning → Action architecture.

## Quick Start

For detailed setup instructions, see **[Quickstart Guide](specs/001-bronze-fte-foundation/quickstart.md)**

### Prerequisites

- Python 3.12+
- Claude Code CLI
- Obsidian 1.10.6+
- Git
- uv (Python package manager)

### Installation (5 minutes)

```bash
# Clone and setup
git clone <repository-url>
cd project-zero
git checkout 001-bronze-fte-foundation

# Install dependencies
uv sync --all-extras

# Configure environment
cp .env.example .env
# Edit .env with your vault path

# Start watcher
source .venv/bin/activate
python src/watchers/run_watcher.py
```

## Architecture

```
┌──────────────┐
│   Inbox/     │ ← User drops files
└──────┬───────┘
       │
       ▼ (Watcher detects)
┌────────────────┐
│ Needs_Action/  │ ← Action files created
└────────┬───────┘
         │
         ▼ (Claude processes)
    ┌────────┐
    │ Done/  │ ← Completed items
    └────────┘
```

## Features

### Bronze Tier (Current)

✅ **Perception Layer**
- File system watcher with event-driven detection
- Structured action files with YAML frontmatter
- Category detection (document, text, data, image, email, unknown)

✅ **Dashboard & Reporting**
- Real-time vault status in Dashboard.md
- Quick console status reports
- Red flag detection and alerts

✅ **AI Processing**
- Inbox processing with handbook rule application
- Auto-approve logic for routine items
- Human-in-the-loop for flagged items

✅ **Governance**
- Company_Handbook.md defines rules and thresholds
- Emergency stop mechanism (EMERGENCY_STOP.md)
- Comprehensive NDJSON audit logging

## Daily Operations

### Start Watcher
```bash
source .venv/bin/activate
python src/watchers/run_watcher.py
```

### Check Status (in Claude Code)
```
"What's the status?"
```

### Process Inbox (in Claude Code)
```
"Process my inbox"
```

### Update Dashboard (in Claude Code)
```
"Update the dashboard"
```

## Documentation

- **[Feature Specification](specs/001-bronze-fte-foundation/spec.md)** - Requirements and user stories
- **[Implementation Plan](specs/001-bronze-fte-foundation/plan.md)** - Architecture and design
- **[Quickstart Guide](specs/001-bronze-fte-foundation/quickstart.md)** - Complete setup walkthrough
- **[Data Model](specs/001-bronze-fte-foundation/data-model.md)** - Entity schemas
- **[Skill Contracts](specs/001-bronze-fte-foundation/contracts/)** - API specifications
- **[Constitution](.specify/memory/constitution.md)** - Governance principles

## Project Structure

```
project-zero/
├── src/                          # Source code
│   └── watchers/                 # File system watchers
├── tests/                        # Test suite
├── .claude/                      # Claude Code configuration
│   └── skills/                   # Agent skills
├── AI_Employee_Vault/            # Obsidian vault
│   ├── Dashboard.md              # Operational dashboard
│   ├── Company_Handbook.md       # Rules engine
│   ├── Inbox/                    # File drop zone
│   ├── Needs_Action/             # Pending items
│   ├── Done/                     # Completed items
│   └── Logs/                     # Audit logs
├── specs/                        # Feature specifications
└── .specify/                     # SDD framework
```

## Constitution Compliance

✅ **Section II**: Vault follows mandated folder structure
✅ **Section IV**: All AI functionality as skills in `.claude/skills/`
✅ **Section V**: Secrets in `.env` (gitignored)
✅ **Section VII**: Structured audit logging
✅ **Section VIII**: Graceful error handling and shutdown
✅ **Section XI**: 2-minute daily check via Dashboard
✅ **Section XII**: Emergency stop mechanism

## Next Steps

### Silver Tier (Planned)
- Gmail watcher via MCP
- Process management (PM2/supervisord)
- Orchestrator for multi-source coordination
- Enhanced dashboard with charts

### Gold Tier (Vision)
- Payment processing integration
- Calendar and meeting management
- Report generation
- Advanced analytics

## Troubleshooting

### Watcher won't start
```bash
# Reinstall dependencies
uv sync --all-extras
```

### Skills not discovered
```bash
# Verify skills directory
ls -la .claude/skills/

# Restart Claude Code
```

### Permission errors
```bash
# Fix vault permissions
chmod -R u+rw AI_Employee_Vault/
```

## Contributing

This project follows Spec-Driven Development (SDD):
1. Feature specs first (`.md` in `specs/`)
2. Implementation plan via `/sp.plan`
3. Task breakdown via `/sp.tasks`
4. Implementation via `/sp.implement`
5. Testing and validation

## License

[Add license information]

## Support

- **Issues**: File in repository issue tracker
- **Documentation**: See `specs/001-bronze-fte-foundation/`
- **Logs**: Check `AI_Employee_Vault/Logs/` for debugging
