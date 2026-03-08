# catalog.json Data-Driven Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move all self-contained atomic tests from 24 Python files into `tests/catalog.json` + a single `tests/test_catalog.py` parametrize runner.

**Architecture:** `test_catalog.py` reads `catalog.json` at pytest collection time, generates one `pytest.param` per test entry with correct marks and xdist_group, then dispatches to `raps.run_ok()` or `raps.run()` exactly like the existing Python tests do. The `ids` fixture is passed in so `${hub_id}`, `${project_id}`, `${account_id}` resolve dynamically. The catalog file sorts alphabetically AFTER all numbered test files (`test_c > test_0`), so remaining Python tests in each file run first within each xdist_group — this is intentional and safe.

**Tech Stack:** Python 3, pytest, pytest-xdist, json (stdlib), re (stdlib). No new dependencies.

---

## What goes where

### Into catalog.json (atomic, self-contained)
Tests that call exactly one `raps.run()` or `raps.run_ok()` and don't depend on a resource ID that was dynamically created by a previous test in the same session.

### Stays in Python (all files keep their file, just atomic functions deleted)
- `test_03_storage.py` — ALL tests: uses `BUCKET_NAME = f"sr-storage-{_TS}"` (dynamic)
- `test_06_design_automation.py` — SR-112 to SR-121: use `_TS`-based bundle/activity IDs
- `test_07_acc_issues.py` — SR-132 to SR-139: use `ISSUE_ID` created by SR-132
- `test_08_acc_rfi.py` — SR-151 to SR-154: use `RFI_ID` created by SR-151
- `test_09_acc_modules.py` — SR-161 to SR-177: use dynamic ASSET_ID/SUBMITTAL_ID/CHECKLIST_ID
- `test_10_webhooks.py` — SR-183, SR-184, SR-187: use `hook_id` created by SR-181
- `test_11_admin_users.py` — SR-193 to SR-206: complex admin ops with user IDs
- `test_12_admin_projects.py` — SR-212 to SR-215: use `PROJECT_ID` created by SR-212
- `test_13_admin_folders.py` — SR-220 to SR-222, SR-225 to SR-228: dynamic IDs
- `test_14_reality_capture.py` — SR-232 to SR-238: use `JOB_ID` created by SR-232
- `test_16_templates.py` — SR-251 to SR-255: use `TEMPLATE_ID` created by SR-251
- `test_21_shell_serve.py` — SR-301: PowerShell-specific Start-Job syntax
- `test_02_config.py` — SR-038 (PowerShell), SR-046 (dynamic SNAP_BUCKET)
- All lifecycle tests (`@pytest.mark.lifecycle`)
- All cleanup helpers (`test_cleanup_*`)

---

## Task 1: Bootstrap — test_catalog.py + minimal catalog.json

**Files:**
- Create: `tests/test_catalog.py`
- Create: `tests/catalog.json`

### Step 1: Create tests/test_catalog.py

```python
"""Data-driven atomic tests — generated from tests/catalog.json."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

_CATALOG_PATH = Path(__file__).parent / "catalog.json"
_RAW = json.loads(_CATALOG_PATH.read_text())


def _resolve(command: str, vars: dict[str, str]) -> str:
    """Replace ${name} with value from vars dict, then RAPS_VAR_NAME env vars."""
    def replace(m: re.Match) -> str:
        name = m.group(1)
        env_key = f"RAPS_VAR_{name.upper()}"
        return os.environ.get(env_key, vars.get(name, m.group(0)))
    return re.sub(r"\$\{(\w+)\}", replace, command)


def _collect() -> list[pytest.param]:
    global_vars = _RAW.get("vars", {})
    params: list[pytest.param] = []
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
            params.append(
                pytest.param(
                    {"test": test, "vars": merged_vars},
                    id=f"{test['id']}-{test['slug']}",
                    marks=marks,
                )
            )
    return params


@pytest.mark.parametrize("entry", _collect())
def test_catalog_atomic(raps, ids, entry):
    test = entry["test"]
    # Merge ids fixture values so ${hub_id} etc. resolve from discovered session IDs
    runtime_vars = {
        "hub_id": ids.hub_id or "",
        "project_id": ids.project_id or "",
        "project_full_id": ids.project_full_id or "",
        "account_id": ids.account_id or "",
        **entry["vars"],
    }
    command = _resolve(test["command"], runtime_vars)
    if test.get("ok", True):
        raps.run_ok(command, sr_id=test["id"], slug=test["slug"])
    else:
        raps.run(command, sr_id=test["id"], slug=test["slug"])
```

### Step 2: Create minimal tests/catalog.json (3 entries to verify wiring)

```json
{
  "vars": {
    "hub_id": "b.demo-hub-001",
    "project_id": "b.demo-project-001",
    "project_full_id": "b.demo-project-001",
    "account_id": "",
    "urn": ""
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
          "id": "SR-031",
          "slug": "config-get",
          "command": "raps config get client_id"
        },
        {
          "id": "SR-047",
          "slug": "snapshot-list",
          "command": "raps snapshot list"
        }
      ]
    }
  ]
}
```

