# RAPS v5.4.0 Alignment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add 18 tests across 6 modified files + 1 new file to cover all new RAPS v5.4.0 CLI commands.

**Architecture:** Each task appends test functions to an existing test file (or creates a new one) following the established pattern: `pytestmark` module-level markers, `@pytest.mark.sr("SR-XXX")` per test, `raps.run()` or `raps.run_ok()` for atomics, `raps.lifecycle()` for multi-step flows. No new fixtures or helpers are needed.

**Tech Stack:** Python 3.10+, pytest, existing `RapsRunner` fixture (`raps`), existing `ids` fixture for 3-leg IDs.

---

## Patterns to follow

**Atomic (may fail gracefully):**
```python
@pytest.mark.sr("SR-XXX")
def test_srXXX_command_name(raps):
    raps.run("raps command args", sr_id="SR-XXX", slug="command-name")
```

**Atomic (must succeed):**
```python
@pytest.mark.sr("SR-XXX")
def test_srXXX_command_name(raps):
    raps.run_ok("raps command args", sr_id="SR-XXX", slug="command-name")
```

**Lifecycle:**
```python
@pytest.mark.sr("SR-XXX")
@pytest.mark.lifecycle
def test_srXXX_lifecycle_name(raps):
    lc = raps.lifecycle("SR-XXX", "lifecycle-name", "Description")
    lc.step("raps command one")
    lc.step("raps command two")
    lc.assert_all_passed()
```

**Verify collection after each task:**
```bash
cd /home/dmytro/github/raps/raps-examples
pytest --collect-only -q 2>&1 | tail -3
```

---

### Task 1: Create test_23_logs.py (SR-310–313)

**Files:**
- Create: `tests/test_23_logs.py`

**Step 1: Write the file**

```python
"""Log management"""

import pytest

pytestmark = [
    pytest.mark.xdist_group("23-logs"),
]


@pytest.mark.sr("SR-310")
def test_sr310_logs_path(raps):
    raps.run_ok("raps logs path", sr_id="SR-310", slug="logs-path")


@pytest.mark.sr("SR-311")
def test_sr311_logs_show(raps):
    raps.run_ok("raps logs show", sr_id="SR-311", slug="logs-show")


@pytest.mark.sr("SR-312")
def test_sr312_logs_clear(raps):
    raps.run_ok("raps logs clear -y", sr_id="SR-312", slug="logs-clear")


@pytest.mark.sr("SR-313")
@pytest.mark.lifecycle
def test_sr313_logs_lifecycle(raps):
    lc = raps.lifecycle("SR-313", "logs-lifecycle", "Clear → show → path")
    lc.step("raps logs clear -y")
    lc.step("raps logs show")
    lc.step("raps logs path")
    lc.assert_all_passed()
```

**Step 2: Verify collection**

```bash
cd /home/dmytro/github/raps/raps-examples
pytest tests/test_23_logs.py --collect-only -q
```
Expected: `4 tests collected`

**Step 3: Run tests**

```bash
pytest tests/test_23_logs.py -v
```
Expected: all 4 pass (logs commands require no auth and no network)

**Step 4: Commit**

```bash
git add tests/test_23_logs.py
git commit -m "feat: add SR-310–313 logs show/path/clear lifecycle tests"
```

---

### Task 2: Add snapshot tests to test_02_config.py (SR-046–049)

**Files:**
- Modify: `tests/test_02_config.py`

**Context:** `test_02_config.py` has `pytestmark = [pytest.mark.xdist_group("02-config")]` — no `require_2leg`. Snapshot `create` needs a real bucket so it should be `require_2leg`. `list` and `diff` work on local files so no auth needed.

**Step 1: Append to test_02_config.py**

Add after the last lifecycle test (after `test_sr045_config_context_lifecycle`):

```python

# ── Snapshot ──────────────────────────────────────────────────────


@pytest.mark.sr("SR-046")
@pytest.mark.require_2leg
def test_sr046_snapshot_create(raps):
    raps.run(
        "raps snapshot create sr-test-bucket",
        sr_id="SR-046",
        slug="snapshot-create",
    )


@pytest.mark.sr("SR-047")
def test_sr047_snapshot_list(raps):
    raps.run_ok("raps snapshot list", sr_id="SR-047", slug="snapshot-list")


@pytest.mark.sr("SR-048")
def test_sr048_snapshot_diff(raps):
    # Diff two non-existent files; command should exit non-zero but not panic
    raps.run(
        "raps snapshot diff ./snap-a.json ./snap-b.json",
        sr_id="SR-048",
        slug="snapshot-diff",
    )


@pytest.mark.sr("SR-049")
@pytest.mark.require_2leg
@pytest.mark.lifecycle
def test_sr049_snapshot_lifecycle(raps):
    lc = raps.lifecycle("SR-049", "snapshot-lifecycle", "Create → list → diff")
    lc.step("raps snapshot create sr-test-bucket --output ./snap-v1.json")
    lc.step("raps snapshot list")
    lc.step("raps snapshot create sr-test-bucket --output ./snap-v2.json")
    lc.step("raps snapshot diff ./snap-v1.json ./snap-v2.json")
    lc.assert_all_passed()
```

