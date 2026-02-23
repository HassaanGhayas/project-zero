# Phase 3: LinkedIn Integration + Plan Generation Skill — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add LinkedIn post publishing (via OAuth2 + API v2) and a Plan Generation Skill that runs the SDD loop for complex inbox tasks.

**Architecture:** LinkedIn watcher polls `Pending_Approval/` for approved `linkedin_post` action files and publishes via `LinkedInServer`. Plan Generation Skill wraps `/sp.specify` + `/sp.plan` + `/sp.tasks` into a single invocable skill, auto-triggered when inbox action file `complexity_score ≥ 3`.

**Tech Stack:** Python 3.12, `requests`, `pyyaml`, LinkedIn API v2, OAuth2 PKCE, `BaseWatcher` (existing), `pytest`, `uv`

---

## Task 1: LinkedIn OAuth2 Token Management

**Files:**
- Create: `src/api/linkedin_oauth.py`
- Test: `tests/test_linkedin_oauth.py`

**Step 1: Write the failing tests**

```python
# tests/test_linkedin_oauth.py
import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.api.linkedin_oauth import load_token, save_token, is_token_expired, refresh_access_token


def test_load_token_returns_dict(tmp_path):
    token_data = {"access_token": "tok", "refresh_token": "ref", "expires_at": 9999999999}
    f = tmp_path / "token.json"
    f.write_text(json.dumps(token_data))
    result = load_token(f)
    assert result["access_token"] == "tok"


def test_load_token_raises_if_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_token(tmp_path / "nonexistent.json")


def test_save_token_creates_file(tmp_path):
    token = {"access_token": "tok", "refresh_token": "ref", "expires_at": 9999999999}
    save_token(token, tmp_path / "token.json")
    assert (tmp_path / "token.json").exists()


def test_is_token_expired_true_for_old_token():
    assert is_token_expired({"expires_at": 1000}) is True


def test_is_token_expired_false_for_fresh_token():
    assert is_token_expired({"expires_at": int(time.time()) + 3600}) is False


def test_refresh_access_token_returns_new_token():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"access_token": "new_tok", "expires_in": 3600}
    with patch("requests.post", return_value=mock_resp):
        result = refresh_access_token(
            {"refresh_token": "ref"}, "client_id", "client_secret"
        )
    assert result["access_token"] == "new_tok"
    assert "expires_at" in result
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_linkedin_oauth.py -v
```
Expected: `ModuleNotFoundError: No module named 'src.api.linkedin_oauth'`

**Step 3: Create `src/api/__init__.py` if it doesn't exist**

```bash
touch src/api/__init__.py
```

(It already exists from Phase 2. Skip if present.)

**Step 4: Write minimal implementation**

```python
# src/api/linkedin_oauth.py
import json
import time
from pathlib import Path
from typing import Optional

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
```

**Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/test_linkedin_oauth.py -v
```
Expected: 6 PASSED

**Step 6: Commit**

```bash
git add src/api/linkedin_oauth.py tests/test_linkedin_oauth.py
git commit -m "feat: add LinkedIn OAuth2 token management"
```

---

## Task 2: LinkedIn MCP Server

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


def test_post_text_raises_on_http_error(server):
    import requests as req
    mock_get = MagicMock()
    mock_get.json.return_value = {"sub": "abc123"}
    mock_get.raise_for_status = MagicMock()
    mock_post = MagicMock()
    mock_post.raise_for_status.side_effect = req.HTTPError("400")
    with patch("requests.get", return_value=mock_get):
        with patch("requests.post", return_value=mock_post):
            with pytest.raises(req.HTTPError):
                server.post_text("test")


def test_verify_credentials_returns_true(server):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"sub": "abc123", "name": "Test"}
    mock_resp.raise_for_status = MagicMock()
    with patch("requests.get", return_value=mock_resp):
        assert server.verify_credentials() is True


def test_verify_credentials_returns_false_on_error(server):
    import requests as req
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = req.HTTPError("401")
    with patch("requests.get", return_value=mock_resp):
        assert server.verify_credentials() is False
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_linkedin_server.py -v
```
Expected: `ModuleNotFoundError: No module named 'src.mcp.linkedin_server'`

**Step 3: Write minimal implementation**

