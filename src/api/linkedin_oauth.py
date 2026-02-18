"""
LinkedIn OAuth2 token management utilities.

Provides load/save/expiry-check/refresh operations for OAuth2 tokens
used by the LinkedIn integration. Tokens are stored as JSON files on disk.
"""
import json
import time
from pathlib import Path

import requests


def load_token(token_path: Path) -> dict:
    if not token_path.exists():
        raise FileNotFoundError(f"LinkedIn token not found at {token_path}")
    return json.loads(token_path.read_text())


def save_token(token: dict, token_path: Path) -> None:
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(json.dumps(token, indent=2))


def is_token_expired(token: dict, buffer_seconds: int = 300) -> bool:
    return int(time.time()) >= token.get("expires_at", 0) - buffer_seconds


def refresh_access_token(token: dict, client_id: str, client_secret: str) -> dict:
    resp = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "refresh_token",
            "refresh_token": token["refresh_token"],
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token", token["refresh_token"]),
        "expires_at": int(time.time()) + data["expires_in"],
    }
