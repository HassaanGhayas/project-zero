# tests/test_supervisor.py
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.monitors.supervisor import BACKOFF_RESET_UPTIME, BACKOFF_SEQUENCE, Supervisor


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    v = tmp_path / "vault"
    v.mkdir()
    return v


@pytest.fixture
def sup(vault: Path) -> Supervisor:
    return Supervisor(vault_path=vault, watcher_cmd=["echo", "hello"])


def _proc(exit_code: int) -> MagicMock:
    p = MagicMock()
    p.returncode = exit_code
    p.wait.return_value = exit_code
    p.poll.return_value = None
    return p


# --- clean exit ---

def test_clean_exit_stops_supervisor(sup: Supervisor) -> None:
    with patch("subprocess.Popen", return_value=_proc(0)):
        sup.run()
    assert sup.restart_count == 0


# --- crash + restart ---

def test_crash_triggers_restart(sup: Supervisor) -> None:
    procs = [_proc(1), _proc(0)]
    idx = {"n": 0}

    def side(*a, **kw):
        p = procs[idx["n"]]
        idx["n"] += 1
        return p

    with patch("subprocess.Popen", side_effect=side):
        with patch("time.sleep"):
            sup.run()

    assert sup.restart_count == 1


def test_backoff_increases_on_repeated_crashes(sup: Supervisor) -> None:
    procs = [_proc(1), _proc(1), _proc(1), _proc(0)]
    idx = {"n": 0}

    def side(*a, **kw):
        p = procs[min(idx["n"], len(procs) - 1)]
        idx["n"] += 1
        return p

    sleeps: list[float] = []

    with patch("subprocess.Popen", side_effect=side):
        with patch("time.sleep", side_effect=lambda s: sleeps.append(s)):
            sup.run()

    assert sleeps == [BACKOFF_SEQUENCE[0], BACKOFF_SEQUENCE[1], BACKOFF_SEQUENCE[2]]


def test_backoff_caps_at_max(sup: Supervisor) -> None:
    # 5 crashes → backoff should cap at BACKOFF_SEQUENCE[-1]
    procs = [_proc(1)] * 5 + [_proc(0)]
    idx = {"n": 0}

    def side(*a, **kw):
        p = procs[min(idx["n"], len(procs) - 1)]
        idx["n"] += 1
        return p

    sleeps: list[float] = []

    with patch("subprocess.Popen", side_effect=side):
        with patch("time.sleep", side_effect=lambda s: sleeps.append(s)):
            sup.run()

    assert sleeps[-1] == BACKOFF_SEQUENCE[-1]


def test_backoff_resets_after_long_uptime(sup: Supervisor) -> None:
    # After a long-running process, backoff_index resets → first sleep = BACKOFF_SEQUENCE[0]
    sup.backoff_index = 3  # pre-set to max
    procs = [_proc(1), _proc(0)]
    idx = {"n": 0}

    def side(*a, **kw):
        p = procs[min(idx["n"], len(procs) - 1)]
        idx["n"] += 1
        return p

    sleeps: list[float] = []
    # Fake start_time so uptime > BACKOFF_RESET_UPTIME
    long_ago = time.monotonic() - (BACKOFF_RESET_UPTIME + 10)

    def fake_monotonic():
        return time.monotonic()

    with patch("subprocess.Popen", side_effect=side):
        with patch("time.sleep", side_effect=lambda s: sleeps.append(s)):
            with patch.object(sup, "_start_time", long_ago):
                sup.run()

    assert sleeps[0] == BACKOFF_SEQUENCE[0]


# --- emergency stop ---

def test_emergency_stop_prevents_restart(vault: Path, sup: Supervisor) -> None:
    (vault / "EMERGENCY_STOP.md").touch()
    with patch("subprocess.Popen") as mock_popen:
        sup.run()
    mock_popen.assert_not_called()


# --- state file ---

def test_state_file_written_on_start(vault: Path, sup: Supervisor) -> None:
    with patch("subprocess.Popen", return_value=_proc(0)):
        sup.run()
    state_file = vault / "supervisor_state.json"
    assert state_file.exists()
    state = json.loads(state_file.read_text())
    assert state["restart_count"] == 0
    assert state["status"] == "stopped"


def test_state_restart_count_increments(vault: Path, sup: Supervisor) -> None:
    procs = [_proc(1), _proc(1), _proc(0)]
    idx = {"n": 0}

    def side(*a, **kw):
        p = procs[min(idx["n"], len(procs) - 1)]
        idx["n"] += 1
        return p

    with patch("subprocess.Popen", side_effect=side):
        with patch("time.sleep"):
            sup.run()

    state = json.loads((vault / "supervisor_state.json").read_text())
    assert state["restart_count"] == 2
