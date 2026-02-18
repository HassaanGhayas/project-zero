# T048: Manual E2E Test Procedure

**Purpose**: Validate complete Gmail integration workflow with real Gmail API
**Duration**: ~15 minutes
**Prerequisites**: OAuth2 setup complete (docs/GMAIL_SETUP.md)

---

## Test Environment Setup

```bash
# 1. Verify credentials exist
ls -la ~/.google/credentials.json ~/.google/token.json

# 2. Verify .env configuration
cat .env | grep GMAIL

# Expected output:
# GMAIL_CREDENTIALS_PATH=/home/hasss/.google/credentials.json
# GMAIL_TOKEN_PATH=/home/hasss/.google/token.json
# GMAIL_CHECK_INTERVAL=120
# VAULT_PATH=/home/hasss/projects/project-zero/AI_Employee_Vault

# 3. Start watchers
uv run python -m src.watchers.run_all_watchers &
WATCHER_PID=$!
```

---

## Test Scenario 1: Basic Email Detection

**Steps:**

1. **Send test email to configured Gmail account**
   - From: Your personal email
   - To: Configured Gmail account
   - Subject: "Test Email for AI Employee Detection"
   - Body: "This is a test email to verify Gmail integration works correctly."
   - Mark as **important** (click star icon in Gmail)

2. **Wait for detection (max 5 minutes)**
   ```bash
   # Monitor logs for detection
   tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | grep email_detected

   # Check for action file creation
   watch -n 5 "ls -lh AI_Employee_Vault/Needs_Action/"
   ```

3. **Verify action file created**
   ```bash
   # Should see FILE_<sender>_<subject>.md
   ls AI_Employee_Vault/Needs_Action/FILE_*Test_Email*.md
   ```

4. **Validate action file content**
   ```bash
   ACTION_FILE=$(ls AI_Employee_Vault/Needs_Action/FILE_*Test_Email*.md | head -1)
   cat "$ACTION_FILE"
   ```

**Expected YAML frontmatter:**
```yaml
---
type: email
gmail_message_id: <valid ID>
sender: <your email>
subject: "Test Email for AI Employee Detection"
received_timestamp: <ISO 8601 timestamp>
status: pending
priority: high  # (unknown sender = high priority)
has_attachments: false
attachment_count: 0
category: email
suggested_actions:
  - "Review and approve for archival"
---
```

**Acceptance Criteria:**
- ✅ Action file appears within 5 minutes
- ✅ YAML frontmatter contains all required fields
- ✅ Sender email matches your email
- ✅ Subject matches sent email
- ✅ Priority is "high" (unknown sender)
- ✅ Status is "pending"

---

## Test Scenario 2: Approval Workflow

**Steps:**

1. **Edit action file status**
   ```bash
   # Open action file in editor
   nano "$ACTION_FILE"

   # Change: status: pending → status: approved
   # Save and exit
   ```

2. **Wait for status field watcher (max 2 seconds)**
   ```bash
   # Monitor for file movement
   watch -n 1 "ls AI_Employee_Vault/Approved/"
   ```

