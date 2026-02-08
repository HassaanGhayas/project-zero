# Approval Workflow Documentation

## Overview

The AI Employee implements a **two-stage confirmation workflow** that ensures human oversight for all automated actions. The system responds to user approvals in real-time (1-2 seconds) while maintaining complete audit trails and graceful rejection handling.

## Workflow Diagram

```
┌──────────┐
│  Inbox/  │  ← User drops files
└────┬─────┘
     │ [Filesystem Watcher detects]
     ▼
┌─────────────────┐
│ Needs_Action/   │  ← Action files with status: pending
│ (pending)       │
└────┬────────────┘
     │ [User edits YAML: status: pending → approved]
     │ [Status Field Watcher detects within 1-2s]
     ▼
┌──────────┐
│Approved/ │  ← Status changed to approved
└────┬─────┘
     │ [Approved Watcher executes immediately]
     ▼
┌───────────────────┐
│ In_Progress/      │  ← Confirmation files awaiting final approval
│ (awaiting confirm)│
└────┬──────────────┘
     │ [User reviews and manually moves to Done/]
     ▼
┌───────┐
│ Done/ │  ← Completed actions
└───────┘

Alternative path (rejection):
┌─────────────────┐
│ Needs_Action/   │
│ (pending)       │
└────┬────────────┘
     │ [User edits YAML: status: pending → rejected]
     │ [Status Field Watcher detects]
     ▼
┌───────────┐
│ Rejected/ │  ← Rejected actions
└───────────┘
```

## Components

### 1. Filesystem Watcher
**File**: `src/watchers/filesystem_watcher.py`
**Monitors**: `Inbox/` folder
**Action**: Creates action files in `Needs_Action/` with YAML frontmatter

### 2. Status Field Watcher
**File**: `src/watchers/status_field_watcher.py`
**Monitors**: `Needs_Action/` folder (file modifications)
**Action**: Detects YAML status changes and moves files accordingly:
- `status: approved` → Move to `Approved/`
- `status: rejected` → Move to `Rejected/`

### 3. Approved Watcher
**File**: `src/watchers/approved_watcher.py`
**Monitors**: `Approved/` folder (new files)
**Action**: Executes actions immediately and creates confirmation sub-actions

## Approval Rules

Based on `AI_Employee_Vault/Company_Handbook.md`:

### File Processing
| File Type | Size Threshold | Auto-Approve | Require Review |
|-----------|---------------|--------------|----------------|
| Text (.txt, .md) | < 1MB | ✅ | ❌ |
| Data (.csv, .json) | < 5MB | ✅ | ❌ |
| Images (.jpg, .png) | < 10MB | ✅ | ❌ |
| Documents (.pdf, .docx) | Any | ❌ | ✅ |
| Unknown types | Any | ❌ | ✅ |

### Email Actions
| Action | Threshold | Auto-Approve | Require Review |
|--------|-----------|--------------|----------------|
| Reply to known contact | < 500 chars | ✅ | ❌ |
| Reply to unknown sender | Any | ❌ | ✅ |
| Bulk send | > 5 recipients | ❌ | ✅ |
| Email with attachments | Any | ❌ | ✅ |

### Payment Actions
| Action | Threshold | Auto-Approve | Require Review |
|--------|-----------|--------------|----------------|
| Recurring to known vendor | < $50 | ✅ | ❌ |
| Recurring to known vendor | ≥ $50 | ❌ | ✅ |
| One-time to known vendor | < $100 | ✅ | ❌ |
| One-time payment | ≥ $100 | ❌ | ✅ |
| International transfer | Any | ❌ | ✅ |

### Social Media Actions
| Action | Condition | Auto-Approve | Require Review |
|--------|-----------|--------------|----------------|
| Scheduled post | Pre-approved in calendar | ✅ | ❌ |
| Reply to DM | Any | ❌ | ✅ |
| Public comment | Any | ❌ | ✅ |
| Posts mentioning money | Any | ❌ | ✅ |

## User Operations

### How to Approve an Action

1. Open action file in Obsidian: `Needs_Action/FILE_xxx.md`

2. Edit the YAML frontmatter status field:
   ```yaml
   ---
   type: text
   original_name: invoice.txt
   status: pending    ← Change this line
   ---
   ```

3. Change to:
   ```yaml
   ---
   type: text
   original_name: invoice.txt
   status: approved   ← New value
   ---
   ```

4. Save the file (Ctrl+S or Cmd+S)

5. **Within 1-2 seconds**, the file will automatically:
   - Move to `Approved/`
   - Execute the action (simulated in Bronze tier)
   - Create a confirmation file in `In_Progress/`

6. Review the confirmation file: `In_Progress/CONFIRM_FILE_xxx.md`

