# WhatsApp Business API Setup Guide

Complete guide for setting up WhatsApp message monitoring via the Meta Cloud API
for the AI Employee system (Silver Tier Phase 2).

---

## Overview

The WhatsApp integration uses the **Meta WhatsApp Business Cloud API** — no browser
automation required. Incoming messages are delivered to a local webhook server,
stored in a JSON queue, and picked up by the WhatsApp watcher every 30 seconds.

```
Meta Cloud API
    │  POST /webhook (new messages)
    ▼
src/api/whatsapp_webhook.py  ──writes──▶  ~/.whatsapp/message_queue.json
                                                  │
                                          WhatsAppWatcher (polls every 30s)
                                                  │
                                          AI_Employee_Vault/Needs_Action/*.md
```

**Key advantages over browser automation:**
- No QR code scanning or browser sessions
- Reliable delivery via Meta's infrastructure
- Supports sending replies via API
- Works headlessly in production

---

## Prerequisites

### 1. Meta Developer Account

1. Go to **https://developers.facebook.com**
2. Click **My Apps → Create App → Business**
3. Fill in app name and contact email → **Create App**
4. Under "Add a Product", click **Set Up** next to **WhatsApp**

### 2. Collect Your Credentials

From the **WhatsApp → Getting Started** page:

| Credential | Where to find it |
|---|---|
| `WHATSAPP_PHONE_NUMBER_ID` | "Phone Number ID" field on Getting Started page |
| `WHATSAPP_ACCESS_TOKEN` | "Temporary access token" (24h) or permanent system user token |
| `WHATSAPP_VERIFY_TOKEN` | Any secret string **you choose** — used to verify webhook ownership |

**For a permanent access token (production):**
1. Business Settings → System Users → Add
2. Assign WhatsApp app with Full Control
3. Generate Token → select app → copy

### 3. Add a Test Recipient

On the Getting Started page, under "To":
1. Click **Manage phone number list**
2. Add your personal WhatsApp number
3. Verify with the code sent to your phone

---

## Environment Variables

Add to your `.env` file:

```bash
# WhatsApp Business API (Silver Tier Phase 2)
WHATSAPP_ACCESS_TOKEN=EAABwzLixnjYBO...       # from Meta Developer Console
WHATSAPP_PHONE_NUMBER_ID=123456789012345       # from Meta Developer Console
WHATSAPP_VERIFY_TOKEN=my-secret-verify-token   # any string you choose
WHATSAPP_WEBHOOK_PORT=8081
WHATSAPP_CHECK_INTERVAL=30
WHATSAPP_QUEUE_FILE=/home/hasss/.whatsapp/message_queue.json
```

---

## Startup Sequence

Three processes must run together:

### 1. Start the Webhook Server

```bash
uv run python -m src.api.whatsapp_webhook
# Output: 🚀 Starting WhatsApp webhook server on 0.0.0.0:8081
```

### 2. Expose via ngrok (for local development)

```bash
ngrok http 8081
# Copy the https URL: https://abc123.ngrok-free.app
```

> **Production**: Deploy the webhook server to a VPS or cloud function with a static HTTPS URL.

### 3. Register the Webhook in Meta Developer Console

1. Go to **WhatsApp → Configuration → Webhook**
2. Click **Edit**
3. Set **Callback URL**: `https://abc123.ngrok-free.app/webhook`
4. Set **Verify Token**: same value as `WHATSAPP_VERIFY_TOKEN` in your `.env`
5. Click **Verify and Save** (webhook server must be running!)
6. Click **Manage** → subscribe to **messages**

### 4. Start All Watchers

```bash
uv run python -m src.watchers.run_all_watchers
```

---

## Keyword Configuration

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

Only messages containing at least one keyword create action files.
Edit and restart watchers to apply changes.

---

## Workflow

### 1. Message Received

When someone sends a WhatsApp message to your registered number:
1. Meta POSTs the message to `https://your-url/webhook`
2. Webhook server stores it in `~/.whatsapp/message_queue.json` with `processed: false`
3. Audit log entry written: `whatsapp_message_received`

### 2. Watcher Picks Up (every 30s)

1. Reads all `processed: false` entries from queue
2. Marks them `processed: true`
3. Filters by priority keywords
4. Creates action files in `AI_Employee_Vault/Needs_Action/`

### 3. Human Approval

Review the action file in `Needs_Action/`:

```markdown
---
type: message
whatsapp_message_id: wamid.HBgLMTY1...
sender: Client A
received_timestamp: 2026-02-18T10:00:00
status: pending        # ← change to approved or rejected
priority: high
has_attachments: false
category: whatsapp_message
---

## Message Details

**From:** Client A
**Received:** 2026-02-18T10:00:00

**Message:**
Urgent: Need help with payment invoice ASAP
```

