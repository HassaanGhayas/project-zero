---
name: Process Inbox
description: Process all pending action files in Needs_Action folder according to Company Handbook rules
model: opus
color: blue
---

# Process Inbox Skill

You are processing the AI Employee's inbox. This skill handles all pending action files in `Needs_Action/`, applies the company handbook rules, and routes items to either `Done/` (auto-completed) or `Pending_Approval/` (requiring human review).

## Prerequisites Check

Before processing, you MUST validate:

1. **Vault exists**: Check that `AI_Employee_Vault/` directory exists and is accessible
2. **Required folders exist**: Verify `Needs_Action/`, `Done/`, `Pending_Approval/`, `Logs/` are present
3. **Company Handbook exists**: Confirm `Company_Handbook.md` is readable
4. **No emergency stop**: Verify `EMERGENCY_STOP.md` does NOT exist in vault root

If any precondition fails, abort processing and report the issue to the user.

## Processing Algorithm

Follow these steps in order:

### Step 1: Check for Emergency Stop

```bash
# Check if EMERGENCY_STOP.md exists
if [ -f "AI_Employee_Vault/EMERGENCY_STOP.md" ]; then
    echo "🛑 Emergency stop active - operations halted"
    echo "EMERGENCY_STOP.md detected in vault root."
    echo "No items processed."
    exit 0
fi
```

If emergency stop is active, immediately abort and report to user.

### Step 2: Read Company Handbook Rules

Read `AI_Employee_Vault/Company_Handbook.md` and extract the auto-approve rules:

**Key Rules to Extract**:
- Text files (*.txt, *.md) < 1MB → Auto-process (High confidence)
- Documents (*.pdf, *.docx) → Require review (Medium confidence)
- Data files (*.csv, *.json) < 5MB → Auto-process (High confidence)
- Images (*.jpg, *.png) < 10MB → Auto-process (Low priority)
- Unknown file types → Always flag for approval (Low confidence)

### Step 3: Discover Pending Items

List all `*.md` files in `Needs_Action/` folder and read their YAML frontmatter to find items with `status: pending`.

If zero pending items found:
```
ℹ️  No pending items in inbox
```

Exit gracefully (no error).

### Step 4: Process Each Pending Item

For each action file with `status: pending`:

#### 4a. Read File Metadata

Extract from YAML frontmatter:
- `type`: File category (document, text, data, image, email, unknown)
- `category`: Semantic category
- `size`: File size in bytes
- `file_type`: Extension (e.g., ".pdf", ".txt")
- `original_name`: Source filename
- `priority`: low | medium | high

#### 4b. Apply Auto-Approve Rules

Use the decision tree from Company_Handbook.md:

**High Confidence (Auto-Complete)**:
```
IF type in ["text"] AND size < 1048576:  # 1MB = 1048576 bytes
    confidence = "high"
    action = "auto-complete"
    destination = "Done/"

ELSE IF type in ["data"] AND size < 5242880:  # 5MB
    confidence = "high"
    action = "auto-complete"
    destination = "Done/"

ELSE IF type in ["image"] AND size < 10485760:  # 10MB
    confidence = "high"
    action = "auto-complete"
    destination = "Done/"
```

**Medium Confidence (Require Review)**:
```
ELSE IF type in ["document"]:
    confidence = "medium"
    action = "flag-for-review"
    destination = "Pending_Approval/"
    reason = "Document requires human review"
```

**Low Confidence (Always Flag)**:
```
ELSE IF type == "unknown" OR category == "unknown":
    confidence = "low"
    action = "flag-for-review"
    destination = "Pending_Approval/"
    reason = "Unknown file type requires approval"

ELSE IF size > 10485760:  # > 10MB
    confidence = "medium"
    action = "flag-for-review"
    destination = "Pending_Approval/"
    reason = "Large file requires review"
```

#### 4c. Move File and Update Status

**For Auto-Completed Items**:
1. Read the entire file content
2. Update YAML frontmatter: `status: pending` → `status: completed`
3. Move file from `Needs_Action/` to `Done/`
4. Log action:
   ```json
   {
     "timestamp": "2026-02-08T...",
     "action_id": "skill_inbox_NNN",
     "action_type": "item_completed",
     "actor": "process-inbox",
     "target": "Done/FILE_xxx.md",
     "parameters": {
       "source": "Needs_Action/FILE_xxx.md",
       "category": "text",
       "confidence": "high"
     },
     "approval_status": "approved",
     "approved_by": "auto",
     "result": "success",
     "error": null,
     "duration": 50
   }
   ```