7. If satisfied, manually move confirmation file to `Done/`

### How to Reject an Action

1. Open action file in Obsidian: `Needs_Action/FILE_xxx.md`

2. Edit YAML frontmatter:
   ```yaml
   status: rejected
   ```

3. Save the file

4. **Within 1-2 seconds**, the file will automatically move to `Rejected/`

### How to Review Confirmations

1. Open confirmation file in `In_Progress/`: `CONFIRM_FILE_xxx.md`

2. Review the execution result:
   ```markdown
   ## Execution Result
   
   ✅ Text file 'invoice.txt' processed and archived.
   ```

3. Check the confirmation checklist:
   ```markdown
   - [ ] Review execution result above
   - [ ] Verify action was performed correctly
   - [ ] Move this file to `Done/` to confirm completion
   - [ ] Or move to `Rejected/` if action failed
   ```

4. If satisfied, drag file to `Done/` in Obsidian

5. If not satisfied, drag file to `Rejected/`

## Running the Watchers

### Start All Watchers

```bash
uv run -m src.watchers.run_all_watchers
```

This starts three watchers simultaneously:
- Filesystem Watcher (Inbox → Needs_Action)
- Status Field Watcher (Needs_Action → Approved/Rejected)
- Approved Watcher (Approved → execute → In_Progress)

### Stop Watchers

Press **Ctrl+C** to gracefully stop all watchers.

### View Logs

All operations are logged to: `AI_Employee_Vault/Logs/YYYY-MM-DD.json`

Example log entry:
```json
{
  "timestamp": "2026-02-08T12:07:16Z",
  "action_id": "status_watcher_0001",
  "action_type": "file_moved",
  "actor": "status_field_watcher",
  "target": "Approved/FILE_invoice.txt.md",
  "parameters": {
    "source": "Needs_Action/FILE_invoice.txt.md",
    "destination": "Approved",
    "old_status": "pending",
    "new_status": "approved"
  },
  "approval_status": "approved",
  "approved_by": "human",
  "result": "success",
  "error": null,
  "duration": 15
}
```

## Emergency Stop

To immediately halt all operations:

1. Create file: `AI_Employee_Vault/EMERGENCY_STOP.md`

2. All watchers will detect this within 1-2 seconds and cease operations

3. To resume, delete the `EMERGENCY_STOP.md` file

## Testing

Run the approval workflow test suite:

```bash
uv run pytest tests/test_approval_workflow.py -v
```

Tests cover:
- ✅ End-to-end approval workflow (Inbox → Done)
- ✅ Rejection workflow (Inbox → Rejected)
- ✅ Multiple approvals in sequence
- ✅ Approval rules validation
- ✅ Emergency stop mechanism

## Troubleshooting

### File not moving after status change

**Cause**: Status field watcher not running or YAML syntax error

**Solution**:
1. Check watchers are running: `uv run -m src.watchers.run_all_watchers`
2. Verify YAML frontmatter syntax is valid
3. Check logs: `AI_Employee_Vault/Logs/YYYY-MM-DD.json`

### Confirmation not created

**Cause**: Approved watcher not running

**Solution**:
1. Restart watchers: `uv run -m src.watchers.run_all_watchers`
2. Check for EMERGENCY_STOP.md (remove if present)
3. Review logs for errors

### Duplicate action files

**Cause**: Multiple filesystem watchers running

**Solution**:
1. Stop all watchers (Ctrl+C)
2. Kill any orphaned processes: `ps aux | grep run_watcher`
3. Restart with single orchestrator: `uv run -m src.watchers.run_all_watchers`

## Architecture Decisions

### Why Two-Stage Confirmation?

**Rationale**: Prevents accidental execution of irreversible actions (emails, payments)

**Benefits**:
- User gets immediate feedback (action executed)
- User retains final control (confirm or reject)
- Clear audit trail (execution separate from confirmation)

### Why Real-Time (1-2s)?

**Rationale**: Feels responsive to users, similar to Obsidian sync

**Implementation**: Python watchdog library with file modification events

### Why File-Based Communication?

**Rationale**: Aligns with Obsidian workflow, no database required

**Benefits**:
- Human-readable (markdown + YAML)
- Version-controllable (git-friendly)
- Auditable (NDJSON logs)
- No external dependencies

## Future Enhancements (Silver/Gold Tier)

- **Email MCP**: Real email sending via Gmail API
- **Payment MCP**: Real payment processing via banking APIs
- **Social Media MCP**: Real post scheduling via platform APIs
- **Ralph Loop**: Autonomous multi-step task completion
- **Scheduled Processing**: Cron-based batch processing
- **AI-Powered Categorization**: Claude Code analyzing file contents
