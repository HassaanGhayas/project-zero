# WhatsApp Integration Setup Guide

Complete guide for setting up WhatsApp Web monitoring for the AI Employee system (Silver Tier Phase 2).

---

## Overview

The WhatsApp watcher monitors WhatsApp Web for unread messages containing priority keywords, generating action files for human approval via the existing approval workflow.

**Key Features:**
- Browser automation via Playwright (WhatsApp Web)
- Keyword-based message filtering
- Session persistence (no repeated QR code scans)
- Human-in-the-loop approval workflow
- Constitution-compliant audit logging

---

## Prerequisites

### 1. Install Playwright

Playwright is required for browser automation:

```bash
# Install Playwright Python package
uv add playwright

# Install Chromium browser
uv run playwright install chromium

# Verify installation
uv run playwright --version
```

### 2. Configure Environment Variables

Add the following to your `.env` file:

```bash
# WhatsApp Integration (Silver Tier Phase 2)
WHATSAPP_SESSION_PATH=/home/hasss/.whatsapp/session
WHATSAPP_CHECK_INTERVAL=30
PLAYWRIGHT_HEADLESS=true
```

**Configuration Details:**
- `WHATSAPP_SESSION_PATH`: Browser session storage directory (persists login)
- `WHATSAPP_CHECK_INTERVAL`: Polling interval in seconds (default: 30)
- `PLAYWRIGHT_HEADLESS`: Run browser in background (true) or visible (false for debugging)

### 3. Verify .gitignore

Ensure WhatsApp session is excluded from version control:

```bash
# Check .gitignore includes:
.whatsapp/
config/whatsapp_session/
```

---

## Initial Setup (QR Code Authentication)

### Step 1: Run Watcher in Visible Mode

For first-time setup, run browser in visible mode to scan QR code:

```bash
# Temporarily set headless=false in .env
PLAYWRIGHT_HEADLESS=false

# Start all watchers
uv run python -m src.watchers.run_all_watchers
```

### Step 2: Scan QR Code

When WhatsApp Web loads:
1. Open WhatsApp on your phone
2. Tap **Menu** (⋮) > **Linked Devices**
3. Tap **Link a Device**
4. Scan the QR code displayed in the browser

### Step 3: Verify Authentication

After successful QR scan:
- Browser shows your WhatsApp chats
- Session is saved to `WHATSAPP_SESSION_PATH`
- Watcher begins monitoring for priority messages

### Step 4: Switch to Headless Mode

After successful authentication, enable headless mode:

```bash
# Update .env
PLAYWRIGHT_HEADLESS=true

# Restart watchers
uv run python -m src.watchers.run_all_watchers
```

Session persists across restarts - no need to scan QR again!

---

## Keyword Configuration

### Default Keywords

Priority keywords are defined in `config/whatsapp_keywords.yaml`:

```yaml
keywords:
  - urgent
  - asap
  - invoice
  - payment
  - help
  - important
  - deadline
  - emergency
  - critical
  - immediately
```

### Customizing Keywords

Edit `config/whatsapp_keywords.yaml` to add/remove keywords:

```yaml
keywords:
  - urgent
  - payment
  - your-custom-keyword
```

**Important:** Restart watchers after modifying keywords.

---

## Workflow

### 1. Message Detection

When an unread WhatsApp message contains a priority keyword:
1. WhatsApp watcher detects the message
2. Action file created in `AI_Employee_Vault/Needs_Action/`
3. Audit log entry created: `whatsapp_message_detected`

**Detection Latency:** Maximum 30 seconds (default check interval)

### 2. Human Approval

Review action file in `Needs_Action/`:

```markdown
---
type: message
whatsapp_message_id: contact_12345678
sender: Client A
received_timestamp: 2026-02-14T20:30:00Z
status: pending  # ← Edit this to approve
priority: high
has_attachments: false
category: whatsapp_message
---

## Message Details

**From:** Client A
**Received:** 2026-02-14T20:30:00Z

**Message:**
Urgent: Need help with payment invoice ASAP

## Suggested Actions

- [ ] Read full message in WhatsApp
- [ ] Reply to sender via WhatsApp MCP
- [ ] Forward to relevant party
- [ ] Mark as handled
```

