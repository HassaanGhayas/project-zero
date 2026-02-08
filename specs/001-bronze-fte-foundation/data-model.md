# Data Model: Bronze Tier AI FTE Foundation

**Feature**: Bronze Tier AI FTE Foundation
**Branch**: `001-bronze-fte-foundation`
**Date**: 2026-02-07
**Purpose**: Define schemas for all entities in the Bronze Tier system

---

## Overview

Bronze Tier uses file-based entities (markdown with YAML frontmatter, JSON logs) for coordination. No database or message queue. All entities stored in `AI_Employee_Vault/` following the constitution's mandated folder structure.

---

## Entity 1: Action File

**Description**: Represents a detected event requiring attention. Created by watchers, processed by skills, moved through workflow folders.

**Storage**: `Needs_Action/*.md` → `Pending_Approval/*.md` or `Done/*.md`

**Lifecycle**: Created (pending) → Processed (in_progress) → Completed (moved to Done/) or Flagged (moved to Pending_Approval/)

### Schema (YAML Frontmatter + Markdown Body)

**Required Fields** (from FR-002):
```yaml
---
type: string                    # Action category: document | text | data | image | email | unknown
original_name: string           # Source filename (e.g., "invoice.pdf")
size: integer                   # File size in bytes
file_type: string               # File extension with dot (e.g., ".pdf", ".txt", ".jpg")
category: string                # Semantic category per FR-003 rules
received: string (ISO 8601)     # Detection timestamp (e.g., "2026-02-07T15:30:00Z")
priority: string                # low | medium | high (derived from category)
status: string                  # pending | in_progress | completed | flagged
---

## File Details
[Human-readable context about the detected file]

## Suggested Actions
- [ ] [Action 1]
- [ ] [Action 2]
```

### Category Rules (FR-003)

| File Extension | type | category | priority |
|----------------|------|----------|----------|
| .doc, .docx, .pdf, .ppt, .pptx | document | document | medium |
| .txt, .md, .rtf | text | text | low |
| .csv, .xlsx, .json, .xml | data | data | medium |
| .jpg, .png, .gif, .svg | image | image | low |
| .eml, .msg | email | email | high |
| (unknown) | unknown | unknown | medium |

### Validation Rules

- **Uniqueness**: Filename must be unique within folder (FR-012: prevent duplicates)
- **Required fields**: All 8 fields must be present and non-empty
- **Timestamp format**: Must be valid ISO 8601 with timezone (Z = UTC)
- **Status transitions**: pending → in_progress → (completed OR flagged)
  - Cannot skip states
  - Cannot revert from completed/flagged to pending

### Example Instance

```yaml
---
type: document
original_name: Q4_Report.pdf
size: 524288
file_type: .pdf
category: document
received: 2026-02-07T14:23:15Z
priority: medium
status: pending
---

## File Details
New document dropped in Inbox/ at 2:23 PM. Appears to be a quarterly report based on filename.

## Suggested Actions
- [ ] Review document content
- [ ] Categorize as business report
- [ ] Move to Done/ after processing
```

---

## Entity 2: Audit Log Entry

**Description**: Structured record of every system action. Immutable append-only log stored in daily NDJSON files.

**Storage**: `Logs/YYYY-MM-DD.json` (one file per day)

**Format**: Newline-Delimited JSON (NDJSON) for append-only writes

### Schema (JSON Object per Line)

**Required Fields** (from Constitution Section VII):
```json
{
  "timestamp": "string (ISO 8601)",     // Action execution time
  "action_id": "string",                // Unique identifier (e.g., "watcher_001", "skill_inbox_042")
  "action_type": "string",              // Action category (see types below)
  "actor": "string",                    // Who/what performed the action
  "target": "string",                   // What was acted upon (file path, folder, etc.)
  "parameters": "object",               // Action-specific data (flexible schema)
  "approval_status": "string | null",   // For HITL actions: approved | rejected | pending | null
  "approved_by": "string | null",       // "human" | "auto" | null
  "result": "string",                   // success | error | warning
  "error": "string | null",             // Error message if result = error
  "duration": "number | null"           // Execution time in milliseconds (optional)
}
```

