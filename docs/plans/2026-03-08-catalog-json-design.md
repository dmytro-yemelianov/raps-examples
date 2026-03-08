# Data-Driven Atomic Tests: catalog.json Design

**Date:** 2026-03-08

## Goal

Move all atomic test definitions out of Python code into a single `tests/catalog.json` file so the full list of tested RAPS commands is visible, manageable, and parseable by web dashboards.

Lifecycle tests (multi-step, `@pytest.mark.lifecycle`) stay in Python — they don't fit the data model.

---

## catalog.json Schema

```json
{
  "vars": {
    "bucket": "test-bucket",
    "hub_id": "b.demo-hub-001",
    "project_full_id": "b.demo-project-001"
  },
  "sections": [
    {
      "id": "02-config",
      "marks": [],
      "vars": {},
      "tests": [
        {
          "id": "SR-030",
          "slug": "config-show",
          "command": "raps config profile export -n default"
        },
        {
          "id": "SR-046",
          "slug": "snapshot-create",
          "marks": ["require_2leg"],
          "ok": false,
          "command": "raps snapshot create ${snapshot_bucket}",
          "vars": { "snapshot_bucket": "sr-snap-test" }
        }
      ]
    },
    {
      "id": "03-storage",
      "marks": ["require_2leg"],
      "vars": {},
      "tests": [
        {
          "id": "SR-050",
          "slug": "object-upload",
          "command": "raps object upload ${bucket} ${file}",
          "vars": { "file": "./test-data/sample.ifc" }
        }
      ]
    }
  ]
}
```

### Top-level fields

| Field | Type | Description |
|-------|------|-------------|
| `vars` | object | Global variable defaults, lowest priority |
| `sections` | array | Ordered list of test sections |

### Section fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | Section identifier, used as `xdist_group` (e.g. `"03-storage"`) |
| `marks` | no | Marks applied to all tests in section (e.g. `["require_2leg"]`) |
| `vars` | no | Section-level variable defaults, override global vars |
| `tests` | yes | Array of test entries |

### Test entry fields

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `id` | yes | — | SR-NNN identifier |
| `slug` | yes | — | kebab-case name for reporting |
| `command` | yes | — | Shell command with `${var}` interpolation |
| `vars` | no | `{}` | Test-level variable defaults, highest priority |
| `marks` | no | `[]` | Additional marks beyond section marks |
| `ok` | no | `true` | If `false`, non-zero exit is allowed (`raps.run()` instead of `raps.run_ok()`) |

---

## Variable Syntax

Variables use `${name}` (consistent with RAPS pipeline YAML templates).

**Resolution order (highest priority first):**
1. Environment variable `RAPS_VAR_NAME` (uppercase, e.g. `RAPS_VAR_BUCKET`)
2. Test-level `vars`
3. Section-level `vars`
4. Top-level `vars`

If a variable is unresolved, it is left as-is in the command (for visibility in error output).

---

## Pytest Integration

One new file: `tests/test_catalog.py`. It reads `catalog.json` at collection time and generates one parametrized test per entry with correct marks.

```python
# tests/test_catalog.py
import json, os, re
import pytest
from pathlib import Path

_RAW = json.loads((Path(__file__).parent.parent / "tests" / "catalog.json").read_text())

def _resolve(command: str, vars: dict) -> str:
    def replace(m):
        name = m.group(1)
        env_key = f"RAPS_VAR_{name.upper()}"
        return os.environ.get(env_key, vars.get(name, m.group(0)))
    return re.sub(r'\$\{(\w+)\}', replace, command)

def _collect():
    global_vars = _RAW.get("vars", {})
    params = []
    for section in _RAW["sections"]:
        section_vars = {**global_vars, **section.get("vars", {})}
        xdist_group = section["id"]
        section_marks = section.get("marks", [])
        for test in section["tests"]:
            merged_vars = {**section_vars, **test.get("vars", {})}
            all_marks = section_marks + test.get("marks", [])
            marks = [
                pytest.mark.xdist_group(xdist_group),
                pytest.mark.sr(test["id"]),
                *[getattr(pytest.mark, m) for m in all_marks],
            ]
            params.append(pytest.param(
                {"test": test, "vars": merged_vars},
                id=f"{test['id']}-{test['slug']}",
                marks=marks,
            ))
    return params

@pytest.mark.parametrize("entry", _collect())
def test_catalog_atomic(raps, entry):
    test, vars = entry["test"], entry["vars"]
    command = _resolve(test["command"], vars)
    if test.get("ok", True):
        raps.run_ok(command, sr_id=test["id"], slug=test["slug"])
    else:
        raps.run(command, sr_id=test["id"], slug=test["slug"])
```

---

## Migration Strategy

### Phase 1 (this plan)

Migrate all **atomic** tests — functions that call exactly one `raps.run_ok()` or `raps.run()`.

For each migrated SR:
1. Add entry to `catalog.json` under the correct section
2. Delete the corresponding Python function from the per-section test file
3. If the per-section file becomes empty (only lifecycle/cleanup remain), keep it — it holds non-atomic tests

### What stays in Python

- Lifecycle tests (`@pytest.mark.lifecycle`) — multi-step, use `lc.step()` + `lc.assert_all_passed()`
- Cleanup helpers (`test_cleanup_*`) — conditional, not SR-tagged
- Tests with complex Python logic (dynamic IDs, file generation, tmp_path)

### Phase 2 (future, optional)

Lifecycle support in catalog via `steps` array instead of single `command`. Not in scope for this plan.

---

## Files Touched

| File | Action |
|------|--------|
| `tests/catalog.json` | Create |
| `tests/test_catalog.py` | Create |
| `tests/test_02_config.py` | Remove migrated atomic functions |
| `tests/test_03_storage.py` | Remove migrated atomic functions |
| `tests/test_04_data_management.py` | Remove migrated atomic functions |
| `tests/test_05_model_derivative.py` | Remove migrated atomic functions |
| `tests/test_06_webhooks.py` | Remove migrated atomic functions |
| `tests/test_07_reality_capture.py` | Remove migrated atomic functions |
| `tests/test_08_autospecs.py` | Remove migrated atomic functions |
| `tests/test_09_acc_modules.py` | Remove migrated atomic functions |
| `tests/test_10_issues.py` | Remove migrated atomic functions |
| `tests/test_11_assets.py` | Remove migrated atomic functions |
| `tests/test_12_sheets.py` | Remove migrated atomic functions |
| `tests/test_13_rfis.py` | Remove migrated atomic functions |
| `tests/test_14_submittals.py` | Remove migrated atomic functions |
| `tests/test_15_forms.py` | Remove migrated atomic functions |
| `tests/test_16_cost.py` | Remove migrated atomic functions |
| `tests/test_17_account_admin.py` | Remove migrated atomic functions |
| `tests/test_18_pipelines.py` | Remove migrated atomic functions |
| `tests/test_19_generate.py` | Remove migrated atomic functions |
| `tests/test_20_mcp.py` | Remove migrated atomic functions |
| `tests/test_21_output_formats.py` | Remove migrated atomic functions |
| `tests/test_22_demo.py` | Remove migrated atomic functions |
| `tests/test_23_logs.py` | Remove migrated atomic functions |
| `tests/test_30_workflows.py` | Remove migrated atomic functions |
| `README.md` | Update test counts |
