"""RAPS Test Results Dashboard."""
from __future__ import annotations

import asyncio
import json
import os
import re
import secrets
import subprocess
import threading
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Query, WebSocket
from fastapi.responses import HTMLResponse, StreamingResponse

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent
CATALOG_PATH = ROOT / "tests" / "catalog.json"
RESULTS_PATH = Path(__file__).parent / "results.json"
RUN_PID_PATH = Path(__file__).parent / "run.pid"
RUN_LOG_PATH = Path(__file__).parent / "run.log"
HTML_PATH = Path(__file__).parent / "index.html"

# Load .env from repo root so APS_CLIENT_ID/SECRET are available
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
_TOKEN = os.environ.get("RAPS_DASHBOARD_TOKEN", "")

# ---------------------------------------------------------------------------
# Output scrubber — redacts sensitive env var values from streamed output
# ---------------------------------------------------------------------------
_SECRET_ENV = re.compile(
    r"secret|password|token|key|credential|client_id|client_secret", re.IGNORECASE
)
_SENSITIVE: list[str] = [
    v for k, v in os.environ.items()
    if _SECRET_ENV.search(k) and len(v) > 4
]


def _scrub(line: str) -> str:
    """Replace sensitive env var values with *** in streamed output."""
    for secret in _SENSITIVE:
        if secret in line:
            line = line.replace(secret, "***")
    return line


app = FastAPI(title="RAPS Test Results")

# Global run state
_run_proc: subprocess.Popen | None = None
_run_lock = threading.Lock()