### Action Types

| action_type | Description | Actor | Target Example |
|-------------|-------------|-------|----------------|
| `file_detected` | New file found in Inbox/ | `filesystem_watcher` | `Inbox/document.pdf` |
| `action_file_created` | Action .md file written | `filesystem_watcher` | `Needs_Action/FILE_001.md` |
| `inbox_processed` | Skill processed pending items | `process-inbox` | `Needs_Action/` |
| `item_completed` | Item moved to Done/ | `process-inbox` | `Done/FILE_001.md` |
| `item_flagged` | Item moved to Pending_Approval/ | `process-inbox` | `Pending_Approval/FILE_001.md` |
| `dashboard_updated` | Dashboard.md regenerated | `update-dashboard` | `Dashboard.md` |
| `report_generated` | Status report created | `vault-report` | `(stdout)` |
| `watcher_started` | Watcher service started | `filesystem_watcher` | `Inbox/` |
| `watcher_stopped` | Watcher service stopped | `filesystem_watcher` | `Inbox/` |
| `emergency_stop` | Emergency stop detected | `filesystem_watcher` | `EMERGENCY_STOP.md` |
| `error_occurred` | General error logged | `*` | `(varies)` |

### Validation Rules

- **Timestamp**: Must be ISO 8601 with timezone
- **action_id**: Must be unique across all logs (format: `{actor}_{sequence}`)
- **result**: Must be one of: success | error | warning
- **Append-only**: Never modify existing entries (immutable log)
- **Daily rotation**: New file created at midnight UTC (manual rotation in Bronze)

### Example Instances

**File Detection**:
```json
{"timestamp":"2026-02-07T14:23:15Z","action_id":"watcher_001","action_type":"file_detected","actor":"filesystem_watcher","target":"Inbox/Q4_Report.pdf","parameters":{"size":524288,"file_type":".pdf"},"approval_status":null,"approved_by":null,"result":"success","error":null,"duration":5}
```

**Action File Creation**:
```json
{"timestamp":"2026-02-07T14:23:16Z","action_id":"watcher_002","action_type":"action_file_created","actor":"filesystem_watcher","target":"Needs_Action/FILE_Q4_Report.pdf.md","parameters":{"source":"Inbox/Q4_Report.pdf","category":"document"},"approval_status":null,"approved_by":null,"result":"success","error":null,"duration":12}
```

**Error Example**:
```json
{"timestamp":"2026-02-07T14:30:00Z","action_id":"watcher_015","action_type":"error_occurred","actor":"filesystem_watcher","target":"Inbox/","parameters":{"error_type":"PermissionError"},"approval_status":null,"approved_by":null,"result":"error","error":"Permission denied: cannot read Inbox/ (check folder permissions)","duration":null}
```

---

## Entity 3: Dashboard

**Description**: Live summary of vault state. Regenerated on demand by `update-dashboard` skill. Human-readable markdown file.

**Storage**: `Dashboard.md` (vault root)

**Update Frequency**: On-demand via skill invocation (not automatically updated)

### Schema (Markdown Document)

