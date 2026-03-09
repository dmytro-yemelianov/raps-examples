# Test Infrastructure Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 6 quality issues in raps-examples test infrastructure: token save/restore logic, exit code tracking, catalog var validation, webapp security, lifecycle collision detection, and binary test stub sizing.

**Architecture:** Each fix is surgical and file-local. No new abstractions or cross-cutting changes. Tests first where unit-testable; direct implementation where integration context is required.

**Tech Stack:** Python 3.12, pytest 9, FastAPI, subprocess-based CLI runner

---

### Task 1: Token management — simplify `auth.py`

**Files:**
- Modify: `tests/helpers/auth.py` (lines 100–195)
- Test: `tests/helpers/test_auth_unit.py` (new file)

**Context:**
`save_token()` has an early-return comment but doesn't actually return — it falls through to platform-specific code even when file storage already saved the token. The fix is two early `return` statements.

**Step 1: Write the failing test**

Create `tests/helpers/test_auth_unit.py`:

```python
"""Unit tests for AuthManager token save/restore logic."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tests.helpers.auth import AuthManager


def test_save_token_file_storage_skips_platform_code(tmp_path):
    """When RAPS_USE_FILE_STORAGE is set and tokens.json exists,
    save_token() must NOT call subprocess (platform-specific fallback)."""
    token_file = tmp_path / "tokens.json"
    token_file.write_text('{"access_token": "test-tok"}')

    manager = AuthManager(
        target="real",
        env={"RAPS_USE_FILE_STORAGE": "true"},
    )

    with (
        patch("tests.helpers.auth.Path.home", return_value=tmp_path / ".home"),
        patch("subprocess.run") as mock_run,
    ):
        # Create the expected token file path
        token_dir = tmp_path / ".home" / ".config" / "raps"
        token_dir.mkdir(parents=True)
        (token_dir / "tokens.json").write_text('{"access_token": "test-tok"}')

        manager.save_token()

    # subprocess.run must NOT have been called
    mock_run.assert_not_called()
    assert manager._saved_token_file == '{"access_token": "test-tok"}'


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
```

**Step 2: Run test to verify it fails**

```bash
cd /home/dmytro/github/raps/raps-examples
python3 -m pytest tests/helpers/test_auth_unit.py -v
```

Expected: FAIL (subprocess.run IS called in current code)

**Step 3: Implement the fix**

In `tests/helpers/auth.py`, in `save_token()` — add `return` after file storage succeeds:

```python
def save_token(self) -> None:
    """Save the current 3-legged token for later restoration."""
    env = self._env or {}
    if env.get("RAPS_USE_FILE_STORAGE"):
        token_file = Path.home() / ".config" / "raps" / "tokens.json"
        if token_file.exists():
            self._saved_token_file = token_file.read_text()
        return  # <-- ADD THIS: skip platform-specific code

    try:
        if sys.platform == "win32":
            # ... existing Windows code unchanged ...
        else:
            # ... existing Unix code unchanged ...
```

In `restore_token()` — add `return` after file restore:

```python
def restore_token(self) -> None:
    """Restore saved 3-legged token after destructive operations."""
    self._has_2leg = None
    self._has_3leg = None

    if self._saved_token_file:
        token_file = Path.home() / ".config" / "raps" / "tokens.json"
        token_file.write_text(self._saved_token_file)
        token_file.chmod(0o600)
        self.has_2leg()
        self.has_3leg()
        return  # <-- ADD THIS: skip token re-injection code

    # ... rest of existing restore code unchanged ...
```

**Step 4: Run test to verify it passes**

```bash
python3 -m pytest tests/helpers/test_auth_unit.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add tests/helpers/auth.py tests/helpers/test_auth_unit.py
git commit -m "fix: simplify token save/restore — early return after file storage"
```

---

### Task 2: Structured exit code tracking (replace regex)

**Files:**
- Modify: `tests/helpers/runner.py` (add `_captured_codes` dict, update `_store_log`, `clear_captured_logs`)
- Modify: `tests/helpers/json_report.py` (update `_parse_worst_cli_exit`, import)
- Test: `tests/helpers/test_runner_unit.py` (new file)

