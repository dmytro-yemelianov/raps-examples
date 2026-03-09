"""Unit tests for RapsRunner exit code tracking."""
from __future__ import annotations

from tests.helpers.runner import (
    RunResult,
    _captured_codes,
    _store_log,
    clear_captured_logs,
)
from tests.helpers.json_report import _parse_worst_cli_exit


def _make_result(sr_id, exit_code, timed_out=False):
    return RunResult(
        sr_id=sr_id,
        slug="test",
        command="raps test",
        exit_code=exit_code,
        stdout="",
        stderr="",
        duration=0.1,
        timed_out=timed_out,
    )


def setup_function():
    clear_captured_logs()


def test_store_log_records_exit_code():
    """_store_log must record exit code in _captured_codes."""
    result = _make_result("SR-999", 3)
    _store_log("SR-999", result)
    assert "SR-999" in _captured_codes
    assert 3 in _captured_codes["SR-999"]


def test_store_log_records_timeout_as_124():
    """Timeouts must be recorded as exit code 124."""
    result = _make_result("SR-998", 124, timed_out=True)
    _store_log("SR-998", result)
    assert 124 in _captured_codes["SR-998"]


def test_parse_worst_cli_exit_uses_structured_data():
    """_parse_worst_cli_exit must return max code from _captured_codes."""
    _captured_codes["SR-997"] = [0, 3, 5]
    assert _parse_worst_cli_exit("SR-997") == 5


def test_parse_worst_cli_exit_returns_none_for_unknown():
    assert _parse_worst_cli_exit("SR-000-unknown") is None


def test_lifecycle_steps_fold_into_base_id():
    """SR-996/step1 and SR-996/step2 must both fold into SR-996 codes."""
    _store_log("SR-996/step1", _make_result("SR-996/step1", 0))
    _store_log("SR-996/step2", _make_result("SR-996/step2", 6))
    assert 0 in _captured_codes["SR-996"]
    assert 6 in _captured_codes["SR-996"]