### Step 3: Verify pytest collects the 3 new entries

Run:
```bash
python3 -m pytest tests/test_catalog.py --collect-only -q 2>&1 | head -20
```

Expected output contains:
```
tests/test_catalog.py::test_catalog_atomic[SR-030-config-show]
tests/test_catalog.py::test_catalog_atomic[SR-031-config-get]
tests/test_catalog.py::test_catalog_atomic[SR-047-snapshot-list]
3 tests collected
```

### Step 4: Run just the catalog tests to confirm they pass

```bash
python3 -m pytest tests/test_catalog.py -q
```

Expected: `3 passed` (or skipped if auth not available)

### Step 5: Commit

```bash
git add tests/test_catalog.py tests/catalog.json
git commit -m "feat: add test_catalog.py runner and minimal catalog.json bootstrap"
```

---

## Task 2: Complete catalog.json — all sections

**Files:**
- Modify: `tests/catalog.json`

Replace the minimal catalog.json with the complete version below. This is the FULL content — copy it exactly.

```json
{
  "vars": {
    "hub_id": "b.demo-hub-001",
    "project_id": "b.demo-project-001",
    "project_full_id": "b.demo-project-001",
    "account_id": "",
    "urn": ""
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
          "id": "SR-031",
          "slug": "config-get",
          "command": "raps config get client_id"
        },
        {
          "id": "SR-033",
          "slug": "config-profile-create",
          "command": "raps config profile create staging"
        },
        {
          "id": "SR-035",
          "slug": "config-profile-use",
          "command": "raps config profile use staging"
        },
        {
          "id": "SR-032",
          "slug": "config-set",
          "command": "raps config set base_url https://developer.api.autodesk.com"
        },
        {
          "id": "SR-034",
          "slug": "config-profile-list",
          "command": "raps config profile list"
        },
        {
          "id": "SR-036",
          "slug": "config-profile-current",
          "command": "raps config profile current"
        },
        {
          "id": "SR-037",
          "slug": "config-profile-export",
          "command": "raps config profile export -n staging"
        },
        {
          "id": "SR-039",
          "slug": "config-profile-diff",
          "command": "raps config profile diff default staging"
        },
        {
          "id": "SR-041",
          "slug": "config-context-show",
          "command": "raps config context show"
        },
        {
          "id": "SR-042",
          "slug": "config-context-set",
          "command": "raps config context set hub_id ${hub_id}; raps config context set project_id ${project_full_id}"
        },
        {
          "id": "SR-043",
          "slug": "config-context-clear",
          "command": "raps config context clear"
        },
        {
          "id": "SR-040",
          "slug": "config-profile-delete",
          "ok": false,
          "command": "raps config profile use default; raps config profile delete staging"
        },
        {
          "id": "SR-047",
          "slug": "snapshot-list",
          "command": "raps snapshot list"
        },
        {
          "id": "SR-048",
          "slug": "snapshot-diff",
          "ok": false,
          "command": "raps snapshot diff ./snap-a.json ./snap-b.json"
        }
      ]
    },
    {
      "id": "04-data-management",
      "marks": ["require_3leg"],
      "vars": {},
      "tests": [
        {
          "id": "SR-070",
          "slug": "hub-list",
          "ok": false,
          "command": "raps hub list"
        },
        {
          "id": "SR-071",
          "slug": "hub-info",
          "ok": false,
          "command": "raps hub info ${hub_id}"
        },
        {
          "id": "SR-072",
          "slug": "project-list",
          "ok": false,
          "command": "raps project list ${hub_id}"
        },
        {
          "id": "SR-073",
          "slug": "project-list-interactive",
          "ok": false,
          "command": "raps project list"
        },
        {
          "id": "SR-074",
          "slug": "project-info",
          "ok": false,
          "command": "raps project info ${hub_id} ${project_id}"
        }
      ]
    },
    {
      "id": "05-model-derivative",
      "marks": ["require_2leg"],
      "vars": {},
      "tests": [
        {
          "id": "SR-090",
          "slug": "translate-start",
          "ok": false,
          "command": "raps translate start ${urn} --format svf2"
        },
        {
          "id": "SR-091",
          "slug": "translate-status",
          "ok": false,
          "command": "raps translate status ${urn}"
        },
        {
          "id": "SR-092",
          "slug": "translate-manifest",
          "ok": false,
          "command": "raps translate manifest ${urn}"
        },
        {
          "id": "SR-093",
          "slug": "translate-derivatives",
          "ok": false,
          "command": "raps translate derivatives ${urn}"
        },
        {
          "id": "SR-094",
          "slug": "translate-download",
          "ok": false,
          "command": "raps translate download ${urn} --all --out-dir /tmp/raps-derivative-test/"
        },
        {
          "id": "SR-095",
          "slug": "translate-preset-list",
          "ok": false,
          "command": "raps translate preset list"
        },
        {
          "id": "SR-096",
          "slug": "translate-preset-create",
          "ok": false,
          "command": "raps translate preset create \"svf2-default\" -f svf2"
        },
        {
          "id": "SR-097",
          "slug": "translate-preset-show",
          "ok": false,
          "command": "raps translate preset show \"svf2-default\""
        },
        {
          "id": "SR-098",
          "slug": "translate-preset-use",
          "ok": false,
          "command": "raps translate preset use ${urn} svf2-default"
        },
        {
          "id": "SR-099",
          "slug": "translate-preset-delete",
          "ok": false,
          "command": "raps translate preset delete \"svf2-default\""
        },
        {
          "id": "SR-102",
          "slug": "translate-timeline",
          "ok": false,
          "command": "raps translate timeline ${urn}"
        }
      ]
    },
    {
      "id": "06-design-automation",
      "marks": ["require_2leg"],
      "vars": {},
      "tests": [
        {
          "id": "SR-110",
          "slug": "da-engines",
          "ok": false,
          "command": "raps da engines"
        },
        {
          "id": "SR-111",
          "slug": "da-appbundles-list",
          "ok": false,
          "command": "raps da appbundles"
        }
      ]
    },
    {
      "id": "07-acc-issues",
      "marks": ["require_3leg"],
      "vars": {},
      "tests": [
        {
          "id": "SR-130",
          "slug": "issue-list",
          "ok": false,
          "command": "raps issue list ${project_id}"
        },
        {
          "id": "SR-131",
          "slug": "issue-types",
          "ok": false,
          "command": "raps issue types ${project_id}"
        }
      ]
    },
    {
      "id": "08-acc-rfi",
      "marks": ["require_3leg"],
      "vars": {},
      "tests": [
        {
          "id": "SR-150",
          "slug": "rfi-list",
          "ok": false,
          "command": "raps rfi list ${project_id}"
        }
      ]
    },
    {
      "id": "09-acc-modules",
      "marks": ["require_3leg"],
      "vars": {},
      "tests": [
        {
          "id": "SR-160",
          "slug": "acc-asset-list",
          "ok": false,
          "command": "raps acc asset list ${project_id}"
        },
        {
          "id": "SR-165",
          "slug": "acc-submittal-list",
          "ok": false,
          "command": "raps acc submittal list ${project_id}"
        },
        {
          "id": "SR-170",
          "slug": "acc-checklist-list",
          "ok": false,
          "command": "raps acc checklist list ${project_id}"
        },
        {
          "id": "SR-174",
          "slug": "acc-checklist-templates",
          "ok": false,
          "command": "raps acc checklist templates ${project_id}"
        },
        {
          "id": "SR-178",
          "slug": "acc-export",
          "ok": false,
          "command": "raps acc export ${project_id} --out-dir ./tmp/acc-export-sr178"
        }
      ]
    },
    {
      "id": "10-webhooks",
      "marks": ["require_2leg"],
      "vars": {},
      "tests": [
        {
          "id": "SR-180",
          "slug": "webhook-events",
          "ok": false,
          "command": "raps webhook events"
        },
        {
          "id": "SR-181",
          "slug": "webhook-create",
          "ok": false,
          "command": "raps webhook create -e \"dm.version.added\" -u \"https://example.com/raps-test-hook\""
        },
        {
          "id": "SR-182",
          "slug": "webhook-list",
          "ok": false,
          "command": "raps webhook list"
        },
        {
          "id": "SR-185",
          "slug": "webhook-test",
          "ok": false,
          "command": "raps webhook test \"https://example.com/webhook\""
        },
        {
          "id": "SR-186",
          "slug": "webhook-verify-signature",
          "ok": false,
          "command": "raps webhook verify-signature '{\"event\":\"test\"}' --signature \"abc123\" --secret \"my-secret\""
        }
      ]
    },
    {
      "id": "11-admin-users",
      "marks": ["require_3leg"],
      "vars": {},
      "tests": [
        {
          "id": "SR-190",
          "slug": "admin-user-list-account",
          "ok": false,
          "command": "raps admin user list -a ${account_id}"
        },
        {
          "id": "SR-191",
          "slug": "admin-user-list-project",
          "ok": false,
          "command": "raps admin user list -a ${account_id} -p ${project_id}"
        },
        {
          "id": "SR-192",
          "slug": "admin-user-list-filtered",
          "ok": false,
          "command": "raps admin user list -a ${account_id} --role \"project_admin\" --status \"active\" --search \"john\""
        }
      ]
    },
    {
      "id": "12-admin-projects",
      "marks": ["require_3leg"],
      "vars": {},
      "tests": [
        {
          "id": "SR-210",
          "slug": "admin-project-list",
          "ok": false,
          "command": "raps admin project list -a ${account_id}"
        },
        {
          "id": "SR-211",
          "slug": "admin-project-list-filtered",
          "ok": false,
          "command": "raps admin project list -a ${account_id} -f \"name:*Tower*\" --status active --platform acc --limit 10"
        }
      ]
    },
    {
      "id": "13-admin-folders",
      "marks": ["require_3leg"],
      "vars": {},
      "tests": [
        {
          "id": "SR-223",
          "slug": "admin-company-list",
          "ok": false,
          "command": "raps admin company-list -a ${account_id}"
        },
        {
          "id": "SR-224",
          "slug": "admin-operation-list",
          "ok": false,
          "command": "raps admin operation list --status completed --limit 5"
        }
      ]
    },
    {
      "id": "14-reality-capture",
      "marks": ["require_3leg"],
      "vars": {},
      "tests": [
        {
          "id": "SR-230",
          "slug": "reality-list",
          "ok": false,
          "command": "raps reality list"
        },
        {
          "id": "SR-231",
          "slug": "reality-formats",
          "ok": false,
          "command": "raps reality formats"
        }
      ]
    },
    {
      "id": "15-reporting",
      "marks": ["require_3leg"],
      "vars": {},
      "tests": [
        {
          "id": "SR-240",
          "slug": "report-rfi-summary",
          "ok": false,
          "command": "raps report rfi-summary -a ${account_id} -f \"name:*Tower*\" --status open --since \"2026-01-01\""
        },
        {
          "id": "SR-241",
          "slug": "report-issues-summary",
          "ok": false,
          "command": "raps report issues-summary -a ${account_id} -f \"name:*Phase 2*\" --status open"
        },
        {
          "id": "SR-242",
          "slug": "report-submittals-summary",
          "ok": false,
          "command": "raps report submittals-summary -a ${account_id}"
        },
        {
          "id": "SR-243",
          "slug": "report-checklists-summary",
          "ok": false,
          "command": "raps report checklists-summary -a ${account_id} --status \"in_progress\""
        },
        {
          "id": "SR-244",
          "slug": "report-assets-summary",
          "ok": false,
          "command": "raps report assets-summary -a ${account_id} -f \"name:*Hospital*\""
        }
      ]
    },
    {
      "id": "16-templates",
      "marks": ["require_3leg"],
      "vars": {},
      "tests": [
        {
          "id": "SR-250",
          "slug": "template-list",
          "ok": false,
          "command": "raps template list -a ${account_id}"
        }
      ]
    },
    {
      "id": "17-plugins",
      "marks": [],
      "vars": {},
      "tests": [
        {
          "id": "SR-260",
          "slug": "plugin-list",
          "command": "raps plugin list"
        },
        {
          "id": "SR-261",
          "slug": "plugin-enable",
          "command": "raps plugin enable my-plugin"
        },
        {
          "id": "SR-262",
          "slug": "plugin-disable",
          "command": "raps plugin disable my-plugin"
        },
        {
          "id": "SR-263",
          "slug": "plugin-alias-list",
          "command": "raps plugin alias list"
        },
        {
          "id": "SR-264",
          "slug": "plugin-alias-add",
          "command": "raps plugin alias add \"bl\" \"bucket list\""
        },
        {
          "id": "SR-265",
          "slug": "plugin-alias-remove",
          "command": "raps plugin alias remove \"bl\""
        }
      ]
    },
    {
      "id": "18-pipelines",
      "marks": ["require_2leg"],
      "vars": {},
      "tests": [
        {
          "id": "SR-270",
          "slug": "pipeline-sample",
          "command": "raps pipeline sample --out-file ./sample-pipeline.yaml"
        },
        {
          "id": "SR-271",
          "slug": "pipeline-validate",
          "command": "raps pipeline validate ./sample-pipeline.yaml"
        },
        {
          "id": "SR-272",
          "slug": "pipeline-run",
          "ok": false,
          "command": "raps pipeline run ./sample-pipeline.yaml"
        },
        {
          "id": "SR-274",
          "slug": "pipeline-diff",
          "ok": false,
          "command": "raps pipeline sample --out-file ./pipeline-a.yaml; raps pipeline sample --out-file ./pipeline-b.yaml; raps pipeline diff ./pipeline-a.yaml ./pipeline-b.yaml"
        }
      ]
    },
    {
      "id": "19-api-raw",
      "marks": ["require_2leg"],
      "vars": {},
      "tests": [
        {
          "id": "SR-280",
          "slug": "api-get",
          "ok": false,
          "command": "raps api get /oss/v2/buckets"
        },
        {
          "id": "SR-281",
          "slug": "api-post",
          "ok": false,
          "command": "raps api post \"/oss/v2/buckets\" -d '{\"bucketKey\":\"api-raw-test-raps\",\"policyKey\":\"transient\"}'"
        },
        {
          "id": "SR-282",
          "slug": "api-put",
          "ok": false,
          "command": "raps api put \"/webhooks/v1/systems/data/events/dm.version.added/hooks/dummy-hook-id\" -d '{\"status\":\"inactive\"}'"
        },
        {
          "id": "SR-283",
          "slug": "api-patch",
          "ok": false,
          "command": "raps api patch \"/construction/issues/v1/projects/dummy-project/issues/dummy-issue\" -d '{\"title\":\"updated\"}'"
        },
        {
          "id": "SR-284",
          "slug": "api-delete",
          "ok": false,
          "command": "raps api delete \"/oss/v2/buckets/api-raw-nonexistent-bucket\""
        }
      ]
    },
    {
      "id": "20-generation",
      "marks": ["require_2leg"],
      "vars": {},
      "tests": [
        {
          "id": "SR-290",
          "slug": "generate-files-simple",
          "command": "raps generate files -c 1 --out-dir ./gen-simple/ --complexity simple"
        },
        {
          "id": "SR-291",
          "slug": "generate-files-complex",
          "command": "raps generate files -c 10 --out-dir ./gen-complex/ --complexity complex"
        }
      ]
    },
    {
      "id": "21-shell-serve",
      "marks": [],
      "vars": {},
      "tests": [
        {
          "id": "SR-300",
          "slug": "shell-interactive",
          "ok": false,
          "command": "echo \"exit\" | raps shell"
        },
        {
          "id": "SR-302",
          "slug": "completions-bash",
          "command": "raps completions bash"
        },
        {
          "id": "SR-303",
          "slug": "completions-powershell",
          "command": "raps completions powershell"
        },
        {
          "id": "SR-304",
          "slug": "completions-zsh",
          "command": "raps completions zsh"
        },
        {
          "id": "SR-305",
          "slug": "completions-fish",
          "command": "raps completions fish"
        },
        {
          "id": "SR-306",
          "slug": "completions-elvish",
          "command": "raps completions elvish"
        }
      ]
    },
    {
      "id": "22-demo",
      "marks": [],
      "vars": {},
      "tests": [
        {
          "id": "SR-310",
          "slug": "demo-bucket-lifecycle",
          "ok": false,
          "command": "raps demo bucket-lifecycle --non-interactive"
        },
        {
          "id": "SR-311",
          "slug": "demo-model-pipeline",
          "ok": false,
          "command": "raps demo model-pipeline --file ./test-data/sample.rvt --non-interactive"
        },
        {
          "id": "SR-312",
          "slug": "demo-data-management",
          "ok": false,
          "command": "raps demo data-management --non-interactive --export ./dm-report.json"
        },
        {
          "id": "SR-313",
          "slug": "demo-batch-processing",
          "ok": false,
          "command": "raps demo batch-processing --input ./test-data/ --non-interactive"
        }
      ]
    },
    {
      "id": "23-logs",
      "marks": [],
      "vars": {},
      "tests": [
        {
          "id": "SR-314",
          "slug": "logs-path",
          "command": "raps logs path"
        },
        {
          "id": "SR-315",
          "slug": "logs-show",
          "command": "raps logs show"
        },
        {
          "id": "SR-316",
          "slug": "logs-clear",
          "command": "raps logs clear -y"
        }
      ]
    },
    {
      "id": "99-cross-cutting",
      "marks": ["require_2leg"],
      "vars": {},
      "tests": [
        {
          "id": "SR-500",
          "slug": "bucket-list-table",
          "ok": false,
          "command": "raps bucket list --output table"
        },
        {
          "id": "SR-501",
          "slug": "bucket-list-json",
          "ok": false,
          "command": "raps bucket list --output json"
        },
        {
          "id": "SR-502",
          "slug": "bucket-list-yaml",
          "ok": false,
          "command": "raps bucket list --output yaml"
        },
        {
          "id": "SR-503",
          "slug": "bucket-list-csv",
          "ok": false,
          "command": "raps bucket list --output csv"
        },
        {
          "id": "SR-504",
          "slug": "bucket-list-plain",
          "ok": false,
          "command": "raps bucket list --output plain"
        },
        {
          "id": "SR-505",
          "slug": "issue-list-table",
          "ok": false,
          "marks": ["require_3leg"],
          "command": "raps issue list ${project_id} --output table"
        },
        {
          "id": "SR-506",
          "slug": "issue-list-json",
          "ok": false,
          "marks": ["require_3leg"],
          "command": "raps issue list ${project_id} --output json"
        },
        {
          "id": "SR-507",
          "slug": "issue-list-yaml",
          "ok": false,
          "marks": ["require_3leg"],
          "command": "raps issue list ${project_id} --output yaml"
        },
        {
          "id": "SR-508",
          "slug": "issue-list-csv",
          "ok": false,
          "marks": ["require_3leg"],
          "command": "raps issue list ${project_id} --output csv"
        },
        {
          "id": "SR-509",
          "slug": "issue-list-plain",
          "ok": false,
          "marks": ["require_3leg"],
          "command": "raps issue list ${project_id} --output plain"
        },
        {
          "id": "SR-510",
          "slug": "admin-user-list-table",
          "ok": false,
          "marks": ["require_3leg"],
          "command": "raps admin user list -a ${account_id} --output table"
        },
        {
          "id": "SR-511",
          "slug": "admin-user-list-json",
          "ok": false,
          "marks": ["require_3leg"],
          "command": "raps admin user list -a ${account_id} --output json"
        },
        {
          "id": "SR-512",
          "slug": "admin-user-list-yaml",
          "ok": false,
          "marks": ["require_3leg"],
          "command": "raps admin user list -a ${account_id} --output yaml"
        },
        {
          "id": "SR-513",
          "slug": "admin-user-list-csv",
          "ok": false,
          "marks": ["require_3leg"],
          "command": "raps admin user list -a ${account_id} --output csv"
        },
        {
          "id": "SR-514",
          "slug": "admin-user-list-plain",
          "ok": false,
          "marks": ["require_3leg"],
          "command": "raps admin user list -a ${account_id} --output plain"
        },
        {
          "id": "SR-515",
          "slug": "hub-list-table",
          "ok": false,
          "marks": ["require_3leg"],
          "command": "raps hub list --output table"
        },
        {
          "id": "SR-516",
          "slug": "hub-list-json",
          "ok": false,
          "marks": ["require_3leg"],
          "command": "raps hub list --output json"
        },
        {
          "id": "SR-517",
          "slug": "hub-list-yaml",
          "ok": false,
          "marks": ["require_3leg"],
          "command": "raps hub list --output yaml"
        },
        {
          "id": "SR-518",
          "slug": "hub-list-csv",
          "ok": false,
          "marks": ["require_3leg"],
          "command": "raps hub list --output csv"
        },
        {
          "id": "SR-519",
          "slug": "hub-list-plain",
          "ok": false,
          "marks": ["require_3leg"],
          "command": "raps hub list --output plain"
        },
        {
          "id": "SR-520",
          "slug": "da-engines-table",
          "ok": false,
          "command": "raps da engines --output table"
        },
        {
          "id": "SR-521",
          "slug": "da-engines-json",
          "ok": false,
          "command": "raps da engines --output json"
        },
        {
          "id": "SR-522",
          "slug": "da-engines-yaml",
          "ok": false,
          "command": "raps da engines --output yaml"
        },
        {
          "id": "SR-523",
          "slug": "da-engines-csv",
          "ok": false,
          "command": "raps da engines --output csv"
        },
        {
          "id": "SR-524",
          "slug": "da-engines-plain",
          "ok": false,
          "command": "raps da engines --output plain"
        },
        {
          "id": "SR-530",
          "slug": "no-color-bucket-list",
          "ok": false,
          "command": "raps bucket list --no-color"
        },
        {
          "id": "SR-531",
          "slug": "no-color-issue-list",
          "ok": false,
          "marks": ["require_3leg"],
          "command": "raps issue list ${project_id} --no-color"
        },
        {
          "id": "SR-540",
          "slug": "help-top-level",
          "command": "raps --help"
        },
        {
          "id": "SR-541",
          "slug": "help-auth",
          "command": "raps auth --help"
        },
        {
          "id": "SR-542",
          "slug": "help-admin",
          "command": "raps admin --help"
        },
        {
          "id": "SR-543",
          "slug": "help-admin-user",
          "command": "raps admin user --help"
        },
        {
          "id": "SR-544",
          "slug": "help-version",
          "command": "raps --version"
        },
        {
          "id": "SR-561",
          "slug": "lint-pipeline",
          "ok": false,
          "command": "raps pipeline sample --out-file ./lint-test-pipeline.yaml; raps lint ./lint-test-pipeline.yaml"
        }
      ]
    }
  ]
}
```