**Context:**
`json_report.py` uses `_CLI_EXIT_RE` to parse exit codes out of accumulated log text. The log format is controlled by `runner.py:_store_log()`, which already has the structured data. Instead of serializing codes to text and re-parsing, store them in a parallel `_captured_codes` dict.

**Step 1: Write the failing test**

Create `tests/helpers/test_runner_unit.py`:

```python
"""Unit tests for RapsRunner exit code tracking."""
from __future__ import annotations

from tests.helpers.runner import (
    RunResult,
    _captured_codes,
    _captured_logs,
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
```

**Step 2: Run test to verify it fails**

```bash
python3 -m pytest tests/helpers/test_runner_unit.py -v
```

Expected: FAIL — `_captured_codes` not exported, `_parse_worst_cli_exit` still uses regex

**Step 3: Implement — update `runner.py`**

After the existing `_captured_logs` / `_captured_lock` block, add:

```python
# Maps base SR-ID -> list of CLI exit codes (structured, avoids log-text parsing)
_captured_codes: dict[str, list[int]] = {}
```

In `_store_log()`, add code recording after the log entry:

```python
def _store_log(sr_id: str, result: "RunResult") -> None:
    """Accumulate formatted log output and exit code for a sample run."""
    if not sr_id:
        return
    base_id = sr_id.split("/")[0]
    # ... existing log accumulation code unchanged ...

    # Record exit code in structured dict (avoids log-text regex parsing)
    code = 124 if result.timed_out else result.exit_code
    with _captured_lock:
        _captured_codes.setdefault(base_id, [])
        _captured_codes[base_id].append(code)
```

Update `clear_captured_logs()` to also clear codes:

```python
def clear_captured_logs() -> None:
    """Clear accumulated logs and codes."""
    with _captured_lock:
        _captured_logs.clear()
        _captured_codes.clear()
```

**Step 4: Implement — update `json_report.py`**

Replace the regex import and `_parse_worst_cli_exit`:

```python
# Remove: import re (top duplicate), _CLI_EXIT_RE pattern
# Replace with:
from .runner import _captured_logs, _captured_codes


def _parse_worst_cli_exit(sr_id: str) -> int | None:
    """Return worst (max) CLI exit code for sr_id, or None if not recorded."""
    codes = _captured_codes.get(sr_id)
    if not codes:
        return None
    return max(codes)
```

Update the call site in `pytest_runtest_makereport` — change:

```python
# OLD:
run_log = _captured_logs.get(sr_id, "")
if run_log:
    run_entry["log"] = run_log
    cli_exit = _parse_worst_cli_exit(run_log)

# NEW:
run_log = _captured_logs.get(sr_id, "")
if run_log:
    run_entry["log"] = run_log
cli_exit = _parse_worst_cli_exit(sr_id)
if cli_exit is not None:
    run_entry["cli_exit_code"] = cli_exit
```

**Step 5: Run test to verify it passes**

```bash
python3 -m pytest tests/helpers/test_runner_unit.py -v
```

Expected: PASS

**Step 6: Verify integration still works**

```bash
python3 -m pytest tests/test_02_config.py -v 2>&1 | tail -10
```

Expected: all pass or skip (no regressions)

**Step 7: Commit**

```bash
git add tests/helpers/runner.py tests/helpers/json_report.py tests/helpers/test_runner_unit.py
git commit -m "fix: replace log-regex exit code parsing with structured _captured_codes dict"
```

---

### Task 3: Catalog variable resolution — fail fast on unresolved vars

**Files:**
- Modify: `tests/test_catalog.py`
- Test: `tests/helpers/test_catalog_unit.py` (new file)

**Context:**
`_resolve()` silently returns `${var}` when a variable isn't found. Tests then send broken commands like `raps folder create ${project_full_id}` to the CLI, getting obscure CLI errors instead of a clear "missing variable" message.

**Step 1: Write the failing test**

Create `tests/helpers/test_catalog_unit.py`:

