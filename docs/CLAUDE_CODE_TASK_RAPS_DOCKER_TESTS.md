# Claude Code Task: RAPS Docker Integration Test Suite

## Goal
Dockerized environment that builds RAPS CLI from source and runs pytest integration tests against the **real Autodesk Platform Services API**. No mocks — these tests validate that RAPS actually works end-to-end.

---

## Why Docker

- **Reproducible Rust build** — pinned toolchain, no host dependency surprises
- **CI-ready** — runs in GitHub Actions with secrets for APS credentials
- **Demo artifact** — show Cyrille's team tests passing against live API
- **Onboarding** — new contributors run `docker compose up` and everything works

---

## Architecture

```
raps-integration-tests/
├── Dockerfile                  ← Multi-stage: build RAPS + test runner
├── docker-compose.yml          ← Orchestration + env var management
├── .env.example                ← Template for credentials
├── pytest.ini                  ← pytest configuration
├── conftest.py                 ← Shared fixtures (auth, cleanup)
├── tests/
│   ├── test_auth.py            ← Authentication flows
│   ├── test_oss.py             ← Object Storage (buckets, upload/download)
│   ├── test_data_management.py ← Hubs, projects, folders
│   ├── test_model_derivative.py← Translation, manifest, properties
│   ├── test_design_automation.py← Engines, appbundles, activities
│   ├── test_acc.py             ← ACC/BIM360 project access
│   ├── test_webhooks.py        ← Webhook CRUD
│   └── test_workflows.py       ← Multi-step workflows (upload→translate→status)
├── fixtures/
│   ├── sample.rvt              ← Small Revit file for translation tests
│   ├── sample.dwg              ← Small DWG for DA tests
│   ├── sample.ifc              ← IFC for translation tests
│   └── sample.stp              ← STEP file
└── scripts/
    ├── wait-for-translation.sh ← Helper: poll translation status
    └── cleanup.sh              ← Remove test buckets/objects after run
```

---

## Dockerfile

```dockerfile
# Stage 1: Build RAPS from source
FROM rust:1.78-bookworm AS builder

WORKDIR /build

# Cache dependencies first
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main() {}" > src/main.rs && \
    cargo build --release && \
    rm -rf src

# Build actual RAPS
COPY src/ src/
RUN touch src/main.rs && cargo build --release

# Stage 2: Test runner
FROM python:3.12-slim-bookworm

# Install raps binary
COPY --from=builder /build/target/release/raps /usr/local/bin/raps

# Verify binary works
RUN raps --version

# Install test dependencies
COPY pytest.ini conftest.py ./
COPY tests/ tests/
COPY fixtures/ fixtures/

RUN pip install --no-cache-dir \
    pytest \
    pytest-timeout \
    pytest-ordering \
    pytest-json-report

# Default: run all tests
CMD ["pytest", "-v", "--timeout=120", "--json-report"]
```

### Notes for Dockerfile:
- Use `rust:1.78-bookworm` — match the toolchain version you develop with
- Cargo dependency caching layer saves ~3 min on rebuilds
- Final image is Python-slim (~150MB) + raps binary (~15MB)
- No Rust toolchain in final image

---

## docker-compose.yml

```yaml
services:
  raps-tests:
    build:
      context: .
      dockerfile: Dockerfile
    env_file:
      - .env
    environment:
      - RAPS_TEST_MODE=integration
      - RAPS_TEST_CLEANUP=true
    volumes:
      # Mount test results out
      - ./results:/results
    command: >
      pytest -v
        --timeout=120
        --json-report
        --json-report-file=/results/report.json
        --junitxml=/results/junit.xml
        -x
        ${TEST_FILTER:---ignore=skip}
```

### Usage:
```bash
# Run all tests
docker compose up --build

# Run specific test file
TEST_FILTER=tests/test_auth.py docker compose up --build

# Run by marker
TEST_FILTER="-m quick" docker compose up --build
```

---

## .env.example

```bash
# Required — APS Application Credentials
APS_CLIENT_ID=your_client_id
APS_CLIENT_SECRET=your_client_secret

# Required for 3-legged tests — pre-obtained refresh token
APS_REFRESH_TOKEN=your_refresh_token

# Optional — defaults shown
APS_REGION=US
APS_TEST_BUCKET_PREFIX=raps-test-
APS_TEST_HUB_ID=              # for data management tests
APS_TEST_PROJECT_ID=          # for ACC tests

# Test behavior
RAPS_TEST_CLEANUP=true        # delete test resources after run
RAPS_TEST_TIMEOUT=120         # per-test timeout seconds
```

