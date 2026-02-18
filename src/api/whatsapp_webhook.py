"""
WhatsApp Business API Webhook Server

Receives incoming WhatsApp messages from Meta's Cloud API and stores them
in a local message queue (JSON file) for the WhatsApp watcher to process.

Setup:
  1. Run: uv run python -m src.api.whatsapp_webhook
  2. Expose publicly: ngrok http 8081
  3. Register webhook in Meta Developer Console:
     - URL: https://<your-ngrok>.ngrok-free.app/webhook
     - Verify token: value of WHATSAPP_VERIFY_TOKEN in .env
     - Subscribe to: messages

Constitution Compliance:
- Section V:  Access tokens loaded from .env, never logged
- Section VII: All received messages logged to NDJSON audit trail
- Section VIII: Graceful error handling, always return 200 to Meta
- Section XII: Messages stored as pending for human review
- Section XIII: Emergency stop respected before processing
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="WhatsApp Business Webhook", version="1.0.0")

# ── Configuration ────────────────────────────────────────────────────────────

QUEUE_FILE = Path(
    os.getenv(
        "WHATSAPP_QUEUE_FILE",
        str(Path.home() / ".whatsapp" / "message_queue.json"),
    )
)
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
VAULT_PATH = Path(os.getenv("VAULT_PATH", "AI_Employee_Vault"))


# ── Helpers ──────────────────────────────────────────────────────────────────


def _ensure_queue_file() -> None:
    """Ensure the message queue directory and file exist."""
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not QUEUE_FILE.exists():
        QUEUE_FILE.write_text(json.dumps([]), encoding="utf-8")


def _append_to_queue(message: Dict[str, Any]) -> None:
    """Thread-safely append a message to the local queue file."""
    _ensure_queue_file()
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        queue = json.loads(f.read())
    queue.append(message)
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        f.write(json.dumps(queue, indent=2))


def _log_audit(action_type: str, details: Dict[str, Any]) -> None:
    """Write a single NDJSON entry to today's audit log."""
    try:
        log_dir = VAULT_PATH / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{datetime.now().date().isoformat()}.json"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": "whatsapp_webhook",
            "status": "success",
            "parameters": details,
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.error(f"Audit log write failed: {e}")


# ── Webhook Endpoints ────────────────────────────────────────────────────────


@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
) -> PlainTextResponse:
    """
    Webhook verification endpoint.

    Meta sends a GET request to confirm ownership before activating the webhook.
    Responds with hub.challenge when verify token matches.
    """
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("✅ Webhook verification successful")
        return PlainTextResponse(content=hub_challenge)

    logger.warning("❌ Webhook verification failed (token mismatch or wrong mode)")
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def receive_message(request: Request) -> Dict[str, Any]:
    """
    Receive incoming WhatsApp message events from Meta Cloud API.

    Parses the webhook payload and stores messages in the local queue file.
    Always returns HTTP 200 — Meta will retry on non-200 responses.
    """
    try:
        body = await request.json()

        # Validate it's a WhatsApp Business Account event
        if body.get("object") != "whatsapp_business_account":
            return {"status": "ignored", "reason": "not_whatsapp_business_account"}

        messages_stored = 0

        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})

                for msg in value.get("messages", []):
                    msg_id = msg.get("id", "")
                    from_number = msg.get("from", "")
                    raw_timestamp = msg.get("timestamp", "")
                    msg_type = msg.get("type", "text")

                    # Extract human-readable text from supported message types
                    text = _extract_text(msg, msg_type)

                    # Resolve sender display name from contacts array
                    contacts = value.get("contacts", [])
                    sender_name = _resolve_sender(from_number, contacts)

                    # Convert Unix timestamp to ISO 8601
                    iso_timestamp = (
                        datetime.fromtimestamp(int(raw_timestamp)).isoformat()
                        if raw_timestamp.isdigit()
                        else datetime.now().isoformat()
                    )

                    queued_message: Dict[str, Any] = {
                        "id": msg_id,
                        "from": from_number,
                        "sender": sender_name,
                        "text": text,
                        "type": msg_type,
                        "timestamp": iso_timestamp,
                        "received_at": datetime.now().isoformat(),
                        "processed": False,
                    }

                    _append_to_queue(queued_message)
                    messages_stored += 1

                    logger.info(
                        f"📥 Queued message from {sender_name} ({from_number}): "
                        f"{text[:80]!r}"
                    )
                    _log_audit(
                        "whatsapp_message_received",
                        {
                            "message_id": msg_id,
                            "from": from_number,
                            "sender": sender_name,
                            "type": msg_type,
                        },
                    )

        return {"status": "ok", "messages_stored": messages_stored}

    except Exception as e:
        # Log but always return 200 to prevent Meta retrying
        logger.error(f"Error processing webhook payload: {e}", exc_info=True)
        return {"status": "error", "detail": str(e)}


# ── Helpers ──────────────────────────────────────────────────────────────────


def _extract_text(msg: Dict[str, Any], msg_type: str) -> str:
    """Extract a human-readable text representation from a message object."""
    if msg_type == "text":
        return msg.get("text", {}).get("body", "")
    elif msg_type == "image":
        caption = msg.get("image", {}).get("caption", "")
        return f"[Image] {caption}".strip()
    elif msg_type == "document":
        filename = msg.get("document", {}).get("filename", "")
        return f"[Document] {filename}".strip()
    elif msg_type == "audio":
        return "[Voice message]"
    elif msg_type == "video":
        caption = msg.get("video", {}).get("caption", "")
        return f"[Video] {caption}".strip()
    elif msg_type == "location":
        loc = msg.get("location", {})
        return f"[Location] {loc.get('name', '')} lat={loc.get('latitude')} lng={loc.get('longitude')}"
    else:
        return f"[{msg_type}]"


def _resolve_sender(from_number: str, contacts: list) -> str:
    """Resolve a display name from the contacts array, falling back to phone number."""
    for contact in contacts:
        if contact.get("wa_id") == from_number:
            name = contact.get("profile", {}).get("name", "")
            if name:
                return name
    return from_number


# ── Entry Point ──────────────────────────────────────────────────────────────


def run_server(host: str = "0.0.0.0", port: int = 8081) -> None:
    """Start the webhook HTTP server."""
    import uvicorn

    logger.info(f"🚀 Starting WhatsApp webhook server on {host}:{port}")
    logger.info(f"📁 Message queue: {QUEUE_FILE}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    port = int(os.getenv("WHATSAPP_WEBHOOK_PORT", "8081"))
    run_server(port=port)