### Step 1: Write the complete catalog.json

Replace `tests/catalog.json` with the full content above.

### Step 2: Verify pytest collects all entries

```bash
python3 -m pytest tests/test_catalog.py --collect-only -q 2>&1 | tail -5
```

Expected: `~106 tests collected` (count may vary slightly).

### Step 3: Verify tests/catalog.json is valid JSON

```bash
python3 -c "import json; json.load(open('tests/catalog.json')); print('OK')"
```

Expected: `OK`

### Step 4: Run catalog tests only

```bash
python3 -m pytest tests/test_catalog.py -q 2>&1 | tail -5
```

Expected: some passed, none ERROR. Skips are OK (require_2leg/require_3leg).

### Step 5: Commit

```bash
git add tests/catalog.json
git commit -m "feat: complete catalog.json with all atomic test entries"
```

---

## Task 3: Remove migrated atomic functions from Python files

**Files to modify:**
- `tests/test_02_config.py`
- `tests/test_04_data_management.py`
- `tests/test_05_model_derivative.py`
- `tests/test_06_design_automation.py`
- `tests/test_07_acc_issues.py`
- `tests/test_08_acc_rfi.py`
- `tests/test_09_acc_modules.py`
- `tests/test_10_webhooks.py`
- `tests/test_11_admin_users.py`
- `tests/test_12_admin_projects.py`
- `tests/test_13_admin_folders.py`
- `tests/test_14_reality_capture.py`
- `tests/test_15_reporting.py`
- `tests/test_16_templates.py`
- `tests/test_17_plugins.py`
- `tests/test_18_pipelines.py`
- `tests/test_19_api_raw.py`
- `tests/test_20_generation.py`
- `tests/test_21_shell_serve.py`
- `tests/test_22_demo.py`
- `tests/test_23_logs.py`
- `tests/test_99_cross_cutting.py`

