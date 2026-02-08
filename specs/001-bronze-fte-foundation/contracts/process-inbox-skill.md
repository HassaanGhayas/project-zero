# Skill Contract: process-inbox

**Feature**: Bronze Tier AI FTE Foundation
**Skill Name**: `process-inbox`
**Purpose**: Process all pending action files in Needs_Action/ according to Company_Handbook.md rules
**Actor**: Claude Code (reasoning layer)
**Invoked By**: Human operator via natural language (e.g., "Process my inbox", "Handle pending items")

---

## Functional Requirements Satisfied

- **FR-008**: Process Needs_Action/ items, categorize, apply handbook rules, move to Done/ or Pending_Approval/
- **FR-005**: Check for EMERGENCY_STOP.md before processing
- **FR-009**: Update Dashboard.md after processing completes
- **FR-004**: Log all actions to daily audit log

---

## Input Contract

### Preconditions

1. **Vault exists**: `AI_Employee_Vault/` directory is accessible
2. **Folders exist**: `Needs_Action/`, `Done/`, `Pending_Approval/`, `Logs/` are present
3. **Handbook exists**: `Company_Handbook.md` is readable with valid rules
4. **No emergency stop**: `EMERGENCY_STOP.md` does NOT exist in vault root

### Input Parameters

**Natural Language Trigger** (no structured parameters):
- User says: "Process my inbox"
- User says: "Go through pending items"
- User says: "Handle the action files"
- User says: "Check what needs attention"

**Skill discovers inputs** by reading:
- `Needs_Action/*.md` files with `status: pending`
- `Company_Handbook.md` for auto-approve rules

### Input Validation

```python
def validate_preconditions():
    """Validate environment before processing"""
    errors = []

    # Check vault path
    if not Path(VAULT_PATH).exists():
        errors.append("Vault not found at {VAULT_PATH}")

    # Check required folders
    for folder in ["Needs_Action", "Done", "Pending_Approval", "Logs"]:
        if not (Path(VAULT_PATH) / folder).exists():
            errors.append(f"Required folder missing: {folder}")

    # Check handbook
    handbook_path = Path(VAULT_PATH) / "Company_Handbook.md"
    if not handbook_path.exists():
        errors.append("Company_Handbook.md not found")

    # Check emergency stop
    if (Path(VAULT_PATH) / "EMERGENCY_STOP.md").exists():
        errors.append("EMERGENCY_STOP.md detected - halting operations")

    return errors
```

---

## Processing Logic

### Algorithm

```
1. Validate preconditions (abort if any fail)

2. Read Company_Handbook.md to load rules

3. Discover pending items:
   - List all *.md files in Needs_Action/
   - Filter for status: pending in YAML frontmatter
   - If zero pending items: report "No items to process" and exit

4. For each pending item:
   a. Read YAML frontmatter + markdown body
   b. Extract: type, category, size, original_name
   c. Apply auto-approve rules from handbook:
      - Check file size thresholds
      - Check category rules
      - Calculate confidence score (high/medium/low)
   d. Make decision:
      - IF confidence == high AND within thresholds:
          * Summarize item
          * Move to Done/
          * Log: action_type=item_completed, result=success
      - ELSE:
          * Create reasoning note (why flagged)
          * Move to Pending_Approval/
          * Log: action_type=item_flagged, result=success
   e. Update file frontmatter: status → completed OR flagged

5. Generate processing summary:
   - Total items processed: N
   - Auto-completed: X
   - Flagged for approval: Y
   - Errors: Z

6. Update Dashboard.md with new folder counts

7. Return summary to user
```

### Auto-Approve Decision Tree

```
Rule Evaluation (from Company_Handbook.md):

IF file_type in [".txt", ".md"] AND size < 1MB:
    → Auto-process (High confidence)

ELSE IF file_type in [".pdf", ".docx", ".ppt"]:
    → Flag for review (Medium confidence)

ELSE IF file_type == "unknown" OR category == "unknown":
    → Flag for approval (Low confidence)

ELSE IF file has invalid/missing frontmatter:
    → Flag for approval (Low confidence, data integrity issue)

ELSE:
    → Apply default: Flag for review (Medium confidence)
```