---

## conftest.py — Shared Fixtures

```python
import pytest
import subprocess
import json
import os
import time
import uuid


def run_raps(*args, timeout=60, check=True):
    """Execute a raps CLI command and return parsed output."""
    cmd = ["raps"] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"raps {' '.join(args)} failed (rc={result.returncode}):\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
    return result


def run_raps_json(*args, **kwargs):
    """Execute raps command expecting JSON output."""
    result = run_raps(*args, "--output", "json", **kwargs)
    return json.loads(result.stdout)


@pytest.fixture(scope="session")
def raps_version():
    """Verify raps binary is available and return version."""
    result = run_raps("--version")
    version = result.stdout.strip()
    print(f"Testing with: {version}")
    return version


@pytest.fixture(scope="session")
def auth_2legged():
    """Authenticate with 2-legged flow. Session-scoped — runs once."""
    result = run_raps("auth", "login")
    assert result.returncode == 0, f"2-legged auth failed: {result.stderr}"
    return result


@pytest.fixture(scope="session")
def test_bucket_name():
    """Generate unique bucket name for this test run."""
    prefix = os.environ.get("APS_TEST_BUCKET_PREFIX", "raps-test-")
    unique = uuid.uuid4().hex[:8]
    return f"{prefix}{unique}"


@pytest.fixture
def test_bucket(auth_2legged, test_bucket_name):
    """Create a test bucket, yield name, cleanup after."""
    run_raps("oss", "bucket", "create", test_bucket_name)
    yield test_bucket_name
    if os.environ.get("RAPS_TEST_CLEANUP", "true") == "true":
        run_raps("oss", "bucket", "delete", test_bucket_name, check=False)


def wait_for_translation(urn, timeout=300, interval=10):
    """Poll translation status until complete or timeout."""
    elapsed = 0
    while elapsed < timeout:
        result = run_raps_json("md", "manifest", urn)
        status = result.get("status", "")
        if status == "success":
            return result
        if status == "failed":
            raise RuntimeError(f"Translation failed: {json.dumps(result, indent=2)}")
        time.sleep(interval)
        elapsed += interval
    raise TimeoutError(f"Translation not complete after {timeout}s")
```

### Notes for conftest.py:
- Adapt `run_raps` command structure to match actual RAPS CLI syntax
- Check RAPS `--help` for exact subcommand names and flags
- JSON output flag may be `--output json`, `--format json`, or `-o json` — verify
- Bucket/resource naming should match APS naming rules (lowercase, 3-128 chars)

---

## Test Files

### tests/test_auth.py

```python
"""Test RAPS authentication flows against real APS API."""
import pytest
from conftest import run_raps, run_raps_json


class TestTwoLeggedAuth:
    """2-legged (client credentials) authentication."""

    def test_login_succeeds(self):
        result = run_raps("auth", "login")
        assert result.returncode == 0

    def test_token_is_valid(self):
        result = run_raps("auth", "status")
        assert result.returncode == 0
        assert "expired" not in result.stdout.lower()

    def test_token_has_scopes(self):
        """Verify token includes expected scopes."""
        result = run_raps("auth", "status")
        # Check output contains scope info
        assert "data:read" in result.stdout or "scope" in result.stdout.lower()

    def test_login_with_explicit_scopes(self):
        result = run_raps("auth", "login", "--scopes", "data:read data:write")
        assert result.returncode == 0

    def test_invalid_credentials_fail(self, monkeypatch):
        """Verify graceful failure with bad credentials."""
        monkeypatch.setenv("APS_CLIENT_ID", "invalid")
        result = run_raps("auth", "login", check=False)
        assert result.returncode != 0


class TestThreeLeggedAuth:
    """3-legged (authorization code) authentication.
    
    Requires APS_REFRESH_TOKEN in environment.
    Skip if not available.
    """

    @pytest.fixture(autouse=True)
    def require_refresh_token(self):
        import os
        if not os.environ.get("APS_REFRESH_TOKEN"):
            pytest.skip("APS_REFRESH_TOKEN not set")

    def test_refresh_token_exchange(self):
        result = run_raps("auth", "refresh")
        assert result.returncode == 0

    def test_3legged_status_shows_user(self):
        run_raps("auth", "refresh")
        result = run_raps("auth", "status")
        # Should show user identity, not just app
        assert result.returncode == 0
```