# Global auth-login state
_login_proc: subprocess.Popen | None = None
_login_lock = threading.Lock()


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

    Callers that also access _run_proc or _run_log should hold _run_lock.
    """
    # Fast path: in-memory proc still running
    if _run_proc is not None and _run_proc.poll() is None:
        return True
    # Slow path: check disk PID file (handles server-restart case)
    if RUN_PID_PATH.exists():
        try:
            data = json.loads(RUN_PID_PATH.read_text())
            pid = int(data["pid"])
            os.kill(pid, 0)   # signal 0 = liveness check, raises if dead
            return True       # process alive
        except ProcessLookupError:
            # Process dead — stale PID file, clean up
            _delete_pid_file()
        except PermissionError:
            # Process alive but owned by another user — still running
            return True
        except (json.JSONDecodeError, KeyError, ValueError, OSError):
            _delete_pid_file()
    return False


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
        # Open log file; pass to subprocess so it writes directly
        log_fd = open(RUN_LOG_PATH, "w")
        proc = subprocess.Popen(
            cmd,
            cwd=ROOT,
            stdout=log_fd,
            stderr=subprocess.STDOUT,
        )
        log_fd.close()   # subprocess inherited the fd; close our handle
        _write_pid_file(proc.pid)
        _run_proc = proc

    def _cleanup() -> None:
        global _run_proc
        proc.wait()
        _delete_pid_file()
        with _run_lock:
            if _run_proc is proc:
                _run_proc = None
    threading.Thread(target=_cleanup, daemon=True).start()

    return proc


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
                # EOF — check if process still running.
                # No lock held here: _tail_run_log runs on the event loop;
                # the only concurrent writer is the _cleanup thread which sets
                # _run_proc = None. A stale True just adds one extra 50ms
                # sleep iteration, which is harmless.
                if _is_run_alive():
                    await asyncio.sleep(0.05)
                else:
                    # Final drain to catch lines written between poll and EOF
                    remaining = await loop.run_in_executor(None, f.read)
                    for tail_line in remaining.splitlines():
                        yield _scrub(tail_line)
                    break


def _require_token(token: str = Query(..., alias="token")) -> str:
    if not _TOKEN:
        raise HTTPException(500, "RAPS_DASHBOARD_TOKEN not set")
    if not secrets.compare_digest(token, _TOKEN):
        raise HTTPException(401, "Invalid token")
    return token


# ---------------------------------------------------------------------------
# Results merge
# ---------------------------------------------------------------------------

_SECRET_VAR = re.compile(r'secret|password|token|key|credential', re.IGNORECASE)


def _resolve_command(command: str, variables: dict[str, str]) -> str:
    """Resolve ${var} placeholders, masking secret-looking variable names."""
    def replace(m: re.Match) -> str:
        name = m.group(1)
        if _SECRET_VAR.search(name):
            return "***"
        return variables.get(name, m.group(0))
    return re.sub(r"\$\{(\w+)\}", replace, command)


def _sr_id_from_nodeid(nodeid: str) -> str | None:
    """Extract SR-NNN from a pytest node ID.

    Catalog: test_catalog_atomic[SR-030-config-show]  -> SR-030
    Python:  test_sr030_config_show                   -> SR-030
    """
    m = re.search(r"\[SR-(\d+)-", nodeid)
    if m:
        return f"SR-{m.group(1)}"
    m = re.search(r"test_sr(\d+)_", nodeid)
    if m:
        return f"SR-{m.group(1)}"
    return None


def _merge_results() -> dict:
    """Merge catalog.json test definitions with results.json outcomes."""
    try:
        catalog = json.loads(CATALOG_PATH.read_text())
    except FileNotFoundError:
        raise HTTPException(500, "catalog.json not found")

    results_map: dict[str, dict] = {}
    run_meta: dict = {}
    if RESULTS_PATH.exists():
        try:
            raw = json.loads(RESULTS_PATH.read_text())
            run_meta = {
                "created": raw.get("created"),
                "duration": raw.get("duration"),
                "summary": raw.get("summary", {}),
            }
            for test in raw.get("tests", []):
                sr_id = _sr_id_from_nodeid(test["nodeid"])
                if sr_id and sr_id not in results_map:
                    # Extract human-readable output: skip reason or failure traceback
                    output = None
                    for phase in ("call", "setup", "teardown"):
                        lr = test.get(phase, {}).get("longrepr")
                        if lr:
                            # Skipped: pytest-json-report encodes as list [file, lineno, reason]
                            if isinstance(lr, (list, tuple)) and len(lr) == 3:
                                output = str(lr[2])
                            elif isinstance(lr, str):
                                # String tuple repr: "('file', lineno, 'Skipped: reason')"
                                import ast
                                try:
                                    parsed = ast.literal_eval(lr)
                                    if isinstance(parsed, tuple) and len(parsed) == 3:
                                        output = str(parsed[2])
                                    else:
                                        output = lr
                                except Exception:
                                    output = lr
                            else:
                                output = str(lr)
                            break
                    results_map[sr_id] = {
                        "outcome": test.get("outcome", "unknown"),
                        "duration": test.get("duration"),
                        "output": output,
                    }
        except (json.JSONDecodeError, KeyError):
            pass  # results.json is being written — return stale/empty data

    global_vars = catalog.get("vars", {})
    rows: list[dict] = []
    for section in catalog["sections"]:
        section_marks = section.get("marks", [])
        section_vars = {**global_vars, **section.get("vars", {})}
        for test in section["tests"]:
            sr_id = test["id"]
            merged_vars = {**section_vars, **test.get("vars", {})}
            result = results_map.get(sr_id, {"outcome": "not run", "duration": None, "output": None})
            rows.append({
                "id": sr_id,
                "slug": test["slug"],
                "section": section["id"],
                "marks": section_marks + test.get("marks", []),
                "command": _resolve_command(test.get("command", ""), merged_vars),
                "outcome": result["outcome"],
                "duration": result["duration"],
                "output": result.get("output"),
            })

    return {"meta": run_meta, "rows": rows}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/results")
def api_results(token: str = Query(..., alias="token")):
    _require_token(token)
    return _merge_results()


@app.post("/run")
def run_tests(token: str = Query(..., alias="token")):
    _require_token(token)
    proc = _launch_run([
        "python3", "-m", "pytest", "tests/", "-q",
        "--json-report", f"--json-report-file={RESULTS_PATH}",
        "--no-header",
    ])
    return {"status": "started", "pid": proc.pid}


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


@app.get("/api/auth")
def api_auth(token: str = Query(..., alias="token")):
    """Return 2-legged and 3-legged auth status."""
    _require_token(token)
    two_leg = bool(os.environ.get("APS_CLIENT_ID") and os.environ.get("APS_CLIENT_SECRET"))
    three_leg = False
    try:
        proc = subprocess.run(
            ["raps", "auth", "status", "--output", "json", "--quiet"],
            capture_output=True, text=True, timeout=15, cwd=ROOT,
        )
        if proc.returncode == 0:
            data = json.loads(proc.stdout or "{}")
            three_leg = data.get("three_legged", {}).get("logged_in") is True
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError):
        pass
    return {"two_legged": two_leg, "three_legged": three_leg}


@app.post("/run/abort")
def run_abort(token: str = Query(..., alias="token")):
    """Kill any in-progress test run."""
    _require_token(token)
    with _run_lock:
        _kill_run_proc()
    return {"status": "aborted"}


@app.post("/auth/logout")
def auth_logout(token: str = Query(..., alias="token")):
    """Run `raps auth logout` to clear the 3-legged token."""
    _require_token(token)
    try:
        proc = subprocess.run(
            ["raps", "auth", "logout"],
            capture_output=True, text=True, timeout=15, cwd=ROOT,
        )
        if proc.returncode != 0:
            raise HTTPException(500, f"Logout failed: {proc.stderr.strip()}")
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Logout timed out")
    return {"status": "logged_out"}


@app.post("/auth/login")
def auth_login(token: str = Query(..., alias="token")):
    """Spawn `raps auth login --preset all` (opens browser on server)."""
    global _login_proc
    _require_token(token)
    with _login_lock:
        if _login_proc is not None:
            _login_proc.poll()
            if _login_proc.returncode is None:
                _login_proc.terminate()
                try:
                    _login_proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    _login_proc.kill()
        _login_proc = subprocess.Popen(
            ["stdbuf", "-oL", "raps", "auth", "login", "--preset", "all", "--device"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    return {"status": "started", "pid": _login_proc.pid}


@app.get("/stream/auth")
async def stream_auth(token: str = Query(..., alias="token")):
    """SSE — streams raps auth login stdout line by line."""
    _require_token(token)

    async def _lines() -> AsyncIterator[str]:
        for _ in range(10):
            if _login_proc is not None and _login_proc.stdout is not None:
                break
            await asyncio.sleep(0.1)
        else:
            yield "data: No active login\n\n"
            return
        proc = _login_proc
        loop = asyncio.get_running_loop()
        try:
            while True:
                line = await loop.run_in_executor(None, proc.stdout.readline)
                if not line:
                    break
                yield f"data: {_scrub(line.rstrip())}\n\n"
        except Exception:
            pass
        proc.wait()
        yield "data: __done__\n\n"

    return StreamingResponse(
        _lines(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _kill_run_proc() -> None:
    """Kill _run_proc if it is still running."""
    global _run_proc
    if _run_proc is not None and _run_proc.poll() is None:
        _run_proc.terminate()
        try:
            _run_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _run_proc.kill()


_TOTAL_TESTS = 295  # approximate; used for progress bar
_RE_TEST_RESULT = re.compile(r"\s+(PASSED|FAILED|SKIPPED)(\s|\[)")
_RE_SR_ID = re.compile(r"test_sr(\d+)_|\[SR-(\d+)-")


@app.websocket("/ws/run")
async def ws_run(websocket: WebSocket):
    """WebSocket: starts pytest with -v, streams structured JSON progress events.

    Disconnecting does NOT kill the test run. Reconnect via /ws/stream to resume.
    """
    token = websocket.query_params.get("token", "")
    if not _TOKEN or not secrets.compare_digest(token, _TOKEN):
        await websocket.close(code=1008, reason="Unauthorized")
        return

    await websocket.accept()

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
                return  # client disconnected — process keeps running

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


@app.websocket("/ws/stream")
async def ws_stream(websocket: WebSocket):
    """WebSocket: reconnect to an in-progress run (no new run started).

    If no run is in progress, streams whatever is in run.log then sends done.
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
        await websocket.send_json({
            "type": "done",
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
        })
        await websocket.close()
    except Exception:
        pass


@app.get("/", response_class=HTMLResponse)
def index(token: str = Query(..., alias="token")):
    _require_token(token)
    return HTML_PATH.read_text()


def start() -> None:
    """Entry point for `raps-dashboard` script."""
    import uvicorn
    uvicorn.run("webapp.main:app", host="0.0.0.0", port=8002, reload=False)