### What to delete from each file

**Rule:** Delete a Python function if and only if its SR-ID appears in catalog.json. Keep all lifecycle tests, cleanup helpers, and tests that stay in Python (see "What goes where" section at top of this plan).

#### test_02_config.py — delete these functions:
- `test_sr030_config_show`
- `test_sr031_config_get`
- `test_sr033_config_profile_create`
- `test_sr035_config_profile_use`
- `test_sr032_config_set`
- `test_sr034_config_profile_list`
- `test_sr036_config_profile_current`
- `test_sr037_config_profile_export`
- `test_sr039_config_profile_diff`
- `test_sr041_config_context_show`
- `test_sr042_config_context_set`
- `test_sr043_config_context_clear`
- `test_sr040_config_profile_delete`
- `test_sr047_snapshot_list`
- `test_sr048_snapshot_diff`
- Also delete: `test_cleanup_staging_copy`, `test_cleanup_switch_to_default` (replaced by the switch-then-delete command in SR-040 catalog entry)

Keep: `import time`, `_TS`, `SNAP_BUCKET`, `test_sr038_config_profile_import`, `test_sr046_snapshot_create`, lifecycle tests (SR-044, SR-045, SR-049), `pytestmark`.

#### test_04_data_management.py — delete:
- `test_sr070_hub_list`
- `test_sr071_hub_info`
- `test_sr072_project_list`
- `test_sr073_project_list_interactive`
- `test_sr074_project_info`