```python
# src/mcp/linkedin_server.py
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


def create_server_from_env(token_path: Optional[Path] = None) -> LinkedInServer:
    return LinkedInServer(
        client_id=os.environ["LINKEDIN_CLIENT_ID"],
        client_secret=os.environ["LINKEDIN_CLIENT_SECRET"],
        token_path=token_path
        or Path(
            os.environ.get("LINKEDIN_TOKEN_PATH", "~/.linkedin/token.json")
        ).expanduser(),
    )
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_linkedin_server.py -v
```
Expected: 5 PASSED

**Step 5: Commit**

```bash
git add src/mcp/linkedin_server.py tests/test_linkedin_server.py
git commit -m "feat: add LinkedIn MCP server with OAuth2 auto-refresh"
```

---

## Task 3: LinkedIn Watcher

**Files:**
- Create: `src/watchers/linkedin_watcher.py`
- Test: `tests/test_linkedin_watcher.py`

**Step 1: Write the failing tests**

```python
# tests/test_linkedin_watcher.py
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.watchers.linkedin_watcher import LinkedInWatcher


def _write_action_file(path: Path, type_: str = "linkedin_post",
                        status: str = "approved", post_text: str = "Hello!\n") -> None:
    content = f"---\ntype: {type_}\nstatus: {status}\npost_text: |\n  {post_text.strip()}\n---\n"
    path.write_text(content)


@pytest.fixture
def env(tmp_path):
    for d in ["Pending_Approval", "Done", "Logs"]:
        (tmp_path / d).mkdir()
    mock_server = MagicMock()
    mock_server.post_text.return_value = {"id": "urn:li:share:123"}
    watcher = LinkedInWatcher(
        vault_path=str(tmp_path),
        linkedin_server=mock_server,
        check_interval=1,
    )
    return watcher, tmp_path, mock_server


def test_processes_approved_post(env):
    watcher, tmp_path, mock_server = env
    _write_action_file(tmp_path / "Pending_Approval" / "FILE_linkedin-hello.md")
    watcher.check_for_updates()
    mock_server.post_text.assert_called_once()
    assert (tmp_path / "Done" / "FILE_linkedin-hello.md").exists()
    assert not (tmp_path / "Pending_Approval" / "FILE_linkedin-hello.md").exists()


def test_skips_pending_post(env):
    watcher, tmp_path, mock_server = env
    _write_action_file(tmp_path / "Pending_Approval" / "FILE_linkedin-hello.md", status="pending")
    watcher.check_for_updates()
    mock_server.post_text.assert_not_called()


def test_skips_non_linkedin_files(env):
    watcher, tmp_path, mock_server = env
    (tmp_path / "Pending_Approval" / "FILE_email.md").write_text(
        "---\ntype: email\nstatus: approved\n---\n"
    )
    watcher.check_for_updates()
    mock_server.post_text.assert_not_called()


def test_emergency_stop_blocks_posting(env):
    watcher, tmp_path, mock_server = env
    (tmp_path / "EMERGENCY_STOP.md").write_text("STOP")
    _write_action_file(tmp_path / "Pending_Approval" / "FILE_linkedin-hello.md")
    watcher.check_for_updates()
    mock_server.post_text.assert_not_called()


def test_no_duplicate_post_if_in_done(env):
    watcher, tmp_path, mock_server = env
    _write_action_file(tmp_path / "Pending_Approval" / "FILE_linkedin-hello.md")
    _write_action_file(tmp_path / "Done" / "FILE_linkedin-hello.md")
    watcher.check_for_updates()
    mock_server.post_text.assert_not_called()


def test_api_error_leaves_file_in_pending(env):
    import requests as req
    watcher, tmp_path, mock_server = env
    mock_server.post_text.side_effect = req.HTTPError("429")
    _write_action_file(tmp_path / "Pending_Approval" / "FILE_linkedin-hello.md")
    watcher.check_for_updates()
    assert (tmp_path / "Pending_Approval" / "FILE_linkedin-hello.md").exists()


def test_audit_log_written_on_success(env):
    watcher, tmp_path, mock_server = env
    _write_action_file(tmp_path / "Pending_Approval" / "FILE_linkedin-hello.md")
    watcher.check_for_updates()
    log_file = tmp_path / "Logs" / "audit.json"
    assert log_file.exists()
    entry = json.loads(log_file.read_text().strip())
    assert entry["action"] == "linkedin_post_published"
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_linkedin_watcher.py -v
```
Expected: `ModuleNotFoundError: No module named 'src.watchers.linkedin_watcher'`

