# Webapp Persistent Run State Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the webapp's test run survive browser disconnects and server restarts by writing
pytest stdout directly to a log file, tracking the PID on disk, and tail-reading the file for all
streaming (replay + live).

**Architecture:** pytest stdout is redirected to `webapp/run.log` at launch time (no writer
thread needed — subprocess inherits the fd). A minimal cleanup thread calls `proc.wait()` then
deletes `webapp/run.pid`. All streaming (SSE and WebSocket) tails `run.log` from position 0,
scrubbing secrets on the way out. WebSocket no longer kills the process on disconnect.

**Tech Stack:** Python 3.12, FastAPI, asyncio, subprocess, threading (one cleanup thread per run)

---

### Task 1: Add file-based run state helpers

**Files:**
- Modify: `webapp/main.py`
- Test: `tests/test_webapp.py` (extend existing)

**Context:**
`webapp/main.py` currently has `_run_proc` as the only run state (in-memory). We add two path
constants and four small helpers. `RUN_LOG_PATH` and `RUN_PID_PATH` live alongside
`RESULTS_PATH`. The helpers are pure functions that only touch the filesystem.

**Step 1: Read the current constants block**

```bash
head -25 /home/dmytro/github/raps/raps-examples/webapp/main.py
```

**Step 2: Write failing tests**

In `tests/test_webapp.py`, find the existing test class/functions and append:

```python
# ---------------------------------------------------------------------------
# Run-state helpers
# ---------------------------------------------------------------------------
import json as _json
from webapp.main import (
    RUN_PID_PATH,
    RUN_LOG_PATH,
    _write_pid_file,
    _delete_pid_file,
    _is_run_alive,
)


def test_write_and_delete_pid_file(tmp_path, monkeypatch):
    monkeypatch.setattr("webapp.main.RUN_PID_PATH", tmp_path / "run.pid")
    from webapp import main as _m
    _m._write_pid_file(99999)
    data = _json.loads((tmp_path / "run.pid").read_text())
    assert data["pid"] == 99999
    assert "started" in data
    _m._delete_pid_file()
    assert not (tmp_path / "run.pid").exists()


def test_is_run_alive_no_proc_no_pidfile(monkeypatch, tmp_path):
    monkeypatch.setattr("webapp.main.RUN_PID_PATH", tmp_path / "run.pid")
    monkeypatch.setattr("webapp.main._run_proc", None)
    from webapp import main as _m
    assert _m._is_run_alive() is False


def test_is_run_alive_dead_pid_in_file(monkeypatch, tmp_path):
    """PID file with a dead PID → False and file is deleted."""
    pid_path = tmp_path / "run.pid"
    pid_path.write_text(_json.dumps({"pid": 1, "started": "x"}))  # PID 1 is init, won't match
    monkeypatch.setattr("webapp.main.RUN_PID_PATH", pid_path)
    monkeypatch.setattr("webapp.main._run_proc", None)
    from webapp import main as _m
    # Use a definitely-dead PID
    import os
    pid_path.write_text(_json.dumps({"pid": 999999999, "started": "x"}))
    result = _m._is_run_alive()
    assert result is False
    assert not pid_path.exists()
```

**Step 3: Run to confirm failure**

```bash
cd /home/dmytro/github/raps/raps-examples
python3 -m pytest tests/test_webapp.py::test_write_and_delete_pid_file \
    tests/test_webapp.py::test_is_run_alive_no_proc_no_pidfile \
    tests/test_webapp.py::test_is_run_alive_dead_pid_in_file -v
```

