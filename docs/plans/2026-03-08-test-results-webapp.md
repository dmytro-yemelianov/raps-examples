# Test Results Webapp Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** A FastAPI web dashboard at `tests.rapscli.xyz` that displays the last pytest run results and can trigger a new run with live streaming output.

**Architecture:** FastAPI app in `webapp/` at port 8002, serving one vanilla-JS HTML page. Auth via `RAPS_DASHBOARD_TOKEN` query param on all endpoints. Cloudflare Tunnel (existing `raps-smm`, id `5dcfcc14-a27a-4e7e-84eb-4968e772a6a8`) routes `tests.rapscli.xyz → localhost:8002` via a new ingress rule. Pytest writes `webapp/results.json` via `pytest-json-report`; the app merges that with `tests/catalog.json` to show per-SR-ID status.

**Tech Stack:** Python, FastAPI, uvicorn, pytest-json-report, httpx (tests), vanilla JS + inline CSS (no frontend build step).

---

## Task 1: Bootstrap — dependencies + full app skeleton

**Files:**
- Modify: `pyproject.toml`
- Create: `webapp/__init__.py`
- Create: `webapp/main.py`
- Create: `tests/test_webapp.py`

### Step 1: Update pyproject.toml

Add `pytest-json-report` and `httpx` to `test` extras. Add `webapp` extras group. Add script entry:

```toml
[project.optional-dependencies]
test = [
    "pytest>=8.0",
    "pytest-xdist>=3.5",
    "pytest-html>=4.0",
    "pytest-json-report>=1.5",
    "httpx>=0.27",
    "python-dotenv>=1.0",
]
webapp = [
    "fastapi>=0.111",
    "uvicorn[standard]>=0.29",
]

[project.scripts]
raps-dashboard = "webapp.main:start"
```

### Step 2: Install deps

```bash
cd /home/dmytro/github/raps/raps-examples
pip install -e ".[test,webapp]"
```

Expected: installs fastapi, uvicorn, pytest-json-report, httpx without errors.

### Step 3: Create webapp/__init__.py (empty)

Empty file — makes `webapp` a package.

### Step 4: Write failing auth tests

Create `tests/test_webapp.py`:

```python
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
    assert resp.status_code == 200
    assert resp.json()["status"] == "started"
    assert resp.json()["pid"] == 99999
```

### Step 5: Run tests — expect ImportError (no webapp/main.py yet)

```bash
python3 -m pytest tests/test_webapp.py -v 2>&1 | head -15
```

Expected: `ModuleNotFoundError: No module named 'webapp.main'`

### Step 6: Create webapp/main.py

```python
"""RAPS Test Results Dashboard."""
from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
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
    catalog = json.loads(CATALOG_PATH.read_text())

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
        loop = asyncio.get_event_loop()
        while True:
            line = await loop.run_in_executor(None, _run_proc.stdout.readline)
            if not line:
                break
            yield f"data: {line.rstrip()}\n\n"
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
```

### Step 7: Run all tests — expect PASS

```bash
python3 -m pytest tests/test_webapp.py -v
```

Expected: 12 passed.

### Step 8: Commit

```bash
git add pyproject.toml webapp/__init__.py webapp/main.py tests/test_webapp.py
git commit -m "feat: add webapp FastAPI app with auth, results merge, run/stream endpoints"
```

---

## Task 2: Frontend HTML

**Files:**
- Create: `webapp/index.html`

