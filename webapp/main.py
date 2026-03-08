"""RAPS Test Results Dashboard."""
from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import threading
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent
CATALOG_PATH = ROOT / "tests" / "catalog.json"
RESULTS_PATH = Path(__file__).parent / "results.json"
HTML_PATH = Path(__file__).parent / "index.html"

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
_TOKEN = os.environ.get("RAPS_DASHBOARD_TOKEN", "")

app = FastAPI(title="RAPS Test Results")

# Global run state
_run_proc: subprocess.Popen | None = None
_run_lock = threading.Lock()


def _require_token(token: str = Query(..., alias="token")) -> str:
    if not _TOKEN:
        raise HTTPException(500, "RAPS_DASHBOARD_TOKEN not set")
    if token != _TOKEN:
        raise HTTPException(401, "Invalid token")
    return token


# ---------------------------------------------------------------------------
# Results merge
# ---------------------------------------------------------------------------

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
        raw = json.loads(RESULTS_PATH.read_text())
        run_meta = {
            "created": raw.get("created"),
            "duration": raw.get("duration"),
            "summary": raw.get("summary", {}),
        }
        for test in raw.get("tests", []):
            sr_id = _sr_id_from_nodeid(test["nodeid"])
            if sr_id and sr_id not in results_map:
                results_map[sr_id] = {
                    "outcome": test.get("outcome", "unknown"),
                    "duration": test.get("duration"),
                }

    rows: list[dict] = []
    for section in catalog["sections"]:
        section_marks = section.get("marks", [])
        for test in section["tests"]:
            sr_id = test["id"]
            result = results_map.get(sr_id, {"outcome": "not run", "duration": None})
            rows.append({
                "id": sr_id,
                "slug": test["slug"],
                "section": section["id"],
                "marks": section_marks + test.get("marks", []),
                "outcome": result["outcome"],
                "duration": result["duration"],
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


@app.get("/stream")
async def stream_output(token: str = Query(..., alias="token")):
    """SSE — streams pytest stdout line by line."""
    _require_token(token)

    async def _lines() -> AsyncIterator[str]:
        if _run_proc is None or _run_proc.stdout is None:
            yield "data: No active run\n\n"
            return
        loop = asyncio.get_running_loop()
        try:
            while True:
                line = await loop.run_in_executor(None, _run_proc.stdout.readline)
                if not line:
                    break
                yield f"data: {line.rstrip()}\n\n"
        except Exception:
            pass
        yield "data: __done__\n\n"

    return StreamingResponse(
        _lines(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/", response_class=HTMLResponse)
def index(token: str = Query(..., alias="token")):
    _require_token(token)
    return HTML_PATH.read_text()


def start() -> None:
    """Entry point for `raps-dashboard` script."""
    import uvicorn
    uvicorn.run("webapp.main:app", host="0.0.0.0", port=8002, reload=False)
