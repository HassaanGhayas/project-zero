# Manual E2E Testing Guide - Gmail Integration

**Objective**: Validate complete workflow: Email Detection → Approval → Execution

**Estimated Time**: 15-20 minutes

---

## 🔐 Phase 0: OAuth Setup (One-time)

### Prerequisites
- Google account with Gmail
- Access to Google Cloud Console

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project: `AI-Employee-Gmail`
3. Enable Gmail API:
   - Search "Gmail API"
   - Click "Enable"

### Step 2: Create OAuth2 Credentials
1. Go to "Credentials" in sidebar
2. Click "Create Credentials" → "OAuth client ID"
3. Application type: "Desktop application"
4. Download JSON file
5. Copy to: `/home/hasss/.google/credentials.json`

### Step 3: Run OAuth Setup Script
```bash
cd /home/hasss/projects/project-zero
uv run python scripts/setup_gmail_oauth.py
```

This will:
- Open browser for Google consent
- Ask for Gmail permissions
- Create `/home/hasss/.google/token.json`
- Display "✅ Authentication successful"

**Expected Output:**
```
✅ Token saved successfully: /home/hasss/.google/token.json
Credentials are valid and ready to use.
```

---

## 📋 Phase 1: Start Watchers (T048 Part 1)

### Step 1: Open Terminal
```bash
cd /home/hasss/projects/project-zero
```

### Step 2: Start All Watchers
```bash
source .env  # Load environment variables
uv run -m src.watchers.run_all_watchers
```

**Expected Output:**
```
============================================================
AI Employee Vault - Master Orchestrator
============================================================
Vault path: /home/hasss/projects/project-zero/AI_Employee_Vault

Initializing watchers...

Starting watchers...

✅ Filesystem watcher started (Inbox/ → Needs_Action/)
✅ Gmail watcher started (Gmail API → Needs_Action/)
✅ Status field watcher started (Needs_Action/ → Approved/Rejected/)
✅ Approved watcher started (Approved/ → execute → In_Progress/)

============================================================
🚀 All watchers running - Real-time AI Employee active
============================================================

Workflow:
  1. Drop file in Inbox/ OR Email arrives in Gmail → Action file created in Needs_Action/
  2. Edit status: pending → approved → Moves to Approved/
  3. Action executes immediately → Confirmation in In_Progress/
  4. Review confirmation → Move to Done/

Press Ctrl+C to stop
```

✅ **If you see this, watchers are running!**

---

## 📧 Phase 2: Send Test Email (T048 Part 2)

### Step 1: Open Gmail in Browser
- Go to https://mail.google.com
- Sign in with your Gmail account

### Step 2: Compose Test Email to Yourself
- **To**: your.email@gmail.com
- **Subject**: `Test Email for AI Employee - Please Process`
- **Body**:
```
This is a test email to validate Gmail integration.

Expected: Action file should appear in Needs_Action/ within 2 minutes.
```

### Step 3: Mark as Important
- Click star/flag icon to mark as important (⭐)
- This ensures it matches Gmail query: `is:important is:unread`

### Step 4: Send Email
- Click "Send" button
- Wait 10-20 seconds for delivery

**What happens next:**
- Gmail watcher polls every 120 seconds
- On next poll, should detect your email
- Creates action file in `Needs_Action/` folder

---

## ✅ Phase 3: Verify Action File Created (T048 Part 3)

### Step 1: Check Needs_Action Folder
```bash
# Open new terminal (keep watchers running)
ls -la /home/hasss/projects/project-zero/AI_Employee_Vault/Needs_Action/
```

**Expected Output:**
```
-rw-r--r-- 1 user user 2234 Feb 10 10:45 FILE_test@example.com_Test_Email.md
```

### Step 2: View Action File Content
```bash
cat /home/hasss/projects/project-zero/AI_Employee_Vault/Needs_Action/FILE_test@example.com_*.md
```

**Expected Content:**
```yaml
---
type: email
gmail_message_id: [some_id]
sender: your.email@gmail.com
sender_name: Your Name
subject: Test Email for AI Employee - Please Process
received_timestamp: 2026-02-10T10:45:00Z
status: pending
priority: high
has_attachments: false
attachment_count: 0
category: email
suggested_actions:
  - Review email content in Gmail
  - Approve for archival if no action needed
  - Edit YAML status field to 'approved' to archive
---

## Email Details
**From**: your.email@gmail.com
**Subject**: Test Email for AI Employee - Please Process
**Received**: 2026-02-10T10:45:00Z

## Email Snippet
> This is a test email to validate Gmail integration...
```

✅ **If you see this file, email detection is working!**

---

## 🎯 Phase 4: Approve Email (T048 Part 4)

### Step 1: Edit Action File in Obsidian
1. Open Obsidian vault
2. Navigate to `Needs_Action` folder
3. Open the test email action file
4. Find this line: `status: pending`
5. **Change to**: `status: approved`
6. **Save file** (Ctrl+S or Cmd+S)

**Example:**
```yaml
---
type: email
gmail_message_id: [id]
sender: your.email@gmail.com
status: approved  # ← CHANGED FROM "pending"
priority: high
...
---
```

### Step 2: Watch for File Movement
Within 2 seconds, file should move from `Needs_Action/` to `Approved/`

```bash
# Check Approved folder
ls -la /home/hasss/projects/project-zero/AI_Employee_Vault/Approved/
```