---

### tests/test_oss.py

```python
"""Test RAPS Object Storage Service commands against real APS API."""
import pytest
import os
import tempfile
from conftest import run_raps, run_raps_json


class TestBuckets:

    def test_create_bucket(self, auth_2legged, test_bucket_name):
        result = run_raps("oss", "bucket", "create", test_bucket_name)
        assert result.returncode == 0

    def test_list_buckets(self, auth_2legged):
        result = run_raps("oss", "bucket", "list")
        assert result.returncode == 0

    def test_bucket_details(self, test_bucket):
        result = run_raps("oss", "bucket", "details", test_bucket)
        assert result.returncode == 0

    def test_create_duplicate_bucket_fails(self, test_bucket):
        result = run_raps("oss", "bucket", "create", test_bucket, check=False)
        assert result.returncode != 0  # 409 Conflict


class TestUploadDownload:

    @pytest.fixture
    def sample_file(self):
        """Create a temp file for upload testing."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("RAPS integration test file content\n" * 100)
            return f.name

    def test_upload_small_file(self, test_bucket, sample_file):
        result = run_raps("oss", "upload", sample_file, "--bucket", test_bucket)
        assert result.returncode == 0

    def test_download_file(self, test_bucket, sample_file, tmp_path):
        # Upload first
        run_raps("oss", "upload", sample_file, "--bucket", test_bucket)
        
        filename = os.path.basename(sample_file)
        download_path = str(tmp_path / filename)
        result = run_raps("oss", "download", filename,
                         "--bucket", test_bucket,
                         "--output", download_path)
        assert result.returncode == 0
        assert os.path.exists(download_path)

    def test_list_objects(self, test_bucket, sample_file):
        run_raps("oss", "upload", sample_file, "--bucket", test_bucket)
        result = run_raps("oss", "list", "--bucket", test_bucket)
        assert result.returncode == 0
        assert os.path.basename(sample_file) in result.stdout

    @pytest.mark.slow
    def test_upload_large_file_chunked(self, test_bucket):
        """Test chunked upload for files > 5MB."""
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
            f.write(os.urandom(6 * 1024 * 1024))  # 6MB
            large_file = f.name
        try:
            result = run_raps("oss", "upload", large_file,
                             "--bucket", test_bucket,
                             timeout=120)
            assert result.returncode == 0
        finally:
            os.unlink(large_file)
```

---

### tests/test_model_derivative.py

```python
"""Test Model Derivative (translation) commands against real APS API."""
import pytest
import os
from conftest import run_raps, run_raps_json, wait_for_translation


# These tests need a real file uploaded — use fixture files
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")


@pytest.mark.slow
class TestTranslation:
    """Translation tests are slow (minutes) — mark accordingly."""

    @pytest.fixture(scope="class")
    def uploaded_urn(self, test_bucket):
        """Upload a fixture file and return its URN."""
        filepath = os.path.join(FIXTURE_DIR, "sample.stp")
        if not os.path.exists(filepath):
            pytest.skip("sample.stp fixture not found")
        
        result = run_raps("oss", "upload", filepath, "--bucket", test_bucket)
        # Parse URN from upload output
        # Adapt based on actual raps output format
        urn = result.stdout.strip().split()[-1]  # adjust parsing
        return urn

    def test_start_translation(self, uploaded_urn):
        result = run_raps("md", "translate", uploaded_urn)
        assert result.returncode == 0

    def test_check_manifest(self, uploaded_urn):
        run_raps("md", "translate", uploaded_urn)
        result = run_raps("md", "manifest", uploaded_urn)
        assert result.returncode == 0
        assert any(s in result.stdout for s in ["inprogress", "success", "pending"])

    def test_wait_for_translation(self, uploaded_urn):
        run_raps("md", "translate", uploaded_urn)
        manifest = wait_for_translation(uploaded_urn, timeout=300)
        assert manifest["status"] == "success"

    def test_extract_properties(self, uploaded_urn):
        """After translation, extract model properties."""
        wait_for_translation(uploaded_urn, timeout=300)
        result = run_raps("md", "properties", uploaded_urn)
        assert result.returncode == 0

    def test_get_thumbnail(self, uploaded_urn):
        wait_for_translation(uploaded_urn, timeout=300)
        result = run_raps("md", "thumbnail", uploaded_urn)
        assert result.returncode == 0


class TestURNHandling:
    """Quick tests for URN encoding/decoding."""

    def test_urn_encode(self):
        result = run_raps("urn", "encode", "urn:adsk.objects:os.object:bucket/file.rvt")
        assert result.returncode == 0
        assert "==" not in result.stdout or "safe" in result.stdout.lower()

    def test_urn_decode(self):
        result = run_raps("urn", "encode", "urn:adsk.objects:os.object:bucket/file.rvt")
        encoded = result.stdout.strip()
        result2 = run_raps("urn", "decode", encoded)
        assert result2.returncode == 0
        assert "bucket/file.rvt" in result2.stdout
```

