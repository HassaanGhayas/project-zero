"""
Unit tests for WhatsApp Watcher (Business API edition)

Tests message detection, duplicate prevention, keyword filtering, queue reading,
and action file generation. Uses a temp JSON queue file instead of browser mocks.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from src.watchers.whatsapp_watcher import WhatsAppWatcher


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def vault_path(tmp_path):
    """Create temporary vault structure for testing."""
    vault = tmp_path / "AI_Employee_Vault"
    (vault / "Needs_Action").mkdir(parents=True)
    (vault / "Logs").mkdir(parents=True)
    return vault


@pytest.fixture
def queue_file(tmp_path):
    """Create an empty message queue JSON file."""
    queue = tmp_path / ".whatsapp" / "message_queue.json"
    queue.parent.mkdir(parents=True)
    queue.write_text(json.dumps([]), encoding="utf-8")
    return queue


@pytest.fixture
def mock_logger():
    """Create mock logger."""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def whatsapp_watcher(vault_path, queue_file, mock_logger):
    """Create WhatsAppWatcher instance with temp queue file and keywords config."""
    config_path = Path("config/whatsapp_keywords.yaml")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("keywords:\n  - urgent\n  - payment\n  - help\n")

    watcher = WhatsAppWatcher(
        vault_path=vault_path,
        queue_file=queue_file,
        check_interval=30,
        logger=mock_logger,
    )
    return watcher


def _write_queue(queue_file: Path, messages: list) -> None:
    """Helper: write messages to the queue file."""
    queue_file.write_text(json.dumps(messages, indent=2), encoding="utf-8")


def _make_message(
    msg_id: str = "test_001",
    sender: str = "Client A",
    text: str = "Urgent: Need help with payment",
) -> dict:
    """Helper: build a minimal message dict."""
    return {
        "id": msg_id,
        "from": "15551234567",
        "sender": sender,
        "text": text,
        "type": "text",
        "timestamp": "2026-02-18T10:00:00",
        "received_at": "2026-02-18T10:00:00",
        "processed": False,
    }


# ── Tests: Message Detection ──────────────────────────────────────────────────


class TestMessageDetection:
    def test_detect_message_with_keyword(self, whatsapp_watcher, queue_file):
        """Messages containing a priority keyword create action files."""
        _write_queue(queue_file, [_make_message(text="Urgent payment needed")])

        whatsapp_watcher.check_for_updates()

        files = list((whatsapp_watcher.vault_path / "Needs_Action").glob("*.md"))
        assert len(files) == 1

    def test_action_file_contains_required_fields(self, whatsapp_watcher, queue_file):
        """Generated action files include all required YAML frontmatter fields."""
        _write_queue(queue_file, [_make_message(text="Help needed urgently")])

        whatsapp_watcher.check_for_updates()

        files = list((whatsapp_watcher.vault_path / "Needs_Action").glob("*.md"))
        assert len(files) == 1

        content = files[0].read_text()
        required_fields = [
            "type: message",
            "whatsapp_message_id:",
            "sender:",
            "received_timestamp:",
            "status: pending",
            "priority: high",
            "has_attachments:",
            "category: whatsapp_message",
        ]
        for field in required_fields:
            assert field in content, f"Missing required field: {field}"

    def test_no_action_file_for_no_keyword(self, whatsapp_watcher, queue_file):
        """Messages without priority keywords are silently ignored."""
        _write_queue(queue_file, [_make_message(text="Hey, how are you?")])

        whatsapp_watcher.check_for_updates()

        files = list((whatsapp_watcher.vault_path / "Needs_Action").glob("*.md"))
        assert len(files) == 0

    def test_empty_queue_no_action_files(self, whatsapp_watcher, queue_file):
        """Empty queue produces no action files."""
        whatsapp_watcher.check_for_updates()

        files = list((whatsapp_watcher.vault_path / "Needs_Action").glob("*.md"))
        assert len(files) == 0


# ── Tests: Duplicate Prevention ───────────────────────────────────────────────


class TestDuplicatePrevention:
    def test_duplicate_message_not_processed_twice(self, whatsapp_watcher, queue_file):
        """The same message ID is not processed more than once per session."""
        msg = _make_message(msg_id="dup_001", text="Urgent payment reminder")
        _write_queue(queue_file, [msg])

        whatsapp_watcher.check_for_updates()
        first_count = len(
            list((whatsapp_watcher.vault_path / "Needs_Action").glob("*.md"))
        )

        # Queue is now all-processed; inject same ID via processed_ids shortcut
        _write_queue(queue_file, [msg])
        whatsapp_watcher.check_for_updates()
        second_count = len(
            list((whatsapp_watcher.vault_path / "Needs_Action").glob("*.md"))
        )

        assert first_count == 1
        assert second_count == 1  # No new file
        assert "dup_001" in whatsapp_watcher._processed_message_ids

    def test_queue_messages_marked_processed(self, whatsapp_watcher, queue_file):
        """After processing, all queue entries are marked processed=True."""
        msgs = [
            _make_message(msg_id="m1", text="urgent help"),
            _make_message(msg_id="m2", text="payment due"),
        ]
        _write_queue(queue_file, msgs)

        whatsapp_watcher.check_for_updates()

        updated = json.loads(queue_file.read_text())
        assert all(m["processed"] for m in updated)


# ── Tests: Keyword Filtering ──────────────────────────────────────────────────


class TestKeywordFiltering:
    def test_keyword_matching_is_case_insensitive(self, whatsapp_watcher, queue_file):
        """Keyword matching works regardless of message case."""
        _write_queue(queue_file, [_make_message(text="URGENT meeting at 3pm")])

        whatsapp_watcher.check_for_updates()

        files = list((whatsapp_watcher.vault_path / "Needs_Action").glob("*.md"))
        assert len(files) == 1

    def test_keywords_loaded_correctly(self, whatsapp_watcher):
        """Keywords config is loaded and contains expected entries."""
        assert "urgent" in whatsapp_watcher.keywords
        assert "payment" in whatsapp_watcher.keywords
        assert len(whatsapp_watcher.keywords) >= 3

    def test_multiple_keyword_messages_all_processed(self, whatsapp_watcher, queue_file):
        """All keyword-matching messages in a batch create action files."""
        msgs = [
            _make_message(msg_id="k1", text="urgent issue"),
            _make_message(msg_id="k2", text="help needed"),
            _make_message(msg_id="k3", text="payment overdue"),
        ]
        _write_queue(queue_file, msgs)

        whatsapp_watcher.check_for_updates()

        files = list((whatsapp_watcher.vault_path / "Needs_Action").glob("*.md"))
        assert len(files) == 3


# ── Tests: Queue Reading ──────────────────────────────────────────────────────


class TestQueueReading:
    def test_missing_queue_file_returns_empty(self, whatsapp_watcher, tmp_path):
        """Watcher handles absent queue file gracefully."""
        watcher = WhatsAppWatcher(
            vault_path=whatsapp_watcher.vault_path,
            queue_file=tmp_path / "nonexistent.json",
            logger=whatsapp_watcher.logger,
        )
        result = watcher._read_message_queue()
        assert result == []

    def test_corrupt_queue_file_returns_empty(self, whatsapp_watcher, queue_file):
        """Watcher handles a corrupt queue file without crashing."""
        queue_file.write_text("not valid json", encoding="utf-8")
        result = whatsapp_watcher._read_message_queue()
        assert result == []

    def test_already_processed_messages_skipped(self, whatsapp_watcher, queue_file):
        """Messages with processed=True are not returned."""
        msgs = [
            {**_make_message(msg_id="p1", text="urgent"), "processed": True},
            {**_make_message(msg_id="p2", text="payment"), "processed": True},
        ]
        _write_queue(queue_file, msgs)

        result = whatsapp_watcher._read_message_queue()
        assert result == []


# ── Tests: Threading Lifecycle ────────────────────────────────────────────────


class TestThreadingLifecycle:
    def test_start_creates_background_thread(self, whatsapp_watcher):
        """start() spawns a daemon thread."""
        whatsapp_watcher.start()

        assert whatsapp_watcher._running is True
        assert whatsapp_watcher._thread is not None
        assert whatsapp_watcher._thread.daemon is True
        assert whatsapp_watcher._thread.is_alive()

        whatsapp_watcher.stop()

    def test_stop_gracefully_terminates_thread(self, whatsapp_watcher):
        """stop() joins the background thread cleanly."""
        whatsapp_watcher.start()
        assert whatsapp_watcher._running is True

        whatsapp_watcher.stop()

        assert whatsapp_watcher._running is False
        if whatsapp_watcher._thread:
            whatsapp_watcher._thread.join(timeout=1.0)
            assert not whatsapp_watcher._thread.is_alive()


# ── Tests: Emergency Stop ─────────────────────────────────────────────────────


class TestEmergencyStop:
    def test_emergency_stop_prevents_queue_reading(self, whatsapp_watcher, queue_file):
        """EMERGENCY_STOP.md prevents any queue polling."""
        emergency_path = whatsapp_watcher.vault_path / "EMERGENCY_STOP.md"
        emergency_path.write_text("# Emergency Stop\nAll watchers paused.")

        _write_queue(queue_file, [_make_message(text="urgent")])

        with patch.object(
            whatsapp_watcher, "_read_message_queue", return_value=[]
        ) as mock_read:
            whatsapp_watcher.check_for_updates()
            mock_read.assert_not_called()


# ── Tests: Audit Logging ──────────────────────────────────────────────────────


class TestAuditLogging:
    def test_message_detected_event_logged(self, whatsapp_watcher, queue_file):
        """whatsapp_message_detected entries appear in the NDJSON audit log."""
        _write_queue(queue_file, [_make_message(text="urgent payment")])

        whatsapp_watcher.check_for_updates()

        from datetime import date

        log_file = (
            whatsapp_watcher.vault_path / "Logs" / f"{date.today().isoformat()}.json"
        )
        assert log_file.exists(), "Audit log file not created"

        lines = log_file.read_text().splitlines()
        assert len(lines) > 0

        events = [json.loads(ln) for ln in lines if ln.strip()]
        whatsapp_events = [
            e for e in events if "whatsapp" in e.get("action_type", "")
        ]
        assert len(whatsapp_events) > 0, "No WhatsApp events in audit log"

    def test_audit_entries_are_valid_ndjson(self, whatsapp_watcher, queue_file):
        """Every audit log line is valid JSON with required keys."""
        _write_queue(queue_file, [_make_message(text="urgent")])
        whatsapp_watcher.check_for_updates()

        from datetime import date

        log_file = (
            whatsapp_watcher.vault_path / "Logs" / f"{date.today().isoformat()}.json"
        )
        for line in log_file.read_text().splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            assert "timestamp" in entry
            assert "action_type" in entry


# ── Tests: Error Handling ─────────────────────────────────────────────────────


class TestErrorHandling:
    def test_queue_read_error_logged_and_watcher_continues(self, whatsapp_watcher):
        """Errors during queue reading are logged but do not crash the watcher."""
        with patch.object(
            whatsapp_watcher,
            "_read_message_queue",
            side_effect=RuntimeError("Disk read error"),
        ):
            whatsapp_watcher.check_for_updates()  # must not raise

        error_calls = [str(c) for c in whatsapp_watcher.logger.error.call_args_list]
        assert any("error" in c.lower() for c in error_calls)


# ── Tests: Action File Generation ─────────────────────────────────────────────


class TestActionFileGeneration:
    def test_action_file_yaml_structure(self, whatsapp_watcher):
        """Generated action files start with valid YAML frontmatter."""
        msg = _make_message(msg_id="yaml_001", sender="YAML Contact", text="Help me")
        action_file = whatsapp_watcher.create_action_file(msg)

        content = action_file.read_text()
        assert content.startswith("---\n")
        assert "\n---\n" in content
        assert "type: message" in content
        assert "status: pending" in content
        assert "priority: high" in content

    def test_action_file_markdown_sections(self, whatsapp_watcher):
        """Generated action files contain all required markdown sections."""
        msg = _make_message(msg_id="md_001", sender="Section Tester", text="payment")
        action_file = whatsapp_watcher.create_action_file(msg)
        content = action_file.read_text()

        for section in ["## Message Details", "## Suggested Actions", "## Audit Context"]:
            assert section in content, f"Missing section: {section}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
