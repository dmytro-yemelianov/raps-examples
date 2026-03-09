# Test Infrastructure Improvements Design

**Date**: 2026-03-09
**Scope**: raps-examples — 6 targeted improvements to test infra quality

---

## 1. Token management — simplify `auth.py`

**Problem**: `save_token()` runs file-storage fast path then falls through to platform-specific
branches regardless. Two separate fields (`_saved_token` vs `_saved_token_file`) create ambiguous
restore logic.

**Fix**:
- Early-return in `save_token()` after file storage path succeeds
- Early-return in `restore_token()` after file restore succeeds
- Remove dead code paths that are never reached when `RAPS_USE_FILE_STORAGE=true`
- Keep Windows PowerShell path intact for cross-platform compatibility

**Files**: `tests/helpers/auth.py`

---

## 2. Exit code parsing — replace regex with structured data

**Problem**: `_parse_worst_cli_exit()` in `json_report.py` parses log text with a regex
(`r"->\s+(?:exit\s+(\d+)|TIMEOUT)\s+"`). Fragile — breaks if log format changes.

**Fix**:
- Add `_captured_codes: dict[str, list[int]]` alongside `_captured_logs` in `runner.py`
- `_store_log()` already has `result.exit_code` and `result.timed_out` — record codes there
- `_parse_worst_cli_exit()` reads from `_captured_codes` directly; regex removed
- Add `clear_captured_codes()` parallel to `clear_captured_logs()`

**Files**: `tests/helpers/runner.py`, `tests/helpers/json_report.py`

---

## 3. Catalog variable resolution — fail fast on unresolved vars

**Problem**: `_resolve()` in `test_catalog.py` silently returns literal `${var}` when a variable
is not found. The broken command reaches the CLI and fails with an obscure error.

**Fix**:
- After resolution, scan for remaining `${...}` patterns
- If any remain, `pytest.fail()` with a clear message: which vars were unresolved and what was
  available in the resolution context
- No change to resolution priority order (env var > section vars > global vars)

**Files**: `tests/test_catalog.py`

---

## 4. Webapp security — constant-time token comparison

**Problem**: `token != _TOKEN` is a plain string equality check (timing-attack surface). The `/run`
endpoint also lacks an HTTP-level guard against concurrent runs.

**Fix**:
- Replace `token != _TOKEN` with `not secrets.compare_digest(token, _TOKEN)` in `_require_token()`
- Return HTTP 409 from `POST /run` if a test run is already in progress (currently checked but
  returns no clear error response)

**Files**: `webapp/main.py`

---

## 5. Lifecycle step naming — collision detection

**Problem**: `_store_log()` folds both direct (`SR-063`) and lifecycle step (`SR-063/step1`) logs
into the same `_captured_logs["SR-063"]` key. If the same SR-ID were used for both, logs would
silently merge without warning.

**Fix**:
- Track whether each base SR-ID has received a direct log entry vs step entries
- In `_store_log()`, emit `warnings.warn()` when a base ID receives both a direct entry and a
  lifecycle step entry

**Files**: `tests/helpers/runner.py`

---

## 6. Test data stubs — pad binary files to 4096 bytes

**Problem**: Generated RVT (1024 bytes) and DWG (512 bytes) stubs are below typical APS minimum
upload sizes. May fail stricter API validation.

**Fix**:
- Pad `_generate_rvt()` output to 4096 bytes with deterministic pattern
- Pad `_generate_dwg()` output to 4096 bytes with deterministic pattern
- IFC and STP are text files — no change needed

**Files**: `tests/test_00_setup.py`
