---
name: Vault Report
description: Generate a read-only status report of the AI Employee Vault without modifying any files. Shows queue counts, recent activity, and alerts. Use when user asks "What's the status?", "Give me a vault report", "Show me what's in the vault", or "Quick status check". Always read-only - never writes files or logs.
model: haiku
color: blue
---

# Vault Report Skill

Generate a concise, emoji-formatted console status report of the AI Employee Vault without modifying any files.

## Core Algorithm

### 1. Safety Check (First Priority)
Check if EMERGENCY_STOP.md exists in vault root:
- **If yes**: Return emergency stop report immediately, skip all processing
- **If no**: Continue with normal report

### 2. Get Current Timestamp
`timestamp = current UTC time (ISO 8601: YYYY-MM-DD HH:MM:SS UTC)`
`today_date = YYYY-MM-DD`

### 3. Count Files in Key Folders
```
Inbox/          → count all files
Needs_Action/   → count all files
Pending_Approval/ → count all files
Done/           → count only today's files (by modification date)
```
If folder missing: use 0 (graceful degradation)

### 4. Read Recent Activity (Last 3 Entries)
```
today_log_path = Logs/YYYY-MM-DD.json
IF file exists:
  Parse as NDJSON (one JSON object per line)
  Extract last 3 lines
  For each: timestamp, action_type, target
  Format as: [HH:MM] action_type → target
ELSE:
  "No activity logged today"
```

### 5. Detect Alerts
```
alerts = []

IF pending_approval_count > 0:
  alerts.append("⚠️  Pending approvals: {count} items awaiting review")

IF needs_action_count > 10:
  alerts.append("⚠️  Backlog building: {count} items in Needs_Action")

IF recent_activity contains ERROR:
  alerts.append("⚠️  Errors detected in recent activity")

IF alerts empty: status = "✅ No critical alerts"
ELSE: status = formatted alert list
```

### 6. Determine Status Indicator
```
IF EMERGENCY_STOP.md detected:
  indicator = "🛑 Status: EMERGENCY STOP ACTIVE"
ELSE:
  indicator = "🟢 Status: Operational"
```

### 7. Format Report Output
Combine all sections into structured text report with:
- Header: "📊 AI Employee Vault Status"
- Separator line
- Timestamp
- Status indicator
- Queue summary (counts with emoji bullets)
- Recent activity (last 3 entries)
- Alerts or "No critical alerts"

### 8. Print and Return
```
print(report_text)
DO NOT write any file
DO NOT create log entry
return report_text
```

## Output Examples

### Normal Report
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

### Emergency Stop Report
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

## Error Handling

| Error | Handling |
|-------|----------|
| Vault not found | Print "❌ Vault not found at {path}" and exit gracefully |
| Logs/ missing | Print "ℹ️  No logs available - showing folder counts only" and continue |
| Today's log missing | Print "ℹ️  No activity logged today" and continue |
| Folder not readable | Show "N/A" and note "⚠️  Cannot read {folder} - check permissions" |
| Corrupted log entry | Skip that entry, continue with next |

Always provide partial report with available data - never abort completely.

## Side Effects: STRICTLY ZERO

This skill MUST be completely read-only:
- ❌ NO files created
- ❌ NO files modified
- ❌ NO files moved or deleted
- ❌ NO log entries written
- ❌ NO directories created
- ✅ Console output only

## Example Triggers

<example>
User: "What's the status?"
User: "Give me a vault report"
User: "Show me what's in the vault"
User: "Quick status check"
User: "Vault overview"
User: "What's happening?"
</example>
