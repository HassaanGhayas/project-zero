# Phase 0 Research: Bronze Tier AI FTE Foundation

**Feature**: Bronze Tier AI FTE Foundation
**Branch**: `001-bronze-fte-foundation`
**Date**: 2026-02-07
**Purpose**: Resolve technical unknowns identified in plan.md before proceeding to Phase 1 design

## Research Overview

This document resolves the 4 research questions identified in plan.md Technical Context section. All decisions are informed by the hackathon blueprint (documents/doc.md) and industry best practices.

---

## Research Task 1: Watchdog Library Best Practices

**Question**: What is the recommended pattern for using Python `watchdog` library for event-driven file monitoring vs polling?

### Investigation

The hackathon document provides three watcher implementation patterns:
1. **Gmail Watcher**: Polling with `check_interval` (BaseWatcher pattern)
2. **WhatsApp Watcher**: Polling with Playwright (30-second intervals)
3. **Filesystem Watcher**: Event-driven using `watchdog.events.FileSystemEventHandler`

For Bronze Tier file system monitoring, the event-driven pattern (Option 3) is superior to polling because:
- **Instant detection**: No latency between file drop and action file creation (vs 5-second polling delay)
- **Zero CPU when idle**: Observer thread sleeps until filesystem events occur
- **Simpler code**: No manual loop management or sleep() calls
- **Proven pattern**: Official watchdog library recommendation for local file monitoring

### Decision

**Use event-driven Observer pattern with FileSystemEventHandler**

**Rationale**:
- Bronze Tier scope is exclusively local file system monitoring (no Gmail/WhatsApp requiring API polling)
- The hackathon doc explicitly demonstrates this pattern for filesystem watchers (lines 353-380)
- Meets FR-001 requirement: "detect additions within one check cycle" — event-driven provides sub-second detection
- Constitution Section VIII requires graceful error handling — Observer pattern provides built-in exception isolation

**Alternatives Considered**:
1. **Polling-based BaseWatcher** (rejected): Adds unnecessary 5-second latency, higher CPU usage, more complex error handling
2. **Hybrid approach** (deferred to Silver): Would make sense for multi-source watchers (Gmail + filesystem) but Bronze has only one source

**Implementation Pattern** (from doc.md lines 353-369):
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DropFolderHandler(FileSystemEventHandler):
    def __init__(self, vault_path: str):
        self.needs_action = Path(vault_path) / 'Needs_Action'

    def on_created(self, event):
        if event.is_directory:
            return
        # Create action file in Needs_Action/
```

**Bronze Tier Adaptation**:
- Extend `FileSystemEventHandler` directly (skip BaseWatcher abstraction for simplicity)
- Implement `on_created()` to create structured markdown action files
- Use `Observer` to watch `Inbox/` folder
- Handle SIGINT/SIGTERM for graceful shutdown per constitution Section VIII

---

## Research Task 2: YAML Frontmatter Standard

**Question**: What is the standard format for YAML frontmatter in markdown files for metadata?

### Investigation

YAML frontmatter is a widely adopted standard across static site generators (Jekyll, Hugo, Eleventy) and Obsidian. The hackathon doc provides three examples:

1. **Email action file** (doc.md lines 294-301):
```yaml
---
type: email
from: User Name
subject: Subject Line
received: 2026-01-07T10:30:00Z
priority: high
status: pending
---
```

2. **Approval request file** (doc.md lines 446-456):
```yaml
---
type: approval_request
action: payment
amount: 500.00
recipient: Client A
reason: Invoice #1234 payment
created: 2026-01-07T10:30:00Z
expires: 2026-01-08T10:30:00Z
status: pending
---
```

3. **File drop action** (doc.md lines 372-377):
```yaml
---
type: file_drop
original_name: document.pdf
size: 2048
---
```

### Decision

**Use YAML frontmatter with triple-dash delimiters and required fields per FR-002**

**Required Fields** (from spec.md FR-002):
- `type`: Action category (document, text, data, image, email, unknown)
- `original_name`: Source filename
- `size`: File size in bytes
- `file_type`: File extension (e.g., ".pdf", ".txt")
- `category`: Semantic category per FR-003 rules
- `received`: ISO 8601 timestamp
- `priority`: low | medium | high (based on category)
- `status`: pending | in_progress | completed | flagged

**Standard Format**:
```yaml
---
type: document
original_name: invoice.pdf
size: 204800
file_type: .pdf
category: document
received: 2026-02-07T15:30:00Z
priority: medium
status: pending
---