```python
"""Unit tests for catalog variable resolution."""
from __future__ import annotations

import pytest

# Import the private helpers — they live at module level in test_catalog.py
import importlib, sys

# We test the _resolve function directly
from tests.test_catalog import _resolve


def test_resolve_substitutes_known_var():
    assert _resolve("raps hub list ${hub_id}", {"hub_id": "b.123"}) == "raps hub list b.123"


def test_resolve_multiple_vars():
    cmd = _resolve(
        "raps project list ${hub_id} --project ${project_id}",
        {"hub_id": "b.1", "project_id": "p.2"},
    )
    assert cmd == "raps project list b.1 --project p.2"


def test_resolve_unresolved_var_raises():
    """Unresolved ${var} must cause pytest.fail(), not silent passthrough."""
    with pytest.raises(pytest.fail.Exception):
        _resolve("raps folder create ${missing_var}", {})


def test_resolve_env_var_takes_priority(monkeypatch):
    """RAPS_VAR_HUB_ID env var must override the variables dict."""
    monkeypatch.setenv("RAPS_VAR_HUB_ID", "env-hub")
    result = _resolve("raps hub list ${hub_id}", {"hub_id": "dict-hub"})
    assert result == "raps hub list env-hub"
```

**Step 2: Run test to verify it fails**

```bash
python3 -m pytest tests/helpers/test_catalog_unit.py::test_resolve_unresolved_var_raises -v
```

Expected: FAIL — current code returns `${missing_var}` instead of failing

**Step 3: Implement — update `_resolve()` in `test_catalog.py`**

```python
def _resolve(command: str, variables: dict[str, str]) -> str:
    """Replace ${name}: RAPS_VAR_NAME env var takes priority over variables dict.

    Raises pytest.fail if any ${var} remains unresolved after substitution.
    """
    def replace(m: re.Match) -> str:
        name = m.group(1)
        env_key = f"RAPS_VAR_{name.upper()}"
        return os.environ.get(env_key, variables.get(name, m.group(0)))

    resolved = re.sub(r"\$\{(\w+)\}", replace, command)

    # Detect unresolved variables and fail fast with a clear message
    unresolved = re.findall(r"\$\{(\w+)\}", resolved)
    if unresolved:
        available = sorted(variables.keys())
        pytest.fail(
            f"Unresolved catalog variables: {unresolved}\n"
            f"  Command: {command!r}\n"
            f"  Available vars: {available}"
        )

    return resolved
```

**Step 4: Run all catalog unit tests**

```bash
python3 -m pytest tests/helpers/test_catalog_unit.py -v
```

Expected: all 4 PASS

**Step 5: Run catalog integration tests to check no regressions**

```bash
python3 -m pytest tests/test_catalog.py -v 2>&1 | tail -20
```

Expected: same pass/skip counts as before (no test now fails due to unresolved vars — if any do, those were already broken silently)

**Step 6: Commit**

```bash
git add tests/test_catalog.py tests/helpers/test_catalog_unit.py
git commit -m "fix: fail fast on unresolved catalog \${var} placeholders"
```

---

### Task 4: Webapp security — constant-time token comparison + 409 on concurrent run

**Files:**
- Modify: `webapp/main.py` (lines 67–72 for token check; `/run` handler for 409)
- Test: manual `curl` verification (no unit test framework for FastAPI routes here)

**Context:**
`token != _TOKEN` is a plain string comparison. Replace with `secrets.compare_digest()`. Also `/run` starts a new subprocess even if one is running — should return 409 instead of silently spawning a second process.

**Step 1: Add `import secrets` and fix `_require_token`**

Read current `_require_token` (lines 67–72 in `webapp/main.py`):

```python
def _require_token(token: str = Query(..., alias="token")) -> str:
    if not _TOKEN:
        raise HTTPException(500, "RAPS_DASHBOARD_TOKEN not set")
    if token != _TOKEN:
        raise HTTPException(401, "Invalid token")
    return token
```

Replace with:

```python
import secrets  # add to imports at top of file

def _require_token(token: str = Query(..., alias="token")) -> str:
    if not _TOKEN:
        raise HTTPException(500, "RAPS_DASHBOARD_TOKEN not set")
    if not secrets.compare_digest(token, _TOKEN):
        raise HTTPException(401, "Invalid token")
    return token
```

**Step 2: Find the `/run` POST handler and add 409 guard**

