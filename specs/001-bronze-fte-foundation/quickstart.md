# Quickstart Guide: Bronze Tier AI FTE Foundation

**Feature**: Bronze Tier AI FTE Foundation
**Branch**: `001-bronze-fte-foundation`
**Date**: 2026-02-07
**Estimated Setup Time**: 15-20 minutes

---

## Overview

This guide walks you through setting up and running the Bronze Tier AI FTE system. By the end, you'll have:
- ✅ A file system watcher monitoring `Inbox/` for dropped files
- ✅ Three Claude Code agent skills for vault operations
- ✅ A populated Obsidian vault with Dashboard and Company Handbook
- ✅ Structured audit logging

---

## Prerequisites

Before starting, ensure you have:

| Requirement | Version | Installation |
|-------------|---------|--------------|
| Python | 3.12+ | [python.org/downloads](https://python.org/downloads/) |
| Claude Code | Latest | [claude.com/product/claude-code](https://claude.com/product/claude-code) |
| Obsidian | 1.10.6+ | [obsidian.md/download](https://obsidian.md/download) |
| Git | Any recent | [git-scm.com](https://git-scm.com/) |
| uv (Python package manager) | Latest | `pip install uv` |

**Verify installations**:
```bash
python --version   # Should show 3.12 or higher
claude --version   # Should show Claude Code CLI
git --version
uv --version
```

---

## Step 1: Clone and Setup Project

```bash
# Clone the repository
git clone <repository-url>
cd project-zero

# Checkout the Bronze Tier branch
git checkout 001-bronze-fte-foundation

# Install Python dependencies
uv sync

# Verify watchdog is installed
python -c "from watchdog.observers import Observer; print('✅ Watchdog installed')"
```

---

## Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

**Required .env settings**:
```bash
# Path to your Obsidian vault (absolute path)
VAULT_PATH=/home/yourusername/project-zero/AI_Employee_Vault

# Inbox folder path (relative to vault or absolute)
INBOX_WATCH_PATH=/home/yourusername/project-zero/AI_Employee_Vault/Inbox

# Watcher check interval (not used in Bronze event-driven mode, but required)
WATCHER_CHECK_INTERVAL=5

# Development mode (safe defaults)
DRY_RUN=false
DEV_MODE=true
```

**Important**: Replace `/home/yourusername/` with your actual home directory path.

---

## Step 3: Verify Vault Structure

The vault should already exist with the following structure:

```bash
AI_Employee_Vault/
├── Dashboard.md                  # Will be populated by update-dashboard skill
├── Company_Handbook.md           # Pre-populated with Bronze Tier rules
├── Inbox/                        # Watched by filesystem watcher
├── Needs_Action/                 # Action files created here
├── Plans/                        # Reserved for Silver Tier
├── Pending_Approval/             # Flagged items go here
├── Approved/                     # Reserved for HITL workflow
├── Rejected/                     # Reserved for HITL workflow
├── In_Progress/                  # Reserved for Silver Tier
├── Done/                         # Completed items
├── Logs/                         # Daily NDJSON audit logs
├── Briefings/                    # Reserved for Gold Tier
├── Accounting/                   # Reserved for Gold Tier
└── Invoices/                     # Reserved for Gold Tier
```

**Verify structure**:
```bash
ls -la AI_Employee_Vault/
```

If any folders are missing, create them:
```bash
mkdir -p AI_Employee_Vault/{Inbox,Needs_Action,Plans,Pending_Approval,Approved,Rejected,In_Progress,Done,Logs,Briefings,Accounting,Invoices}
```

---

## Step 4: Open Vault in Obsidian

1. Launch Obsidian
2. Click "Open folder as vault"
3. Navigate to `project-zero/AI_Employee_Vault/`
4. Click "Open"

**Verify in Obsidian**:
- You should see `Dashboard.md` and `Company_Handbook.md` in the file list
- All folders visible in left sidebar
- Open `Company_Handbook.md` to review Bronze Tier rules

---

## Step 5: Install Claude Code Skills

Claude Code skills are markdown files in `.claude/skills/` that define AI capabilities.

**Verify skills directory**:
```bash
ls -la .claude/skills/
```

You should see:
- `process-inbox.md`
- `update-dashboard.md`
- `vault-report.md`

**Test skill discovery**:
```bash
# Start Claude Code CLI
claude

# In Claude, type:
# "What skills are available?"
```

Claude should list the three Bronze Tier skills.

---

## Step 6: Start the File System Watcher

The watcher monitors `Inbox/` for new files and creates action files in `Needs_Action/`.

**Start watcher (foreground)**:
```bash
# From project root
python src/watchers/run_watcher.py
```

**Expected output**:
```
[2026-02-07 15:30:00] INFO: Starting filesystem_watcher
[2026-02-07 15:30:00] INFO: Watching: /home/user/project-zero/AI_Employee_Vault/Inbox
[2026-02-07 15:30:00] INFO: Watcher started successfully
[2026-02-07 15:30:00] INFO: Press Ctrl+C to stop
```

**Leave this terminal running**. The watcher will now detect files dropped into `Inbox/`.

---

## Step 7: Test the Complete Flow

Open a **new terminal** (keep watcher running) and test the end-to-end flow.

### 7.1: Drop a Test File

```bash
# Create a test file
echo "This is a test document" > /tmp/test_document.txt

# Copy to Inbox
cp /tmp/test_document.txt AI_Employee_Vault/Inbox/
```

### 7.2: Verify Action File Created

**Watcher terminal should show**:
```
[2026-02-07 15:31:00] INFO: File detected: test_document.txt
[2026-02-07 15:31:00] INFO: Action file created: Needs_Action/FILE_test_document.txt.md
```

**Check the action file**:
```bash
cat AI_Employee_Vault/Needs_Action/FILE_test_document.txt.md
```

**Expected content**:
```yaml
---
type: text
original_name: test_document.txt
size: 26
file_type: .txt
category: text
received: 2026-02-07T15:31:00Z
priority: low
status: pending
---

## File Details
Detected new file drop for processing.

## Suggested Actions
- [ ] Review content
- [ ] Process or flag for approval
- [ ] Move to Done/ when complete
```

### 7.3: Check Audit Log

```bash
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json
```

**Expected entries** (NDJSON format):
```json
{"timestamp":"2026-02-07T15:30:00Z","action_id":"watcher_001","action_type":"watcher_started","actor":"filesystem_watcher","target":"Inbox/","parameters":{},"approval_status":null,"approved_by":null,"result":"success","error":null,"duration":null}
{"timestamp":"2026-02-07T15:31:00Z","action_id":"watcher_002","action_type":"file_detected","actor":"filesystem_watcher","target":"Inbox/test_document.txt","parameters":{"size":26,"file_type":".txt"},"approval_status":null,"approved_by":null,"result":"success","error":null,"duration":5}
{"timestamp":"2026-02-07T15:31:00Z","action_id":"watcher_003","action_type":"action_file_created","actor":"filesystem_watcher","target":"Needs_Action/FILE_test_document.txt.md","parameters":{"source":"Inbox/test_document.txt","category":"text"},"approval_status":null,"approved_by":null,"result":"success","error":null,"duration":12}
```

### 7.4: Process with Claude Code Skill

```bash
# Start Claude Code (in new terminal or same terminal)
claude

# In Claude, type:
# "Process my inbox"
```

**Expected Claude response**:
```
✅ Inbox processing complete

📊 Summary:
- Total items processed: 1
- Auto-completed: 1 (text file under threshold)
- Flagged for approval: 0
- Errors: 0

✅ Completed (moved to Done/):
  - FILE_test_document.txt.md (text file, 26 bytes)

📋 Dashboard updated with current queue status
```

### 7.5: Verify File Moved

```bash
# Check that file moved to Done/
ls AI_Employee_Vault/Done/FILE_test_document.txt.md

# Check Needs_Action is now empty
ls AI_Employee_Vault/Needs_Action/
```

### 7.6: Check Dashboard

Open `Dashboard.md` in Obsidian. You should see:
- Updated timestamp
- Queue counts reflecting the processed item
- Recent activity showing the inbox processing

**Or use vault-report skill**:
```bash
claude

# In Claude:
# "What's the status?"
```

---

## Step 8: Test Emergency Stop

Bronze Tier includes an emergency stop mechanism per constitution Section XII.

```bash
# Create emergency stop file
touch AI_Employee_Vault/EMERGENCY_STOP.md

# Try to process inbox (in Claude)
# "Process my inbox"
```

**Expected response**:
```
🛑 Emergency stop active - operations halted

EMERGENCY_STOP.md detected in vault root.
No items processed.
```

**Remove emergency stop**:
```bash
rm AI_Employee_Vault/EMERGENCY_STOP.md
```

---

## Common Issues & Solutions

### Issue 1: Watcher doesn't start

**Error**: `ModuleNotFoundError: No module named 'watchdog'`

**Solution**:
```bash
uv sync
# or
pip install watchdog>=4.0.0
```

### Issue 2: Permission denied on Inbox/

**Error**: `PermissionError: [Errno 13] Permission denied: 'Inbox/'`

**Solution**:
```bash
chmod -R u+rw AI_Employee_Vault/
```

### Issue 3: Skills not discovered by Claude

**Solution**:
1. Verify skills are in `.claude/skills/`
2. Check YAML frontmatter is valid
3. Restart Claude Code CLI

### Issue 4: Log file not created

**Error**: No log file in `Logs/`

**Solution**:
```bash
# Ensure Logs/ folder exists
mkdir -p AI_Employee_Vault/Logs

# Check folder permissions
chmod u+w AI_Employee_Vault/Logs/
```

### Issue 5: Dashboard not updating

**Solution**:
1. Manually invoke: `claude` → "Update the dashboard"
2. Check Dashboard.md file permissions
3. Verify logs are being written

---

## Daily Operations

### Morning Routine (2 minutes)

```bash
# Start Claude Code
claude

# Get quick status
# "What's the status?"

# Review any pending approvals in Obsidian
# Open: Pending_Approval/ folder

# Process inbox if items pending
# "Process my inbox"
```

### Starting Watcher

```bash
# Foreground (Bronze Tier)
python src/watchers/run_watcher.py

# Or in background (press Ctrl+Z, then):
bg
disown

# Or use tmux/screen for persistent sessions
```

### Stopping Watcher

```bash
# In watcher terminal
Ctrl+C

# Graceful shutdown will log watcher_stopped entry
```

### Reviewing Audit Logs

```bash
# View today's log
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | jq .

# Count today's actions
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | wc -l

# Filter errors only
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | jq 'select(.result=="error")'
```

---

## Next Steps

Once Bronze Tier is working, consider:

1. **Add more test files**: Drop various file types (PDF, images, data files) to test categorization
2. **Customize Company_Handbook.md**: Adjust auto-approve thresholds
3. **Review audit logs**: Verify all actions are logged correctly
4. **Plan Silver Tier**: Gmail watcher, MCP servers, process management

---

## Constitution Compliance Checklist

✅ **Section II**: Vault folders follow mandated structure
✅ **Section IV**: All AI functionality implemented as skills
✅ **Section V**: Secrets in `.env` (gitignored)
✅ **Section VII**: Structured audit logging to `Logs/`
✅ **Section VIII**: Watcher handles SIGINT/SIGTERM gracefully
✅ **Section XI**: Dashboard supports 2-minute daily check
✅ **Section XII**: Emergency stop mechanism (EMERGENCY_STOP.md)

---

## Troubleshooting Support

If you encounter issues:

1. **Check logs**: `AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json`
2. **Verify environment**: Review `.env` settings
3. **Test components individually**:
   - Watcher: Drop test file in Inbox/
   - Skill: Manually invoke in Claude
   - Dashboard: Check file permissions

---

## References

- **Spec**: `specs/001-bronze-fte-foundation/spec.md`
- **Plan**: `specs/001-bronze-fte-foundation/plan.md`
- **Data Model**: `specs/001-bronze-fte-foundation/data-model.md`
- **Skill Contracts**: `specs/001-bronze-fte-foundation/contracts/`
- **Constitution**: `.specify/memory/constitution.md`