**Step 3: Write minimal implementation**

```python
# src/watchers/linkedin_watcher.py
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from src.watchers.base_watcher import BaseWatcher

logger = logging.getLogger(__name__)


class LinkedInWatcher(BaseWatcher):
    def __init__(
        self,
        vault_path: str,
        linkedin_server,
        check_interval: int = 60,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(vault_path=vault_path, check_interval=check_interval, logger=logger)
        self.linkedin_server = linkedin_server
        self.pending_dir = self.vault_path / "Pending_Approval"
        self.done_dir = self.vault_path / "Done"
        self.logs_dir = self.vault_path / "Logs"

    def _is_emergency_stop(self) -> bool:
        return (self.vault_path / "EMERGENCY_STOP.md").exists()

    def check_for_updates(self) -> None:
        if self._is_emergency_stop():
            self.logger.warning("Emergency stop active — LinkedIn watcher halted")
            return
        for action_file in self.pending_dir.glob("FILE_linkedin-*.md"):
            if (self.done_dir / action_file.name).exists():
                self.logger.debug(f"Skipping duplicate: {action_file.name}")
                continue
            self._process_post(action_file)

    def _process_post(self, action_file: Path) -> None:
        try:
            frontmatter, _ = self._parse_action_file(action_file)
        except Exception as e:
            self.logger.error(f"Failed to parse {action_file.name}: {e}")
            return
        if frontmatter.get("type") != "linkedin_post":
            return
        if frontmatter.get("status") != "approved":
            return
        post_text = frontmatter.get("post_text", "")
        self.logger.info(f"Publishing LinkedIn post from {action_file.name}")
        try:
            result = self.linkedin_server.post_text(post_text)
            self.logger.info(f"Published: {result.get('id')}")
            self._log_audit(action_file.name, "linkedin_post_published", result.get("id", ""))
            action_file.rename(self.done_dir / action_file.name)
        except Exception as e:
            self.logger.error(f"Failed to publish {action_file.name}: {e}")
            self._log_audit(action_file.name, "linkedin_post_failed", str(e))

    def _parse_action_file(self, path: Path) -> tuple[dict, str]:
        text = path.read_text()
        parts = text.split("---", 2)
        if len(parts) < 3:
            return {}, text
        frontmatter = yaml.safe_load(parts[1]) or {}
        return frontmatter, parts[2]

    def _log_audit(self, filename: str, action: str, detail: str) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "file": filename,
            "detail": detail,
        }
        log_file = self.logs_dir / "audit.json"
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_linkedin_watcher.py -v
```
Expected: 7 PASSED

**Step 5: Commit**

```bash
git add src/watchers/linkedin_watcher.py tests/test_linkedin_watcher.py
git commit -m "feat: add LinkedIn watcher with approval workflow and audit logging"
```

---

## Task 4: Complexity Scorer Utility

**Files:**
- Create: `src/utils/__init__.py`
- Create: `src/utils/complexity_scorer.py`
- Test: `tests/test_complexity_scorer.py`

**Step 1: Write the failing tests**

```python
# tests/test_complexity_scorer.py
from src.utils.complexity_scorer import complexity_score


def test_short_simple_text_scores_zero():
    assert complexity_score("Fix the login bug") == 0


def test_long_text_adds_one():
    text = " ".join(["word"] * 201)
    assert complexity_score(text) >= 1


def test_api_mention_adds_one():
    assert complexity_score("Integrate with the Stripe API for payments") >= 1


def test_multiple_steps_adds_one():
    assert complexity_score("First do X, then do Y, next do Z") >= 1


def test_multiple_stakeholders_adds_one():
    assert complexity_score("Coordinate with the frontend team and backend database") >= 1


def test_complex_task_scores_three_or_more():
    text = (
        "Integrate with Stripe API to process payments. "
        "First create the endpoint, then add webhook handling, next update the database. "
        "Coordinate with the frontend team and backend system. " * 20
    )
    assert complexity_score(text) >= 3


def test_api_keyword_case_insensitive():
    assert complexity_score("Use the REST api for this") >= 1
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_complexity_scorer.py -v
```
Expected: `ModuleNotFoundError: No module named 'src.utils'`

**Step 3: Write implementation**

```bash
mkdir -p src/utils && touch src/utils/__init__.py
```