---

## Output Contract

### Success Response

**Format**: Human-readable summary (printed to console)

```
✅ Inbox processing complete

📊 Summary:
- Total items processed: 5
- Auto-completed: 3
- Flagged for approval: 2
- Errors: 0

✅ Completed (moved to Done/):
  - FILE_meeting_notes.txt.md (text file, 12 KB)
  - FILE_readme.md.md (text file, 4 KB)
  - FILE_status_update.txt.md (text file, 8 KB)

⚠️  Flagged for Approval (moved to Pending_Approval/):
  - FILE_contract.pdf.md (document requires review)
  - FILE_unknown_data.xyz.md (unknown file type)

📋 Dashboard updated with current queue status
```

### Side Effects (File System Changes)

1. **Files moved**:
   - `Needs_Action/*.md` → `Done/*.md` (auto-completed items)
   - `Needs_Action/*.md` → `Pending_Approval/*.md` (flagged items)

2. **Frontmatter updated** (in moved files):
   - `status: pending` → `status: completed` (Done/)
   - `status: pending` → `status: flagged` (Pending_Approval/)

3. **Audit log entries created** (`Logs/YYYY-MM-DD.json`):
```json
{"timestamp":"2026-02-07T15:45:00Z","action_id":"skill_inbox_001","action_type":"inbox_processed","actor":"process-inbox","target":"Needs_Action/","parameters":{"total":5,"completed":3,"flagged":2},"approval_status":null,"approved_by":"auto","result":"success","error":null,"duration":1250}
{"timestamp":"2026-02-07T15:45:00Z","action_id":"skill_inbox_002","action_type":"item_completed","actor":"process-inbox","target":"Done/FILE_meeting_notes.txt.md","parameters":{"source":"Needs_Action/FILE_meeting_notes.txt.md","category":"text","confidence":"high"},"approval_status":"approved","approved_by":"auto","result":"success","error":null,"duration":50}
```

4. **Dashboard.md updated**: Queue counts refreshed to reflect new state

---

## Error Handling

### Error Scenarios

| Error Condition | Handling | User-Facing Message | Log Entry |
|-----------------|----------|---------------------|-----------|
| EMERGENCY_STOP.md detected | Abort immediately, log | "🛑 Emergency stop active - operations halted" | action_type=emergency_stop, result=warning |
| No pending items | Skip processing, report | "ℹ️  No pending items in inbox" | (no log entry) |
| Invalid frontmatter | Flag item, continue | "⚠️  FILE_X has invalid metadata - flagged for review" | action_type=error_occurred, result=warning |
| Permission denied on file | Skip file, continue | "❌ Cannot access FILE_X - check permissions" | action_type=error_occurred, result=error |
| Company_Handbook.md missing | Use default rules, warn | "⚠️  Handbook missing - using conservative defaults" | action_type=error_occurred, result=warning |
| Cannot write to Done/ | Abort processing | "❌ Cannot move files to Done/ - check folder permissions" | action_type=error_occurred, result=error |

### Graceful Degradation

**If Company_Handbook.md is missing or unreadable**:
- Apply conservative defaults: Flag ALL items for approval
- Log warning
- Notify user: "Using conservative defaults - all items flagged for review"