**Step 2: Verify collection**

```bash
pytest tests/test_02_config.py --collect-only -q
```
Expected: previous count + 4

**Step 3: Commit**

```bash
git add tests/test_02_config.py
git commit -m "feat: add SR-046–049 snapshot create/list/diff lifecycle tests"
```

---

### Task 3: Add object audit + tag tests to test_03_storage.py (SR-067–072)

**Files:**
- Modify: `tests/test_03_storage.py`

**Context:** File has `pytestmark = [pytest.mark.require_2leg, pytest.mark.xdist_group("03-storage")]` and module-level `BUCKET_NAME = f"sr-test-{_TS}"`. The audit and tag tests reuse that bucket.

**Step 1: Append to test_03_storage.py**

Add after the last lifecycle test (`test_sr065_batch_upload_lifecycle`):

```python

# ── Object audit ─────────────────────────────────────────────────


@pytest.mark.sr("SR-067")
def test_sr067_object_audit(raps):
    raps.run(
        f"raps object audit {BUCKET_NAME}",
        sr_id="SR-067",
        slug="object-audit",
    )


# ── Object tag ───────────────────────────────────────────────────


@pytest.mark.sr("SR-068")
def test_sr068_object_tag_set(raps):
    raps.run(
        f"raps object tag set {BUCKET_NAME} sample.ifc env=test owner=qa",
        sr_id="SR-068",
        slug="object-tag-set",
    )


@pytest.mark.sr("SR-069")
def test_sr069_object_tag_get(raps):
    raps.run(
        f"raps object tag get {BUCKET_NAME} sample.ifc",
        sr_id="SR-069",
        slug="object-tag-get",
    )


@pytest.mark.sr("SR-070")
def test_sr070_object_tag_delete(raps):
    raps.run(
        f"raps object tag delete {BUCKET_NAME} sample.ifc owner",
        sr_id="SR-070",
        slug="object-tag-delete",
    )


@pytest.mark.sr("SR-071")
def test_sr071_object_tag_search(raps):
    raps.run(
        f"raps object tag search {BUCKET_NAME} env=test",
        sr_id="SR-071",
        slug="object-tag-search",
    )


@pytest.mark.sr("SR-072")
@pytest.mark.lifecycle
def test_sr072_object_tag_lifecycle(raps):
    lc = raps.lifecycle("SR-072", "object-tag-lifecycle", "Set → get → search → delete")
    lc.step(f"raps object tag set {BUCKET_NAME} sample.ifc project=raps-test")
    lc.step(f"raps object tag get {BUCKET_NAME} sample.ifc")
    lc.step(f"raps object tag search {BUCKET_NAME} project=raps-test")
    lc.step(f"raps object tag delete {BUCKET_NAME} sample.ifc project")
    lc.assert_all_passed()
```

**Step 2: Verify collection**

```bash
pytest tests/test_03_storage.py --collect-only -q
```
Expected: previous count + 6

**Step 3: Commit**

```bash
git add tests/test_03_storage.py
git commit -m "feat: add SR-067–072 object audit and tag lifecycle tests"
```

---

### Task 4: Add translate timeline to test_05_model_derivative.py (SR-102)

**Files:**
- Modify: `tests/test_05_model_derivative.py`

**Context:** File has module-level `URN` variable (base64 of `BUCKET_NAME/sample.ifc`). Reuse it.

**Step 1: Append to test_05_model_derivative.py**

Add after `test_sr101_translate_preset_lifecycle`:

```python

@pytest.mark.sr("SR-102")
def test_sr102_translate_timeline(raps):
    raps.run(
        f"raps translate timeline {URN}",
        sr_id="SR-102",
        slug="translate-timeline",
    )
```

**Step 2: Verify collection**

```bash
pytest tests/test_05_model_derivative.py --collect-only -q
```
Expected: previous count + 1

**Step 3: Commit**

```bash
git add tests/test_05_model_derivative.py
git commit -m "feat: add SR-102 translate timeline test"
```

---

### Task 5: Add acc export to test_09_acc_modules.py (SR-178)

**Files:**
- Modify: `tests/test_09_acc_modules.py`