```python
# src/utils/complexity_scorer.py
import re

_STEP_PATTERN = re.compile(
    r"\b(first|second|third|then|after that|next|step \d+|finally)\b",
    re.IGNORECASE,
)
_API_PATTERN = re.compile(
    r"\b(api|webhook|integration|endpoint|sdk|oauth|rest|graphql|mcp)\b",
    re.IGNORECASE,
)
_STAKEHOLDER_PATTERN = re.compile(
    r"\b(team|system|service|frontend|backend|database|stakeholder|coordinate)\b",
    re.IGNORECASE,
)


def complexity_score(text: str) -> int:
    """Score a task description for SDD loop auto-trigger. Returns 0–4."""
    score = 0
    if len(text.split()) > 200:
        score += 1
    if _API_PATTERN.search(text):
        score += 1
    if len(_STEP_PATTERN.findall(text)) >= 2:
        score += 1
    if len(_STAKEHOLDER_PATTERN.findall(text)) >= 2:
        score += 1
    return score
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_complexity_scorer.py -v
```
Expected: 7 PASSED

**Step 5: Commit**

```bash
git add src/utils/__init__.py src/utils/complexity_scorer.py tests/test_complexity_scorer.py
git commit -m "feat: add complexity scorer for SDD auto-trigger"
```

---

## Task 5: Generate-Plan Skill

**Files:**
- Create: `.claude/skills/generate-plan/SKILL.md`

No automated tests — skill files are markdown invoked manually.

**Step 1: Create skill directory and file**

```bash
mkdir -p .claude/skills/generate-plan
```

```markdown
---
name: generate-plan
description: >
  Orchestrate the full SDD loop (sp.specify → sp.plan → sp.tasks) for a given task
  description, then route a review action file to Pending_Approval/ for HITL approval.
color: blue
---

# Generate Plan Skill

Given a task description, this skill:
1. Slugifies the description into a feature name
2. Runs /sp.specify to create specs/<slug>/spec.md
3. Runs /sp.plan to create specs/<slug>/plan.md
4. Runs /sp.tasks to create specs/<slug>/tasks.md
5. Writes a plan review action file to Pending_Approval/

## Usage

```
/generate-plan "Brief description of the task"
```

## Steps

### 1. Slugify the description

Convert the description to a slug: lowercase, spaces → hyphens, strip special chars.
Example: "Build Stripe payment integration" → `build-stripe-payment-integration`

Check if `specs/<slug>/` already exists. If so, append `-2`, `-3`, etc.

### 2. Run SDD loop

Invoke in sequence:
- `/sp.specify` with the task description as input
- `/sp.plan` using the generated spec
- `/sp.tasks` using the generated plan

Each writes to `specs/<slug>/`.

### 3. Write review action file

Create `Pending_Approval/FILE_plan-<slug>.md`:

```yaml
---
type: plan_review
feature: <slug>
status: pending
complexity_score: <n>
created: <ISO timestamp>
triggered_by: manual
spec_path: specs/<slug>/spec.md
plan_path: specs/<slug>/plan.md
tasks_path: specs/<slug>/tasks.md
---

## Plan Review

Feature: **<slug>**

Review the SDD artifacts linked above.
Set `status: approved` to proceed with implementation.
```

### 4. Confirm to user

Report:
- Feature slug created
- Paths to spec/plan/tasks
- Pending_Approval/ action file path
```

**Step 2: Verify skill appears in skill list**

```bash
ls -la .claude/skills/generate-plan/
```
Expected: `SKILL.md` present

**Step 3: Commit**

```bash
git add .claude/skills/generate-plan/SKILL.md
git commit -m "feat: add generate-plan skill for SDD auto-loop"
```

---

## Task 6: Wire LinkedIn Watcher into run_all_watchers.py

**Files:**
- Modify: `src/watchers/run_all_watchers.py`
- Modify: `.env.example`
- Create: `docs/LINKEDIN_SETUP.md`

**Step 1: Add env vars to `.env.example`**

Add after the WhatsApp block:

```bash
# LinkedIn Integration (Silver Tier Phase 3)
# Get Client ID/Secret from https://www.linkedin.com/developers/apps
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_TOKEN_PATH=/home/hasss/.linkedin/token.json
LINKEDIN_CHECK_INTERVAL=60
```

**Step 2: Wire into run_all_watchers.py**

Add import at top of imports block:

```python
from .linkedin_watcher import LinkedInWatcher
from src.mcp.linkedin_server import create_server_from_env
```

