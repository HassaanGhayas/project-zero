---
name: Update Dashboard
description: Regenerate Dashboard.md with current vault state including folder counts, recent activity, red flags, and system status. Use when the user says "Update the dashboard", "Refresh dashboard", "Show me the current status", or after completing inbox processing. This skill scans all vault workflow folders, reads today's audit log, checks for emergency stop conditions, identifies stale approvals, and produces a comprehensive markdown dashboard in AI_Employee_Vault/Dashboard.md.
model: opus
color: green
---

# Update Dashboard Skill

Regenerate `AI_Employee_Vault/Dashboard.md` with current vault state. This skill is safe to run during emergency stop (provides visibility). It is idempotent and can be run multiple times.

## Prerequisites

Before executing, verify:

1. `AI_Employee_Vault/` directory exists and is accessible
2. All workflow folders exist: `Inbox/`, `Needs_Action/`, `Plans/`, `Pending_Approval/`, `Approved/`, `Rejected/`, `In_Progress/`, `Done/`
3. `Logs/` directory exists (if missing, proceed with empty data and warn)

## Execution Steps

Follow these steps in exact order.

### Step 1: Get Current Timestamp

Generate an ISO 8601 UTC timestamp for the dashboard header (e.g., `2026-02-07T15:30:00Z`).

### Step 2: Scan for Red Flags

Check ALL of the following conditions. Collect each detected flag into a list:

1. **Emergency Stop**: Check if `AI_Employee_Vault/EMERGENCY_STOP.md` exists. If yes, add red flag: `EMERGENCY_STOP.md is active -- all autonomous operations halted`
2. **Stale Approvals**: List all `.md` files in `AI_Employee_Vault/Pending_Approval/`. For each file, read the YAML frontmatter and parse the `received` timestamp. If the item is older than 24 hours, add red flag: `Pending approval overdue: {filename} ({age} hours)`
3. **Error Spike**: Read today's log file `AI_Employee_Vault/Logs/YYYY-MM-DD.json` (NDJSON format, one JSON object per line). Count entries where `result` equals `"error"` and `timestamp` is within the last hour. If count > 5, add red flag: `High error rate: {count} errors in the last hour`

### Step 3: Determine System Status

Read today's log file. Search for the most recent entry where `action_type` equals `"watcher_started"`.

- If found and its timestamp is within the last 10 minutes: **Watcher status = "Running"**, record the timestamp as "Last Check", and compute uptime from the `watcher_started` timestamp to now
- If found but older than 10 minutes: **Watcher status = "Unknown"**, note last known start time
- If not found: **Watcher status = "Stopped"**

Determine overall status:

- If `EMERGENCY_STOP.md` exists: **"Emergency Stop Active"**
- If error red flags were found: **"Errors Detected"**
- Otherwise: **"Operational"**

### Step 4: Get Pending Approvals

List all `.md` files in `AI_Employee_Vault/Pending_Approval/`. For each file:

1. Read YAML frontmatter (content between `---` delimiters at top of file)
2. Parse the `received` timestamp field
3. Calculate age = now - received
4. If age > 1 hour, include in the Pending Approvals table with columns: File, Age, Type (from `type` field in frontmatter)

If no items older than 1 hour, display: `No items pending approval.`

### Step 5: Get Recent Activity

Read today's log file (`AI_Employee_Vault/Logs/YYYY-MM-DD.json`). Each line is a separate JSON object (NDJSON format).

1. Parse all entries from the last 24 hours
2. Sort by `timestamp` descending (newest first)
3. Take the first 10 entries
4. Format each as: `- [{HH:MM}] {action_type} -> {target} ({result})`

If no log file exists for today, display: `No activity logged today.`

If a log line is corrupted (invalid JSON), skip it silently and continue processing remaining lines.

### Step 6: Get Queue Status

Count files in each workflow folder (exclude hidden files starting with `.`):

| Folder | Path |
|--------|------|
| Inbox | `AI_Employee_Vault/Inbox/` |
| Needs_Action | `AI_Employee_Vault/Needs_Action/` |
| Plans | `AI_Employee_Vault/Plans/` |
| Pending_Approval | `AI_Employee_Vault/Pending_Approval/` |
| In_Progress | `AI_Employee_Vault/In_Progress/` |
| Done (today) | `AI_Employee_Vault/Done/` -- only count files modified today |

### Step 7: Get Errors

From today's log file, filter entries where `result` equals `"error"` in the last 24 hours. Format each as:

`- [{HH:MM}] {action_type}: {error}`

If no errors found, display: `No errors logged`

### Step 7.5: Read Supervisor State

