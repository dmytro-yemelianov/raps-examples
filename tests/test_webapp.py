"""Tests for the RAPS test results webapp."""
from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

# Must set token BEFORE importing app.
os.environ["RAPS_DASHBOARD_TOKEN"] = "test-token"

from fastapi.testclient import TestClient  # noqa: E402
from webapp.main import app, _sr_id_from_nodeid, _merge_results  # noqa: E402

client = TestClient(app)
TOKEN = "test-token"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def test_auth_missing_token_returns_422():
    resp = client.get("/api/results")
    assert resp.status_code == 422


def test_auth_wrong_token_returns_401():
    resp = client.get("/api/results?token=wrong")
    assert resp.status_code == 401


def test_auth_valid_token_returns_200(tmp_path, monkeypatch):
    monkeypatch.setattr("webapp.main.RESULTS_PATH", tmp_path / "results.json")
    minimal_catalog = {"vars": {}, "sections": []}
    (tmp_path / "catalog.json").write_text(json.dumps(minimal_catalog))
    monkeypatch.setattr("webapp.main.CATALOG_PATH", tmp_path / "catalog.json")
    resp = client.get(f"/api/results?token={TOKEN}")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# SR-ID extraction
# ---------------------------------------------------------------------------

def test_sr_id_catalog_test():
    nodeid = "tests/test_catalog.py::test_catalog_atomic[SR-030-config-show]"
    assert _sr_id_from_nodeid(nodeid) == "SR-030"


def test_sr_id_python_test():
    nodeid = "tests/test_02_config.py::test_sr030_config_show"
    assert _sr_id_from_nodeid(nodeid) == "SR-030"


def test_sr_id_three_digits():
    nodeid = "tests/test_18_pipelines.py::test_sr273_pipeline_author_and_run"
    assert _sr_id_from_nodeid(nodeid) == "SR-273"


def test_sr_id_unknown_returns_none():
    assert _sr_id_from_nodeid("tests/conftest.py::some_fixture") is None


# ---------------------------------------------------------------------------
# _merge_results
# ---------------------------------------------------------------------------

def test_merge_no_results_file(tmp_path, monkeypatch):
    monkeypatch.setattr("webapp.main.RESULTS_PATH", tmp_path / "results.json")
    data = _merge_results()
    assert "rows" in data
    assert len(data["rows"]) > 0
    assert all(r["outcome"] == "not run" for r in data["rows"])


def test_merge_with_passed_outcome(tmp_path, monkeypatch):
    monkeypatch.setattr("webapp.main.RESULTS_PATH", tmp_path / "results.json")
    results = {
        "created": 1_700_000_000.0,
        "duration": 10.0,
        "summary": {"passed": 1},
        "tests": [
            {
                "nodeid": "tests/test_catalog.py::test_catalog_atomic[SR-030-config-show]",
                "outcome": "passed",
                "duration": 0.42,
            }
        ],
    }
    (tmp_path / "results.json").write_text(json.dumps(results))
    data = _merge_results()
    row = next(r for r in data["rows"] if r["id"] == "SR-030")
    assert row["outcome"] == "passed"
    assert abs(row["duration"] - 0.42) < 0.001
    assert row["slug"] == "config-show"
    assert "command" in row


# ---------------------------------------------------------------------------
# POST /run
# ---------------------------------------------------------------------------

def test_run_returns_409_when_already_running(monkeypatch):
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None  # still running
    monkeypatch.setattr("webapp.main._run_proc", mock_proc)
    resp = client.post(f"/run?token={TOKEN}")
    assert resp.status_code == 409


def test_run_starts_subprocess(monkeypatch):
    monkeypatch.setattr("webapp.main._run_proc", None)
    mock_proc = MagicMock()
    mock_proc.pid = 99999
    mock_proc.poll.return_value = None
    with patch("webapp.main.subprocess.Popen", return_value=mock_proc):
        resp = client.post(f"/run?token={TOKEN}")
    monkeypatch.setattr("webapp.main._run_proc", None)  # cleanup
    assert resp.status_code == 200
    assert resp.json()["status"] == "started"
    assert resp.json()["pid"] == 99999


# ---------------------------------------------------------------------------
# Run-state helpers (Task 1)
# ---------------------------------------------------------------------------


