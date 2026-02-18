# Test Silent Failures — Analysis & Remediation

## Summary

**Pytest can report "passed" while underlying CLI commands fail.** The test harness uses `may_fail=True` extensively, which suppresses assertions on CLI exit codes. The HTML report's "pass rate" reflects **pytest outcome**, not actual CLI success.

| Metric | Without .env (23-35) | With .env (23-54) |
|--------|----------------------|-------------------|
| Pytest result | 255 passed, 6 skipped | ~255 passed |
| Actual CLI runs | 455 | 455 |
| Actual CLI failures | 417 (91.6%) | 344 (75.6%) |
| **Actual pass rate** | **8.4%** | **24.4%** |

## Root Cause: `may_fail=True`

### How it works

1. **`raps.run(cmd, may_fail=True)`** — Runs the command but never asserts. The test passes regardless of exit code.
2. **`lc.step(cmd, may_fail=True)`** — Same for lifecycle steps. `assert_all_passed()` only fails for steps where `may_fail=False`.
3. **JSON reporter** — Stores `exit_code` from **pytest outcome** (0=passed, 1=failed), not the actual CLI exit code. Real exit codes live only in the log text (`-> exit 6 (0.54s)`).

### Tests that silently suppress failures

| File | Pattern | Count |
|------|---------|-------|
| `test_17_plugins.py` | All 7 tests use `may_fail=True` | 7 |
| `test_18_pipelines.py` | All steps `may_fail=True` | 2 |
| `test_05_model_derivative.py` | SR-090..SR-101 all `may_fail=True` | 12 |
| `test_06_design_automation.py` | SR-110, SR-111, SR-114 + others | 12 |
| `test_03_storage.py` | SR-051 bucket-list, etc. | 26 |
| `test_10_webhooks.py` | SR-180, SR-182 | 9 |
| `test_01_auth.py` | SR-010, SR-019, etc. | 14 |
| `test_99_cross_cutting.py` | SR-540..SR-544 help/version | 5 |
| `test_30_workflows.py` | All lifecycle steps | 12 |
| ... | many more | ~200+ |

## How to Find Actual Failures

### 1. Run tests with JSON report

```powershell
cd raps-examples
$ts = Get-Date -Format "yyyy-MM-dd-HH-mm"
pytest tests/ --json-report-dir "reports\$ts" -q
```

### 2. Analyze logs for actual CLI exit codes

```powershell
python scripts/analyze-log-failures.py reports/2026-02-17-23-54
```

Output shows which commands actually failed (exit != 0), with stderr previews.

### 3. Generate HTML report (shows pytest outcome, not CLI)

```powershell
python scripts/generate-run-report.py reports/2026-02-17-23-54 -o reports/2026-02-17-23-54/report.html
```

**Note:** The HTML report's "Passed" count is based on pytest outcome. Use `analyze-log-failures.py` for real CLI pass/fail.

## Fixes Applied (2026-02)

1. **JSON reporter** — Parses actual CLI exit codes from logs (`-> exit N`), stores `cli_exit_code` in run entries. HTML report uses `cli_exit_code` when present for pass/fail counts.
2. **Auth inspect** — `raps auth inspect --output json` → `raps -o json auth inspect` (global `--output`).
3. **Config set** — Use valid key `base_url` instead of non-existent `output_format`.
4. **Config profile import** — Export with `-o path -n profile`; import takes file only (no `-n`).
5. **Bucket create** — `raps bucket create -k KEY -p transient -r US` (use `-k` for key).
6. **Translate preset use** — `raps translate preset use URN preset-name` (separate subcommand, not `translate start --preset`).

## Remediation Options

### Option A: Replace `may_fail=True` with `run_ok()` where success is expected

For commands that **should** pass when credentials are present:

```python
# Before (silent failure)
raps.run("raps plugin list", sr_id="SR-260", slug="plugin-list", may_fail=True)

# After (asserts success)
raps.run_ok("raps plugin list", sr_id="SR-260", slug="plugin-list")
```

### Option B: Keep `may_fail` but add CI gate on actual failures

Run `analyze-log-failures.py` in CI and fail the build if actual failure count exceeds a threshold.

### Option C: Fix JSON reporter to store actual CLI exit codes

Parse `-> exit N` from logs and store `cli_exit_code` in run entries so the HTML report reflects reality.

## Key Findings from Log Analysis

### With .env (client_id/secret set)

- **Plugins (SR-260..SR-266):** 100% pass when credentials present
- **Translate preset list (SR-095):** Passes
- **Auth test (SR-010):** Passes
- **Config get/set:** Most pass; `config set output_format` fails (key name mismatch)
- **Config context:** Fails — RAPS CLI may not have `config context` subcommand

### Persistent failures (CLI/API mismatches)

1. `raps auth inspect --output json` — unexpected argument `--output`
2. `raps config context show/set/clear` — unrecognized subcommand
3. `raps config profile export -n staging` — unexpected `-n`
4. `raps config set output_format` — unknown key (valid: client_id, client_secret, base_url, ...)
5. `raps translate start ... --preset "svf2-default"` — unexpected `--preset`
6. `raps bucket create sr-test-bucket-raps --policy transient` — argument order/names

## Files

- `scripts/analyze-log-failures.py` — Parse .log files, report actual CLI failures
- `tests/helpers/runner.py` — `run()`, `run_ok()`, `lifecycle()`, `may_fail`
- `tests/helpers/json_report.py` — Pytest plugin, stores pytest outcome as exit_code