**Expected Output:**
```
-rw-r--r-- 1 user user 2234 Feb 10 10:46 FILE_test@example.com_Test_Email.md
```

✅ **If file moved to Approved/, approval workflow is working!**

---

## ⚡ Phase 5: Watch Execution (T048 Part 5)

### Step 1: Check In_Progress Folder
```bash
# Check In_Progress folder for confirmation files
ls -la /home/hasss/projects/project-zero/AI_Employee_Vault/In_Progress/
```

**Expected Output:**
```
-rw-r--r-- 1 user user 1456 Feb 10 10:47 CONFIRM_FILE_test@example.com_*.md
-rw-r--r-- 1 user user 2234 Feb 10 10:47 EXECUTED_FILE_test@example.com_*.md
```

### Step 2: View Execution Confirmation
```bash
cat /home/hasss/projects/project-zero/AI_Employee_Vault/In_Progress/CONFIRM_*.md
```

**Expected Content:**
```markdown
---
type: confirmation
original_file: FILE_test@example.com_Test_Email.md
executed: 2026-02-10T10:47:00Z
status: awaiting_confirmation
---

## Action Executed

The following action has been completed:

**Original File**: FILE_test@example.com_Test_Email.md
**Type**: email
**Executed**: 2026-02-10T10:47:00Z

## Execution Result

✅ Email '[subject]' archived

**From**: your.email@gmail.com
**Message ID**: [gmail_id]
**Result**: archived
**Timestamp**: 2026-02-10T10:47:00Z
```

✅ **If confirmation exists, execution is working!**

---

## 🔍 Phase 6: Verify Gmail Action (T048 Part 6)

### Step 1: Check Gmail Inbox
1. Open Gmail in browser
2. Go to Inbox
3. **Your test email should be GONE** (archived)

**Expected:**
- Email no longer in Inbox
- Email still in "All Mail" (not deleted)

### Step 2: Verify Archive
1. Click "All Mail" folder
2. Search for test email subject
3. Email should appear there with no "Inbox" label

✅ **If email is archived in Gmail, MCP server worked!**

---

## 📊 Phase 7: Check Audit Logs (T048 Part 7)

### Step 1: View Today's Audit Log
```bash
cat /home/hasss/projects/project-zero/AI_Employee_Vault/Logs/2026-02-10.json | jq '.' | head -100
```

**Expected Log Entries:**
```json
{"timestamp": "2026-02-10T10:45:00Z", "event_type": "email_detected", ...}
{"timestamp": "2026-02-10T10:46:00Z", "action_type": "file_moved", ...}
{"timestamp": "2026-02-10T10:47:00Z", "action_type": "email_executed", ...}
```

✅ **If logs show all events, audit trail is complete!**

---

## 🧪 Phase 8: Test Exponential Backoff (T049)

### Step 1: Simulate Rate Limit
This test is advanced - for now, observe:
- If Gmail API returns 429 (rate limit)
- Check logs for increased `check_interval`
- Default: 120s → After rate limit: 240s → 480s → etc.

**Skip for now** - will happen naturally if you hit rate limits

---

## 🔑 Phase 9: Test OAuth Expiration (T050)

### Step 1: Token Refresh Mechanism
The system automatically:
1. Checks token expiration on startup
2. Refreshes token if needed
3. Logs clear re-authentication instructions

**What to look for:**
```
✅ Gmail credentials valid and refreshed
```

**If token expires:**
- Watcher logs: "Token expired, run scripts/setup_gmail_oauth.py"
- Simply re-run: `uv run python scripts/setup_gmail_oauth.py`

---

## ✅ Success Checklist - Complete Workflow

- [ ] Watchers started (4 watchers running)
- [ ] Test email sent to Gmail
- [ ] Action file created in `Needs_Action/`
- [ ] File contains correct metadata (type: email, sender, subject)
- [ ] Edited status to "approved" in Obsidian
- [ ] File moved to `Approved/` (within 2 seconds)
- [ ] Confirmation file created in `In_Progress/`
- [ ] Email archived in Gmail
- [ ] Audit logs contain all events
- [ ] Watcher still running (no errors)

✅ **If all checks pass, Gmail Integration MVP is VALIDATED!**

---

## 🐛 Troubleshooting

### Issue: Action file not created after 3 minutes
**Check:**
1. Is Gmail watcher running? (Check terminal output)
2. Is email marked as important? (⭐)
3. Do you see any errors in watcher logs?
4. Check logs: `tail -f /path/to/Logs/2026-02-10.json`

### Issue: OAuth Error
**Solution:**
```bash
rm ~/.google/token.json
uv run python scripts/setup_gmail_oauth.py  # Re-authenticate
```

### Issue: Email not archived in Gmail
**Check:**
1. Is MCP server running?
2. Do you see "gmail_executed" in audit logs?
3. Check error logs for MCP errors

### Issue: File not moving from Needs_Action
**Check:**
1. Did you save the file after editing status?
2. Is status field exactly: `status: approved` (lowercase)
3. Is it valid YAML? (No syntax errors)

---

## 📌 Next Steps

After successful E2E test:
1. **Mark T048 Complete** ✅
2. **Skip T049-T050** (advanced edge case tests)
3. **Proceed to Phase 8: Documentation**
   - Create GMAIL_SETUP.md
   - Update README
   - Write user guide

---

**Ready? Start the watchers now!**
```bash
cd /home/hasss/projects/project-zero
uv run -m src.watchers.run_all_watchers
```