---

### tests/test_design_automation.py

```python
"""Test Design Automation commands against real APS API."""
import pytest
from conftest import run_raps, run_raps_json


class TestDADiscovery:
    """Read-only DA tests — safe to run anytime."""

    def test_list_engines(self, auth_2legged):
        result = run_raps("da", "engines")
        assert result.returncode == 0
        # Should list at least AutoCAD and Revit engines
        assert "AutoCAD" in result.stdout or "Autodesk" in result.stdout

    def test_list_appbundles(self, auth_2legged):
        result = run_raps("da", "appbundles")
        assert result.returncode == 0

    def test_list_activities(self, auth_2legged):
        result = run_raps("da", "activities")
        assert result.returncode == 0


@pytest.mark.slow
class TestDAExecution:
    """Workitem tests — cost tokens, run sparingly."""

    @pytest.fixture(autouse=True)
    def require_da_config(self):
        """Skip if no DA activity configured for testing."""
        import os
        if not os.environ.get("APS_TEST_DA_ACTIVITY"):
            pytest.skip("APS_TEST_DA_ACTIVITY not set")

    def test_create_workitem(self):
        import os
        activity = os.environ["APS_TEST_DA_ACTIVITY"]
        result = run_raps("da", "workitem", "create",
                         "--activity", activity,
                         timeout=180)
        assert result.returncode == 0

    def test_workitem_status(self):
        # Would need workitem ID from creation
        pass
```

---

### tests/test_data_management.py

```python
"""Test Data Management commands against real APS API."""
import pytest
import os
from conftest import run_raps


class TestHubs:

    @pytest.fixture(autouse=True)
    def require_3legged(self):
        if not os.environ.get("APS_REFRESH_TOKEN"):
            pytest.skip("3-legged auth required for hub access")
        run_raps("auth", "refresh")

    def test_list_hubs(self):
        result = run_raps("dm", "hubs")
        assert result.returncode == 0

    def test_list_projects(self):
        hub_id = os.environ.get("APS_TEST_HUB_ID")
        if not hub_id:
            pytest.skip("APS_TEST_HUB_ID not set")
        result = run_raps("dm", "projects", "--hub", hub_id)
        assert result.returncode == 0

    def test_list_folders(self):
        project_id = os.environ.get("APS_TEST_PROJECT_ID")
        if not project_id:
            pytest.skip("APS_TEST_PROJECT_ID not set")
        result = run_raps("dm", "folders", "--project", project_id)
        assert result.returncode == 0


class TestACC:

    @pytest.fixture(autouse=True)
    def require_acc(self):
        if not os.environ.get("APS_TEST_PROJECT_ID"):
            pytest.skip("APS_TEST_PROJECT_ID not set for ACC tests")

    def test_acc_project_info(self):
        project_id = os.environ["APS_TEST_PROJECT_ID"]
        result = run_raps("acc", "project", project_id)
        assert result.returncode == 0
```

---

### tests/test_webhooks.py

```python
"""Test Webhook CRUD commands against real APS API."""
import pytest
from conftest import run_raps


class TestWebhookDiscovery:
    """Read-only webhook tests."""

    def test_list_events(self, auth_2legged):
        result = run_raps("webhook", "events")
        assert result.returncode == 0

    def test_list_hooks(self, auth_2legged):
        result = run_raps("webhook", "list")
        assert result.returncode == 0
```

---

### tests/test_workflows.py

