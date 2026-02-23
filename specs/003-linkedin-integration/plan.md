# Implementation Plan: LinkedIn Integration

**Feature**: 003-linkedin-integration
**Date**: 2026-02-18
**Status**: Approved

---

## Architecture

### Flow

```
Pending_Approval/FILE_linkedin-<slug>.md  (status: approved, type: linkedin_post)
    │
    ▼
src/watchers/linkedin_watcher.py
    │  polls every LINKEDIN_CHECK_INTERVAL seconds
    │  reads post_text from action file body
    ▼
src/mcp/linkedin_server.py
    │  loads OAuth2 token from ~/.linkedin/token.json
    │  auto-refreshes on 401
    ▼
LinkedIn API v2
    POST /v2/ugcPosts
    │
    ▼
Move action file → Done/
Log to Logs/audit.json
```

---

## Components

### `src/mcp/linkedin_server.py`

- `post_text(text: str) -> dict` — publishes a text post, returns post URN
- `get_member_urn() -> str` — resolves `urn:li:person:<id>` via `/v2/userinfo`
- `verify_credentials() -> bool` — checks token validity
- `_refresh_token() -> None` — uses refresh token to get new access token
- Token loaded from `LINKEDIN_TOKEN_PATH` env var

### `src/watchers/linkedin_watcher.py`

- Extends `BaseWatcher`
- `check_for_updates()` — scans `Pending_Approval/` for `type: linkedin_post` + `status: approved`
- `_process_post(action_file: Path)` — calls `linkedin_server.post_text()`, moves file, logs
- Duplicate guard: skips files already in `Done/`
- Emergency stop check before every post

### `src/api/linkedin_oauth.py`

- `run_oauth_flow()` — CLI helper: opens browser for OAuth2 PKCE authorization code flow, exchanges code for tokens, saves to `LINKEDIN_TOKEN_PATH`
- `load_token() -> dict` — loads and validates token JSON
- `refresh_token(token: dict) -> dict` — calls `/v2/oauth/v2/accessToken` with grant_type=refresh_token

---

## Environment Variables

```bash
# LinkedIn Integration (Silver Tier Phase 3)
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_TOKEN_PATH=/home/hasss/.linkedin/token.json
LINKEDIN_CHECK_INTERVAL=60
```

---

## Action File Format (LinkedIn Post)

```yaml
---
type: linkedin_post
status: approved        # pending | approved | rejected
post_text: |
  Your post content here.
  Supports multiple lines.
created: 2026-02-18T10:00:00Z
approved_at: 2026-02-18T10:05:00Z
published_at: null      # filled after posting
linkedin_urn: null      # filled after posting
---
```

---

## Error Handling

| Scenario | Response |
|----------|----------|
| 401 Unauthorized | Auto-refresh; if fails → alert action file in Needs_Action/ |
| 429 Rate Limited | Exponential backoff: 2 → 4 → 8 min, max 3 retries |
| Network error | Log + retry next poll cycle |
| Emergency stop | Skip all posts, log halt |
| Malformed action file | Log warning, skip file |

---

## Testing Strategy

- `tests/test_linkedin_watcher.py` — mock filesystem + mock MCP server
- `tests/test_linkedin_server.py` — mock `requests`, test token refresh path
- No live API calls in tests
- Emergency stop test coverage mandatory
- Target ≥ 85% coverage on new modules
