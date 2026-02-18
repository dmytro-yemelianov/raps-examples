"""SectionJsonReporter — pytest plugin that writes per-section JSON files.

Output format is backward-compatible with the bash harness JSON, so the
existing generate-run-report.py HTML report generator works unchanged.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

import re

from .runner import _captured_logs

_CLI_EXIT_RE = re.compile(r"->\s+(?:exit\s+(\d+)|TIMEOUT)\s+")


def _parse_worst_cli_exit(log_text: str) -> int | None:
    """Parse log for CLI exit codes; return worst (max) non-zero, or 0 if all passed."""
    matches = _CLI_EXIT_RE.findall(log_text)
    if not matches:
        return None
    codes = [124 if m == "" else int(m) for m in matches]
    return max(codes)


class SectionJsonReporter:
    """Collect test results and write per-section JSON files."""

    def __init__(self, report_dir: Path) -> None:
        self.report_dir = report_dir
        self.report_dir.mkdir(parents=True, exist_ok=True)
        # section_name -> {title, target, timestamp, runs: [...]}
        self._sections: dict[str, dict] = {}
        self._timings: dict[str, float] = {}

    # --- Hooks ---

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(self, item: pytest.Item) -> None:
        self._timings[item.nodeid] = time.monotonic()

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: pytest.Item, call):
        outcome = yield
        report = outcome.get_result()

        # Only process the "call" phase (not setup/teardown)
        if report.when != "call":
            return

        # Extract section name from the module filename
        # e.g. test_03_storage -> 03-storage
        module_name = item.module.__name__.rsplit(".", 1)[-1]
        m = re.match(r"test_(\d+)_(.+)", module_name)
        if not m:
            return
        section_num = m.group(1)
        section_slug = m.group(2).replace("_", "-")
        section_name = f"{section_num}-{section_slug}"

        # Extract SR ID from markers
        sr_id = ""
        for marker in item.iter_markers("sr"):
            sr_id = marker.args[0] if marker.args else ""
            break

        # Extract slug from test name (test_sr051_bucket_list -> bucket-list)
        test_name = item.name
        slug_match = re.match(r"test_sr\d+_(.+)", test_name)
        slug = slug_match.group(1).replace("_", "-") if slug_match else test_name

        # Compute duration
        start = self._timings.pop(item.nodeid, time.monotonic())
        duration = round(time.monotonic() - start, 2)

        # Determine exit code from report outcome
        if report.skipped:
            exit_code = 0
            command = f"(skipped: {report.longrepr[2] if isinstance(report.longrepr, tuple) else ''})"
        elif report.failed:
            exit_code = 1
            command = test_name
        else:
            exit_code = 0
            command = test_name

        # Check if lifecycle
        is_lifecycle = any(item.iter_markers("lifecycle"))
        if is_lifecycle and exit_code == 0:
            command = f"(lifecycle: {test_name})"

        # Initialize section if needed
        if section_name not in self._sections:
            # Try to get title from module docstring
            title = ""
            if item.module.__doc__:
                title = item.module.__doc__.strip().split("\n")[0]
            if not title:
                title = section_name

            self._sections[section_name] = {
                "section": section_name,
                "title": title,
                "target": _get_target(item),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "runs": [],
            }

        # Build run entry with embedded log from captured output
        run_entry = {
            "id": sr_id or test_name,
            "slug": slug,
            "command": command,
            "exit_code": exit_code,
            "duration_seconds": duration,
            "target": _get_target(item),
        }

        # Attach per-run log from the runner's captured output
        run_log = _captured_logs.get(sr_id, "")
        if run_log:
            run_entry["log"] = run_log
            # Parse actual CLI exit codes from log (-> exit N or -> TIMEOUT)
            cli_exit = _parse_worst_cli_exit(run_log)
            if cli_exit is not None:
                run_entry["cli_exit_code"] = cli_exit

        self._sections[section_name]["runs"].append(run_entry)

    def pytest_sessionfinish(self, session: pytest.Session) -> None:
        """Write all section JSON and companion .log files."""
        for section_name, data in self._sections.items():
            # Write JSON
            path = self.report_dir / f"{section_name}.json"
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")

            # Write companion .log from accumulated per-run logs
            log_parts = []
            for run in data["runs"]:
                run_log = run.get("log", "")
                if run_log:
                    log_parts.append(run_log)
            if log_parts:
                log_path = self.report_dir / f"{section_name}.log"
                log_path.write_text("\n".join(log_parts), encoding="utf-8")


def _get_target(item: pytest.Item) -> str:
    """Get target (real/mock) from the test session config."""
    return item.config.getoption("--mock", default=False) and "mock" or "real"
