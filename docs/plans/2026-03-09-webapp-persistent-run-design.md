# Webapp Persistent Run State Design

**Date**: 2026-03-09
**Scope**: `webapp/main.py` — fix three run-state problems: orphan detection, WebSocket
lifetime coupling, and reconnect support.

---

## Problem Summary

1. `_run_proc` is in-memory only — server restart loses all awareness of a running pytest
2. WebSocket `finally` block kills pytest on browser disconnect
3. No way to reconnect to an in-progress run (SSE or WebSocket)

---

## Solution: File-Based Run State

### New files

- **`webapp/run.pid`** — JSON `{"pid": 12345, "started": "2026-03-09T14:22:00Z"}`,
  written at run start, deleted at run end
- **`webapp/run.log`** — raw pytest stdout written line by line, cleared at each new run start

### Startup orphan check

On first request that touches run state, check `run.pid`:
- If it does not exist → no run in progress
- If it exists and `os.kill(pid, 0)` succeeds → process alive, adopt as current run
- If it exists and process is dead → delete both files (orphan cleanup)

### Run launch

Both `/run` (SSE) and `/ws/run` (WebSocket) use the same launch function:
1. Check for in-progress run (memory `_run_proc` + PID file)
2. Clear `run.log`
3. Start pytest with stdout piped
4. Write `run.pid`
5. Start background thread: reads stdout line by line, writes to `run.log`, closes on EOF,
   deletes `run.pid` when done

### Streaming (both SSE and WebSocket)

Replace direct pipe reading with **file tailing**:
1. Open `run.log` for reading
2. Seek to position 0 (full replay) or current EOF (live only) — always replay from 0 for
   single-user simplicity
3. Yield lines; when at EOF, check if process still alive; if yes, sleep 50ms and retry;
   if no, send `__done__` and stop

### WebSocket disconnect

Remove the `finally` block that calls `proc.terminate()`. Disconnect = socket close only.
The background writer thread keeps the process running independently.

### Dependency

Use `os.kill(pid, 0)` for PID liveness (Unix-only is fine — server runs Linux). No new
dependencies.

---

## Files Changed

- `webapp/main.py` — all changes confined here