def test_write_and_delete_pid_file(tmp_path, monkeypatch):
    """_write_pid_file must create run.pid with pid and started fields."""
    monkeypatch.setattr("webapp.main.RUN_PID_PATH", tmp_path / "run.pid")
    from webapp import main as _m
    _m._write_pid_file(99999)
    data = json.loads((tmp_path / "run.pid").read_text())
    assert data["pid"] == 99999
    assert "started" in data
    _m._delete_pid_file()
    assert not (tmp_path / "run.pid").exists()


def test_is_run_alive_no_proc_no_pidfile(monkeypatch, tmp_path):
    """No in-memory proc and no PID file → False."""
    monkeypatch.setattr("webapp.main.RUN_PID_PATH", tmp_path / "run.pid")
    monkeypatch.setattr("webapp.main._run_proc", None)
    from webapp import main as _m
    assert _m._is_run_alive() is False


def test_is_run_alive_dead_pid_in_file(monkeypatch, tmp_path):
    """PID file with a definitely-dead PID → False and file is deleted.

    PID 999999999 exceeds Linux's pid_max (4194304), so os.kill always raises
    ProcessLookupError — guaranteed dead on Linux/macOS.
    """
    pid_path = tmp_path / "run.pid"
    pid_path.write_text(json.dumps({"pid": 999999999, "started": "x"}))
    monkeypatch.setattr("webapp.main.RUN_PID_PATH", pid_path)
    monkeypatch.setattr("webapp.main._run_proc", None)
    from webapp import main as _m
    result = _m._is_run_alive()
    assert result is False
    assert not pid_path.exists()


# ---------------------------------------------------------------------------
# _launch_run (Task 2)
# ---------------------------------------------------------------------------


def test_launch_run_creates_log_and_pid(tmp_path, monkeypatch):
    """_launch_run must write run.log and run.pid, return a Popen."""
    monkeypatch.setattr("webapp.main.RUN_PID_PATH", tmp_path / "run.pid")
    monkeypatch.setattr("webapp.main.RUN_LOG_PATH", tmp_path / "run.log")
    monkeypatch.setattr("webapp.main._run_proc", None)
    from webapp import main as _m
    proc = _m._launch_run(["python3", "-c", "print('hello'); import time; time.sleep(0.2)"])
    try:
        assert (tmp_path / "run.pid").exists()
        pid_data = json.loads((tmp_path / "run.pid").read_text())
        assert pid_data["pid"] == proc.pid
        proc.wait(timeout=2)
        import time; time.sleep(0.1)  # let cleanup thread run
        assert (tmp_path / "run.log").read_text().strip() == "hello"
        assert not (tmp_path / "run.pid").exists()
    finally:
        if proc.poll() is None:
            proc.kill()


def test_launch_run_raises_409_if_running(monkeypatch):
    """_launch_run must raise HTTPException(409) if a run is in progress."""
    from fastapi import HTTPException
    from webapp import main as _m

    fake_proc = type("P", (), {"poll": lambda self: None})()
    monkeypatch.setattr("webapp.main._run_proc", fake_proc)
    with pytest.raises(HTTPException) as exc_info:
        _m._launch_run(["echo", "hi"])
    assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# _tail_run_log (Task 3)
# ---------------------------------------------------------------------------
import asyncio as _asyncio


def test_tail_run_log_reads_existing_content(tmp_path, monkeypatch):
    """_tail_run_log must yield all lines written to run.log."""
    log_path = tmp_path / "run.log"
    log_path.write_text("line1\nline2\nline3\n")
    monkeypatch.setattr("webapp.main.RUN_LOG_PATH", log_path)
    monkeypatch.setattr("webapp.main._run_proc", None)
    from webapp import main as _m

    async def collect():
        lines = []
        async for line in _m._tail_run_log():
            lines.append(line)
        return lines

    result = _asyncio.run(collect())
    assert result == ["line1", "line2", "line3"]


def test_tail_run_log_no_file_yields_nothing(tmp_path, monkeypatch):
    """_tail_run_log must yield nothing if run.log does not exist."""
    monkeypatch.setattr("webapp.main.RUN_LOG_PATH", tmp_path / "run.log")
    monkeypatch.setattr("webapp.main._run_proc", None)
    from webapp import main as _m

    async def collect():
        return [line async for line in _m._tail_run_log()]

    assert _asyncio.run(collect()) == []