**Required Sections** (from FR-006):
```markdown
# AI Employee Dashboard

**Last Updated**: [ISO 8601 timestamp]
**Status**: [Operational | Emergency Stop Active | Errors Detected]

---

## 🚨 Red Flags
[Critical alerts requiring immediate attention]
- EMERGENCY_STOP.md detected
- Pending approvals older than 24 hours
- Error count > 5 in last hour

---

## System Status
- **Watcher**: [Running | Stopped | Unknown]
- **Last Check**: [timestamp]
- **Uptime**: [duration since watcher_started log entry]

---

## Pending Approvals
[Items in Pending_Approval/ older than 1 hour]
| File | Age | Reason |
|------|-----|--------|
| FILE_payment.md | 3 hours | Payment over threshold |

---

## Recent Activity (Last 24 Hours)
[Last 10 log entries with action_type, timestamp, result]
- [14:23] file_detected → Inbox/Q4_Report.pdf (success)
- [14:23] action_file_created → Needs_Action/FILE_Q4_Report.pdf.md (success)

---

## Queue Status
| Folder | Count |
|--------|-------|
| Inbox | 2 |
| Needs_Action | 5 |
| Plans | 0 |
| Pending_Approval | 1 |
| In_Progress | 0 |
| Done (today) | 12 |

---

## Errors (Last 24 Hours)
[Log entries with result = "error"]
- [14:30] error_occurred: Permission denied on Inbox/
```

### Validation Rules

- **Freshness**: "Last Updated" timestamp must be within last 5 minutes to be considered current
- **Red Flags**: Must appear at top of file (above all other sections)
- **Queue counts**: Must match actual file counts in folders
- **Recent activity**: Must be sorted by timestamp descending (newest first)

### Example Instance

```markdown
# AI Employee Dashboard

**Last Updated**: 2026-02-07T15:30:00Z
**Status**: Operational

---

## 🚨 Red Flags
✅ No critical alerts

---

## System Status
- **Watcher**: Running
- **Last Check**: 2026-02-07T15:29:55Z
- **Uptime**: 4 hours 15 minutes

---

## Pending Approvals
No items pending approval.

---

## Recent Activity (Last 24 Hours)
- [15:29] file_detected → Inbox/invoice.pdf (success)
- [15:29] action_file_created → Needs_Action/FILE_invoice.pdf.md (success)
- [14:23] inbox_processed → processed 5 items (success)
- [14:22] item_completed → Done/FILE_Q4_Report.pdf.md (success)

---

## Queue Status
| Folder | Count |
|--------|-------|
| Inbox | 1 |
| Needs_Action | 1 |
| Plans | 0 |
| Pending_Approval | 0 |
| In_Progress | 0 |
| Done (today) | 8 |

---

## Errors (Last 24 Hours)
✅ No errors logged
```

---

## Entity 4: Company Handbook

**Description**: Configuration file defining auto-approve rules, thresholds, and AI behavior policies. Read by skills to guide decision-making.

**Storage**: `Company_Handbook.md` (vault root)

**Update Frequency**: Manual edits by human operator

### Schema (Markdown Document)

**Required Sections** (from FR-007):
```markdown
# Company Handbook

**Version**: 1.0.0
**Last Updated**: [ISO 8601 timestamp]

---

## Communication Rules
[Guidelines for email/message handling]
- Auto-reply to known contacts: [enabled/disabled]
- Flag messages from unknown senders: [yes/no]
- Response tone: [formal | casual | technical]

---

## Auto-Approve Thresholds
[Rules for autonomous action without human approval]

### File Processing
- Text files < 1MB: Auto-process
- Documents (PDF/DOCX): Require review
- Unknown file types: Always flag

### Financial Actions
- Payments < $50 to known vendors: Auto-approve
- Payments ≥ $50 OR new payees: Require approval

---

## Confidence Scoring Rules
[How to assess whether to auto-process or flag]
- High confidence: Clear categorization, known sender, routine action
- Medium confidence: Ambiguous content, first-time sender, unusual request
- Low confidence: Cannot categorize, suspicious content, critical action

---

## Known Contacts
[Whitelist for auto-approve decisions]
- client_a@example.com
- vendor_b@example.com

---

## Opt-Out List
[Contacts requiring human approval for ALL actions]
- important_client@example.com
- legal_team@example.com

---

## Financial Rules
[Payment and accounting thresholds]
- Flag payments > $500
- Flag recurring subscriptions > $100/month
- Auto-log routine expenses < $50

---

## Watcher Rules
[Inbox monitoring behavior]
- Check interval: 5 seconds (event-driven, not used in Bronze)
- Ignore hidden files: Yes
- Ignore temp files (*.tmp): Yes
- Auto-create missing folders: Yes
```

