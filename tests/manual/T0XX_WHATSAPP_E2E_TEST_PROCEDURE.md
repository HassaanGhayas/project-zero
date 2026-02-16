# WhatsApp Integration - Manual End-to-End Test Procedure

**Test ID:** T0XX (WhatsApp E2E Testing)
**Objective:** Validate WhatsApp Web monitoring, action file generation, and approval workflow
**Prerequisites:** Playwright installed, WhatsApp account with active phone number
**Estimated Time:** 15-20 minutes

---

## Pre-Test Setup

### 1. Verify Environment Configuration

```bash
# Check .env contains WhatsApp configuration
grep WHATSAPP .env

# Expected output:
# WHATSAPP_SESSION_PATH=/home/hasss/.whatsapp/session
# WHATSAPP_CHECK_INTERVAL=30
# PLAYWRIGHT_HEADLESS=false  # Use false for initial testing
```

### 2. Verify Playwright Installation

```bash
# Check Playwright is installed
uv run playwright --version

# Expected output: Version 1.x.x or similar

# Verify Chromium browser installed
ls ~/.cache/ms-playwright/chromium-*/
```

### 3. Clean Test Environment

```bash
# Remove any existing action files
rm -f AI_Employee_Vault/Needs_Action/FILE_*.md

# Clean session data (start fresh)
rm -rf ~/.whatsapp/session/*

# Verify clean start
ls -la ~/.whatsapp/session/
# Should be empty or not exist
```

---

## Test Scenario 1: QR Code Authentication

**Objective:** Verify first-time WhatsApp Web session setup

### Steps:

1. **Start watchers in visible mode:**
   ```bash
   # Ensure headless=false in .env
   sed -i 's/PLAYWRIGHT_HEADLESS=true/PLAYWRIGHT_HEADLESS=false/' .env

   # Start all watchers
   uv run python -m src.watchers.run_all_watchers
   ```

2. **Wait for browser to launch:**
   - Chromium browser window should appear
   - WhatsApp Web should load with QR code
   - Timeout: 30 seconds max

3. **Scan QR code:**
   - Open WhatsApp on your phone
   - Navigate to: Menu > Linked Devices
   - Tap "Link a Device"
   - Scan QR code displayed in browser

4. **Verify authentication:**
   ```bash
   # Check session files created
   ls -la ~/.whatsapp/session/

   # Expected:
   # - cookies.json
   # - localStorage.json
   # - User Data/ directory
   ```

5. **Check watcher logs:**
   ```bash
   # Should see successful session initialization
   tail -10 AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | grep whatsapp
   ```

### Expected Results:
- ✅ Browser launched successfully
- ✅ QR code displayed within 30 seconds
- ✅ Authentication successful after scan
- ✅ Session data saved to ~/.whatsapp/session/
- ✅ No auth errors in logs

### Failure Modes:
- ❌ Browser timeout: Check internet connection
- ❌ QR code expired: Refresh page and rescan
- ❌ Session not saved: Check WHATSAPP_SESSION_PATH permissions

---

## Test Scenario 2: Message Detection (Priority Keyword)

**Objective:** Verify watcher detects messages with priority keywords

### Steps:

1. **Send test message from phone:**
   - Using another phone/WhatsApp account
   - Send message to your WhatsApp: **"Urgent: Test message for AI Employee"**
   - Leave message unread

2. **Wait for detection:**
   ```bash
   # Maximum wait time: 30 seconds (check interval)
   # Monitor logs in real-time
   tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | grep whatsapp_message_detected
   ```

3. **Verify action file created:**
   ```bash
   # List action files
   ls -lh AI_Employee_Vault/Needs_Action/

   # Should see: FILE_<sender>_<id>.md

   # Read action file
   cat AI_Employee_Vault/Needs_Action/FILE_*.md
   ```

4. **Validate action file structure:**
   ```bash
   # Check required YAML fields
   head -20 AI_Employee_Vault/Needs_Action/FILE_*.md

   # Expected fields:
   # - type: message
   # - whatsapp_message_id: <unique_id>
   # - sender: <contact_name>
   # - received_timestamp: <ISO8601>
   # - status: pending
   # - priority: high
   # - category: whatsapp_message
   ```

### Expected Results:
- ✅ Message detected within 30 seconds
- ✅ Action file created in Needs_Action/
- ✅ Filename: FILE_<sender>_<msg_id>.md
- ✅ All 8+ required YAML fields present
- ✅ Message text visible in file body
- ✅ Audit log entry: whatsapp_message_detected

### Failure Modes:
- ❌ No detection: Verify message contains keyword ("urgent")
- ❌ No action file: Check watcher is running, check logs for errors
- ❌ Missing fields: Verify YAML structure in action file

---

## Test Scenario 3: Message Without Keyword (No Detection)

