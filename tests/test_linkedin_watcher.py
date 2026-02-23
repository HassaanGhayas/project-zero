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
