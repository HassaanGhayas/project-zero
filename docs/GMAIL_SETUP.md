# Gmail OAuth2 Setup Guide

Complete step-by-step instructions to authenticate with Gmail API and enable email automation.

## Prerequisites

- Google account with Gmail
- Python 3.12+ installed
- Project cloned: `git clone <repo> && cd project-zero`

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click **Create Project**
3. Enter name: `AI-Employee-Gmail`
4. Click **Create**
5. Wait for project to initialize (1-2 minutes)

## Step 2: Enable Gmail API

1. In Google Cloud Console, search for **Gmail API**
2. Click **Gmail API** result
3. Click **Enable**
4. Wait for enablement to complete

## Step 3: Create OAuth2 Credentials

1. In left sidebar, click **Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. If prompted: "Configure OAuth consent screen first"
   - Click **Configure Consent Screen**
   - Choose **External** user type
   - Click **Create**
   - Fill in **App name**: `AI Employee`
   - Fill in **User support email**: your-email@gmail.com
   - Fill in **Developer contact**: your-email@gmail.com
   - Click **Save and Continue**
   - Click **Save and Continue** on scopes page
   - Click **Save and Continue** on summary page
   - Return to credentials page

4. Click **+ Create Credentials** → **OAuth client ID** again
5. Choose **Application type**: Desktop application
6. Click **Create**
7. Click **Download JSON** (save as `credentials.json`)

## Step 4: Place Credentials File

```bash
# Create ~/.google directory
mkdir -p ~/.google

# Copy credentials.json
cp ~/Downloads/credentials.json ~/.google/credentials.json

# Verify
ls -la ~/.google/credentials.json
```

Expected output:
```
-rw-r--r--  1 user  staff  1234 Feb 10 10:00 credentials.json
```

## Step 5: Run OAuth Setup Script

```bash
cd /home/hasss/projects/project-zero

# Run the setup script
uv run python scripts/setup_gmail_oauth.py
```

**What happens:**
1. Browser opens to Google OAuth consent screen
2. You see: "AI Employee wants access to your Gmail"
3. Click **Allow** to grant permissions
4. Browser redirects to: `http://localhost:8080/` with success message
5. Script creates `~/.google/token.json`

**Expected output:**
```
✅ OAuth2 authentication successful!
✅ Token saved to: /home/hasss/.google/token.json
✅ Credentials are valid and ready to use
```

## Step 6: Configure Environment Variables

```bash
cd /home/hasss/projects/project-zero

# Edit .env file
nano .env
```

Update these lines:
```bash
GMAIL_CREDENTIALS_PATH=/home/hasss/.google/credentials.json
GMAIL_TOKEN_PATH=/home/hasss/.google/token.json
GMAIL_CHECK_INTERVAL=120
VAULT_PATH=/home/hasss/projects/project-zero/AI_Employee_Vault
```

Save and exit (Ctrl+X, Y, Enter)

## Step 7: Verify Setup

```bash
# Load environment variables
source .env

# Test Gmail API connection
uv run python scripts/setup_gmail_oauth.py

# Expected output
✅ Token is valid and not expired
✅ Gmail API connection successful
```

## Step 8: Start Watchers

```bash
# Start all 4 watchers
uv run -m src.watchers.run_all_watchers
```

You should see:
```
============================================================
🚀 All watchers running - Real-time AI Employee active
============================================================
✅ Gmail watcher started (Gmail API → Needs_Action/)
```

## Troubleshooting

### Error: "credentials.json not found"

**Solution:**
```bash
# Verify file exists
ls -la ~/.google/credentials.json

# If not, download from Google Cloud Console again:
# Google Cloud Console → Credentials → OAuth 2.0 Client IDs → Download JSON
```

### Error: "Token expired"

**Solution:**
```bash
# Remove old token
rm ~/.google/token.json

# Re-authenticate
uv run python scripts/setup_gmail_oauth.py
```

### Error: "Invalid grant"

**Cause:** Token has been revoked or credentials invalid
**Solution:**
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Scroll to "Third-party apps with account access"
3. Find "AI Employee" and click **Remove access**
4. Run setup script again

### Browser doesn't open automatically

**Solution:**
```bash
# Check console output for localhost URL
# Manually open in browser: http://localhost:8080
```

### Error: "SSL certificate verify failed"

**Solution (macOS only):**
```bash
# Run Python certificate installer
/Applications/Python\ 3.12/Install\ Certificates.command
```

## Gmail API Permissions

Your OAuth token grants:
- ✅ Read emails (get, list, query)
- ✅ Modify emails (archive, mark as read)
- ✅ Create labels
- ❌ Send emails (intentionally restricted - requires approval)
- ❌ Delete emails (intentionally restricted)

This is intentional for safety - no autonomous sending/deletion.

## Security Notes

1. **Never commit credentials.json or token.json to Git**
   - Already in `.gitignore`
   - Verify: `git status | grep google`

2. **Token is stored locally**
   - File: `~/.google/token.json`
   - Readable only by your user
   - Expires every 7 days (auto-refreshed)

3. **Revoking access**
   ```bash
   # Remove both files
   rm ~/.google/credentials.json ~/.google/token.json

   # Then revoke in Google Account Security
   # https://myaccount.google.com/security
   ```

4. **Using on multiple machines**
   - Each machine needs its own `token.json`
   - Run `setup_gmail_oauth.py` on each machine
   - Share only `credentials.json` (it's a public client ID)

## What Happens Next

After setup, Gmail watcher will:
1. Poll Gmail API every 120 seconds
2. Search for: `is:unread is:important label:inbox`
3. Create action files in `Needs_Action/` folder
4. Wait for your approval (edit status to "approved")
5. Archive email in Gmail when approved

See `MANUAL_E2E_TEST_GUIDE.md` to test the complete workflow.

## Advanced: Custom Scopes

To modify Gmail permissions, edit `scripts/setup_gmail_oauth.py`:

```python
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',  # Current: read + modify
    # 'https://www.googleapis.com/auth/gmail.send',    # Add to: enable sending
    # 'https://www.googleapis.com/auth/gmail.labels',  # Add to: manage labels
]
```

Then re-authenticate by running `setup_gmail_oauth.py`.

## Help

```bash
# View setup script
cat scripts/setup_gmail_oauth.py

# Check token validity
python -c "import json; print(json.load(open('/home/hasss/.google/token.json')))"

# View recent Gmail API calls
tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | grep gmail
```

---

**Next step**: [Test the system with MANUAL_E2E_TEST_GUIDE.md](../MANUAL_E2E_TEST_GUIDE.md)