**Objective:** Verify watcher ignores messages without priority keywords

### Steps:

1. **Send non-priority message:**
   - Send message: **"Hello, how are you?"** (no keyword)
   - Leave message unread

2. **Wait for check cycle:**
   ```bash
   # Wait 30+ seconds
   sleep 35
   ```

3. **Verify no action file created:**
   ```bash
   # Count action files (should be same as before)
   ls AI_Employee_Vault/Needs_Action/FILE_*.md | wc -l
   ```

4. **Check logs for filtering:**
   ```bash
   # Should see debug message about no priority messages
   tail -20 AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | jq 'select(.actor=="whatsapp_watcher")'
   ```

### Expected Results:
- ✅ No action file created for non-keyword message
- ✅ Watcher continues running normally
- ✅ Logs show successful check (no errors)

### Failure Modes:
- ❌ Action file created: Verify keyword filtering logic
- ❌ Watcher stopped: Check for errors in logs

---

## Test Scenario 4: Approval Workflow Integration

**Objective:** Verify action file approval moves to Approved/ folder

### Steps:

1. **Edit action file status:**
   ```bash
   # Find action file from Scenario 2
   ACTION_FILE=$(ls AI_Employee_Vault/Needs_Action/FILE_*.md | head -1)

   # Edit status field
   sed -i 's/status: pending/status: approved/' "$ACTION_FILE"
   ```

2. **Wait for StatusFieldWatcher detection:**
   ```bash
   # Maximum wait: 2 seconds (StatusFieldWatcher is fast)
   sleep 3
   ```

3. **Verify file moved to Approved/:**
   ```bash
   # Check Needs_Action/ is empty
   ls AI_Employee_Vault/Needs_Action/FILE_*.md
   # Expected: No such file or directory

   # Check file in Approved/
   ls AI_Employee_Vault/Approved/FILE_*.md
   # Expected: File present
   ```

4. **Verify audit log entry:**
   ```bash
   # Check for status_change event
   cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | jq 'select(.action_type=="status_change")'
   ```

### Expected Results:
- ✅ File moved from Needs_Action/ to Approved/ within 2 seconds
- ✅ Status field updated to "approved"
- ✅ Audit log shows status_change event

### Failure Modes:
- ❌ File not moved: Verify StatusFieldWatcher is running
- ❌ File duplicated: Check for race conditions in logs

---

## Test Scenario 5: Duplicate Prevention

**Objective:** Verify same message is not processed twice

### Steps:

1. **Send same test message again:**
   - Send identical message: **"Urgent: Test message for AI Employee"**
   - This will have different timestamp but same sender/content

2. **Wait for check cycle:**
   ```bash
   sleep 35
   ```

3. **Count action files:**
   ```bash
   # Should only have ONE new action file (different message ID)
   ls AI_Employee_Vault/Needs_Action/FILE_*.md | wc -l
   ```

4. **Verify processed IDs tracking:**
   ```bash
   # Check watcher logs for duplicate detection
   tail -50 AI_Employee_Vault/Logs/$(date +%Y-%m-% d).json | grep "duplicate\|processed"
   ```

### Expected Results:
- ✅ New message creates new action file (different content hash)
- ✅ Exact duplicate (same message ID) is skipped
- ✅ Watcher maintains processed_message_ids set

**Note:** Since WhatsApp generates unique message IDs, true duplicates are rare in practice.

---

## Test Scenario 6: Emergency Stop Mechanism

**Objective:** Verify EMERGENCY_STOP.md halts WhatsApp polling

### Steps:

1. **Create emergency stop file:**
   ```bash
   echo "# Emergency Stop\nAll watchers paused for testing." > AI_Employee_Vault/EMERGENCY_STOP.md
   ```

2. **Send test message:**
   - Send message with keyword: **"Urgent payment needed"**

3. **Wait for check cycle:**
   ```bash
   sleep 35
   ```

4. **Verify no action file created:**
   ```bash
   # No new files should appear
   ls -lt AI_Employee_Vault/Needs_Action/ | head -5
   ```

5. **Check logs for emergency stop:**
   ```bash
   # Should see emergency stop warning
   tail -10 AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | grep "EMERGENCY STOP"
   ```

6. **Remove emergency stop:**
   ```bash
   rm AI_Employee_Vault/EMERGENCY_STOP.md
   ```

7. **Verify polling resumes:**
   - Send another test message
   - Verify action file created after stop file removed

### Expected Results:
- ✅ No messages processed while EMERGENCY_STOP.md exists
- ✅ Logs show emergency stop warnings
- ✅ Watcher resumes after file removed
- ✅ No crashes or errors during stop period

### Failure Modes:
- ❌ Message processed during stop: Check emergency stop logic in code
- ❌ Watcher crashed: Verify graceful handling in logs

---