### Step 1: Create webapp/index.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RAPS Test Results</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: ui-monospace, 'Cascadia Code', monospace; background: #0f0f0f; color: #e0e0e0; min-height: 100vh; }

    header { background: #1a1a1a; border-bottom: 1px solid #333; padding: 16px 24px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
    h1 { font-size: 1.1rem; color: #fff; letter-spacing: 0.05em; }
    #meta { font-size: 0.8rem; color: #888; flex: 1; }
    #run-btn { padding: 8px 18px; background: #2563eb; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-family: inherit; }
    #run-btn:disabled { background: #374151; cursor: not-allowed; }
    #run-btn:hover:not(:disabled) { background: #1d4ed8; }

    #filters { padding: 12px 24px; background: #151515; border-bottom: 1px solid #222; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
    #filters label { font-size: 0.8rem; color: #aaa; display: flex; align-items: center; gap: 4px; cursor: pointer; }
    #filters select { background: #1f1f1f; border: 1px solid #333; color: #e0e0e0; border-radius: 4px; padding: 4px 8px; font-size: 0.8rem; font-family: inherit; }

    #summary-bar { padding: 8px 24px; background: #111; font-size: 0.75rem; color: #555; border-bottom: 1px solid #1a1a1a; }

    .table-wrap { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
    th { text-align: left; padding: 10px 14px; color: #555; border-bottom: 1px solid #222; font-weight: 500; position: sticky; top: 0; background: #0f0f0f; }
    td { padding: 8px 14px; border-bottom: 1px solid #1a1a1a; vertical-align: middle; }
    tr:hover td { background: #161616; }

    .badge { display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
    .badge-passed  { background: #14532d; color: #4ade80; }
    .badge-failed  { background: #450a0a; color: #f87171; }
    .badge-skipped { background: #1c1917; color: #a8a29e; }
    .badge-not-run { background: #111; color: #555; border: 1px solid #2a2a2a; }
    .badge-error   { background: #7c2d12; color: #fb923c; }

    .mark-chip { display: inline-block; padding: 1px 6px; border-radius: 4px; font-size: 0.68rem; background: #1e293b; color: #7dd3fc; margin-right: 3px; }

    #log-panel { margin: 16px 24px; background: #111; border: 1px solid #222; border-radius: 8px; overflow: hidden; display: none; }
    #log-header { padding: 10px 14px; background: #1a1a1a; border-bottom: 1px solid #222; display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; color: #aaa; }
    #log-close { cursor: pointer; color: #666; background: none; border: none; font-size: 1rem; line-height: 1; }
    #log-output { padding: 14px; font-size: 0.78rem; line-height: 1.6; white-space: pre-wrap; max-height: 400px; overflow-y: auto; color: #ccc; }

    #token-gate { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; gap: 12px; }
    #token-gate input { padding: 10px 14px; background: #1a1a1a; border: 1px solid #333; color: #e0e0e0; border-radius: 6px; font-family: inherit; font-size: 0.9rem; width: 280px; }
    #token-gate button { padding: 10px 20px; background: #2563eb; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-family: inherit; font-size: 0.9rem; }
    #token-gate button:hover { background: #1d4ed8; }
    #token-error { color: #f87171; font-size: 0.8rem; display: none; }
    #app { display: none; }
  </style>
</head>
<body>

<div id="token-gate">
  <h2 style="color:#fff;font-size:1.1rem;letter-spacing:0.05em">RAPS Test Results</h2>
  <input id="token-input" type="password" placeholder="Dashboard token" autocomplete="current-password" />
  <button onclick="submitToken()">Access Dashboard</button>
  <p id="token-error">Invalid token — try again</p>
</div>

<div id="app">
  <header>
    <h1>RAPS Test Results</h1>
    <div id="meta">Loading…</div>
    <button id="run-btn" onclick="triggerRun()">Run Tests</button>
  </header>

  <div id="filters">
    <select id="f-section" onchange="renderTable()">
      <option value="">All sections</option>
    </select>
    <select id="f-status" onchange="renderTable()">
      <option value="">All statuses</option>
      <option>passed</option>
      <option>failed</option>
      <option>skipped</option>
      <option>not run</option>
    </select>
    <label><input type="checkbox" value="require_2leg" onchange="renderTable()"> require_2leg</label>
    <label><input type="checkbox" value="require_3leg" onchange="renderTable()"> require_3leg</label>
    <label><input type="checkbox" value="lifecycle" onchange="renderTable()"> lifecycle</label>
  </div>

  <div id="summary-bar">—</div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>SR-ID</th>
          <th>Slug</th>
          <th>Section</th>
          <th>Marks</th>
          <th>Status</th>
          <th>Duration</th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>

  <div id="log-panel">
    <div id="log-header">
      <span>Live output</span>
      <button id="log-close" onclick="document.getElementById('log-panel').style.display='none'">&#x2715;</button>
    </div>
    <pre id="log-output"></pre>
  </div>
</div>

<script>
  let TOKEN = localStorage.getItem('raps_token') || '';
  let rows = [];

  if (TOKEN) attemptAutoLogin();

  async function attemptAutoLogin() {
    const resp = await fetch('/api/results?token=' + encodeURIComponent(TOKEN));
    if (resp.ok) {
      showApp();
      applyData(await resp.json());
    } else {
      localStorage.removeItem('raps_token');
      TOKEN = '';
    }
  }

  async function submitToken() {
    TOKEN = document.getElementById('token-input').value.trim();
    const resp = await fetch('/api/results?token=' + encodeURIComponent(TOKEN));
    if (resp.status === 401) {
      document.getElementById('token-error').style.display = 'block';
      return;
    }
    localStorage.setItem('raps_token', TOKEN);
    showApp();
    applyData(await resp.json());
  }

  function showApp() {
    document.getElementById('token-gate').style.display = 'none';
    document.getElementById('app').style.display = 'block';
  }

  async function loadResults() {
    const resp = await fetch('/api/results?token=' + encodeURIComponent(TOKEN));
    if (resp.ok) applyData(await resp.json());
  }

  function applyData(data) {
    rows = data.rows || [];
    updateMeta(data.meta || {});
    populateSections();
    renderTable();
  }

  function updateMeta(meta) {
    const el = document.getElementById('meta');
    if (!meta.created) { el.textContent = 'No run data yet'; return; }
    const d = new Date(meta.created * 1000).toLocaleString();
    const s = meta.summary || {};
    el.textContent = 'Last run: ' + d + ' · ' + (s.passed||0) + ' passed · ' +
      (s.failed||0) + ' failed · ' + (s.skipped||0) + ' skipped · ' +
      (meta.duration||0).toFixed(1) + 's';
  }

  function populateSections() {
    const sel = document.getElementById('f-section');
    const current = sel.value;
    sel.innerHTML = '<option value="">All sections</option>';
    [...new Set(rows.map(r => r.section))].forEach(s => {
      const o = document.createElement('option');
      o.value = s; o.textContent = s;
      if (s === current) o.selected = true;
      sel.appendChild(o);
    });
  }

  function renderTable() {
    const sec   = document.getElementById('f-section').value;
    const st    = document.getElementById('f-status').value;
    const marks = [...document.querySelectorAll('#filters input[type=checkbox]:checked')].map(c => c.value);

    const filtered = rows.filter(r => {
      if (sec   && r.section !== sec) return false;
      if (st    && r.outcome !== st)  return false;
      if (marks.length && !marks.every(m => r.marks.includes(m))) return false;
      return true;
    });

    document.getElementById('summary-bar').textContent =
      'Showing ' + filtered.length + ' of ' + rows.length + ' tests';

    document.getElementById('tbody').innerHTML = filtered.map(r =>
      '<tr>' +
      '<td style="color:#94a3b8;font-weight:600">' + r.id + '</td>' +
      '<td>' + r.slug + '</td>' +
      '<td style="color:#475569">' + r.section + '</td>' +
      '<td>' + (r.marks||[]).map(m => '<span class="mark-chip">' + m + '</span>').join('') + '</td>' +
      '<td><span class="badge badge-' + r.outcome.replace(' ', '-') + '">' + r.outcome + '</span></td>' +
      '<td style="color:#475569">' + (r.duration != null ? r.duration.toFixed(2) + 's' : '&#x2014;') + '</td>' +
      '</tr>'
    ).join('');
  }

  async function triggerRun() {
    const btn = document.getElementById('run-btn');
    btn.disabled = true;
    btn.textContent = 'Starting\u2026';

    const resp = await fetch('/run?token=' + encodeURIComponent(TOKEN), { method: 'POST' });
    if (resp.status === 409) {
      alert('A run is already in progress');
      btn.disabled = false; btn.textContent = 'Run Tests';
      return;
    }

    const logPanel  = document.getElementById('log-panel');
    const logOutput = document.getElementById('log-output');
    logPanel.style.display = 'block';
    logOutput.textContent = '';
    btn.textContent = 'Running\u2026';

    const es = new EventSource('/stream?token=' + encodeURIComponent(TOKEN));
    es.onmessage = function(e) {
      if (e.data === '__done__') {
        es.close();
        btn.disabled = false;
        btn.textContent = 'Run Tests';
        loadResults();
      } else {
        logOutput.textContent += e.data + '\n';
        logOutput.scrollTop = logOutput.scrollHeight;
      }
    };
    es.onerror = function() {
      es.close();
      btn.disabled = false;
      btn.textContent = 'Run Tests';
    };
  }

  document.getElementById('token-input').addEventListener('keydown', function(e) {
    if (e.key === 'Enter') submitToken();
  });
</script>
</body>
</html>
```

### Step 2: Smoke-test locally

```bash
cd /home/dmytro/github/raps/raps-examples
RAPS_DASHBOARD_TOKEN=test python3 -m uvicorn webapp.main:app --port 8002
```

Open `http://localhost:8002/?token=test` — enter "test", dashboard should load with 124 rows all "not run". Kill with Ctrl-C.

### Step 3: Run full test suite — confirm nothing broken

```bash
python3 -m pytest tests/test_webapp.py -v
```

Expected: 12 passed.

### Step 4: Commit

```bash
git add webapp/index.html
git commit -m "feat: add single-page dashboard frontend"
```

---

## Task 3: Cloudflare tunnel + gitignore + launch

**Files:**
- Create: `.gitignore`
- Modify: `~/.cloudflared/config.yml` (host file, not in repo)

### Step 1: Add webapp/results.json to .gitignore

Create `.gitignore` in repo root:

```
webapp/results.json
```

### Step 2: Add DNS CNAME for tests.rapscli.xyz

The Cloudflare API token (`52CRGe_EEqb4oHHnuyxlfVp2Rqk1_hXXHanC-q0i`) expires 2026-03-08T23:59:59Z — run this immediately:

```bash
export CLOUDFLARE_API_TOKEN="52CRGe_EEqb4oHHnuyxlfVp2Rqk1_hXXHanC-q0i"

ZONE_ID=$(curl -s "https://api.cloudflare.com/client/v4/zones?name=rapscli.xyz" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['result'][0]['id'])")

curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data "{
    \"type\": \"CNAME\",
    \"name\": \"tests\",
    \"content\": \"5dcfcc14-a27a-4e7e-84eb-4968e772a6a8.cfargotunnel.com\",
    \"proxied\": true,
    \"ttl\": 1
  }" | python3 -m json.tool
```

Expected: `"success": true`.

### Step 3: Add ingress rule to ~/.cloudflared/config.yml

Edit `~/.cloudflared/config.yml` — insert before the catch-all:

```yaml
tunnel: 5dcfcc14-a27a-4e7e-84eb-4968e772a6a8
credentials-file: /home/dmytro/.cloudflared/5dcfcc14-a27a-4e7e-84eb-4968e772a6a8.json

ingress:
  - hostname: smm.rapscli.xyz
    service: http://localhost:8000
  - hostname: lifeforge.rapscli.xyz
    service: http://localhost:8080
  - hostname: news8bit.rapscli.xyz
    service: http://localhost:8001
  - hostname: tests.rapscli.xyz
    service: http://localhost:8002
  - service: http_status:404
```

### Step 4: Validate and reload cloudflared

```bash
cloudflared tunnel ingress validate
```

Expected: no errors.

```bash
pkill -HUP cloudflared
```

(or `sudo systemctl reload cloudflared` if running as a service)

### Step 5: Start the webapp

```bash
cd /home/dmytro/github/raps/raps-examples
RAPS_DASHBOARD_TOKEN=<choose-a-strong-token> python3 -m uvicorn webapp.main:app --host 0.0.0.0 --port 8002
```

### Step 6: Verify end-to-end

Open `https://tests.rapscli.xyz` — token gate appears. Enter token — 124-row table loads, all "not run". Click "Run Tests" — log panel opens with live pytest output.

### Step 7: Commit and push

```bash
cd /home/dmytro/github/raps/raps-examples
git add .gitignore
git commit -m "chore: gitignore webapp/results.json, configure tests.rapscli.xyz tunnel"
git push
```