### Validation Rules

- **Version**: Semantic versioning (MAJOR.MINOR.PATCH)
- **Thresholds**: Must be numeric with units ($, MB, seconds)
- **Lists**: Known Contacts and Opt-Out List must not overlap
- **Changes**: Require manual edit + git commit (no programmatic edits)

### Example Instance

```markdown
# Company Handbook

**Version**: 1.0.0
**Last Updated**: 2026-02-07T10:00:00Z

---

## Communication Rules
- Auto-reply to known contacts: disabled (Bronze Tier has no email MCP)
- Flag messages from unknown senders: yes
- Response tone: professional

---

## Auto-Approve Thresholds

### File Processing
- Text files (*.txt, *.md) < 1MB: Auto-process
- Documents (*.pdf, *.docx): Require review
- Unknown file types: Always flag for approval

### Financial Actions
- Payments < $50 to known vendors: Auto-approve (Silver Tier)
- Payments ≥ $50 OR new payees: Require approval (Silver Tier)

---

## Confidence Scoring Rules
- **High confidence**: File type recognized, size < 1MB, common format
- **Medium confidence**: Large file (> 1MB), unusual extension
- **Low confidence**: Corrupted file, invalid frontmatter, permission errors

---

## Known Contacts
(No external contacts in Bronze Tier - file system only)

---

## Opt-Out List
(No external contacts in Bronze Tier - file system only)

---

## Financial Rules
(Deferred to Silver Tier - Bronze has no payment integration)

---

## Watcher Rules
- Check interval: N/A (event-driven Observer pattern)
- Ignore hidden files: Yes
- Ignore temp files (*.tmp, *.swp): Yes
- Auto-create missing folders: Yes
```

---

## Data Flow Diagram

```
┌─────────────────┐
│ Inbox/          │  (User drops file)
│ file.pdf        │
└────────┬────────┘
         │
         │ (Watcher detects on_created event)
         ▼
┌─────────────────────────────────────┐
│ Needs_Action/                       │
│ FILE_file.pdf.md                    │
│ ─────────────────────────           │
│ type: document                      │
│ original_name: file.pdf             │
│ size: 524288                        │
│ status: pending                     │
│ ...                                 │
└────────┬────────────────────────────┘
         │
         │ (process-inbox skill reads)
         ▼
┌─────────────────────────────────────┐
│ Company_Handbook.md                 │  (Check rules)
│ - Document < 1MB? Yes               │
│ - Auto-approve? Yes                 │
└─────────┬───────────────────────────┘
          │
          ▼
     ┌────────┐
     │Decision│
     └───┬────┘
         │
    ┌────┴─────┐
    │          │
    ▼          ▼
┌────────┐  ┌──────────────────┐
│Done/   │  │Pending_Approval/ │
└────────┘  └──────────────────┘
    │
    │ (All actions logged)
    ▼
┌─────────────────────────────┐
│ Logs/2026-02-07.json        │
│ {"timestamp":"..."}         │
│ {"timestamp":"..."}         │
└─────────────────────────────┘
    │
    │ (Dashboard reads logs + folder counts)
    ▼
┌─────────────────────────────┐
│ Dashboard.md                │
│ - Queue Status              │
│ - Recent Activity           │
│ - Red Flags                 │
└─────────────────────────────┘
```

---

## Summary

All entities defined with schemas, validation rules, and examples. No additional entities needed for Bronze Tier scope. Data flow follows constitution's mandated folder structure and file-based coordination pattern.

**Next Step**: Generate skill API contracts in `contracts/` directory.
