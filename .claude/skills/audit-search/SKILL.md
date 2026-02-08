---
name: Audit Search
description: Search audit logs (Logs/*.json) for specific actions, errors, or patterns. Use when investigating past actions, debugging issues, or analyzing AI FTE behavior. Trigger when user says "search logs for", "find audit entries", "what actions did we take on", "show me errors from", "audit trail for".
color: blue
---

# Audit Search Skill

Search NDJSON audit logs in `AI_Employee_Vault/Logs/` directory.

## Purpose

Provides queryable access to append-only audit logs. Enables operators to investigate past actions, debug errors, and analyze AI FTE behavior patterns over time.

## Parameters

User can provide any combination of:
- **query**: Text to search (action_type, target filename, error message)
- **date_range**: Optional "YYYY-MM-DD" or "YYYY-MM-DD to YYYY-MM-DD"
- **result_filter**: Optional "success" | "error" | "warning"
- **actor_filter**: Optional actor name (e.g., "process-inbox", "filesystem_watcher")
- **limit**: Optional result limit (default: 10)

## Algorithm

1. **Discover log files**: List all `*.json` files in `AI_Employee_Vault/Logs/`
2. **Filter by date**: If date_range provided, only read matching files
3. **Parse NDJSON**: Read each line as separate JSON object (NDJSON format)
4. **Apply filters**:
   - If query: Match against `action_type`, `target`, `error` fields (case-insensitive)
   - If result_filter: Match `result` field exactly
   - If actor_filter: Match `actor` field exactly
5. **Sort by timestamp**: Descending (newest first)
6. **Return top N**: Default limit 10, user-adjustable

## Output Format

```
📋 Audit Search Results

Query: "{query}"
Date Range: {start} to {end}
Filters: {filters}

Found {count} matching entries:

- [2026-02-08 15:30] file_detected → Inbox/invoice.pdf (success)
  Actor: filesystem_watcher
  Duration: 50ms

- [2026-02-08 15:29] action_file_created → Needs_Action/FILE_invoice.pdf.md (success)
  Actor: filesystem_watcher
  Duration: 120ms

- [2026-02-08 14:45] item_completed → Done/FILE_report.txt.md (success)
  Actor: process-inbox
  Parameters: {"category": "text", "confidence": "high"}
  Duration: 85ms

{If errors found, include error messages}
- [2026-02-08 10:15] inbox_processed → 5 items (error)
  Actor: process-inbox
  Error: Failed to read Company_Handbook.md - file not found
  Duration: 200ms
```

## Example Invocations

**Search for errors**:
```
User: "Search logs for errors in the last 24 hours"
→ Filter: result="error", date_range=today
```

**Find specific file actions**:
```
User: "What actions did we take on invoice.pdf?"
→ Query: "invoice.pdf"
```

**Investigate actor behavior**:
```
User: "Show me all process-inbox actions from yesterday"
→ Actor: "process-inbox", date_range=2026-02-07
```

**Debug emergency stops**:
```
User: "Find audit entries for emergency halt"
→ Query: "emergency", action_type="emergency_halt"
```

## Error Handling

| Error | Handling |
|-------|----------|
| Logs/ directory missing | Return: "No logs found - Logs/ directory does not exist" |
| No matching entries | Return: "No audit entries match your query" |
| Corrupted JSON line | Skip silently, continue processing other lines |
| Invalid date format | Return: "Invalid date format - use YYYY-MM-DD" |

## Constitution Compliance

This skill implements:
- ✅ **Section VII**: Audit logging transparency (provides queryable access to logs)
- ✅ **Section X**: Transparency principles (enables operator investigation)
- ✅ **Section XI**: Human oversight (supports 2-minute daily check workflow)

## Safety Rules

1. **Read-only** - Only reads log files, never modifies them
2. **Append-only logs** - Logs are never edited or deleted by this skill
3. **Graceful degradation** - Skips corrupted entries, continues processing
4. **No data loss** - All operations are non-destructive

## Notes

- This is a **Bronze Tier** skill: File-based log search only
- Log format: NDJSON (one JSON object per line)
- Log files named: `YYYY-MM-DD.json`
- Each log entry has 11 required fields per Entity 4 schema (data-model.md)
- For complex analysis, consider exporting logs and using external tools
