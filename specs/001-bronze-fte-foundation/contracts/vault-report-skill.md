# Skill Contract: vault-report

**Feature**: Bronze Tier AI FTE Foundation
**Skill Name**: `vault-report`
**Purpose**: Generate read-only status report of vault state without modifying any files
**Actor**: Claude Code (reasoning layer)
**Invoked By**: Human operator via natural language (e.g., "What's the status?", "Give me a vault report")

---

## Functional Requirements Satisfied

- **FR-010**: Generate read-only vault status report without modifying any files
- **FR-006** (partial): Show queue counts and recent activity (but without writing Dashboard.md)

---

## Input Contract

### Preconditions

1. **Vault exists**: `AI_Employee_Vault/` directory is accessible
2. **Folders exist**: Workflow folders are readable

### Input Parameters

**Natural Language Trigger**:
- "What's the status?"
- "Give me a vault report"
- "Show me what's in the vault"
- "Quick status check"

**Skill discovers inputs** by:
- Counting files in workflow folders
- Reading last 3 entries from today's log
- Checking for `EMERGENCY_STOP.md`

---

## Processing Logic

### Algorithm

```
1. Get current timestamp

2. Quick safety check:
   - If EMERGENCY_STOP.md exists: Report emergency stop condition

3. Count files in key folders:
   - Inbox/
   - Needs_Action/
   - Pending_Approval/
   - Done/ (today only)

4. Read recent activity:
   - Open today's log file
   - Get last 3 entries
   - Format as bullet list

5. Identify alerts:
   - Pending approvals > 0
   - Needs_Action > 10 (backlog building)
   - Errors in last 3 log entries

6. Format report as concise text

7. Print report to console

8. DO NOT write any files
9. DO NOT log this action (read-only operation)
10. Return report text
```

---

## Output Contract

### Success Response

**Format**: Concise text report (printed to console only)

```
📊 AI Employee Vault Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
As of: 2026-02-07 15:45:00 UTC

🟢 Status: Operational

📥 Queue Summary:
  • Inbox: 2 items
  • Needs Action: 5 items
  • Pending Approval: 1 item
  • Done (today): 12 items

🕒 Recent Activity:
  • [15:29] file_detected → Inbox/invoice.pdf
  • [15:29] action_file_created → Needs_Action/FILE_invoice.pdf.md
  • [14:23] inbox_processed → 5 items processed

✅ No critical alerts
```

**Alternative Format (with emergency stop)**:
```
📊 AI Employee Vault Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
As of: 2026-02-07 15:45:00 UTC

🛑 Status: EMERGENCY STOP ACTIVE

⚠️  EMERGENCY_STOP.md detected in vault root
⚠️  All automation is halted

📥 Current State:
  • Inbox: 2 items (not being processed)
  • Needs Action: 5 items (not being processed)
  • Pending Approval: 1 item

To resume: Delete EMERGENCY_STOP.md
```

### Side Effects

**None** - This is a read-only operation:
- ❌ NO files created
- ❌ NO files modified
- ❌ NO files moved
- ❌ NO log entries written
- ✅ Only reads vault state and prints to console

---

## Error Handling

| Error Condition | Handling | User Message |
|-----------------|----------|--------------|
| Vault not found | Report error | "❌ Vault not found at {path}" |
| Logs/ missing | Show folder counts only | "ℹ️  No logs available - showing folder counts" |
| Today's log missing | Skip recent activity | "ℹ️  No activity logged today" |
| Folder not readable | Show "N/A" for that folder | "⚠️  Cannot read {folder} - check permissions" |

**Graceful Degradation**: Always provide partial report with available data, never abort completely.

---

## Performance Expectations

- **Latency**: < 1 second (no file writes, minimal reads)
- **Resource usage**: Read-only scans, no memory-intensive operations

---

## Testing Acceptance Criteria

### Test Scenario 1: Normal Report

**Given**: Vault has files in various folders, today's log has entries

**When**: Skill is invoked

**Then**:
- ✅ Report printed to console
- ✅ Shows accurate folder counts
- ✅ Shows last 3 log entries
- ✅ Status shows "Operational"
- ✅ No files modified in vault (verify with `git status`)

### Test Scenario 2: Emergency Stop Report

**Given**: EMERGENCY_STOP.md exists in vault root

**When**: Skill is invoked

**Then**:
- ✅ Status shows "EMERGENCY STOP ACTIVE"
- ✅ Report prominently displays warning
- ✅ Still shows folder counts (read-only is safe)

### Test Scenario 3: Empty Vault

**Given**: All workflow folders are empty

**When**: Skill is invoked

**Then**:
- ✅ Shows all counts as 0
- ✅ Recent activity shows "No activity logged today"
- ✅ Status shows "Operational"

### Test Scenario 4: Read-Only Verification

**Given**: Vault has files in various states

**When**: Skill is invoked

**Then**:
- ✅ Run `git status` after report
- ✅ Verify no modified/created files in vault
- ✅ Verify no new log entries in Logs/

---

## Integration Points

### Reads From
- `Inbox/` (count only)
- `Needs_Action/` (count only)
- `Pending_Approval/` (count only)
- `Done/` (count today's files only)
- `Logs/YYYY-MM-DD.json` (last 3 entries)
- `EMERGENCY_STOP.md` (existence check)

### Writes To
- **None** (console output only)

### Called By
- Human operator via natural language
- Useful for daily 2-minute status check (constitution Section XI)

---

## Comparison with update-dashboard

| Feature | vault-report | update-dashboard |
|---------|--------------|------------------|
| Modifies files | ❌ No | ✅ Yes (Dashboard.md) |
| Writes logs | ❌ No | ✅ Yes |
| Output format | Console text | Markdown file |
| Use case | Quick check | Persistent summary |
| Safe during emergency | ✅ Yes | ✅ Yes |
| Latency | < 1 sec | < 2 sec |

---

## Notes

- **Daily oversight tool**: This skill supports the constitution's 2-minute daily check requirement
- **Zero side effects**: Can be called repeatedly without affecting vault state
- **Lightweight**: Minimal reads, instant feedback
- **Emergency-safe**: Provides visibility even when automation is halted
