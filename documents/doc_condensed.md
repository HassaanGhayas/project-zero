# AI Employee: Autonomous Digital FTE

**Concept**: Build an AI agent (hired as an employee) that works 24/7 on personal/business automation.

## Why This Matters

| Metric | Human | Digital FTE |
|--------|-------|-------------|
| Availability | 2,000 hrs/year | 8,760 hrs/year |
| Cost | $4K-8K/month | $500-2K/month |
| Cost per task | ~$5 | ~$0.50 |
| Setup time | 3-6 months | Instant |

**Bottom line**: 85-90% cost reduction at scale.

---

## Architecture

```
Claude Code (Brain)
  ↓
Watchers (Senses) → Detect file/email/message
  ↓
Reasoning (Skills) → Process & decide
  ↓
MCP Servers (Hands) → Execute actions
  ↓
Obsidian Vault (Memory) → Store state
  ↓
Audit Logs (Transparency) → Track everything
```

**Key Components:**
- **Claude Code**: Main reasoning engine (orchestrates via skills)
- **Watchers**: File monitors (Filesystem, Gmail, Status changes, Approved queue)
- **MCP**: External integrations (Gmail API, Browser, etc.)
- **Obsidian**: Local-first knowledge base + action dashboard
- **NDJSON Logs**: Immutable audit trail

---

## Tech Stack

**Language**: Python 3.12+ (lightweight watchers)
**Agent Executor**: Claude Code CLI with Agent Skills
**Knowledge Base**: Obsidian (local markdown)
**APIs**: Google Gmail API, Model Context Protocol
**Package Manager**: `uv` (fast Python installer)
**Testing**: pytest (automated + manual)

---

## Three-Tier Roadmap

### Bronze Tier ✅ COMPLETE
- File monitoring (Inbox/ → Needs_Action/)
- Two-stage approval (Needs_Action/ → Approved/)
- Action execution simulation
- Emergency stop mechanism
- Audit logging
- **Status**: 62/62 tasks done, 87% test coverage

### Silver Tier 🔄 IN PROGRESS
- **Phase 1 MVP**: Gmail integration (email detection, approval, archival)
  - 42/42 implementation tasks ✅
  - 71/93 tests passing (76%)
  - E2E integration validated ✅

- **Phases 2-4**: Categorization, execution, rules
  - Known contacts whitelist
  - Financial keyword detection
  - Priority assignment
  - Email categorization

### Gold Tier 📋 PLANNED
- WhatsApp/Telegram integration
- Calendar/scheduling
- Payment processing
- Advanced analytics

---

## Quick Setup

```bash
# 1. Install dependencies
uv sync

# 2. Configure OAuth2 (Google Cloud Console)
uv run python scripts/setup_gmail_oauth.py

# 3. Start watchers
uv run -m src.watchers.run_all_watchers

# 4. Send test email
# (Email arrives → action file created → approve via Obsidian → archived)
```

See `MANUAL_E2E_TEST_GUIDE.md` for detailed walkthrough.

---

## Constitution: 13 Non-Negotiables

Every agent implementation must:

1. **Emergency Stop** - EMERGENCY_STOP.md halts ALL operations
2. **Human in Loop** - Sensitive actions require approval
3. **Secrets in .env** - Never hardcode credentials
4. **Audit Everything** - NDJSON logs for compliance
5. **Graceful Degradation** - Fail safely, never crash
6. **No Autonomous Send** - Never send messages/money without approval
7. **Token Tracking** - Monitor API usage
8. **Idempotency** - Safe to retry any operation
9. **Rate Limiting** - Exponential backoff on 429 errors
10. **Error Handling** - Structured error responses
11. **Data Retention** - Clear retention policies
12. **Security** - Input validation, no injection
13. **Transparency** - Users understand what agent does

---

## Key Design Decisions

### Why Local-First?
- Privacy: No data leaves your machine
- Speed: Zero network latency
- Cost: No cloud bills
- Control: You own your setup

### Why Watchers?
- Wake agent only when needed (efficient)
- Prevents "lazy agent" problem
- Scales to multiple triggers
- Decoupled from Claude Code

### Why Obsidian?
- Human-readable (markdown)
- Version control friendly (git)
- Plugins ecosystem
- Fast search/navigation
- Works offline

### Why MCP?
- Standard interface for external actions
- Portable across agents
- Composable tools
- Easy to add new capabilities

---

## What Works Today (Silver MVP)

✅ Email detection (120s polling)
✅ Action file creation (YAML frontmatter)
✅ Approval workflow (Obsidian editing)
✅ Email execution (archive via Gmail API)
✅ MCP server (idempotent operations)
✅ Categorization (priority logic, keywords)
✅ Audit logging (NDJSON trail)
✅ OAuth2 (automatic refresh)
✅ Duplicate prevention (message ID tracking)
✅ Rate limiting (exponential backoff)

---

## How to Build Your Own

**Phase 1**: Fork this repo, follow Bronze Tier tutorial
**Phase 2**: Add one watcher (Gmail, WhatsApp, Slack, etc.)
**Phase 3**: Implement approval workflow (status field or button)
**Phase 4**: Create MCP server for execution
**Phase 5**: Add categorization logic (rules, ML, etc.)

Each phase: ~10-20 hours, ~50-100 tasks

---

## Resources

- **MANUAL_E2E_TEST_GUIDE.md** - Test the system
- **CLAUDE.md** - Development rules & commands
- **CONSTITUTION_COMPLIANCE.md** - Requirements checklist
- **specs/001-bronze-fte-foundation/** - Detailed architecture
- **specs/002-gmail-integration/** - Gmail feature spec

---

## Metrics

**Current Implementation**:
- 4 watchers running
- 2 MCP servers
- 15 Python modules
- 73 unit tests
- 71/93 tests passing (76%)
- ~2,000 lines of code

**Next Phase**:
- 5 watchers (add calendar)
- 3 MCP servers (add Slack)
- 10,000 lines of code
- 150+ tests

---

**Start here**: `README_QUICKSTART.md`
**Deep dive**: `documents/doc.md` (full 1200-line version)
**Test it**: `MANUAL_E2E_TEST_GUIDE.md`