Find the route `@app.post("/run")` in `webapp/main.py`. At the top of the handler body, after the token check, add:

```python
with _run_lock:
    if _run_proc is not None and _run_proc.poll() is None:
        raise HTTPException(409, "A test run is already in progress")
```

**Step 3: Verify manually**

Start the webapp in a test shell:

```bash
cd /home/dmytro/github/raps/raps-examples
RAPS_DASHBOARD_TOKEN=test123 python3 -m uvicorn webapp.main:app --port 8099 &
sleep 2

# Should get 401 with wrong token
curl -s -o /dev/null -w "%{http_code}" "http://localhost:8099/?token=wrong"
# Expected: 401

# Kill test server
pkill -f "port 8099" 2>/dev/null; kill %1 2>/dev/null
```

**Step 4: Commit**

```bash
git add webapp/main.py
git commit -m "fix: use secrets.compare_digest for token auth; return 409 on concurrent run"
```

---

### Task 5: Lifecycle collision detection — warn on mixed direct+step logs

**Files:**
- Modify: `tests/helpers/runner.py` (`_store_log` function)
- Test: add to `tests/helpers/test_runner_unit.py`

**Context:**
`_store_log()` folds both `SR-063` (direct) and `SR-063/step1` (lifecycle step) into the same key. If the same SR-ID is used for both a direct test AND a lifecycle, logs silently merge. We add a `_log_types` dict tracking whether each base ID has received `"direct"` or `"step"` entries, and warn on collision.

**Step 1: Add test to `test_runner_unit.py`**

Append to `tests/helpers/test_runner_unit.py`:

```python
import warnings


def test_lifecycle_collision_warning():
    """Direct + step logs for same SR-ID must emit a warning."""
    clear_captured_logs()
    # Direct entry first
    _store_log("SR-995", _make_result("SR-995", 0))
    # Then a lifecycle step with same base ID — should warn
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        _store_log("SR-995/step1", _make_result("SR-995/step1", 0))
    assert any("SR-995" in str(x.message) for x in w), (
        "Expected warning about SR-995 receiving both direct and step logs"
    )


def test_no_warning_for_lifecycle_steps_only():
    """Multiple steps for same base ID must NOT warn."""
    clear_captured_logs()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        _store_log("SR-994/step1", _make_result("SR-994/step1", 0))
        _store_log("SR-994/step2", _make_result("SR-994/step2", 3))
    assert not any("SR-994" in str(x.message) for x in w)
```

**Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/helpers/test_runner_unit.py::test_lifecycle_collision_warning -v
```

Expected: FAIL — no warning is currently emitted

**Step 3: Implement — update `runner.py`**

Add after the `_captured_codes` declaration:

```python
# Tracks whether each base SR-ID has received a "direct" or "step" log entry
# Used to detect accidental reuse of the same SR-ID for both types
_log_types: dict[str, str] = {}  # base_id -> "direct" | "step"
```

In `_store_log()`, after computing `base_id`, add detection logic:

```python
def _store_log(sr_id: str, result: "RunResult") -> None:
    """Accumulate formatted log output and exit code for a sample run."""
    if not sr_id:
        return
    base_id = sr_id.split("/")[0]
    entry_type = "step" if "/" in sr_id else "direct"

    # Detect mixed direct+step usage for same base ID
    with _captured_lock:
        prior = _log_types.get(base_id)
        if prior and prior != entry_type:
            import warnings
            warnings.warn(
                f"SR-ID collision: '{base_id}' has both direct and lifecycle-step log entries. "
                f"Check that SR-IDs are not shared between direct tests and lifecycle tests.",
                stacklevel=3,
            )
        _log_types[base_id] = entry_type

    # ... rest of existing _store_log code unchanged ...
```

Update `clear_captured_logs()` to also clear `_log_types`:

```python
def clear_captured_logs() -> None:
    """Clear accumulated logs, codes, and type tracking."""
    with _captured_lock:
        _captured_logs.clear()
        _captured_codes.clear()
        _log_types.clear()