Keep all folder/item CRUD tests, lifecycle tests, `pytestmark`.

#### test_05_model_derivative.py — delete:
- `test_sr090_translate_start`
- `test_sr091_translate_status`
- `test_sr092_translate_manifest`
- `test_sr093_translate_derivatives`
- `test_sr094_translate_download`
- `test_sr095_translate_preset_list`
- `test_sr096_translate_preset_create`
- `test_sr097_translate_preset_show`
- `test_sr098_translate_preset_use`
- `test_sr099_translate_preset_delete`
- `test_sr102_translate_timeline`

Keep all lifecycle tests (SR-100, SR-101, SR-550), `pytestmark`, `URN` constant if present.

#### test_06_design_automation.py — delete:
- `test_sr110_da_engines`
- `test_sr111_da_appbundles_list`

Keep SR-112 through SR-121, lifecycle tests, `_TS` constant, `pytestmark`.

#### test_07_acc_issues.py — delete:
- `test_sr130_issue_list`
- `test_sr131_issue_types`

Keep SR-132 through SR-141, lifecycle tests, `pytestmark`.

#### test_08_acc_rfi.py — delete:
- `test_sr150_rfi_list`

Keep SR-151 through SR-155, lifecycle tests, `pytestmark`.

#### test_09_acc_modules.py — delete:
- `test_sr160_acc_asset_list`
- `test_sr165_acc_submittal_list`
- `test_sr170_acc_checklist_list`
- `test_sr174_acc_checklist_templates`
- `test_sr178_acc_export`