## Test Scenario 7: Session Persistence

**Objective:** Verify session persists across watcher restarts

### Steps:

1. **Stop all watchers:**
   ```bash
   # Ctrl+C in terminal running watchers
   # Or: pkill -f run_all_watchers
   ```

2. **Verify session data exists:**
   ```bash
   ls -lh ~/.whatsapp/session/cookies.json
   # Should exist with recent timestamp
   ```

3. **Restart watchers in headless mode:**
   ```bash
   # Switch to headless mode
   sed -i 's/PLAYWRIGHT_HEADLESS=false/PLAYWRIGHT_HEADLESS=true/' .env

   # Restart watchers
   uv run python -m src.watchers.run_all_watchers
   ```

4. **Verify no QR code required:**
   - No browser window appears (headless mode)
   - Watcher logs show successful session load
   - No authentication errors

5. **Test message detection:**
   - Send test message with keyword
   - Verify action file created (proves session is valid)

### Expected Results:
- ✅ Session persists after watcher restart
- ✅ No QR code scan required on restart
- ✅ Headless mode works with existing session
- ✅ Message detection continues normally

### Failure Modes:
- ❌ QR code required again: Check session_path is correct
- ❌ Auth errors: Session may have expired (re-authenticate)

---

## Post-Test Cleanup

### 1. Stop All Watchers

```bash
# Graceful stop
pkill -SIGINT -f run_all_watchers

# Or force stop
pkill -9 -f run_all_watchers
```

### 2. Clean Test Data

```bash
# Remove test action files
rm -f AI_Employee_Vault/Needs_Action/FILE_*.md
rm -f AI_Employee_Vault/Approved/FILE_*.md

# Optional: Clean session data
# rm -rf ~/.whatsapp/session/*
```

### 3. Reset Configuration

```bash
# Switch back to headless mode if needed
sed -i 's/PLAYWRIGHT_HEADLESS=false/PLAYWRIGHT_HEADLESS=true/' .env
```

---

## Test Report Template

### WhatsApp Integration E2E Test Results

**Date:** YYYY-MM-DD
**Tester:** [Name]
**Environment:** [dev/staging/production]

| Test Scenario | Status | Notes |
|---------------|--------|-------|
| 1. QR Authentication | ✅ PASS | Session saved successfully |
| 2. Message Detection | ✅ PASS | Detected within 25 seconds |
| 3. Non-Keyword Filter | ✅ PASS | Correctly ignored |
| 4. Approval Workflow | ✅ PASS | Moved to Approved/ in 1s |
| 5. Duplicate Prevention | ✅ PASS | No duplicates created |
| 6. Emergency Stop | ✅ PASS | Polling halted correctly |
| 7. Session Persistence | ✅ PASS | No re-auth needed |

**Overall Result:** ✅ PASS / ❌ FAIL

**Issues Found:**
- [List any failures, unexpected behavior, or bugs]

**Recommendations:**
- [Suggestions for improvements or next steps]

---

## Troubleshooting Guide

### Issue: Browser Doesn't Launch

**Symptoms:** No browser window appears, timeout errors
**Checks:**
```bash
# Verify Playwright installed
uv run playwright --version

# Reinstall browser
uv run playwright install chromium

# Check for zombie processes
ps aux | grep chromium
pkill -9 chromium
```

### Issue: QR Code Doesn't Appear

**Symptoms:** Blank browser page, "Loading..." message
**Checks:**
- Internet connection active
- WhatsApp Web not blocked by firewall
- Browser extensions disabled (shouldn't be any in Playwright)

### Issue: Session Expired

**Symptoms:** Re-authentication required on restart
**Solution:**
```bash
# Clear session and re-authenticate
rm -rf ~/.whatsapp/session/*
PLAYWRIGHT_HEADLESS=false uv run python -m src.watchers.run_all_watchers
# Scan new QR code
```

### Issue: No Messages Detected

**Symptoms:** Messages sent but no action files created
**Checks:**
```bash
# Verify watcher running
ps aux | grep whatsapp_watcher

# Check keywords config
cat config/whatsapp_keywords.yaml

# Verify message contains keyword
grep -i "urgent\|payment\|help" <<< "your message text"

# Enable debug logging
tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json
```

---

**Next Steps After Successful Testing:**
1. Mark test scenarios as complete in test report
2. Document any discovered issues or edge cases
3. Switch to headless mode for production use
4. Monitor dashboard for WhatsApp status
5. Proceed with production deployment

---

**Test Procedure Version:** 1.0
**Last Updated:** 2026-02-14
**Related Documentation:**
- Setup Guide: `docs/WHATSAPP_SETUP.md`
- Implementation Plan: `~/.claude/plans/proud-splashing-snail.md`
- Unit Tests: `tests/test_whatsapp_watcher.py`