```python
"""End-to-end workflow tests — the money tests for demos."""
import pytest
import os
from conftest import run_raps, wait_for_translation


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")


@pytest.mark.slow
@pytest.mark.workflow
class TestUploadTranslateView:
    """Full upload → translate → verify workflow."""

    def test_full_stp_workflow(self, test_bucket):
        filepath = os.path.join(FIXTURE_DIR, "sample.stp")
        if not os.path.exists(filepath):
            pytest.skip("sample.stp not found")

        # 1. Upload
        upload = run_raps("oss", "upload", filepath, "--bucket", test_bucket)
        assert upload.returncode == 0
        urn = upload.stdout.strip().split()[-1]  # adapt parsing

        # 2. Translate
        translate = run_raps("md", "translate", urn)
        assert translate.returncode == 0

        # 3. Wait for completion
        manifest = wait_for_translation(urn, timeout=300)
        assert manifest["status"] == "success"

        # 4. Verify derivatives exist
        props = run_raps("md", "manifest", urn)
        assert props.returncode == 0

        # 5. Extract properties
        properties = run_raps("md", "properties", urn)
        assert properties.returncode == 0
```

---

## pytest.ini

```ini
[pytest]
markers =
    slow: marks tests as slow (translation, DA — deselect with '-m "not slow"')
    workflow: end-to-end workflow tests
    auth: authentication tests
testpaths = tests
timeout = 120
```

### Run patterns:
```bash
# Quick smoke test (auth + read-only)
pytest -m "not slow" -v

# Full suite
pytest -v

# Only workflows (for demos)
pytest -m workflow -v

# Specific API area
pytest tests/test_oss.py -v
```

---

## GitHub Actions Integration

```yaml
# .github/workflows/integration-tests.yml
name: RAPS Integration Tests

on:
  schedule:
    - cron: '0 6 * * 1'    # Weekly Monday 6am UTC
  workflow_dispatch:         # Manual trigger

jobs:
  integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and test
        run: docker compose up --build --exit-code-from raps-tests
        env:
          APS_CLIENT_ID: ${{ secrets.APS_CLIENT_ID }}
          APS_CLIENT_SECRET: ${{ secrets.APS_CLIENT_SECRET }}
          APS_REFRESH_TOKEN: ${{ secrets.APS_REFRESH_TOKEN }}
          APS_TEST_HUB_ID: ${{ secrets.APS_TEST_HUB_ID }}
          APS_TEST_PROJECT_ID: ${{ secrets.APS_TEST_PROJECT_ID }}

      - name: Upload test report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: results/
```

---

## Fixture Files

### What to include in `fixtures/`

| File | Size | Purpose |
|------|------|---------|
| `sample.stp` | <5MB | STEP file — universal translation test |
| `sample.dwg` | <2MB | DWG — AutoCAD DA tests |
| `sample.ifc` | <5MB | IFC — translation method testing |
| `sample.rvt` | <10MB | Revit — if testing RVT workflows |

### Where to get small test files:
- STEP/IGES: GrabCAD free models, export as STEP
- DWG: AutoCAD sample files (ship with AutoCAD)
- IFC: buildingSMART IFC sample files (public domain)
- Generate minimal files programmatically if possible

### Git LFS for fixtures:
```bash
git lfs track "fixtures/*.rvt"
git lfs track "fixtures/*.dwg"
git lfs track "fixtures/*.stp"
```

---

## Test Resource Cleanup

All tests that create resources must clean up. The `RAPS_TEST_CLEANUP=true` env var controls this.

**Cleanup scope:**
- OSS buckets created during tests → delete
- Uploaded objects → deleted with bucket
- Translation manifests → delete manifest endpoint
- Webhooks → delete after test

**Safety:** test bucket names include UUID prefix (`raps-test-a1b2c3d4`) — impossible to collide with real data.

---

## Adapting to Actual RAPS CLI

**IMPORTANT:** The command syntax in these tests is illustrative. Before implementing:

1. Run `raps --help` and `raps <subcommand> --help` to get exact syntax
2. Check how RAPS returns URNs, IDs, and status info
3. Verify JSON output flag (`--output json`, `--format json`, etc.)
4. Adapt `run_raps` parsing to match actual output format
5. Some subcommands may be named differently (e.g., `md` vs `model-derivative`)

The test structure and patterns are what matter — command strings need to match your CLI.

---

## Success Criteria

1. `docker compose up --build` builds RAPS + runs tests in <5 min (excluding slow tests)
2. `pytest -m "not slow"` completes in <60 seconds (auth + read-only tests)
3. Full suite passes against live APS API
4. Tests are idempotent — can run repeatedly without manual cleanup
5. GitHub Actions workflow runs weekly without intervention
6. Test report shows per-test timing (identifies slow API calls)
7. Zero test fixtures committed that exceed 10MB (use Git LFS)