**Context:** File has `pytestmark = [pytest.mark.require_3leg, pytest.mark.xdist_group("09-acc-modules")]` and uses `ids` fixture for `ids.project_id`.

**Step 1: Append to test_09_acc_modules.py**

Add after the last test (`test_sr177_checklist_inspection_lifecycle`):

```python

@pytest.mark.sr("SR-178")
def test_sr178_acc_export(raps, ids):
    pid = ids.project_id or "demo-project-001"
    raps.run(
        f"raps acc export {pid} --out-dir ./tmp/acc-export-sr178",
        sr_id="SR-178",
        slug="acc-export",
    )
```

**Step 2: Verify collection**

```bash
pytest tests/test_09_acc_modules.py --collect-only -q
```
Expected: previous count + 1

**Step 3: Commit**

```bash
git add tests/test_09_acc_modules.py
git commit -m "feat: add SR-178 acc export test"
```

---

### Task 6: Add pipeline diff to test_18_pipelines.py (SR-274)

**Files:**
- Modify: `tests/test_18_pipelines.py`

**Context:** `pipeline diff` takes two YAML files and needs no auth. We produce two sample files first (reusing `raps pipeline sample`), then diff them.

**Step 1: Append to test_18_pipelines.py**

Add after `test_sr273_pipeline_author_and_run`:

```python

@pytest.mark.sr("SR-274")
def test_sr274_pipeline_diff(raps):
    raps.run(
        "raps pipeline sample --out-file ./pipeline-a.yaml"
        "; raps pipeline sample --out-file ./pipeline-b.yaml"
        "; raps pipeline diff ./pipeline-a.yaml ./pipeline-b.yaml",
        sr_id="SR-274",
        slug="pipeline-diff",
    )
```

**Step 2: Verify collection**

```bash
pytest tests/test_18_pipelines.py --collect-only -q
```
Expected: previous count + 1

**Step 3: Commit**

```bash
git add tests/test_18_pipelines.py
git commit -m "feat: add SR-274 pipeline diff test"
```

---

### Task 7: Add --log-file and lint to test_99_cross_cutting.py (SR-560–561)

**Files:**
- Modify: `tests/test_99_cross_cutting.py`

**Context:** Cross-cutting tests use `pytestmark = [pytest.mark.require_2leg, pytest.mark.xdist_group("99-cross-cutting")]`. `raps lint` and `--log-file` need no auth but the module marker applies. Use `raps.run()` (not `run_ok`) since lint may exit 1 when it finds nothing to lint.

**Step 1: Append to test_99_cross_cutting.py**

Add at the end of the file:

```python

# ── --log-file global flag ───────────────────────────────────────


@pytest.mark.sr("SR-560")
def test_sr560_log_file_flag(raps, tmp_path):
    log_file = tmp_path / "raps-test.log"
    raps.run_ok(
        f"raps --log-file {log_file} bucket list",
        sr_id="SR-560",
        slug="log-file-flag",
    )


# ── raps lint ────────────────────────────────────────────────────


@pytest.mark.sr("SR-561")
def test_sr561_lint_pipeline(raps):
    raps.run(
        "raps pipeline sample --out-file ./lint-test-pipeline.yaml"
        "; raps lint ./lint-test-pipeline.yaml",
        sr_id="SR-561",
        slug="lint-pipeline",
    )
```

**Step 2: Verify collection**

```bash
pytest tests/test_99_cross_cutting.py --collect-only -q
```
Expected: previous count + 2

**Step 3: Commit**

```bash
git add tests/test_99_cross_cutting.py
git commit -m "feat: add SR-560–561 --log-file flag and lint tests"
```

---

### Task 8: Update README

**Files:**
- Modify: `README.md`

**Step 1: Update three values in README.md**

1. Change `**263 tests**` → `**281 tests**`
2. Change `**25 sections**` → `**26 sections**`
3. Add section 23 row to the sections table:

After the `| 22 | Demo | 4 | None | \`test_22_demo.py\` |` row, add:
```
| 23 | Logs | 4 | None | `test_23_logs.py` |
```

**Step 2: Verify README looks correct**

```bash
grep -n "281 tests\|26 sections\|test_23_logs" README.md
```
Expected: 3 matches

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update test count and section table for v5.4.0 alignment"
```

---

### Task 9: Final verification

**Step 1: Full collection check**

```bash
cd /home/dmytro/github/raps/raps-examples
pytest --collect-only -q 2>&1 | tail -3
```
Expected: `281 tests collected`

**Step 2: Smoke-run no-auth tests**

```bash
pytest tests/test_23_logs.py tests/test_18_pipelines.py::test_sr274_pipeline_diff -v
```
Expected: tests pass or skip (not error)

**Step 3: Push**

```bash
git push
```
