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
