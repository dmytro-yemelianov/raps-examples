"""Unit tests for AuthManager token save/restore logic."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from tests.helpers.auth import AuthManager


def test_save_token_file_storage_skips_platform_code(tmp_path):
    """When RAPS_USE_FILE_STORAGE is set and tokens.json exists,
    save_token() must NOT call subprocess (platform-specific fallback)."""
    manager = AuthManager(
        target="real",
        env={"RAPS_USE_FILE_STORAGE": "true"},
    )

    with (
        patch("tests.helpers.auth.Path.home", return_value=tmp_path / ".home"),
        patch("subprocess.run") as mock_run,
    ):
        token_dir = tmp_path / ".home" / ".config" / "raps"
        token_dir.mkdir(parents=True)
        (token_dir / "tokens.json").write_text('{"access_token": "test-tok"}')

        manager.save_token()

    mock_run.assert_not_called()
    assert manager._saved_token_file == '{"access_token": "test-tok"}'


def test_save_token_file_storage_from_os_environ(tmp_path, monkeypatch):
    """RAPS_USE_FILE_STORAGE in os.environ must be honored when env= not passed."""
    monkeypatch.setenv("RAPS_USE_FILE_STORAGE", "true")
    manager = AuthManager(target="real")  # no env= passed

    with (
        patch("tests.helpers.auth.Path.home", return_value=tmp_path / ".home"),
        patch("subprocess.run") as mock_run,
    ):
        token_dir = tmp_path / ".home" / ".config" / "raps"
        token_dir.mkdir(parents=True)
        (token_dir / "tokens.json").write_text('{"access_token": "env-tok"}')

        manager.save_token()

    mock_run.assert_not_called()
    assert manager._saved_token_file == '{"access_token": "env-tok"}'


def test_restore_token_file_storage_skips_platform_code(tmp_path):
    """When _saved_token_file is set, restore_token() must write the file
    and NOT call subprocess for re-injection."""
    manager = AuthManager(target="real", env={})
    manager._saved_token_file = '{"access_token": "restored-tok"}'

    with (
        patch("tests.helpers.auth.Path.home", return_value=tmp_path / ".home"),
        patch("subprocess.run") as mock_run,
    ):
        token_dir = tmp_path / ".home" / ".config" / "raps"
        token_dir.mkdir(parents=True)

        manager.restore_token()

        written = (token_dir / "tokens.json").read_text()

    assert written == '{"access_token": "restored-tok"}'
    mock_run.assert_not_called()
