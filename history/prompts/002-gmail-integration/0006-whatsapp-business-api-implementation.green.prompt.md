---
id: "0006"
title: "WhatsApp Business API Implementation"
stage: green
date: "2026-02-18"
surface: agent
model: claude-sonnet-4-6
feature: "002-gmail-integration"
branch: 002-gmail-integration
user: hasss
command: "continue"
labels: ["whatsapp", "business-api", "webhook", "fastapi", "refactor"]
links:
  spec: "null"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - src/api/__init__.py
  - src/api/whatsapp_webhook.py
  - src/watchers/whatsapp_watcher.py
  - src/mcp/whatsapp_server.py
  - src/watchers/run_all_watchers.py
  - tests/test_whatsapp_watcher.py
  - .env.example
  - pyproject.toml
tests:
  - tests/test_whatsapp_watcher.py (20/20 passed)
---

## Prompt

> research whatsapp business api and implement it

(Session continuation: Playwright browser automation had been blocked by WhatsApp's
anti-automation detection, prompting switch to the official Meta Cloud API.)

## Response

Replaced the Playwright-based WhatsApp Web scraping approach (blocked by
anti-automation detection) with the official WhatsApp Business Cloud API (Meta
Graph API v20.0). Full end-to-end implementation:

### New: `src/api/whatsapp_webhook.py`
FastAPI webhook server that:
- Handles GET `/webhook` for Meta ownership verification (hub.challenge)
- Handles POST `/webhook` for incoming message events
- Parses Meta's webhook payload (entry → changes → value → messages)
- Stores unprocessed messages in a local JSON queue file (`~/.whatsapp/message_queue.json`)
- Writes NDJSON audit entries for every received message
- Always returns HTTP 200 to Meta (prevents retries on processing errors)

### Updated: `src/watchers/whatsapp_watcher.py`
- Constructor changed: `session_path` → `queue_file` (no browser session needed)
- `_scan_whatsapp_web()` replaced with `_read_message_queue()`:
  - Reads unprocessed messages from the JSON queue file
  - Marks all entries `processed: True` after reading (prevents re-delivery)
  - Applies keyword filtering (case-insensitive)
  - Handles missing/corrupt queue file gracefully
- Docstring updated to reflect new architecture

### Updated: `src/mcp/whatsapp_server.py`
- Fully rewritten with real Graph API calls
- `send_message(to, text)`: POST to `graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages`
- `send_template(to, template_name, language, components)`: Template message support
- `verify_credentials()`: GET phone number details to confirm token validity
- Proper error categorisation (timeout, connection, API error codes)

### Updated: `src/watchers/run_all_watchers.py`
- WhatsApp watcher init updated: `session_path=` → `queue_file=`
- Reads `WHATSAPP_QUEUE_FILE` env var

### Updated: `tests/test_whatsapp_watcher.py`
- Expanded from 11 to 20 tests (all passing)
- New `TestQueueReading` class (3 tests)
- New `TestDuplicatePrevention.test_queue_messages_marked_processed` test
- All mock targets updated: `_scan_whatsapp_web` → `_read_message_queue`
- Fixtures use `queue_file` (JSON temp file) instead of browser session path

### Updated: `.env.example`
Added new required credentials:
```
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_VERIFY_TOKEN=...
WHATSAPP_WEBHOOK_PORT=8081
WHATSAPP_QUEUE_FILE=~/.whatsapp/message_queue.json
```

### Updated: `pyproject.toml`
Added: `requests>=2.31.0`, `fastapi>=0.110.0`, `uvicorn[standard]>=0.27.0`

### Architecture
```
Meta Cloud API
    │  POST /webhook (incoming messages)
    ▼
src/api/whatsapp_webhook.py  ──writes──▶  ~/.whatsapp/message_queue.json
                                                  │
                                            WhatsAppWatcher
                                          (polls every 30s)
                                                  │
                                          Needs_Action/*.md  (action files)
```

To start the webhook server:
```bash
uv run python -m src.api.whatsapp_webhook
# Then expose via: ngrok http 8081
# Register webhook URL in Meta Developer Console
```

## Outcome

- 20/20 WhatsApp watcher tests passing
- 96/115 total tests passing (no regressions; 19 pre-existing failures unchanged)
- Playwright dependency removed from WhatsApp watcher logic
- Constitution compliant: credentials in .env, NDJSON audit trail, emergency stop, human-in-the-loop