Read `AI_Employee_Vault/supervisor_state.json` if it exists.

If it exists, parse the following fields:
- `status` (string): current supervisor status
- `started_at` (ISO timestamp): when the supervisor last started
- `restart_count` (int): number of restarts since last start
- `last_exit_code` (int or null): exit code of last subprocess exit
- `backoff_seconds` (int or null): current backoff delay

Map `status` to a display emoji:
- `running` → `✅ Running`
- `restarting` → `🔄 Restarting`
- `halted` → `🚨 HALTED (emergency stop)`
- `stopped` → `⏹ Stopped`
- any other value → `❓ Unknown`

If `supervisor_state.json` does not exist, skip this section entirely (supervisor not running or never started). Set a flag `supervisor_section_available = false`.

### Step 8: Generate Dashboard.md

Write the following markdown to `AI_Employee_Vault/Dashboard.md` (overwrite existing content completely):

```markdown
# AI Employee Dashboard

**Last Updated**: {timestamp}
**Status**: {overall_status}

---

## 🚨 Red Flags
{red_flags_content_or "✅ No critical alerts"}

---

## System Status
- **Watcher**: {watcher_status}
- **Last Check**: {last_check_timestamp}
- **Uptime**: {uptime_duration}

---

## Pending Approvals
{pending_approvals_table_or_message}

---

## Recent Activity (Last 24 Hours)
{recent_activity_list}

---

## Queue Status
| Folder | Count |
|--------|-------|
| Inbox | {inbox_count} |
| Needs_Action | {needs_action_count} |
| Plans | {plans_count} |
| Pending_Approval | {pending_approval_count} |
| In_Progress | {in_progress_count} |
| Done (today) | {done_today_count} |

---

## Errors (Last 24 Hours)
{errors_list}

---

## 🤖 Process Health

{process_health_table_or_omit}
```

If `supervisor_section_available` is true, replace `{process_health_table_or_omit}` with:

```markdown
| Component  | Status         | Since                | Restarts |
|------------|----------------|----------------------|----------|
| Supervisor | {status_emoji} | {started_at}         | {restart_count} |
```

If `supervisor_section_available` is false, omit the entire `## 🤖 Process Health` section from the output.

### Step 9: Log Dashboard Update

Append a single NDJSON line to `AI_Employee_Vault/Logs/YYYY-MM-DD.json`:

```json
{"timestamp":"{current_iso_timestamp}","action_id":"skill_dash_{sequence}","action_type":"dashboard_updated","actor":"update-dashboard","target":"Dashboard.md","parameters":{"total_items":{sum},"red_flags":{count}},"approval_status":null,"approved_by":null,"result":"success","error":null,"duration":{ms}}
```

### Step 10: Print Summary

Print confirmation to console showing system status, queue counts, red flags, and last updated timestamp.

## Error Handling

| Error Condition | Handling | User Message |
|-----------------|----------|--------------|
| Logs/ directory missing | Use empty data, warn | "Logs folder missing - showing minimal data" |
| Cannot write Dashboard.md | Abort, report error | "Cannot write Dashboard.md - check permissions" |
| Today's log file missing | Show folder counts only | "No log file for today - showing folder counts" |
| Corrupted log entry | Skip entry, continue | "Skipped corrupted log entry" |

## Example Triggers

<example>
User: "Update the dashboard"
User: "Refresh dashboard"
User: "Show me the current status"
User: "Regenerate the dashboard"
</example>

## Constitution Compliance

This skill implements:
- ✅ **Section IV**: Skills-based AI functionality (Claude Code skill in .claude/skills/)
- ✅ **Section VII**: Comprehensive audit logging (Step 9 logs dashboard_updated to NDJSON)
- ✅ **Section XI**: Human Oversight & Accountability (enables 2-minute daily operator check)
- ✅ **Section XII**: HITL enforcement (detects EMERGENCY_STOP.md and stale approvals)

## Safety Rules

1. **Read-only vault scanning** - Only reads workflow folders and logs; writes only to Dashboard.md and Logs/
2. **Safe during emergency stop** - This skill is explicitly allowed to run during emergency stop (provides visibility)
3. **No data loss** - Dashboard.md is overwritten atomically; no other files are modified or deleted
4. **Idempotent** - Safe to run multiple times; each run produces a fresh snapshot of current state

## Notes

- This is a **Bronze Tier** skill: File-based vault scanning only, no external APIs
- Dashboard output follows Entity 3 schema from data-model.md
- All timestamps use ISO 8601 UTC format for consistency
- Corrupted log entries are skipped silently to ensure dashboard always renders