Keep SR-161 to SR-164, SR-166 to SR-169, SR-171 to SR-173, lifecycle tests, `pytestmark`.

#### test_10_webhooks.py — delete:
- `test_sr180_webhook_events`
- `test_sr181_webhook_create`
- `test_sr182_webhook_list`
- `test_sr185_webhook_test`
- `test_sr186_webhook_verify_signature`

Keep SR-183, SR-184, SR-187, SR-188, lifecycle tests, `_EVENT`/`hook_id` module constants, `pytestmark`.

#### test_11_admin_users.py — delete:
- `test_sr190_admin_user_list_account`
- `test_sr191_admin_user_list_project`
- `test_sr192_admin_user_list_filtered`

Keep SR-193 through SR-206, lifecycle tests, `pytestmark`.

#### test_12_admin_projects.py — delete:
- `test_sr210_admin_project_list`
- `test_sr211_admin_project_list_filtered`

Keep SR-212 through SR-215, lifecycle tests, `pytestmark`.

#### test_13_admin_folders.py — delete:
- `test_sr223_admin_company_list`
- `test_sr224_admin_operation_list`

Keep SR-220 through SR-222, SR-225 through SR-228, lifecycle tests, `pytestmark`.

#### test_14_reality_capture.py — delete:
- `test_sr230_reality_list`
- `test_sr231_reality_formats`