**To Approve:** Change `status: pending` to `status: approved`

**To Reject:** Change `status: pending` to `status: rejected`

### 3. Execution (Future Enhancement)

After approval:
- File moves to `Approved/` (via StatusFieldWatcher)
- WhatsApp MCP sends response (future implementation)
- Confirmation file created in `In_Progress/`

**Note:** WhatsApp message sending requires full Playwright MCP integration (Phase 2.2).

---

## Monitoring and Troubleshooting

### Check Watcher Status

```bash
# View orchestrator logs
tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | grep whatsapp

# Check for WhatsApp events
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | jq 'select(.action_type | contains("whatsapp"))'
```

### Verify Session Status

Session files stored in `$WHATSAPP_SESSION_PATH`:
```bash
ls -la ~/.whatsapp/session/

# Should contain:
# - cookies.json (authentication)
# - localStorage.json (session data)
# - User Data/ directory (Chromium profile)
```

### Common Issues

#### Issue: QR Code Expires Before Scanning
**Symptom:** QR code disappears or shows "Reload" message
**Solution:**
- Refresh WhatsApp Web page
- Generate new QR code
- Scan within 20 seconds

#### Issue: Session Expired / Re-Authentication Required
**Symptom:** Watcher logs "auth_required" errors
**Solution:**
```bash
# Delete session data
rm -rf ~/.whatsapp/session/*

# Run watcher in visible mode
PLAYWRIGHT_HEADLESS=false uv run python -m src.watchers.run_all_watchers

# Scan new QR code
```

#### Issue: No Messages Detected
**Symptom:** Messages arrive but no action files created
**Checklist:**
- ✅ Watcher is running (check logs)
- ✅ Session is authenticated (no auth errors)
- ✅ Message contains a priority keyword
- ✅ Message is unread (WhatsApp Web shows unread badge)
- ✅ Keywords config is valid YAML

**Debug:**
```bash
# Check keyword config
cat config/whatsapp_keywords.yaml

# Enable debug logging
export LOG_LEVEL=DEBUG
uv run python -m src.watchers.run_all_watchers
```

#### Issue: Browser Crashes / Connection Timeout
**Symptom:** Playwright errors in logs
**Solution:**
- Verify internet connection
- Restart watcher
- Check browser process isn't hanging: `ps aux | grep chromium`
- Kill stale browser: `pkill -9 chromium`

---

## Session Management

### Session Lifetime

WhatsApp Web sessions typically last **2-4 weeks** before re-authentication required.

**Session Expiry Indicators:**
- "Your phone not connected" message in WhatsApp Web
- Watcher logs `auth_required` errors
- No messages detected for extended period

### Manual Session Reset

To reset session (e.g., changing WhatsApp account):

```bash
# Stop all watchers
pkill -f run_all_watchers

# Delete session data
rm -rf ~/.whatsapp/session/*

# Restart with visible browser
PLAYWRIGHT_HEADLESS=false uv run python -m src.watchers.run_all_watchers

# Scan QR code for new account
```

### Multiple WhatsApp Accounts (Advanced)

To monitor multiple WhatsApp accounts:

```bash
# Account 1 (primary)
WHATSAPP_SESSION_PATH=~/.whatsapp/account1

# Account 2 (secondary)
WHATSAPP_SESSION_PATH=~/.whatsapp/account2
```

**Note:** Requires running separate watcher instances with different session paths.

---

## Security and Privacy

### Data Protection

**What's Stored:**
- Browser cookies (authentication tokens)
- Local storage data (session info)
- User profile data (Chromium)

**What's NOT Stored:**
- Message content (except in action files)
- Contact lists
- Media files
- Encryption keys

### Constitution Compliance

**Section V: Zero-Trust Secret Handling**
- Session data stored outside repository (`~/.whatsapp/`)
- `.gitignore` prevents accidental commits
- No credentials in logs or code