```

**Step 4: Run all runner unit tests**

```bash
python3 -m pytest tests/helpers/test_runner_unit.py -v
```

Expected: all PASS

**Step 5: Commit**

```bash
git add tests/helpers/runner.py tests/helpers/test_runner_unit.py
git commit -m "fix: warn on SR-ID collision between direct and lifecycle-step log entries"
```

---

### Task 6: Binary test stub padding — 4096 bytes for RVT and DWG

**Files:**
- Modify: `tests/test_00_setup.py` (`_generate_rvt`, `_generate_dwg`)

**Context:**
Generated RVT stubs are 1024 bytes (512-byte OLE2 header + 512-byte pattern). DWG stubs are 512 bytes. APS upload endpoints may enforce minimum sizes. Pad both to 4096 bytes with deterministic patterns.

**Step 1: Verify current file sizes (to see the "before")**

```bash
python3 -m pytest tests/test_00_setup.py::test_sr003_setup_generate_test_files -v
ls -la test-data/sample.rvt test-data/sample.dwg
```

Note the current sizes.

**Step 2: Update `_generate_rvt()`**

Current: 512-byte header + 512-byte pattern = 1024 bytes total.

Change to 4096 bytes:

```python
def _generate_rvt(path: Path) -> None:
    """Generate a binary file with Revit OLE Compound Document magic bytes.

    Real RVT files are OLE2 compound documents. The magic bytes are
    D0 CF 11 E0 A1 B1 1A E1 followed by a 512-byte header.
    Padded to 4096 bytes for APS upload compatibility.
    """
    magic = bytes([0xD0, 0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1])
    header = bytearray(512)
    header[0:8] = magic
    header[24:26] = b'\x3E\x00'  # Minor version
    header[26:28] = b'\x03\x00'  # Major version (3 = V3)
    header[28:30] = b'\xFE\xFF'  # Byte order (little-endian)
    header[30:32] = b'\x09\x00'  # Sector size power (2^9 = 512)
    header[32:34] = b'\x06\x00'  # Mini sector size power (2^6 = 64)
    # Pad to 4096 bytes with deterministic pattern
    padding = (bytes(range(256)) * 16)[:3584]  # 3584 bytes to reach 4096 total
    path.write_bytes(bytes(header) + padding)
```

**Step 3: Update `_generate_dwg()`**

Current: 512-byte header only.

Change to 4096 bytes:

```python
def _generate_dwg(path: Path) -> None:
    """Generate a binary file with DWG magic bytes (AutoCAD 2018+ format).

    DWG files start with a 6-byte version string (AC1032 for 2018+).
    Padded to 4096 bytes for APS upload compatibility.
    """
    magic = b'AC1032'  # AutoCAD 2018 format
    header = bytearray(512)
    header[0:6] = magic
    header[6] = 0x00   # Maintenance version
    header[7] = 0x01   # One byte after version
    # Pad to 4096 bytes with deterministic pattern
    padding = (bytes(range(256)) * 16)[:3584]  # 3584 bytes to reach 4096 total
    path.write_bytes(bytes(header) + padding)
```

**Step 4: Run test and verify new sizes**

```bash
python3 -m pytest tests/test_00_setup.py::test_sr003_setup_generate_test_files -v
ls -la test-data/sample.rvt test-data/sample.dwg
```

Expected: both files are 4096 bytes, test passes

**Step 5: Commit**

```bash
git add tests/test_00_setup.py
git commit -m "fix: pad RVT and DWG stubs to 4096 bytes for APS upload compatibility"
```

---

### Task 7: Final smoke test

**Step 1: Run all unit tests**

```bash
python3 -m pytest tests/helpers/ -v
```

Expected: all pass (test_auth_unit, test_runner_unit, test_catalog_unit)

**Step 2: Run a fast integration subset**

```bash
python3 -m pytest tests/test_00_setup.py tests/test_02_config.py tests/test_catalog.py -v 2>&1 | tail -20
```

Expected: same pass/skip distribution as before all changes

**Step 3: Confirm no warnings appear for existing tests**

```bash
python3 -m pytest tests/test_30_workflows.py -v -W error::UserWarning 2>&1 | tail -20
```

Expected: passes without SR-ID collision warnings (confirms existing SR-IDs don't accidentally share between direct and lifecycle)
