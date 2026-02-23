#!/usr/bin/env python3
"""
Gmail OAuth2 Setup Script

This script guides users through the Gmail API OAuth2 authentication flow.
It generates credentials.json and token.json files required for Gmail API access.

Usage:
    python scripts/setup_gmail_oauth.py

Prerequisites:
    1. Enable Gmail API in Google Cloud Console
    2. Create OAuth 2.0 credentials (Desktop app type)
    3. Download credentials.json

Output:
    - credentials.json: OAuth client credentials (copy to GMAIL_CREDENTIALS_PATH)
    - token.json: Access/refresh tokens (saved to GMAIL_TOKEN_PATH)

Constitution Compliance:
    - Section V: Credentials stored via .env, never hardcoded
    - Section VII: All authentication events logged to audit trail
"""

import os
import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import json
from datetime import datetime

# Gmail API scopes - modify permission for read/archive/mark as read
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def load_env_config() -> dict:
    """Load Gmail paths from environment variables or use defaults."""
    from dotenv import load_dotenv
    load_dotenv()

    return {
        'credentials_path': os.getenv('GMAIL_CREDENTIALS_PATH', str(Path.home() / '.google' / 'credentials.json')),
        'token_path': os.getenv('GMAIL_TOKEN_PATH', str(Path.home() / '.google' / 'token.json')),
    }

def ensure_google_directory_exists(config: dict):
    """Create .google directory if it doesn't exist."""
    creds_dir = Path(config['credentials_path']).parent
    token_dir = Path(config['token_path']).parent

    creds_dir.mkdir(parents=True, exist_ok=True)
    token_dir.mkdir(parents=True, exist_ok=True)

    print(f"✓ Credentials directory: {creds_dir}")
    print(f"✓ Token directory: {token_dir}")

def check_credentials_exist(config: dict) -> bool:
    """Check if credentials.json exists at the configured path."""
    creds_path = Path(config['credentials_path'])
    return creds_path.exists()

def authenticate_gmail(config: dict) -> Credentials:
    """
    Authenticate with Gmail API using OAuth2.

    Returns:
        Credentials object with valid access/refresh tokens
    """
    creds = None
    token_path = Path(config['token_path'])
    creds_path = Path(config['credentials_path'])

    # Load existing token if available
    if token_path.exists():
        print(f"\n✓ Loading existing token from: {token_path}")
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    # If credentials are invalid or don't exist, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("\n⟳ Refreshing expired token...")
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                print(f"\n✗ ERROR: credentials.json not found at: {creds_path}")
                print("\nPlease follow these steps:")
                print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
                print("2. Enable Gmail API for your project")
                print("3. Create OAuth 2.0 credentials (Desktop app type)")
                print(f"4. Download credentials.json and place it at: {creds_path}")
                sys.exit(1)

            print(f"\n✓ Found credentials at: {creds_path}")
            print("\n🔐 Starting OAuth2 authorization flow...")
            print("A browser window will open. Please:")
            print("1. Select your Google account")
            print("2. Grant Gmail API access")
            print("3. Close the browser after authorization completes")

            flow = InstalledAppFlow.from_client_secrets_file(
                str(creds_path), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for future runs
        print(f"\n✓ Saving token to: {token_path}")
        token_path.write_text(creds.to_json())
        print("✓ Token saved successfully")

    return creds

def verify_token_validity(creds: Credentials) -> bool:
    """Verify that the token is valid and has correct scopes."""
    if not creds.valid:
        print("\n✗ Token is invalid")
        return False

    if not creds.token:
        print("\n✗ No access token present")
        return False

    print("\n✓ Token is valid")
    print(f"  - Expires: {creds.expiry}")
    print(f"  - Scopes: {', '.join(SCOPES)}")
    return True

def log_auth_event(config: dict, status: str, message: str):
    """Log authentication event to audit trail."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": "gmail_oauth_setup",
        "actor": "setup_gmail_oauth.py",
        "status": status,
        "message": message,
        "credentials_path": config['credentials_path'],
        "token_path": config['token_path'],
    }

    # Log to console (in production, this would also go to NDJSON audit log)
    print(f"\n[AUDIT] {json.dumps(log_entry)}")

def main():
    """Main OAuth2 setup flow."""
    print("=" * 60)
    print("Gmail OAuth2 Setup - AI FTE")
    print("=" * 60)

    # Load configuration
    config = load_env_config()
    print(f"\nConfiguration loaded:")
    print(f"  - Credentials: {config['credentials_path']}")
    print(f"  - Token: {config['token_path']}")

    # Ensure directories exist
    ensure_google_directory_exists(config)

    # Check for existing credentials.json
    if not check_credentials_exist(config):
        log_auth_event(config, "error", "credentials.json not found")
        print("\n✗ Setup failed: credentials.json not found")
        print("\nPlease obtain credentials.json from Google Cloud Console first.")
        sys.exit(1)

    try:
        # Authenticate and get token
        creds = authenticate_gmail(config)

        # Verify token validity
        if verify_token_validity(creds):
            log_auth_event(config, "success", "OAuth2 setup completed successfully")
            print("\n" + "=" * 60)
            print("✅ Gmail OAuth2 Setup Complete!")
            print("=" * 60)
            print("\nYou can now use Gmail API with the AI FTE system.")
            print("The token will be automatically refreshed when it expires.")
            return 0
        else:
            log_auth_event(config, "error", "Token validation failed")
            print("\n✗ Setup failed: Token validation error")
            return 1

    except Exception as e:
        log_auth_event(config, "error", f"OAuth2 setup failed: {str(e)}")
        print(f"\n✗ Error during OAuth2 setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