Change `status: pending` → `status: approved` to approve.

### 4. Sending Replies

Use the WhatsApp MCP server:

```python
from src.mcp.whatsapp_server import WhatsAppMCPServer

server = WhatsAppMCPServer()
result = server.send_message(to="15551234567", text="We received your message!")
# {"status": "sent", "to": "15551234567", "message_id": "wamid.HBg..."}
```

Or send an approved template:

```python
result = server.send_template(
    to="15551234567",
    template_name="hello_world",
    language="en_US",
)
```

---

## Verifying Credentials

```bash
uv run python -c "
from src.mcp.whatsapp_server import WhatsAppMCPServer
s = WhatsAppMCPServer()
print(s.verify_credentials())
"
# {"valid": true, "phone_number_id": "...", "display_phone_number": "+1 555 ..."}
```

---

## Monitoring and Troubleshooting

### Check Watcher Status

```bash
# View recent WhatsApp events in audit log
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | python3 -c "
import sys, json
for line in sys.stdin:
    e = json.loads(line)
    if 'whatsapp' in e.get('action_type',''):
        print(e)
"
```

### Inspect the Message Queue

```bash
cat ~/.whatsapp/message_queue.json | python3 -m json.tool
```

### Test the Webhook Locally

```bash
# Simulate an incoming message (no Meta credentials needed)
curl -X POST http://localhost:8081/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "id": "test_001",
            "from": "15551234567",
            "timestamp": "1739880000",
            "type": "text",
            "text": {"body": "Urgent: payment needed ASAP"}
          }],
          "contacts": [{"wa_id": "15551234567", "profile": {"name": "Test User"}}]
        }
      }]
    }]
  }'
# Response: {"status":"ok","messages_stored":1}
```

### Common Issues

#### Webhook Verification Fails
- Ensure webhook server is running before clicking "Verify and Save"
- Confirm `WHATSAPP_VERIFY_TOKEN` in `.env` matches the token in Meta Console
- Test manually: `curl "http://localhost:8081/webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=testchallenge"`

#### Messages Not Appearing in Queue
- Check webhook server logs for incoming POST requests
- Verify webhook is subscribed to "messages" in Meta Console (Manage → messages)
- Confirm your number is in the test recipient list

#### No Action Files Created
- Check keywords: `cat config/whatsapp_keywords.yaml`
- Check queue file: `cat ~/.whatsapp/message_queue.json`
- Run watcher in debug mode: `LOG_LEVEL=DEBUG uv run python -m src.watchers.run_all_watchers`

#### Access Token Expired (24h token)
- Replace `WHATSAPP_ACCESS_TOKEN` in `.env` with a fresh token from Meta Console
- Or generate a permanent system user token (recommended for production)

---

## Security

### What's Stored Locally
- Message queue: `~/.whatsapp/message_queue.json` (outside repo)
- Audit logs: `AI_Employee_Vault/Logs/` (message metadata only, no content)

### What's Never Logged
- Access tokens
- Full message content (only metadata in audit trail)

### Constitution Compliance
- **Section V**: Credentials in `.env`, never committed
- **Section VII**: NDJSON audit trail for every received and sent message
- **Section XII**: Human approval required before any action
- **Section XIII**: Emergency stop — create `AI_Employee_Vault/EMERGENCY_STOP.md`

---

## Testing

### Automated Unit Tests

```bash
uv run pytest tests/test_whatsapp_watcher.py -v
# Expected: 20/20 PASSED
```

### End-to-End Test (with real credentials)

1. Start webhook server and ngrok
2. Register webhook in Meta Console
3. Send a WhatsApp message containing "urgent" to your test number
4. Within 30s: verify action file in `AI_Employee_Vault/Needs_Action/`
5. Change `status: pending` → `status: approved`
6. Verify file moves to `AI_Employee_Vault/Approved/`

---

## Architecture Reference

| Component | File | Purpose |
|---|---|---|
| Webhook server | `src/api/whatsapp_webhook.py` | Receives messages from Meta, stores to queue |
| Watcher | `src/watchers/whatsapp_watcher.py` | Polls queue, creates action files |
| MCP server | `src/mcp/whatsapp_server.py` | Sends messages via Graph API |
| Keywords | `config/whatsapp_keywords.yaml` | Priority filter |
| Queue | `~/.whatsapp/message_queue.json` | Local message buffer |

---

**Last Updated:** 2026-02-18
**Phase:** Silver Tier Phase 2 — WhatsApp Business API
**Status:** Ready for Production