**If Dashboard.md update fails**:
- Continue processing (don't block)
- Log error
- Notify user: "⚠️  Dashboard update failed (see logs)"

---

## Performance Expectations

- **Latency**: Process N items in < 5 seconds + 100ms per item
  - Example: 10 items = < 6 seconds total
- **Throughput**: Handle up to 100 pending items per invocation
- **Resource usage**: Read entire Needs_Action/ folder in single scan (no repeated reads)

---

## Security & Safety

### Safety Checks

1. **Pre-flight validation**: MUST check for EMERGENCY_STOP.md before ANY file operations
2. **Atomic moves**: Use `shutil.move()` (atomic operation) to prevent partial moves
3. **No file deletion**: Never delete action files — only move them
4. **Idempotency**: Safe to run multiple times (already-completed items have status != pending)

### Audit Trail

**Every action MUST be logged** with:
- Timestamp
- Unique action_id
- What was processed (target file path)
- Decision made (auto-complete vs flag)
- Confidence level
- Result (success/error/warning)

---

## Testing Acceptance Criteria

### Test Scenario 1: Happy Path (Auto-Process)

**Given**:
- Needs_Action/ contains: `FILE_notes.txt.md` (status: pending, size: 5KB, type: text)
- Company_Handbook.md: "Text files < 1MB: Auto-process"

**When**: Skill is invoked

**Then**:
- ✅ File moved to Done/FILE_notes.txt.md
- ✅ Frontmatter updated: status → completed
- ✅ Log entry created: action_type=item_completed, result=success
- ✅ Dashboard.md updated
- ✅ User sees summary: "1 item auto-completed"

### Test Scenario 2: Flag for Approval

**Given**:
- Needs_Action/ contains: `FILE_contract.pdf.md` (status: pending, type: document)
- Company_Handbook.md: "Documents: Require review"

**When**: Skill is invoked

**Then**:
- ✅ File moved to Pending_Approval/FILE_contract.pdf.md
- ✅ Frontmatter updated: status → flagged
- ✅ Log entry created: action_type=item_flagged, result=success
- ✅ Dashboard.md updated
- ✅ User sees summary: "1 item flagged for approval"

### Test Scenario 3: Emergency Stop

**Given**:
- EMERGENCY_STOP.md exists in vault root
- Needs_Action/ contains 5 pending items

**When**: Skill is invoked

**Then**:
- ✅ No files moved
- ✅ User sees: "🛑 Emergency stop active - operations halted"
- ✅ Log entry created: action_type=emergency_stop, result=warning
- ✅ Processing aborted immediately

### Test Scenario 4: Mixed Batch

**Given**:
- Needs_Action/ contains:
  - 2 text files (< 1MB each)
  - 1 PDF document
  - 1 unknown file type (.xyz)

**When**: Skill is invoked

**Then**:
- ✅ 2 text files → Done/
- ✅ 1 PDF + 1 unknown → Pending_Approval/
- ✅ 4 log entries (1 inbox_processed + 2 item_completed + 1 item_flagged)
- ✅ Dashboard updated
- ✅ Summary shows: "2 completed, 2 flagged"

---

## Integration Points

### Reads From

- `Needs_Action/*.md` (action files)
- `Company_Handbook.md` (rules)
- `EMERGENCY_STOP.md` (safety check)

### Writes To

- `Done/*.md` (completed items)
- `Pending_Approval/*.md` (flagged items)
- `Logs/YYYY-MM-DD.json` (audit trail)
- `Dashboard.md` (queue counts)

### Depends On

- `update-dashboard` skill (called after processing to refresh counts)

### Called By

- Human operator via natural language trigger
- Potentially: Orchestrator cron job (Silver Tier)

---

## Future Enhancements (Silver Tier)

- **Automatic triggering**: Orchestrator invokes skill when Needs_Action/ count > threshold
- **Batch size limits**: Process max N items per invocation, leave rest for next cycle
- **Priority sorting**: Process high-priority items first
- **Confidence tuning**: Machine learning model for confidence scoring
- **External integrations**: Call MCP servers for document analysis, OCR, etc.

---

## Notes

- **Bronze Tier Simplicity**: This skill focuses on file-based categorization only. No external API calls, no payment processing, no email sending.
- **Human Oversight**: Flagged items in Pending_Approval/ require explicit human review before action.
- **Constitution Compliance**: Meets Section IV (skills-based AI), Section VII (audit logging), Section XII (HITL enforcement).
