"""Data-driven atomic tests — generated from tests/catalog.json."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

_CATALOG_PATH = Path(__file__).parent / "catalog.json"
_RAW = json.loads(_CATALOG_PATH.read_text())


def _resolve(command: str, variables: dict[str, str]) -> str:
    """Replace ${name}: RAPS_VAR_NAME env var takes priority over variables dict."""
    def replace(m: re.Match) -> str:
        name = m.group(1)
        env_key = f"RAPS_VAR_{name.upper()}"
        return os.environ.get(env_key, variables.get(name, m.group(0)))
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