Expected: ImportError (symbols don't exist yet)

**Step 4: Implement the helpers in main.py**

After the existing `RESULTS_PATH` line, add:

```python
RUN_PID_PATH = Path(__file__).parent / "run.pid"
RUN_LOG_PATH = Path(__file__).parent / "run.log"
```

After the `_run_lock` / `_login_lock` block, add:

```python
def _write_pid_file(pid: int) -> None:
    """Write run.pid with current PID and ISO timestamp."""
    from datetime import datetime, timezone
    RUN_PID_PATH.write_text(json.dumps({
        "pid": pid,
        "started": datetime.now(timezone.utc).isoformat(),
    }))


def _delete_pid_file() -> None:
    """Remove run.pid if it exists."""
    RUN_PID_PATH.unlink(missing_ok=True)


def _is_run_alive() -> bool:
    """Return True if a test run is currently in progress.

    Checks in-memory _run_proc first, then falls back to run.pid on disk.
    Cleans up a stale PID file if the process is dead.
    """
    global _run_proc
    # Fast path: in-memory proc still running
    if _run_proc is not None and _run_proc.poll() is None:
        return True
    # Slow path: check disk PID file (handles server-restart case)
    if RUN_PID_PATH.exists():
        try:
            data = json.loads(RUN_PID_PATH.read_text())
            pid = int(data["pid"])
            os.kill(pid, 0)   # signal 0 = liveness check, no-op if alive
            return True       # process alive — server restarted mid-run
        except (ProcessLookupError, PermissionError):
            # Process dead — stale PID file, clean up
            _delete_pid_file()
            RUN_LOG_PATH_local = RUN_LOG_PATH  # avoid closure issues
            # Don't delete run.log — it has the partial output for the user to see
        except (json.JSONDecodeError, KeyError, ValueError, OSError):
            _delete_pid_file()
    return False
```

Note: `import os` is already present in main.py.

**Step 5: Run tests**

```bash
python3 -m pytest tests/test_webapp.py::test_write_and_delete_pid_file \
    tests/test_webapp.py::test_is_run_alive_no_proc_no_pidfile \
    tests/test_webapp.py::test_is_run_alive_dead_pid_in_file -v
```

Expected: all 3 PASS

**Step 6: Commit**

```bash
git add webapp/main.py tests/test_webapp.py
git commit -m "feat: add RUN_PID_PATH/RUN_LOG_PATH constants and PID file helpers"
```

---

### Task 2: Extract _launch_run() — shared run launcher

**Files:**
- Modify: `webapp/main.py`

**Context:**
Currently `POST /run` and `/ws/run` each have their own `subprocess.Popen(...)` call with
slightly different flags (`-q` vs `-v`). We extract a common `_launch_run(extra_flags)` that:
1. Raises 409 if already running
2. Clears `run.log`
3. Opens `run.log` for writing and passes it as stdout to Popen (subprocess writes directly)
4. Writes `run.pid`
5. Starts a daemon cleanup thread (`proc.wait()` → `_delete_pid_file()`)
6. Returns the `Popen` object

The key change: **stdout goes to the file fd, not a PIPE**. The cleanup thread is the only
background work needed.

**Step 1: Write failing test**

Append to `tests/test_webapp.py`:

```python
def test_launch_run_creates_log_and_pid(tmp_path, monkeypatch):
    """_launch_run must write run.log and run.pid, return a Popen."""
    import subprocess
    monkeypatch.setattr("webapp.main.RUN_PID_PATH", tmp_path / "run.pid")
    monkeypatch.setattr("webapp.main.RUN_LOG_PATH", tmp_path / "run.log")
    monkeypatch.setattr("webapp.main._run_proc", None)
    from webapp import main as _m
    proc = _m._launch_run(["python3", "-c", "print('hello'); import time; time.sleep(0.2)"])
    try:
        assert (tmp_path / "run.pid").exists()
        pid_data = _json.loads((tmp_path / "run.pid").read_text())
        assert pid_data["pid"] == proc.pid
        proc.wait(timeout=2)
        import time; time.sleep(0.1)  # cleanup thread
        # run.log should have content
        assert (tmp_path / "run.log").read_text().strip() == "hello"
        # run.pid should be deleted after process exits
        assert not (tmp_path / "run.pid").exists()
    finally:
        if proc.poll() is None:
            proc.kill()


def test_launch_run_raises_409_if_running(monkeypatch):
    """_launch_run must raise HTTPException(409) if a run is in progress."""
    from webapp import main as _m
    import subprocess

    fake_proc = type("P", (), {"poll": lambda self: None})()
    monkeypatch.setattr("webapp.main._run_proc", fake_proc)
    with pytest.raises(HTTPException) as exc_info:
        _m._launch_run(["echo", "hi"])
    assert exc_info.value.status_code == 409
```

**Step 2: Run to confirm failure**

```bash
python3 -m pytest tests/test_webapp.py::test_launch_run_creates_log_and_pid \
    tests/test_webapp.py::test_launch_run_raises_409_if_running -v
```

Expected: ImportError (`_launch_run` not defined)

**Step 3: Implement _launch_run in main.py**

Add after `_is_run_alive()`:

```python
def _launch_run(cmd: list[str]) -> "subprocess.Popen[str]":
    """Launch a subprocess, writing stdout to run.log. Thread-safe.

    Raises HTTPException(409) if a run is already in progress.
    Returns the Popen object (stdout is NOT a pipe — use run.log for output).
    """
    global _run_proc
    with _run_lock:
        if _is_run_alive():
            raise HTTPException(409, "A test run is already in progress")
        # Clear previous log
        RUN_LOG_PATH.write_text("")
        # Open log file; pass to subprocess so it writes directly (no writer thread needed)
        log_fd = open(RUN_LOG_PATH, "w")
        proc = subprocess.Popen(
            cmd,
            cwd=ROOT,
            stdout=log_fd,
            stderr=subprocess.STDOUT,
        )
        log_fd.close()   # subprocess inherited the fd; we can close our handle
        _write_pid_file(proc.pid)
        _run_proc = proc

    # Cleanup thread: wait for process exit, then remove PID file
    def _cleanup() -> None:
        proc.wait()
        _delete_pid_file()
    threading.Thread(target=_cleanup, daemon=True).start()

    return proc
```

**Step 4: Run tests**

```bash
python3 -m pytest tests/test_webapp.py::test_launch_run_creates_log_and_pid \
    tests/test_webapp.py::test_launch_run_raises_409_if_running -v
```

Expected: both PASS

**Step 5: Commit**

```bash
git add webapp/main.py tests/test_webapp.py
git commit -m "feat: add _launch_run() — shared subprocess launcher with log file + pid file"
```

---

### Task 3: Add _tail_run_log() async generator

**Files:**
- Modify: `webapp/main.py`

**Context:**
This is the core of reconnect support. The generator opens `run.log`, reads from position 0
(full replay), yields lines, and when it hits EOF it checks if the process is still alive. If
alive → sleep 50ms and retry. If dead → stop. The caller sends `__done__` after the generator
finishes. Lines are scrubbed before yielding.

**Step 1: Write failing test**

Append to `tests/test_webapp.py`:

```python
import asyncio as _asyncio


def test_tail_run_log_reads_existing_content(tmp_path, monkeypatch):
    """_tail_run_log must yield all lines written to run.log."""
    log_path = tmp_path / "run.log"
    log_path.write_text("line1\nline2\nline3\n")
    monkeypatch.setattr("webapp.main.RUN_LOG_PATH", log_path)
    monkeypatch.setattr("webapp.main._run_proc", None)  # no live process
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
```

**Step 2: Run to confirm failure**

```bash
python3 -m pytest tests/test_webapp.py::test_tail_run_log_reads_existing_content \
    tests/test_webapp.py::test_tail_run_log_no_file_yields_nothing -v
```

Expected: ImportError (`_tail_run_log` not defined)

**Step 3: Implement _tail_run_log in main.py**

Add after `_launch_run()`:

```python
async def _tail_run_log() -> AsyncIterator[str]:
    """Async generator: replay run.log from start, then follow live output.

    Yields scrubbed lines (without trailing newline).
    Stops when the file is exhausted AND the run process is no longer alive.
    """
    if not RUN_LOG_PATH.exists():
        return
    loop = asyncio.get_running_loop()
    with open(RUN_LOG_PATH, "r") as f:
        while True:
            line = await loop.run_in_executor(None, f.readline)
            if line:
                yield _scrub(line.rstrip())
            else:
                # EOF — check if process still running
                if _is_run_alive():
                    await asyncio.sleep(0.05)
                else:
                    # One final drain to catch last lines written between poll and EOF
                    remaining = await loop.run_in_executor(None, f.read)
                    for tail_line in remaining.splitlines():
                        yield _scrub(tail_line)
                    break
```

**Step 4: Run tests**

```bash
python3 -m pytest tests/test_webapp.py::test_tail_run_log_reads_existing_content \
    tests/test_webapp.py::test_tail_run_log_no_file_yields_nothing -v
```

Expected: both PASS

**Step 5: Commit**

```bash
git add webapp/main.py tests/test_webapp.py
git commit -m "feat: add _tail_run_log() async generator for replay+live file tailing"
```

---

### Task 4: Update POST /run and GET /stream to use new infrastructure

**Files:**
- Modify: `webapp/main.py` (lines ~191–244)

**Context:**
`POST /run` currently builds a Popen inline. Replace with `_launch_run(cmd)`.
`GET /stream` currently reads from `proc.stdout` pipe. Replace with `_tail_run_log()`.
The SSE path still works exactly the same from the client's perspective — it just reconnects
cleanly now.

**Step 1: Read current POST /run and GET /stream**

```bash
sed -n '191,244p' /home/dmytro/github/raps/raps-examples/webapp/main.py
```

**Step 2: Replace POST /run**

Old (lines 191–210):
```python
@app.post("/run")
def run_tests(token: str = Query(..., alias="token")):
    global _run_proc
    _require_token(token)
    with _run_lock:
        if _run_proc is not None and _run_proc.poll() is None:
            raise HTTPException(409, "A test run is already in progress")
        _run_proc = subprocess.Popen(
            [
                "python3", "-m", "pytest", "tests/", "-q",
                "--json-report", f"--json-report-file={RESULTS_PATH}",
                "--no-header",
            ],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    return {"status": "started", "pid": _run_proc.pid}
```

New:
```python
@app.post("/run")
def run_tests(token: str = Query(..., alias="token")):
    _require_token(token)
    proc = _launch_run([
        "python3", "-m", "pytest", "tests/", "-q",
        "--json-report", f"--json-report-file={RESULTS_PATH}",
        "--no-header",
    ])
    return {"status": "started", "pid": proc.pid}
```

**Step 3: Replace GET /stream**

Old `_lines()` inner function reads from `proc.stdout` pipe. Replace entire route with:

```python
@app.get("/stream")
async def stream_output(token: str = Query(..., alias="token")):
    """SSE — streams pytest stdout from run.log (supports reconnect/replay)."""
    _require_token(token)

    async def _lines() -> AsyncIterator[str]:
        async for line in _tail_run_log():
            yield f"data: {line}\n\n"
        yield "data: __done__\n\n"

    return StreamingResponse(
        _lines(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

**Step 4: Verify the webapp still imports cleanly**

```bash
python3 -c "import webapp.main; print('OK')"
```

Expected: OK

**Step 5: Commit**

```bash
git add webapp/main.py
git commit -m "refactor: POST /run and GET /stream use _launch_run + _tail_run_log"
```

---

### Task 5: Update /ws/run — file tailing + remove kill-on-disconnect

**Files:**
- Modify: `webapp/main.py` (lines ~365–463)

**Context:**
`/ws/run` has two problems:
1. It builds its own Popen inline (now replaced by `_launch_run`)
2. The `finally` block kills the process on client disconnect

The WebSocket route needs to:
- Use `_launch_run()` with `-v` flags
- Read from `_tail_run_log()` instead of stdout pipe
- Remove the `finally` kill block entirely
- Keep the progress parsing (`_RE_TEST_RESULT`, `_RE_SR_ID`) — just point it at lines from the
  generator instead of pipe

**Step 1: Read the current /ws/run handler**

```bash
sed -n '365,464p' /home/dmytro/github/raps/raps-examples/webapp/main.py
```

**Step 2: Replace /ws/run**

Replace the entire `@app.websocket("/ws/run")` handler with:

```python
@app.websocket("/ws/run")
async def ws_run(websocket: WebSocket):
    """WebSocket: starts pytest with -v, streams structured JSON progress events.

    Disconnecting does NOT kill the test run. Reconnect to resume streaming.
    """
    token = websocket.query_params.get("token", "")
    if not _TOKEN or not secrets.compare_digest(token, _TOKEN):
        await websocket.close(code=1008, reason="Unauthorized")
        return

    await websocket.accept()

    # Start run (or 409 if already running)
    try:
        _launch_run([
            "python3", "-m", "pytest", "tests/", "-v", "--no-header",
            "-p", "no:xdist",
            "-o", "addopts=",
            "--tb=short",
            "--json-report", f"--json-report-file={RESULTS_PATH}",
        ])
    except HTTPException as exc:
        await websocket.send_json({"type": "error", "text": exc.detail})
        await websocket.close()
        return

    passed = failed = skipped = 0
    try:
        async for line in _tail_run_log():
            try:
                await websocket.send_json({"type": "log", "text": line})
            except Exception:
                # Client disconnected — stop streaming but leave process running
                return

            m = _RE_TEST_RESULT.search(line)
            if m:
                outcome = m.group(1)
                if outcome == "PASSED":
                    passed += 1
                elif outcome == "FAILED":
                    failed += 1
                elif outcome == "SKIPPED":
                    skipped += 1
                done = passed + failed + skipped
                sr_m = _RE_SR_ID.search(line)
                sr_num = sr_m.group(1) or sr_m.group(2) if sr_m else None
                current = f"SR-{sr_num}" if sr_num else None
                try:
                    await websocket.send_json({
                        "type": "progress",
                        "passed": passed,
                        "failed": failed,
                        "skipped": skipped,
                        "total": _TOTAL_TESTS,
                        "done": done,
                        "pct": min(100, round(done / _TOTAL_TESTS * 100)),
                        "current": current,
                        "sr_id": current,
                        "outcome": outcome.lower(),
                    })
                except Exception:
                    return  # client disconnected
    except Exception:
        return

    try:
        await websocket.send_json({
            "type": "done",
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
        })
        await websocket.close()
    except Exception:
        pass
```

**Step 3: Verify import**

```bash
python3 -c "import webapp.main; print('OK')"
```

**Step 4: Also add a WebSocket reconnect endpoint** — a separate `/ws/stream` that tails
an **in-progress** run without starting a new one. This allows the dashboard to reconnect
after a page refresh:

```python
@app.websocket("/ws/stream")
async def ws_stream(websocket: WebSocket):
    """WebSocket: reconnect to an in-progress run (no new run started).

    If no run is in progress, sends a 'done' event immediately.
    """
    token = websocket.query_params.get("token", "")
    if not _TOKEN or not secrets.compare_digest(token, _TOKEN):
        await websocket.close(code=1008, reason="Unauthorized")
        return

    await websocket.accept()

    passed = failed = skipped = 0
    try:
        async for line in _tail_run_log():
            try:
                await websocket.send_json({"type": "log", "text": line})
            except Exception:
                return  # client disconnected, run keeps going

            m = _RE_TEST_RESULT.search(line)
            if m:
                outcome = m.group(1)
                if outcome == "PASSED":
                    passed += 1
                elif outcome == "FAILED":
                    failed += 1
                elif outcome == "SKIPPED":
                    skipped += 1
                done = passed + failed + skipped
                sr_m = _RE_SR_ID.search(line)
                sr_num = sr_m.group(1) or sr_m.group(2) if sr_m else None
                current = f"SR-{sr_num}" if sr_num else None
                try:
                    await websocket.send_json({
                        "type": "progress",
                        "passed": passed,
                        "failed": failed,
                        "skipped": skipped,
                        "total": _TOTAL_TESTS,
                        "done": done,
                        "pct": min(100, round(done / _TOTAL_TESTS * 100)),
                        "current": current,
                        "sr_id": current,
                        "outcome": outcome.lower(),
                    })
                except Exception:
                    return
    except Exception:
        return

    try:
        await websocket.send_json({"type": "done", "passed": passed,
                                   "failed": failed, "skipped": skipped})
        await websocket.close()
    except Exception:
        pass
```

**Step 5: Verify import and run existing webapp tests**

```bash
python3 -c "import webapp.main; print('OK')"
python3 -m pytest tests/test_webapp.py -v 2>&1 | tail -20
```

Expected: OK import, existing tests pass

**Step 6: Commit**

```bash
git add webapp/main.py
git commit -m "feat: /ws/run uses _launch_run+_tail_run_log; add /ws/stream for reconnect; remove kill-on-disconnect"
```

---

### Task 6: Update POST /run/abort to handle the new model

**Files:**
- Modify: `webapp/main.py` (lines ~266–272)

**Context:**
`POST /run/abort` calls `_kill_run_proc()`. That function only checks `_run_proc`. Now that
a run can also be detected via PID file (orphan case), abort should also kill a PID-file-only
process. Update `_kill_run_proc()` to handle both.

**Step 1: Read current _kill_run_proc**

```bash
sed -n '349,358p' /home/dmytro/github/raps/raps-examples/webapp/main.py
```

**Step 2: Update _kill_run_proc**

Replace existing `_kill_run_proc`:

```python
def _kill_run_proc() -> None:
    """Kill the running test process (in-memory or PID-file orphan)."""
    global _run_proc
    # In-memory proc
    if _run_proc is not None and _run_proc.poll() is None:
        _run_proc.terminate()
        try:
            _run_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _run_proc.kill()
    # PID-file orphan (server restarted mid-run)
    if RUN_PID_PATH.exists():
        try:
            data = json.loads(RUN_PID_PATH.read_text())
            pid = int(data["pid"])
            os.kill(pid, 15)  # SIGTERM
        except (ProcessLookupError, PermissionError, json.JSONDecodeError,
                KeyError, ValueError, OSError):
            pass
        _delete_pid_file()
```

**Step 3: Verify import**

```bash
python3 -c "import webapp.main; print('OK')"
```

**Step 4: Commit**

```bash
git add webapp/main.py
git commit -m "fix: _kill_run_proc handles PID-file orphan processes"
```

---

### Task 7: Add GET /api/run-status endpoint

**Files:**
- Modify: `webapp/main.py`

**Context:**
The UI needs to know on page load whether a run is in progress (to show a spinner and connect
to `/ws/stream` for replay). Add a lightweight status endpoint.

**Step 1: Add the route**

After `GET /api/auth`, add:

```python
@app.get("/api/run-status")
def api_run_status(token: str = Query(..., alias="token")):
    """Return whether a test run is currently in progress."""
    _require_token(token)
    alive = _is_run_alive()
    started = None
    if alive and RUN_PID_PATH.exists():
        try:
            started = json.loads(RUN_PID_PATH.read_text()).get("started")
        except (json.JSONDecodeError, OSError):
            pass
    return {"running": alive, "started": started}
```

**Step 2: Verify import**

```bash
python3 -c "import webapp.main; print('OK')"
```

**Step 3: Commit**

```bash
git add webapp/main.py
git commit -m "feat: add GET /api/run-status endpoint"
```

---

### Task 8: Final smoke test

**Step 1: Run all webapp unit tests**

```bash
python3 -m pytest tests/test_webapp.py -v 2>&1 | tail -20
```

Expected: all pass (including the 5 new tests from Tasks 1–3)

**Step 2: Verify the app boots and run.pid/run.log cycle works**

```bash
cd /home/dmytro/github/raps/raps-examples
RAPS_DASHBOARD_TOKEN=test123 python3 -m uvicorn webapp.main:app --port 8099 --log-level error &
SERVER_PID=$!
sleep 1

# Start a run
curl -s -X POST "http://localhost:8099/run?token=test123"
sleep 1

# Check run.pid exists while running
ls -la webapp/run.pid webapp/run.log

# Check run-status
curl -s "http://localhost:8099/api/run-status?token=test123"

# Wait a few seconds, check run.pid is deleted after completion
sleep 10
ls webapp/run.pid 2>/dev/null && echo "still there" || echo "cleaned up OK"

kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null
```

Expected: run.pid exists during run, deleted after; run-status shows `{"running": true, ...}` while running

**Step 3: Run helpers unit tests one final time**

```bash
python3 -m pytest tests/helpers/ tests/test_webapp.py -q
```

Expected: all pass, 0 failed