## File Details
Detected new file drop for processing.

## Suggested Actions
- [ ] Review content
- [ ] Process or flag for approval
- [ ] Move to Done/ when complete
```

**Rationale**:
- Triple-dash delimiters (`---`) are the universal standard (Jekyll, Hugo, Obsidian)
- ISO 8601 timestamps (`YYYY-MM-DDTHH:MM:SSZ`) ensure unambiguous parsing
- Field names use snake_case per Python conventions
- Frontmatter is pure metadata; body contains human-readable context and suggestions

**Alternatives Considered**:
1. **JSON frontmatter** (rejected): Less human-readable in Obsidian, not standard
2. **TOML frontmatter** (rejected): Not supported by Obsidian
3. **No frontmatter** (rejected): Violates FR-002 structured metadata requirement

**Obsidian Compatibility**: Obsidian natively parses YAML frontmatter and displays it in Properties pane. All fields will be searchable via Dataview queries (Silver Tier feature).

---

## Research Task 3: JSON Audit Log Schema

**Question**: What is the optimal structure for append-only daily JSON log files?

### Investigation

Constitution Section VII mandates:
- Structured log entries with: timestamp, action_id, action_type, actor, target, parameters, approval_status, result, error, duration
- Minimum 90-day retention
- Append-only writes

The hackathon doc provides the required log schema (doc.md lines 687-698):
```json
{
  "timestamp": "2026-01-07T10:30:00Z",
  "action_type": "email_send",
  "actor": "claude_code",
  "target": "client@example.com",
  "parameters": {"subject": "Invoice #123"},
  "approval_status": "approved",
  "approved_by": "human",
  "result": "success"
}
```

Two options for file structure:

**Option A: Single JSON Array**
```json
[
  { "timestamp": "...", "action": "..." },
  { "timestamp": "...", "action": "..." }
]
```
- Pros: Valid JSON, easy to parse entire day
- Cons: Cannot append (requires rewriting entire file), locking issues

**Option B: Newline-Delimited JSON (NDJSON)**
```json
{"timestamp": "...", "action": "..."}
{"timestamp": "...", "action": "..."}
```
- Pros: True append-only (just `file.write(line + '\n')`), no file locking, streaming-friendly
- Cons: Not valid JSON (requires line-by-line parsing)

### Decision

**Use Newline-Delimited JSON (NDJSON) format**

**Rationale**:
- **Append-only requirement**: Constitution Section VII and spec.md FR-004 require append-only logs. JSON array would require reading, modifying, and rewriting the entire file on every action.
- **Concurrency safety**: Bronze Tier has one watcher + skills that may write logs concurrently. NDJSON append is atomic; JSON array modification requires file locking.
- **Performance**: Appending a line is O(1); rewriting an array is O(n) where n = number of log entries per day.
- **Industry standard**: NDJSON is the standard for append-only log systems (Elasticsearch, Logstash, Fluentd).

**File Format**:
```
/Logs/2026-02-07.json  (NDJSON format)
-----
{"timestamp":"2026-02-07T14:00:00Z","action_id":"watcher_001","action_type":"file_detected","actor":"filesystem_watcher","target":"Inbox/invoice.pdf","parameters":{"size":204800},"result":"success"}
{"timestamp":"2026-02-07T14:00:01Z","action_id":"watcher_002","action_type":"action_file_created","actor":"filesystem_watcher","target":"Needs_Action/FILE_invoice.pdf.md","parameters":{"source":"Inbox/invoice.pdf"},"result":"success"}
```

**Alternatives Considered**:
1. **JSON array** (rejected): Violates append-only requirement, requires file locking
2. **SQLite database** (deferred to Silver): Over-engineered for Bronze, violates local-first file-based coordination
3. **Separate file per action** (rejected): Would create thousands of files, harder to query

**Reading NDJSON** (for Dashboard updates):
```python
def read_daily_log(date: str) -> list[dict]:
    log_path = Path(f"Logs/{date}.json")
    if not log_path.exists():
        return []
    with open(log_path) as f:
        return [json.loads(line) for line in f if line.strip()]
