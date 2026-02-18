"""
LinkedIn API v2 MCP server.

Wraps LinkedIn ugcPosts and userinfo endpoints with OAuth2 token management.
Tokens are auto-refreshed on 401 responses.
"""
import logging
import os
from pathlib import Path
from typing import Optional

import requests

from src.api.linkedin_oauth import is_token_expired, load_token, refresh_access_token, save_token

logger = logging.getLogger(__name__)
LINKEDIN_API_BASE = "https://api.linkedin.com/v2"


class LinkedInServer:
    def __init__(self, client_id: str, client_secret: str, token_path: Path) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_path = token_path
        self._token: Optional[dict] = None

    def _get_token(self) -> dict:
        if self._token is None:
            self._token = load_token(self.token_path)
        if is_token_expired(self._token):
            logger.info("Refreshing expired LinkedIn access token")
            self._token = refresh_access_token(
                self._token, self.client_id, self.client_secret
            )
            save_token(self._token, self.token_path)
        return self._token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_token()['access_token']}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    def get_member_urn(self) -> str:
        resp = requests.get(f"{LINKEDIN_API_BASE}/userinfo", headers=self._headers())
        resp.raise_for_status()
        return f"urn:li:person:{resp.json()['sub']}"

    def post_text(self, text: str) -> dict:
        member_urn = self.get_member_urn()
        payload = {
            "author": member_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }
        resp = requests.post(
            f"{LINKEDIN_API_BASE}/ugcPosts",
            json=payload,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def verify_credentials(self) -> bool:
        try:
            resp = requests.get(f"{LINKEDIN_API_BASE}/userinfo", headers=self._headers())
            resp.raise_for_status()
            return True
        except requests.HTTPError:
            return False


def create_server_from_env(token_path: Optional[Path] = None) -> "LinkedInServer":
    return LinkedInServer(
        client_id=os.environ["LINKEDIN_CLIENT_ID"],
        client_secret=os.environ["LINKEDIN_CLIENT_SECRET"],
        token_path=token_path
        or Path(
            os.environ.get("LINKEDIN_TOKEN_PATH", "~/.linkedin/token.json")
        ).expanduser(),
    )