**Section VII: Comprehensive Audit Logging**
- All detections logged to NDJSON
- Message metadata (sender, timestamp, ID)
- No message content in audit logs (privacy)

**Section XIII: Emergency Stop**
- Create `AI_Employee_Vault/EMERGENCY_STOP.md`
- Watcher stops polling immediately
- No messages processed until file removed

---

## Performance Tuning

### Polling Interval

Default: 30 seconds (2 checks per minute)

**Adjusting Interval:**
```bash
# More responsive (15 seconds)
WHATSAPP_CHECK_INTERVAL=15

# Less frequent (60 seconds)
WHATSAPP_CHECK_INTERVAL=60
```

**Guidelines:**
- **15-30s:** Real-time monitoring (recommended)
- **60s:** Low-priority monitoring
- **120s+:** Batch processing only

**WhatsApp Web Limits:**
- No official rate limits
- 30s is safe and responsive
- Avoid sub-10s intervals (excessive polling)

### Resource Usage

**Browser Memory:**
- Chromium: ~200-400 MB RAM
- Headless mode: ~150 MB (lower)
- Visible mode: ~300 MB (higher)

**CPU Usage:**
- Idle: <1% CPU
- During polling: 5-10% CPU spike
- Session load: 15-20% CPU briefly

---

## Testing

### Manual End-to-End Test

Follow the procedure in `tests/manual/T0XX_WHATSAPP_E2E_TEST_PROCEDURE.md`:

1. **Authentication Test:** QR scan, session save, restart verification
2. **Detection Test:** Send message with keyword, verify action file
3. **Approval Test:** Edit status, verify file moved
4. **Emergency Stop Test:** Create EMERGENCY_STOP.md, verify polling stops

### Automated Unit Tests

```bash
# Run WhatsApp watcher tests
uv run pytest tests/test_whatsapp_watcher.py -v

# Expected: 11/11 tests PASSED
```

---

## Next Steps

After successful setup:

1. **Monitor Dashboard:** Check `AI_Employee_Vault/Dashboard.md` for WhatsApp status
2. **Test Message:** Send test message with "urgent" keyword
3. **Verify Detection:** Action file appears in `Needs_Action/` within 30 seconds
4. **Test Approval:** Edit status to `approved`, verify file moves
5. **Production Use:** Enable headless mode, monitor audit logs

---

## Advanced Configuration (Future)

### Contact-Specific Rules

Future enhancement will support contact-based priority:

```yaml
# config/whatsapp_keywords.yaml
contacts:
  - name: "Boss"
    keywords: []  # All messages = high priority
    auto_notify: true
  - name: "Client A"
    keywords: ["payment", "invoice"]
    priority: high
```

### Auto-Response Templates

Future enhancement will enable template-based responses:

```yaml
# config/whatsapp_responses.yaml
templates:
  - keyword: "invoice"
    response: "Received your invoice. Will process within 24 hours."
    auto_send: false  # Require human approval
```

---

## Support and Troubleshooting

### Logs Location

**Audit Logs:** `AI_Employee_Vault/Logs/YYYY-MM-DD.json`
**Watcher Logs:** Stdout (when running watcher)

### Diagnostic Commands

```bash
# Check watcher is running
ps aux | grep whatsapp_watcher

# View recent WhatsApp events
tail -20 AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | jq 'select(.actor=="whatsapp_watcher")'

# Count messages detected today
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | jq -s '[.[] | select(.action_type=="whatsapp_message_detected")] | length'

# Check session validity
ls -lh ~/.whatsapp/session/cookies.json
```

### Getting Help

For issues not covered in this guide:
1. Check constitution compliance: `.specify/memory/constitution.md`
2. Review implementation plan: `~/.claude/plans/proud-splashing-snail.md`
3. Examine test cases: `tests/test_whatsapp_watcher.py`
4. Review Phase 1 (Gmail) setup for similar patterns: `docs/GMAIL_SETUP.md`

---

**Last Updated:** 2026-02-14
**Phase:** Silver Tier Phase 2 - WhatsApp Integration
**Status:** Ready for Production Testing