```

**90-Day Retention** (constitution requirement):
- Implement log rotation in Silver Tier
- Bronze Tier: Manual cleanup (user responsibility during daily 2-minute check)

---

## Research Task 4: Claude Code Skills Discovery

**Question**: How does Claude Code discover and invoke agent skills from `.claude/skills/`?

### Investigation

From the hackathon doc (line 100):
> "Convert AI functionality into [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)"

Agent Skills are markdown files in `.claude/skills/` with YAML frontmatter. Claude Code automatically discovers and suggests them based on:
1. **Filename**: Should describe the skill's purpose (e.g., `process-inbox.md`, `update-dashboard.md`)
2. **YAML frontmatter**: Contains `name`, `description`, `model`, `color`
3. **Example blocks**: `<example>` tags demonstrate when to trigger the skill

### Decision

**Use Agent Skills with YAML frontmatter and explicit example triggers**

**Standard Skill Structure**:
```markdown
---
name: Process Inbox
description: Process all pending action files in Needs_Action folder
model: opus
color: blue
---

## Instructions

You are processing the AI Employee's inbox. Follow these steps:

1. Read all .md files in Needs_Action/ with status "pending"
2. For each file:
   - Categorize by type (email, document, file_drop, etc.)
   - Check Company_Handbook.md for auto-approve rules
   - If routine: summarize, move to Done/, log action
   - If unclear: create entry in Pending_Approval/, log action
3. Update Dashboard.md with new counts
4. Check for EMERGENCY_STOP.md before every action

<example>
User: "Process my inbox"
User: "Handle all pending items"
User: "Go through the action files"
</example>
```

**Rationale**:
- **Constitution Section IV**: "All AI functionality implemented as skills in `.claude/skills/`"
- **Discoverability**: Claude Code scans `.claude/skills/` on startup and suggests skills based on natural language matching against `description` and `<example>` blocks
- **Explicit triggers**: Examples teach Claude when to invoke the skill vs handling inline
- **Model selection**: `model: opus` ensures skills use the most capable model for reasoning-heavy tasks

**Three Required Skills** (per plan.md):
1. **process-inbox.md**: Handles FR-008 (inbox processing with handbook rules)
2. **update-dashboard.md**: Handles FR-009 (regenerate Dashboard.md from vault state)
3. **vault-report.md**: Handles FR-010 (read-only status report without file modifications)

**Alternatives Considered**:
1. **Inline prompts** (rejected): Violates constitution Section IV mandate for skills
2. **Python scripts called via MCP** (deferred to Silver): Over-engineered for Bronze Tier reasoning tasks
3. **Command aliases** (rejected): Not discoverable or context-aware

**Skill Discovery Flow**:
1. User types: "Process my inbox"
2. Claude Code matches against `<example>` in `process-inbox.md`
3. Claude loads skill instructions and executes with vault context
4. Skill writes audit log entry, updates files, reports completion

---

## Phase 0 Summary

All 4 research questions resolved. No blockers for Phase 1 design.

**Key Decisions**:
1. **Watcher Pattern**: Event-driven Observer with FileSystemEventHandler (instant detection, zero idle CPU)
2. **YAML Frontmatter**: Triple-dash delimiters with 8 required fields per FR-002, Obsidian-compatible
3. **Log Format**: NDJSON (append-only, concurrent-safe, streaming-friendly)
4. **Skills Structure**: YAML frontmatter + example triggers in `.claude/skills/` per constitution Section IV

**Next Steps**: Proceed to Phase 1 to generate:
- `data-model.md`: Action file entity schema, log entry schema, dashboard schema
- `contracts/`: Skill API contracts (inputs, outputs, error handling)
- `quickstart.md`: Setup instructions for first-time users
- Update agent context via `.specify/scripts/bash/update-agent-context.sh`
