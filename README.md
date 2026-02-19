# RAPS CLI Sample Runs

**263 tests** across **25 sections** exercising **100+ CLI subcommands** of the [RAPS CLI](https://rapscli.xyz) for Autodesk Platform Services (APS).

Each test runs a real `raps` command (or lifecycle sequence) and records exit code, stdout, stderr, and duration. Results feed into JSON/HTML reports for validation.

## Prerequisites

- Python 3.10+
- RAPS CLI binary (built from `../raps/` or on PATH)
- `.env` file with APS credentials (for API tests; see below)

## Quick Start

```bash
cd raps-examples

# Install test dependencies
pip install -e ".[test]"

# Run all tests (sequential)
pytest

# Run all tests (parallel, 4 workers)
pytest -n 4 --dist loadgroup
```

### Environment Variables

Create a `.env` file for API-dependent tests:

```env
APS_CLIENT_ID=your_client_id
APS_CLIENT_SECRET=your_client_secret
APS_CALLBACK_URL=http://localhost:8080/callback
```

Without `.env`, auth-dependent tests will be skipped.

## Execution Modes

| Mode | Command | Notes |
|------|---------|-------|
| All tests (sequential) | `pytest` | Safest, no concurrency issues |
| Parallel (4 workers) | `pytest -n 4 --dist loadgroup` | Tests grouped by section |
| Against mock server | `pytest --mock` | Uses raps-mock on port 3000 |
| Single section | `pytest tests/test_03_storage.py` | Run one test file |
| Single SR ID | `pytest -k "sr063"` | Filter by sample run ID |
| Rerun failed | `pytest --lf` | Re-run last failed tests |
| HTML report | `pytest --html=report.html` | pytest-html output |
| JSON report | `pytest --json-report-dir=logs/run` | Per-section JSON files |

### JSON + HTML Report Pipeline

```bash
# Generate JSON reports
pytest --json-report-dir=logs/latest

# Convert to visual HTML report
python scripts/generate-run-report.py logs/latest -o logs/latest/report.html
```

## Test Organization

### SR-IDs

Every test has a unique Sample Run ID (e.g., `SR-051`). Use it to find or filter tests:

```bash
pytest -k "sr051"                    # Run single SR
pytest -k "sr050 or sr051 or sr052"  # Run multiple
```

### Sections (25 test files)

| # | Section | Tests | Auth | File |
|---|---------|-------|------|------|
| 00 | Setup | 3 | None | `test_00_setup.py` |
| 01 | Auth | 15 | 2-leg | `test_01_auth.py` |
| 02 | Config | 18 | None | `test_02_config.py` |
| 03 | Storage | 16 | 2-leg | `test_03_storage.py` |
| 04 | Data Management | 18 | 3-leg | `test_04_data_management.py` |
| 05 | Model Derivative | 12 | 2-leg | `test_05_model_derivative.py` |
| 06 | Design Automation | 12 | 2-leg | `test_06_design_automation.py` |
| 07 | ACC Issues | 12 | 3-leg | `test_07_acc_issues.py` |
| 08 | ACC RFI | 6 | 3-leg | `test_08_acc_rfi.py` |
| 09 | ACC Modules | 18 | 3-leg | `test_09_acc_modules.py` |
| 10 | Webhooks | 9 | 2-leg | `test_10_webhooks.py` |
| 11 | Admin Users | 17 | 3-leg | `test_11_admin_users.py` |
| 12 | Admin Projects | 6 | 3-leg | `test_12_admin_projects.py` |
| 13 | Admin Folders | 9 | 3-leg | `test_13_admin_folders.py` |
| 14 | Reality Capture | 9 | 3-leg | `test_14_reality_capture.py` |
| 15 | Reporting | 5 | 3-leg | `test_15_reporting.py` |
| 16 | Templates | 6 | 3-leg | `test_16_templates.py` |
| 17 | Plugins | 7 | 2-leg | `test_17_plugins.py` |
| 18 | Pipelines | 4 | 2-leg | `test_18_pipelines.py` |
| 19 | API Raw | 5 | 2-leg | `test_19_api_raw.py` |
| 20 | Generation | 2 | None | `test_20_generation.py` |
| 21 | Shell & Serve | 6 | None | `test_21_shell_serve.py` |
| 22 | Demo | 4 | None | `test_22_demo.py` |
| 30 | Workflows | 10 | 3-leg | `test_30_workflows.py` |
| 99 | Cross-Cutting | 32 | None | `test_99_cross_cutting.py` |

### Markers

- `require_2leg` — Requires 2-legged (client credentials) auth
- `require_3leg` — Requires 3-legged (user login) auth
- `require_acc` — Requires ACC account
- `lifecycle` — Multi-step lifecycle test
- `sr(id)` — Sample Run identifier

### xdist Groups

Parallel execution uses `--dist loadgroup`. Each test file is its own xdist group (e.g., `03-storage`), ensuring tests within a section run sequentially while different sections run in parallel.

## Project Structure

```
raps-examples/
├── tests/
│   ├── conftest.py              # Fixtures, CLI options, marker logic
│   ├── helpers/
│   │   ├── runner.py            # RapsRunner (subprocess wrapper)
│   │   ├── auth.py              # AuthManager (2-leg, 3-leg)
│   │   ├── discovery.py         # ID discovery (hub, project, account)
│   │   ├── test_users.py        # Test user emails from .env
│   │   └── json_report.py       # JSON report plugin
│   └── test_*.py                # 25 test files (one per section)
├── scripts/
│   ├── audit_secrets.py         # Secrets & PII audit script
│   ├── generate-run-report.py   # JSON → HTML report generator
│   ├── generate-test-data.py    # Synthetic test data generator
│   ├── analyze-log-failures.py  # CLI exit code analysis
│   └── oauth-automate.py        # OAuth browser automation helper
├── docs/
│   ├── SECRETS-AUDIT.md         # Latest secrets audit report
│   └── CLI-COVERAGE-MATRIX.md   # CLI subcommand coverage map
├── benchmarks/                  # Blog article validation suites
├── data/samples/                # Static sample files
├── pyproject.toml               # Project config, pytest settings
├── Dockerfile                   # Docker build (for benchmarks)
└── docker-compose.yml           # Docker orchestration
```

## Benchmarks

The `benchmarks/` directory contains Docker-based validation suites for [RAPS blog articles](https://rapscli.xyz/blog):

| Article | Suite |
|---------|-------|
| The Manual Tax | `benchmarks/automation-timing/` |
| CI/CD 101 for AEC | `benchmarks/pipeline-timing/` |
| Authentication Chaos | `benchmarks/auth-flows/` |
| File Translation Disasters | `benchmarks/translation-performance/` |
| Rust vs. Node.js 5GB Files | `benchmarks/rust-vs-nodejs/` |
| SDK Version Hell | `benchmarks/version-compatibility/` |
| Zero-Click Releases | `benchmarks/design-automation/` |

Run benchmarks via Docker:

```bash
docker compose up --build
docker compose run --rm benchmarks ./benchmarks/rust-vs-nodejs/run.sh
```

## Contributing

1. Add new tests in the appropriate `test_XX_*.py` file
2. Use the next available SR-ID for your section
3. Follow existing patterns: `raps.run_ok()` for expected-success, `raps.run()` for commands where you need the result
4. Group tests with `@pytest.mark.xdist_group("XX-section-name")`
5. Run `pytest --collect-only` to verify test count

## License

Apache 2.0 — Same as RAPS