Add watcher initialization after the WhatsApp watcher block:

```python
# 6. LinkedIn Watcher (Pending_Approval → LinkedIn API) - Silver Tier Phase 3
linkedin_check_interval = int(os.getenv("LINKEDIN_CHECK_INTERVAL", "60"))
linkedin_server = create_server_from_env()
linkedin_watcher = LinkedInWatcher(
    vault_path=vault_path,
    linkedin_server=linkedin_server,
    check_interval=linkedin_check_interval,
    logger=setup_logging("linkedin_watcher", vault_path),
)
```

Add to shutdown handler:

```python
linkedin_watcher.stop()
```

Add to start block:

```python
linkedin_watcher.start()
logger.info("✅ LinkedIn watcher started (Pending_Approval/ → LinkedIn API)")
```

**Step 3: Run all existing tests to confirm nothing broken**

```bash
uv run pytest tests/ -v --ignore=tests/integration --ignore=tests/manual
```
Expected: all previously passing tests still pass

**Step 4: Commit**

```bash
git add src/watchers/run_all_watchers.py .env.example
git commit -m "feat: wire LinkedIn watcher into orchestrator"
```

---

## Task 7: LinkedIn Setup Docs + tasks.md for both specs

**Files:**
- Create: `docs/LINKEDIN_SETUP.md`
- Create: `specs/003-linkedin-integration/tasks.md`
- Create: `specs/004-plan-generation/tasks.md`

**Step 1: Create LINKEDIN_SETUP.md**

```markdown
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

## Step 2: Run OAuth Flow

```bash
uv run python -m src.api.linkedin_oauth
```

This opens a browser, asks you to authorize, then saves the token to `LINKEDIN_TOKEN_PATH`.

## Step 3: Verify

```bash
uv run python -c "
from src.mcp.linkedin_server import create_server_from_env
s = create_server_from_env()
print('Credentials valid:', s.verify_credentials())
print('Member URN:', s.get_member_urn())
"
```

## Step 4: Test Post

Create `AI_Employee_Vault/Pending_Approval/FILE_linkedin-test.md`:

```yaml
---
type: linkedin_post
status: approved
post_text: |
  Test post from AI Employee. If you see this, Phase 3 is working! 🚀
created: 2026-02-18T10:00:00Z
---
```

Then run the LinkedIn watcher:

```bash
DRY_RUN=false uv run python -c "
import os
from pathlib import Path
from src.mcp.linkedin_server import create_server_from_env
from src.watchers.linkedin_watcher import LinkedInWatcher
server = create_server_from_env()
watcher = LinkedInWatcher(vault_path=os.environ['VAULT_PATH'], linkedin_server=server)
watcher.check_for_updates()
"
```

## Troubleshooting

| Error | Fix |
|-------|-----|
| `401 Unauthorized` | Re-run OAuth flow — token expired or revoked |
| `403 Forbidden` | Check `w_member_social` scope is approved in your app |
| `FileNotFoundError: token.json` | Run OAuth flow first |
| `LINKEDIN_CLIENT_ID not set` | Check your `.env` file |
```

**Step 2: Create tasks.md files**

`specs/003-linkedin-integration/tasks.md` — reference the 7 implementation tasks above (T001–T007 covering OAuth, server, watcher, env wiring).

`specs/004-plan-generation/tasks.md` — reference Task 5 (skill file) and inbox watcher integration.

**Step 3: Commit everything**

```bash
git add docs/LINKEDIN_SETUP.md specs/003-linkedin-integration/tasks.md specs/004-plan-generation/tasks.md
git commit -m "docs: add LinkedIn setup guide and SDD tasks files"
```

---

## Task 8: Full Test Suite Run + PHR

**Step 1: Run full test suite**

```bash
uv run pytest tests/ -v --ignore=tests/integration --ignore=tests/manual
```
Expected: all tests pass, coverage on new modules ≥ 85%

**Step 2: Check coverage on new modules**

```bash
uv run pytest tests/test_linkedin_oauth.py tests/test_linkedin_server.py tests/test_linkedin_watcher.py tests/test_complexity_scorer.py --cov=src/api/linkedin_oauth --cov=src/mcp/linkedin_server --cov=src/watchers/linkedin_watcher --cov=src/utils/complexity_scorer --cov-report=term-missing
```

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: Silver Tier Phase 3 - LinkedIn Integration + Plan Generation Skill"
```
