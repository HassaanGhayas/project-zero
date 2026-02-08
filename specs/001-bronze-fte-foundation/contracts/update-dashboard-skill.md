# Skill Contract: update-dashboard

**Feature**: Bronze Tier AI FTE Foundation
**Skill Name**: `update-dashboard`
**Purpose**: Regenerate Dashboard.md with current vault state (folder counts, recent activity, red flags)
**Actor**: Claude Code (reasoning layer)
**Invoked By**: Human operator via natural language (e.g., "Update the dashboard", "Refresh dashboard")

---

## Functional Requirements Satisfied

- **FR-009**: Regenerate Dashboard.md by scanning vault folders and logs
- **FR-006**: Display red flags, system status, pending approvals, recent activity, queue counts, errors
- **FR-004**: Log dashboard update action to audit log

---

## Input Contract

### Preconditions

1. **Vault exists**: `AI_Employee_Vault/` directory is accessible
2. **Folders exist**: All workflow folders (Inbox/, Needs_Action/, Plans/, Pending_Approval/, Approved/, Rejected/, In_Progress/, Done/) are present
3. **Logs folder exists**: `Logs/` directory is readable

### Input Parameters

**Natural Language Trigger**:
- "Update the dashboard"
- "Refresh dashboard"
- "Show me the current status"

**Skill discovers inputs** by:
- Counting files in all workflow folders
- Reading today's log file: `Logs/YYYY-MM-DD.json`
- Checking for `EMERGENCY_STOP.md`
- Scanning `Pending_Approval/` for stale items (> 24 hours old)

---

## Processing Logic

### Algorithm

```
1. Get current timestamp (ISO 8601 UTC)

2. Scan vault for red flags:
   - Check if EMERGENCY_STOP.md exists
   - Find items in Pending_Approval/ older than 24 hours
   - Count errors in today's log (result="error")
   - If error count > 5 in last hour: Red flag

3. Determine system status:
   - Check today's log for most recent watcher_started entry
   - If found within last 10 minutes: "Running"
   - Else: "Unknown" or "Stopped"

4. Get pending approvals:
   - List Pending_Approval/*.md files
   - For each file:
     - Parse received timestamp from frontmatter
     - Calculate age (now - received)
     - If age > 1 hour: Include in table

5. Get recent activity (last 24 hours):
   - Read today's log file (NDJSON)
   - Filter entries from last 24 hours
   - Sort by timestamp descending
   - Take first 10 entries
   - Format as bullet list

6. Get queue status:
   - Count files in each folder:
     * Inbox/
     * Needs_Action/
     * Plans/
     * Pending_Approval/
     * In_Progress/
     * Done/ (filter for today only)

7. Get errors (last 24 hours):
   - Filter log entries where result="error"
   - Format as bullet list

8. Generate Dashboard.md markdown:
   - Header with timestamp and status
   - Red Flags section (critical alerts)
   - System Status section
   - Pending Approvals section (table)
   - Recent Activity section (bullet list)
   - Queue Status section (table)
   - Errors section (bullet list)

9. Write Dashboard.md (overwrite existing)

10. Log action to audit log

11. Return summary
```

---

## Output Contract

### Success Response

**Format**: Human-readable confirmation (printed to console)

```
✅ Dashboard updated successfully

📊 Current Status:
- System: Operational
- Inbox: 2 items
- Needs_Action: 5 items
- Pending Approval: 1 item (3 hours old)
- Done (today): 12 items

⚠️  Red Flags: None

Last updated: 2026-02-07T15:30:00Z
```

### Side Effects

1. **File overwritten**: `Dashboard.md` regenerated with current data
2. **Audit log entry created**:
```json
{"timestamp":"2026-02-07T15:30:00Z","action_id":"skill_dash_001","action_type":"dashboard_updated","actor":"update-dashboard","target":"Dashboard.md","parameters":{"total_items":20,"red_flags":0},"approval_status":null,"approved_by":null,"result":"success","error":null,"duration":250}
```

### Dashboard.md Output Format

See data-model.md Entity 3 for full schema. Key sections:

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
| File | Age | Type |
|------|-----|------|
| FILE_contract.pdf.md | 3 hours | document |

---

## Recent Activity (Last 24 Hours)
- [15:29] file_detected → Inbox/invoice.pdf (success)
- [15:29] action_file_created → Needs_Action/FILE_invoice.pdf.md (success)
- [14:23] inbox_processed → processed 5 items (success)

---

## Queue Status
| Folder | Count |
|--------|-------|
| Inbox | 2 |
| Needs_Action | 5 |
| Done (today) | 12 |

---

## Errors (Last 24 Hours)
✅ No errors logged
```

---

## Error Handling

| Error Condition | Handling | User Message | Log Entry |
|-----------------|----------|--------------|-----------|
| Logs/ directory missing | Use empty data, warn | "⚠️  Logs folder missing - showing minimal data" | action_type=error_occurred, result=warning |
| Cannot write Dashboard.md | Abort, report error | "❌ Cannot write Dashboard.md - check permissions" | action_type=error_occurred, result=error |
| Today's log file missing | Show folder counts only | "ℹ️  No log file for today - showing folder counts" | (no error logged) |
| Corrupted log entry | Skip entry, continue | "⚠️  Skipped corrupted log entry" | action_type=error_occurred, result=warning |

---

## Performance Expectations

- **Latency**: < 2 seconds for typical vault (< 1000 total files)
- **Resource usage**: Single scan of each folder (no repeated reads)

---

## Testing Acceptance Criteria

### Test Scenario 1: Normal Operation

**Given**: Vault has 20 files across folders, today's log has 15 entries

**When**: Skill is invoked

**Then**:
- ✅ Dashboard.md regenerated with accurate counts
- ✅ Recent activity shows last 10 log entries
- ✅ No red flags section shows "✅ No critical alerts"
- ✅ Queue status table matches actual file counts

### Test Scenario 2: Emergency Stop Detected

**Given**: EMERGENCY_STOP.md exists in vault root

**When**: Skill is invoked

**Then**:
- ✅ Dashboard shows: Status = "Emergency Stop Active"
- ✅ Red Flags section prominently displays emergency stop alert
- ✅ Dashboard still updates (read-only operation, safe during emergency stop)

### Test Scenario 3: Stale Approvals

**Given**: Pending_Approval/ contains FILE_old.md (48 hours old)

**When**: Skill is invoked

**Then**:
- ✅ Red Flags section shows: "Pending approval overdue: FILE_old.md (48 hours)"
- ✅ Pending Approvals section lists the file with age

---

## Integration Points

### Reads From
- All workflow folders (for file counts)
- `Logs/YYYY-MM-DD.json` (for recent activity and errors)
- `EMERGENCY_STOP.md` (safety check)
- Action files in `Pending_Approval/` (for age calculation)

### Writes To
- `Dashboard.md` (overwrite)
- `Logs/YYYY-MM-DD.json` (append dashboard_updated entry)

### Called By
- `process-inbox` skill (after processing completes)
- Human operator via natural language
- Potentially: Scheduled task (Silver Tier)

---

## Notes

- **Read-only vault scan**: This skill only reads files to generate the dashboard (except writing Dashboard.md itself)
- **Safe during emergency stop**: Unlike process-inbox, this skill CAN run during emergency stop (provides visibility)
- **Idempotent**: Safe to run multiple times (always shows current state)
