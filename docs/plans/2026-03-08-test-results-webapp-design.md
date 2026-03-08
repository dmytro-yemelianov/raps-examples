# RAPS Test Results Webapp — Design

**Date:** 2026-03-08

## Goal

A web dashboard at `tests.rapscli.xyz` that shows the last pytest run results and can trigger a new run, backed by `catalog.json` as the source of truth for what tests exist.

---

## Architecture

- **FastAPI** app in `raps-examples/webapp/` listening on port `8002`
- **Cloudflare Tunnel** (`raps-smm`, id `5dcfcc14-a27a-4e7e-84eb-4968e772a6a8`) routes `tests.rapscli.xyz → http://localhost:8002` — added as one ingress rule in `~/.cloudflared/config.yml`
- **Auth:** single `RAPS_DASHBOARD_TOKEN` env var; all endpoints (GET and POST) require `?token=...` or `Authorization: Bearer ...` header
- **No separate frontend build** — FastAPI serves one HTML file with inline JS + CSS

---

## Data Flow

```
tests/catalog.json          — source of truth: SR-IDs, slugs, sections, marks
webapp/results.json         — pytest-json-report output (updated after each run)
```

**Viewing results:**
1. `GET /` — FastAPI reads both files, merges by SR-ID, returns rendered HTML table

**Triggering a run:**
1. `POST /run` (with token) — FastAPI spawns `pytest` subprocess
2. `GET /stream` — SSE endpoint streams subprocess stdout line by line
3. On subprocess exit, `webapp/results.json` is updated
4. Frontend auto-refreshes the results table

**pytest invocation:**
```bash
pytest tests/ --json-report --json-report-file=webapp/results.json -q
```
`pytest-json-report` is added to `[project.optional-dependencies] test`.

---

## Frontend (single HTML page)

- **Results table:** SR-ID | slug | section | status | duration
  - Status badges: `passed` (green) | `failed` (red) | `skipped` (yellow) | `not run` (grey)
- **Filter bar:** by section (dropdown), by status (multi-select), by mark (checkboxes)
- **"Run tests" button:** POST `/run` → opens live log panel fed by SSE from `GET /stream`
- **Auto-refresh table** when SSE stream closes (run complete)
- Vanilla JS, no build step

---

## Files

| File | Action |
|------|--------|
| `webapp/__init__.py` | empty |
| `webapp/main.py` | FastAPI app: routes, auth, subprocess management, SSE |
| `webapp/index.html` | Single-page UI served by FastAPI |
| `webapp/results.json` | Written by pytest-json-report (gitignored) |
| `pyproject.toml` | Add `pytest-json-report` to test deps; add `webapp` start script |
| `~/.cloudflared/config.yml` | Add `tests.rapscli.xyz → http://localhost:8002` ingress |

---

## Auth

All endpoints check for token:
- Query param: `?token=<RAPS_DASHBOARD_TOKEN>`
- Header: `Authorization: Bearer <RAPS_DASHBOARD_TOKEN>`

Token set via env var `RAPS_DASHBOARD_TOKEN` (required at startup).

---

## Constraints

- Only one pytest run at a time (second `POST /run` while running returns 409)
- `webapp/results.json` gitignored
- Port `8002` (free in current tunnel config alongside 8000, 8001, 8080)