Keep SR-232 through SR-238, lifecycle tests, `pytestmark`.

#### test_15_reporting.py — delete:
- `test_sr240_report_rfi_summary`
- `test_sr241_report_issues_summary`
- `test_sr242_report_submittals_summary`
- `test_sr243_report_checklists_summary`
- `test_sr244_report_assets_summary`

If this leaves the file empty (only `pytestmark` and docstring), delete the file entirely and remove it from any imports.

#### test_16_templates.py — delete:
- `test_sr250_template_list`

Keep SR-251 through SR-255, lifecycle tests, `pytestmark`.

#### test_17_plugins.py — delete:
- `test_sr260_plugin_list`
- `test_sr261_plugin_enable`
- `test_sr262_plugin_disable`
- `test_sr263_plugin_alias_list`
- `test_sr264_plugin_alias_add`
- `test_sr265_plugin_alias_remove`

Keep SR-266, lifecycle tests, `pytestmark`.

#### test_18_pipelines.py — delete:
- `test_sr270_pipeline_sample`
- `test_sr271_pipeline_validate`
- `test_sr272_pipeline_run`
- `test_sr274_pipeline_diff`

Keep SR-273, SR-273's lifecycle, `pytestmark`.

#### test_19_api_raw.py — delete:
- `test_sr280_api_get`
- `test_sr281_api_post`
- `test_sr282_api_put`
- `test_sr283_api_patch`
- `test_sr284_api_delete`