3. **Verify file moved to Approved/**
   ```bash
   ls AI_Employee_Vault/Approved/FILE_*Test_Email*.md
   ```

**Acceptance Criteria:**
- ✅ File moves to Approved/ within 2 seconds
- ✅ File no longer in Needs_Action/
- ✅ Audit log shows file_moved event

---

## Test Scenario 3: Email Execution

**Steps:**

1. **Wait for approved watcher execution (max 5 seconds)**
   ```bash
   # Monitor logs for execution
   tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | grep email_executed

   # Check for confirmation file
   watch -n 1 "ls AI_Employee_Vault/In_Progress/"
   ```

2. **Verify confirmation file created**
   ```bash
   ls AI_Employee_Vault/In_Progress/*_confirmation.md
   ```

3. **Check Gmail for archived message**
   - Open Gmail in browser
   - Search for the test email subject
   - Verify it's archived (not in inbox)
   - Check "All Mail" to confirm still exists

**Acceptance Criteria:**
- ✅ Confirmation file created in In_Progress/
- ✅ Email archived in Gmail (not in inbox)
- ✅ Email still exists in "All Mail"
- ✅ Audit log shows email_executed event with success status

---

## Test Scenario 4: Known Contact Prioritization

**Steps:**

1. **Add your email to known_contacts.yaml**
   ```bash
   nano config/known_contacts.yaml
   ```

   Add:
   ```yaml
   known_contacts:
     - email: "your-email@example.com"
       name: "Your Name"
       category: "client"
       priority_override: "medium"
   ```

2. **Restart watcher to reload config**
   ```bash
   kill $WATCHER_PID
   uv run python -m src.watchers.run_all_watchers &
   WATCHER_PID=$!
   ```

3. **Send another test email**
   - From: Your personal email (now in known_contacts)
   - Subject: "Test Email #2 - Known Contact"
   - Body: "Testing known contact prioritization"

4. **Verify priority is "medium"**
   ```bash
   ACTION_FILE=$(ls AI_Employee_Vault/Needs_Action/FILE_*Test_Email_2*.md | head -1)
   grep "priority:" "$ACTION_FILE"
   # Expected: priority: medium
   ```

**Acceptance Criteria:**
- ✅ Known contact email has priority: medium
- ✅ Unknown contact email had priority: high (from Scenario 1)

---

## Test Scenario 5: Attachment Detection

**Steps:**

1. **Send email with attachment**
   - From: Your email
   - Subject: "Test Email with Attachment"
   - Body: "Testing attachment detection"
   - Attach a small PDF file

2. **Verify attachment fields**
   ```bash
   ACTION_FILE=$(ls AI_Employee_Vault/Needs_Action/FILE_*Attachment*.md | head -1)
   grep -A 5 "has_attachments:" "$ACTION_FILE"
   ```

**Expected:**
```yaml
has_attachments: true
attachment_count: 1
attachment_metadata:
  - filename: "document.pdf"
    size_bytes: <size>
```

**Acceptance Criteria:**
- ✅ has_attachments: true
- ✅ attachment_count matches actual count
- ✅ Priority elevated to "high" (attachments always high)

---

## Test Scenario 6: Emergency Stop

**Steps:**

1. **Create emergency stop file**
   ```bash
   touch AI_Employee_Vault/EMERGENCY_STOP.md
   ```

2. **Send test email**
   - Subject: "Emergency Stop Test"

3. **Verify no action file created**
   ```bash
   # Wait 5 minutes
   sleep 300

   # Check - should be empty or no new files
   ls AI_Employee_Vault/Needs_Action/FILE_*Emergency_Stop*.md
   # Expected: No such file or directory
   ```

4. **Remove emergency stop**
   ```bash
   rm AI_Employee_Vault/EMERGENCY_STOP.md
   ```

**Acceptance Criteria:**
- ✅ No action files created while EMERGENCY_STOP.md exists
- ✅ Watcher logs show emergency stop detected
- ✅ Normal operation resumes after removal

---

## Cleanup

```bash
# Stop watchers
kill $WATCHER_PID

# Archive test emails in Gmail
# (manually archive or delete test emails)

# Clean up test action files
rm AI_Employee_Vault/Needs_Action/FILE_*Test*.md
rm AI_Employee_Vault/Approved/FILE_*Test*.md
rm AI_Employee_Vault/In_Progress/*_confirmation.md
```

---

## Test Report Template

```markdown
# Gmail Integration E2E Test Report

**Date**: YYYY-MM-DD
**Tester**: [Your Name]
**Environment**: [WSL/Linux/macOS]

## Results

| Scenario | Status | Notes |
|----------|--------|-------|
| 1. Basic Email Detection | ✅/❌ | |
| 2. Approval Workflow | ✅/❌ | |
| 3. Email Execution | ✅/❌ | |
| 4. Known Contact Prioritization | ✅/❌ | |
| 5. Attachment Detection | ✅/❌ | |
| 6. Emergency Stop | ✅/❌ | |

## Issues Found

1. [Issue description]
   - Expected: [what should happen]
   - Actual: [what happened]
   - Logs: [relevant log entries]

## Overall Status: ✅ PASS / ❌ FAIL

## Recommendations

- [Any improvements or observations]
```

---

## Troubleshooting

### Email not detected
```bash
# Check watcher is running
ps aux | grep gmail_watcher

# Check logs for errors
tail -50 AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | grep -i error

# Verify Gmail API query
# Email must be: unread + important + in inbox
```

### OAuth errors
```bash
# Re-authenticate
uv run python scripts/setup_gmail_oauth.py

# Verify token is valid
python -c "import json; print(json.load(open('~/.google/token.json'.replace('~', '/home/hasss'))))"
```

### Rate limiting
```bash
# Check backoff status in logs
tail AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | grep backoff

# Wait for backoff to reset (max 60 minutes)
```

---

**Next**: After completing all scenarios, mark T048 as complete in tasks.md
