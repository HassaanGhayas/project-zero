---
id: "0008"
title: LinkedIn MCP Server Implementation
stage: green
date: 2026-02-18
surface: agent
model: claude-sonnet-4-6
feature: 002-gmail-integration
branch: 002-gmail-integration
user: hasss
command: Task 2 - LinkedIn MCP Server (TDD)
labels: ["linkedin", "mcp", "tdd", "oauth2", "green"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - src/mcp/linkedin_server.py
  - tests/test_linkedin_server.py
tests:
  - tests/test_linkedin_server.py::test_get_member_urn_returns_urn
  - tests/test_linkedin_server.py::test_post_text_calls_ugcposts
  - tests/test_linkedin_server.py::test_post_text_raises_on_http_error
  - tests/test_linkedin_server.py::test_verify_credentials_returns_true
  - tests/test_linkedin_server.py::test_verify_credentials_returns_false_on_error
---

## Prompt

You are implementing Task 2: LinkedIn MCP Server

## Task Description

**Files:**
- Create: `src/mcp/linkedin_server.py`
- Test: `tests/test_linkedin_server.py`

**Step 1: Write the failing tests**

```python
# tests/test_linkedin_server.py
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.mcp.linkedin_server import LinkedInServer


@pytest.fixture
def token_file(tmp_path):
    token = {"access_token": "tok", "refresh_token": "ref", "expires_at": 9999999999}
    f = tmp_path / "token.json"
    f.write_text(json.dumps(token))
    return f


@pytest.fixture
def server(token_file):
    return LinkedInServer(
        client_id="cid",
        client_secret="csecret",
        token_path=token_file,
    )


def test_get_member_urn_returns_urn(server):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"sub": "abc123"}
    mock_resp.raise_for_status = MagicMock()
    with patch("requests.get", return_value=mock_resp):
        urn = server.get_member_urn()
    assert urn == "urn:li:person:abc123"


def test_post_text_calls_ugcposts(server):
    mock_get = MagicMock()
    mock_get.json.return_value = {"sub": "abc123"}
    mock_get.raise_for_status = MagicMock()
    mock_post = MagicMock()
    mock_post.json.return_value = {"id": "urn:li:share:999"}
    mock_post.raise_for_status = MagicMock()
    with patch("requests.get", return_value=mock_get):
        with patch("requests.post", return_value=mock_post):
            result = server.post_text("Hello LinkedIn!")
    assert result["id"] == "urn:li:share:999"
    call_url = mock_post.call_args[0][0]
    assert "ugcPosts" in call_url
...
```

[Full test suite and implementation provided — 5 tests across get_member_urn, post_text, verify_credentials]

## Response snapshot

Implemented `src/mcp/linkedin_server.py` with `LinkedInServer` class wrapping LinkedIn API v2. Fixed a test bug in `test_post_text_calls_ugcposts` where `mock_post.call_args` was None because `patch("requests.post", return_value=mock_post)` makes mock_post the return value (not the callable). Fixed by capturing the context manager reference (`as patched_post`) and asserting `patched_post.call_args[0][0]` inside the `with` block.

All 5 tests pass. Committed as `ebe5a8a`.

## Outcome

- Impact: LinkedIn MCP server with OAuth2 auto-refresh available for watcher integration
- Tests: 5/5 PASSED (test_get_member_urn_returns_urn, test_post_text_calls_ugcposts, test_post_text_raises_on_http_error, test_verify_credentials_returns_true, test_verify_credentials_returns_false_on_error)
- Files: 2 created (src/mcp/linkedin_server.py, tests/test_linkedin_server.py)
- Next prompts: Task 3 - LinkedIn Watcher
- Reflection: Test spec had a subtle mock scoping bug (call_args accessed on return_value mock rather than patched callable). Fixed by moving assertion inside the `with` block and using the context manager reference.

## Evaluation notes (flywheel)

- Failure modes observed: `mock_post.call_args` was None because patch return_value != the callable itself; corrected with `as patched_post` context variable
- Graders run and results (PASS/FAIL): uv run pytest tests/test_linkedin_server.py -v → 5 PASSED
- Prompt variant (if applicable): TDD green phase
- Next experiment: Token refresh path coverage (is_token_expired=True scenario)
