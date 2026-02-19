# LinkedIn Integration Setup

## Prerequisites

- LinkedIn Developer account at https://www.linkedin.com/developers/
- App created with `w_member_social` permission approved

## Step 1: Create LinkedIn App

1. Go to https://www.linkedin.com/developers/apps/new
2. Fill in app name, company, and logo
3. Under **Auth**, add redirect URL: `http://localhost:8082/callback`
4. Under **Products**, request **Share on LinkedIn** (grants `w_member_social`)
5. Copy **Client ID** and **Client Secret** to `.env`

## Step 2: Configure Environment

Add to your `.env` file (copy from `.env.example`):

```bash
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_TOKEN_PATH=/home/hasss/.linkedin/token.json
LINKEDIN_CHECK_INTERVAL=60
```

## Step 3: Run OAuth Flow

```bash
uv run python -c "
import os, json, time, webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
import requests

CLIENT_ID = os.environ['LINKEDIN_CLIENT_ID']
CLIENT_SECRET = os.environ['LINKEDIN_CLIENT_SECRET']
TOKEN_PATH = Path(os.environ.get('LINKEDIN_TOKEN_PATH', '~/.linkedin/token.json')).expanduser()
REDIRECT_URI = 'http://localhost:8082/callback'
SCOPE = 'openid profile w_member_social'

auth_url = (
    'https://www.linkedin.com/oauth/v2/authorization?'
    + urlencode({'response_type': 'code', 'client_id': CLIENT_ID,
                 'redirect_uri': REDIRECT_URI, 'scope': SCOPE})
)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        code = parse_qs(urlparse(self.path).query).get('code', [None])[0]
        if code:
            resp = requests.post('https://www.linkedin.com/oauth/v2/accessToken', data={
                'grant_type': 'authorization_code', 'code': code,
                'redirect_uri': REDIRECT_URI, 'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
            })
            token = resp.json()
            token['expires_at'] = int(time.time()) + token.get('expires_in', 3600)
            TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
            TOKEN_PATH.write_text(json.dumps(token, indent=2))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Token saved. You can close this window.')
            raise SystemExit(0)
        self.send_response(400)
        self.end_headers()
    def log_message(self, *args): pass

print(f'Opening browser: {auth_url}')
webbrowser.open(auth_url)
HTTPServer(('localhost', 8082), Handler).handle_request()
"
```

This opens a browser for OAuth2 authorization and saves the token to `LINKEDIN_TOKEN_PATH`.

## Step 4: Verify

```bash
uv run python -c "
from src.mcp.linkedin_server import create_server_from_env
s = create_server_from_env()
print('Credentials valid:', s.verify_credentials())
print('Member URN:', s.get_member_urn())
"
```

## Step 5: Test Post (Optional)

Create `AI_Employee_Vault/Pending_Approval/FILE_linkedin-test.md`:

```yaml
---
type: linkedin_post
status: approved
post_text: |
  Test post from AI Employee. Phase 3 working! 🚀
created: 2026-02-18T10:00:00Z
---
```

Then run the LinkedIn watcher manually:

```bash
DRY_RUN=false uv run python -c "
import os
from pathlib import Path
from src.mcp.linkedin_server import create_server_from_env
from src.watchers.linkedin_watcher import LinkedInWatcher
server = create_server_from_env()
watcher = LinkedInWatcher(vault_path=os.environ['VAULT_PATH'], linkedin_server=server)
watcher.check_for_updates()
print('Done')
"
```

## Troubleshooting

| Error | Fix |
|-------|-----|
| `KeyError: LINKEDIN_CLIENT_ID` | Add credentials to `.env` and `source .env` |
| `401 Unauthorized` | Token expired — re-run OAuth flow (Step 3) |
| `403 Forbidden` | Check `w_member_social` scope approved in your app |
| `FileNotFoundError: token.json` | Run OAuth flow (Step 3) first |
| Watcher skipped at startup | Token not configured — see Step 3 |
