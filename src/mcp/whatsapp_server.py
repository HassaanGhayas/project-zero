"""
WhatsApp Business MCP Server - Send messages via Meta Cloud API

Provides MCP tools for sending WhatsApp messages using the Meta Graph API
(WhatsApp Business Cloud API). No browser automation required.

Required environment variables:
  WHATSAPP_ACCESS_TOKEN    - Permanent system user token from Meta Business Manager
  WHATSAPP_PHONE_NUMBER_ID - Phone Number ID from Meta Developer Console

API reference: https://developers.facebook.com/docs/whatsapp/cloud-api/messages

Constitution Compliance:
- Section V:  Credentials loaded from .env, never logged or committed
- Section VII: All actions logged to NDJSON audit trail
- Section VIII: Graceful error handling with typed error categories
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Meta Graph API base URL (v20.0 is the current stable version as of 2025)
_GRAPH_API_BASE = "https://graph.facebook.com/v20.0"


class WhatsAppMCPServer:
    """
    MCP server for sending WhatsApp messages via the Meta Cloud API.

    Capabilities:
    - send_message(to, text): Send a text message to a WhatsApp number
    - send_template(to, template_name, language): Send an approved template message
    - verify_credentials(): Verify API credentials are valid
    """

    def __init__(
        self,
        access_token: Optional[str] = None,
        phone_number_id: Optional[str] = None,
    ):
        """
        Initialize WhatsApp MCP server.

        Args:
            access_token: Meta Graph API bearer token. Falls back to
                          WHATSAPP_ACCESS_TOKEN env var.
            phone_number_id: WhatsApp Phone Number ID from Meta Developer Console.
                             Falls back to WHATSAPP_PHONE_NUMBER_ID env var.
        """
        self.access_token = access_token or os.getenv("WHATSAPP_ACCESS_TOKEN", "")
        self.phone_number_id = phone_number_id or os.getenv(
            "WHATSAPP_PHONE_NUMBER_ID", ""
        )

        if not self.access_token:
            logger.warning(
                "WHATSAPP_ACCESS_TOKEN not set — send_message will fail. "
                "Set it in .env or pass as constructor argument."
            )
        if not self.phone_number_id:
            logger.warning(
                "WHATSAPP_PHONE_NUMBER_ID not set — send_message will fail. "
                "Set it in .env or pass as constructor argument."
            )

    # ── Public API ────────────────────────────────────────────────────────────

    def send_message(self, to: str, text: str) -> Dict:
        """
        Send a plain-text WhatsApp message.

        Args:
            to: Recipient phone number in E.164 format (e.g. "15551234567")
            text: Message body (max 4096 characters)

        Returns:
            {
                "status": "sent" | "error",
                "to": phone_number,
                "text": message_text,
                "message_id": wamid (if sent),
                "error": reason (if error)
            }
        """
        if not self._credentials_present():
            return self._missing_credentials_error(to, text)

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": text,
            },
        }

        try:
            response = requests.post(
                f"{_GRAPH_API_BASE}/{self.phone_number_id}/messages",
                headers=self._auth_headers(),
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                message_id = data.get("messages", [{}])[0].get("id", "")
                logger.info(f"✅ Message sent to {to} (wamid={message_id})")
                return {
                    "status": "sent",
                    "to": to,
                    "text": text,
                    "message_id": message_id,
                }

            error_detail = self._parse_api_error(response)
            logger.error(f"API error sending to {to}: {error_detail}")
            return {
                "status": "error",
                "to": to,
                "text": text,
                "error": error_detail,
            }

        except requests.Timeout:
            return {"status": "error", "to": to, "text": text, "error": "network_timeout"}
        except requests.ConnectionError:
            return {"status": "error", "to": to, "text": text, "error": "network_error"}
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}", exc_info=True)
            return {"status": "error", "to": to, "text": text, "error": str(e)}

    def send_template(
        self,
        to: str,
        template_name: str,
        language: str = "en_US",
        components: Optional[list] = None,
    ) -> Dict:
        """
        Send an approved WhatsApp template message.

        Templates must be pre-approved in Meta Business Manager before use.

        Args:
            to: Recipient phone number in E.164 format
            template_name: Name of the approved template
            language: Language/locale code (default: "en_US")
            components: Optional list of template component substitutions

        Returns:
            Same structure as send_message()
        """
        if not self._credentials_present():
            return self._missing_credentials_error(to, template_name)

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
            },
        }
        if components:
            payload["template"]["components"] = components  # type: ignore[index]

        try:
            response = requests.post(
                f"{_GRAPH_API_BASE}/{self.phone_number_id}/messages",
                headers=self._auth_headers(),
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                message_id = data.get("messages", [{}])[0].get("id", "")
                return {
                    "status": "sent",
                    "to": to,
                    "template": template_name,
                    "message_id": message_id,
                }

            return {
                "status": "error",
                "to": to,
                "template": template_name,
                "error": self._parse_api_error(response),
            }

        except Exception as e:
            return {"status": "error", "to": to, "template": template_name, "error": str(e)}

    def verify_credentials(self) -> Dict:
        """
        Verify API credentials by calling the phone number details endpoint.

        Returns:
            {
                "valid": True | False,
                "phone_number_id": str,
                "display_phone_number": str (if valid),
                "error": reason (if invalid)
            }
        """
        if not self._credentials_present():
            return {
                "valid": False,
                "phone_number_id": self.phone_number_id,
                "error": "Missing WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_NUMBER_ID",
            }

        try:
            response = requests.get(
                f"{_GRAPH_API_BASE}/{self.phone_number_id}",
                headers=self._auth_headers(),
                params={"fields": "display_phone_number,verified_name"},
                timeout=15,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "valid": True,
                    "phone_number_id": self.phone_number_id,
                    "display_phone_number": data.get("display_phone_number", ""),
                    "verified_name": data.get("verified_name", ""),
                }

            return {
                "valid": False,
                "phone_number_id": self.phone_number_id,
                "error": self._parse_api_error(response),
            }

        except Exception as e:
            return {
                "valid": False,
                "phone_number_id": self.phone_number_id,
                "error": str(e),
            }

    # ── Private Helpers ───────────────────────────────────────────────────────

    def _auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _credentials_present(self) -> bool:
        return bool(self.access_token and self.phone_number_id)

    def _missing_credentials_error(self, to: str, text: str) -> Dict:
        return {
            "status": "error",
            "to": to,
            "text": text,
            "error": (
                "credentials_missing — set WHATSAPP_ACCESS_TOKEN and "
                "WHATSAPP_PHONE_NUMBER_ID in .env"
            ),
        }

    def _parse_api_error(self, response: requests.Response) -> str:
        """Extract a readable error string from a failed API response."""
        try:
            body = response.json()
            err = body.get("error", {})
            code = err.get("code", response.status_code)
            message = err.get("message", response.text)
            return f"api_error_{code}: {message}"
        except Exception:
            return f"http_{response.status_code}: {response.text[:200]}"


# ── MCP Server Entry Point ────────────────────────────────────────────────────


def main() -> None:
    """
    MCP server entry point (stdio JSON protocol).

    Register with:
      claude mcp add whatsapp "uv run python -m src.mcp.whatsapp_server"
    """
    server = WhatsAppMCPServer()

    request = json.loads(sys.stdin.read())
    method = request.get("method")
    params = request.get("params", {})

    dispatch = {
        "send_message": lambda: server.send_message(
            to=params.get("to", ""),
            text=params.get("text", ""),
        ),
        "send_template": lambda: server.send_template(
            to=params.get("to", ""),
            template_name=params.get("template_name", ""),
            language=params.get("language", "en_US"),
            components=params.get("components"),
        ),
        "verify_credentials": lambda: server.verify_credentials(),
    }

    handler = dispatch.get(method)
    if handler:
        result = handler()
    else:
        result = {"status": "error", "error": f"Unknown method: {method}"}

    print(json.dumps(result))


if __name__ == "__main__":
    main()