**For Flagged Items**:
1. Read the entire file content
2. Update YAML frontmatter: `status: pending` → `status: flagged`
3. Add a note to the markdown body explaining why it was flagged
4. Move file from `Needs_Action/` to `Pending_Approval/`
5. Log action:
   ```json
   {
     "timestamp": "2026-02-08T...",
     "action_id": "skill_inbox_NNN",
     "action_type": "item_flagged",
     "actor": "process-inbox",
     "target": "Pending_Approval/FILE_xxx.md",
     "parameters": {
       "source": "Needs_Action/FILE_xxx.md",
       "category": "document",
       "confidence": "medium",
       "reason": "Document requires review"
     },
     "approval_status": "pending",
     "approved_by": null,
     "result": "success",
     "error": null,
     "duration": 50
   }
   ```

### Step 5: Generate Summary

Create a processing summary with:
- Total items processed
- Auto-completed count
- Flagged for approval count
- Error count (if any)

List each completed and flagged item with filename and reason.

### Step 6: Update Dashboard

After processing completes, invoke the `update-dashboard` skill to refresh the Dashboard.md with new folder counts.

### Step 7: Return Summary to User

Format output as:

```
✅ Inbox processing complete

📊 Summary:
- Total items processed: N
- Auto-completed: X
- Flagged for approval: Y
- Errors: Z

✅ Completed (moved to Done/):
  - FILE_xxx.md (text file, size)
  - FILE_yyy.md (data file, size)

⚠️  Flagged for Approval (moved to Pending_Approval/):
  - FILE_zzz.md (reason)

📋 Dashboard updated with current queue status
```

## Error Handling

### If Company_Handbook.md is Missing

Use conservative defaults:
- **Flag ALL items for approval**
- Log warning
- Report to user: "⚠️  Handbook missing - using conservative defaults (all items flagged for review)"

### If File Cannot Be Moved

- Skip the file
- Log error with filename
- Continue processing remaining items
- Report error in summary

### If Invalid Frontmatter Detected

- Flag item for approval
- Add note: "Invalid metadata detected - requires human review"
- Log warning
- Continue processing

## Audit Logging

Every action MUST be logged to `Logs/YYYY-MM-DD.json` in NDJSON format.

**Required log entry fields**:
- `timestamp`: ISO 8601 format
- `action_id`: Unique ID (e.g., "skill_inbox_001")
- `action_type`: "inbox_processed", "item_completed", "item_flagged", "emergency_stop", "error_occurred"
- `actor`: "process-inbox"
- `target`: File path acted upon
- `parameters`: Action-specific data (category, confidence, etc.)
- `approval_status`: "approved" (auto), "pending" (flagged), null
- `approved_by`: "auto" (auto-completed), null (flagged)
- `result`: "success" | "error" | "warning"
- `error`: Error message if result = error
- `duration`: Processing time in milliseconds (optional)

## Safety Rules

1. **Never delete files** - Only move them
2. **Check emergency stop FIRST** - Before any file operations
3. **Atomic operations** - Use move operations (not copy+delete)
4. **Preserve data** - Never truncate or lose information
5. **Log everything** - Every decision must be auditable

## Performance Expectations

- Process up to 100 items per invocation
- Target: < 5 seconds + 100ms per item
- Read entire Needs_Action/ folder in single scan

## Example Triggers

<example>
User: "Process my inbox"
User: "Handle all pending items"
User: "Go through the action files"
User: "Check what needs attention"
User: "Process pending work"
User: "Handle the queue"
</example>

## Constitution Compliance

This skill implements:
- ✅ **Section IV**: Skills-based AI functionality
- ✅ **Section VII**: Comprehensive audit logging
- ✅ **Section IX**: No autonomous actions (only after explicit invocation)
- ✅ **Section XII**: HITL enforcement via Pending_Approval/ folder
- ✅ **Section XII**: Emergency stop mechanism

## Notes

- This is a **Bronze Tier** skill: File-based categorization only, no external APIs
- Human oversight required for flagged items in Pending_Approval/
- All decisions are based on Company_Handbook.md rules (no hardcoded logic)
- Idempotent: Safe to run multiple times (already-processed items have status != pending)