If this leaves the file empty, delete it entirely.

#### test_20_generation.py — delete:
- `test_sr290_generate_files_simple`
- `test_sr291_generate_files_complex`

If this leaves the file empty, delete it entirely.

#### test_21_shell_serve.py — delete:
- `test_sr300_shell_interactive`
- `test_sr302_completions_bash`
- `test_sr303_completions_powershell`
- `test_sr304_completions_zsh`
- `test_sr305_completions_fish`
- `test_sr306_completions_elvish`

Keep SR-301 (serve-mcp, PowerShell), `pytestmark`.

#### test_22_demo.py — delete:
- `test_sr310_demo_bucket_lifecycle`
- `test_sr311_demo_model_pipeline`
- `test_sr312_demo_data_management`
- `test_sr313_demo_batch_processing`

If this leaves the file empty, delete it entirely.

#### test_23_logs.py — delete:
- `test_sr314_logs_path`
- `test_sr315_logs_show`
- `test_sr316_logs_clear`

Keep SR-317 lifecycle, `pytestmark`.

#### test_99_cross_cutting.py — delete:
- `test_bucket_list_output_format` (entire parametrized function — all 5 SR-500-504)
- `test_issue_list_output_format` (entire parametrized function — SR-505-509)
- `test_admin_user_list_output_format` (entire parametrized function — SR-510-514)
- `test_hub_list_output_format` (entire parametrized function — SR-515-519)
- `test_da_engines_output_format` (entire parametrized function — SR-520-524)
- `test_sr530_no_color_bucket_list`
- `test_sr531_no_color_issue_list`
- `test_sr540_help_top_level`
- `test_sr541_help_auth`
- `test_sr542_help_admin`
- `test_sr543_help_admin_user`
- `test_sr544_help_version`
- `test_sr561_lint_pipeline`

Keep: `test_sr560_log_file_flag` (uses `tmp_path` fixture), `pytestmark`.

### Step 1: Make all the deletions above

Work file by file. For each file: read it, delete the listed functions, save. If only `pytestmark` / docstring remain after deletions, delete the file.

### Step 2: Verify no duplicate SR-IDs (catalog vs remaining Python)

```bash
python3 -m pytest tests/ --collect-only -q 2>&1 | grep -E "ERRORS|error" | head -10
```

Expected: no duplicate node ID errors.

### Step 3: Run the full test suite

```bash
python3 -m pytest tests/ -q 2>&1 | tail -5
```

Expected: same pass/skip counts as before (150 passed, 136 skipped), 0 failed.

### Step 4: Commit

```bash
git add tests/
git commit -m "refactor: migrate atomic tests to catalog.json, remove from Python files"
```

---

## Task 4: Update README and verify

**Files:**
- Modify: `README.md`

### Step 1: Update test counts in README.md

Find the test count summary table. Update:
- Total test count: was X, now may be same count (same tests, just different location)
- Note that `test_15_reporting.py`, `test_19_api_raw.py`, `test_20_generation.py`, `test_22_demo.py` may have been deleted
- Add a row or note for `test_catalog.py` (data-driven atomics)
- Update the "N test files" count if any files were deleted

### Step 2: Add a note about catalog.json in README.md

Find the test infrastructure section and add:

```markdown
### Data-Driven Atomics

Self-contained atomic tests are defined in `tests/catalog.json` and run by
`tests/test_catalog.py`. Each entry specifies an SR-ID, slug, command, and
optional marks/vars. Variable interpolation: `${hub_id}`, `${project_id}`, etc.
resolve from the `ids` session fixture (or `RAPS_VAR_HUB_ID` env var overrides).

To add a new atomic test, append an entry to the appropriate section in
`tests/catalog.json` — no Python required.
```

### Step 3: Final verification

```bash
python3 -m pytest tests/ -q 2>&1 | tail -3
```

Expected: 0 failed, consistent passed/skipped counts.

### Step 4: Commit and push

```bash
git add README.md
git commit -m "docs: update README for catalog.json data-driven test architecture"
git push
```
