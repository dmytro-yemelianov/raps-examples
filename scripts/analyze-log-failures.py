#!/usr/bin/env python3
"""
analyze-log-failures.py — Parse report logs to find actual CLI failures.

The pytest JSON reporter stores exit_code=0 when a test passes (e.g. due to may_fail=True),
but the actual CLI exit codes are in the log text as "-> exit N (Xs)".

This script parses .log files and reports which commands actually failed.

Usage:
    python scripts/analyze-log-failures.py reports/2026-02-17-23-35
    python scripts/analyze-log-failures.py reports/latest-run
"""

import re
import sys
from pathlib import Path

# Matches: "  -> exit 6 (0.54s)" or "  -> TIMEOUT (30s)"
EXIT_RE = re.compile(r"->\s+(?:exit\s+(\d+)|TIMEOUT)\s+\([\d.]+s\)")
SR_ID_RE = re.compile(r"\[(SR-\d+(?:/step\d+)?)\]\s+(\S+):\s+(.+)")


def parse_log_file(path: Path) -> list[dict]:
    """Parse a .log file and return list of {sr_id, slug, command, exit_code, stderr_preview}."""
    text = path.read_text(encoding="utf-8", errors="replace")
    results = []
    current = None
    for line in text.splitlines():
        sr_match = SR_ID_RE.match(line)
        if sr_match:
            if current and current.get("exit_code") is not None:
                results.append(current)
            current = {
                "sr_id": sr_match.group(1),
                "slug": sr_match.group(2),
                "command": sr_match.group(3).strip(),
                "exit_code": None,
                "timed_out": False,
                "stderr_preview": "",
            }
            continue
        if current is not None:
            exit_match = EXIT_RE.search(line)
            if exit_match:
                if exit_match.group(1):
                    current["exit_code"] = int(exit_match.group(1))
                else:
                    current["exit_code"] = 124
                    current["timed_out"] = True
            elif line.strip().startswith("stderr:"):
                current["stderr_preview"] = line.strip()[7:].strip()[:200]
    if current and current.get("exit_code") is not None:
        results.append(current)
    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/analyze-log-failures.py <report_dir>", file=sys.stderr)
        sys.exit(1)
    report_dir = Path(sys.argv[1])
    if not report_dir.exists():
        print(f"ERROR: Directory not found: {report_dir}", file=sys.stderr)
        sys.exit(1)

    total_failures = 0
    total_runs = 0
    by_section = []

    for log_file in sorted(report_dir.glob("*.log")):
        section = log_file.stem
        runs = parse_log_file(log_file)
        failures = [r for r in runs if r["exit_code"] != 0]
        total_runs += len(runs)
        total_failures += len(failures)
        by_section.append((section, runs, failures))

    print("=" * 80)
    print("RAPS Sample Run — Actual CLI Failures (from log analysis)")
    print("=" * 80)
    print(f"Report dir: {report_dir}")
    print(f"Total command runs: {total_runs}")
    print(f"Actual CLI failures (exit != 0): {total_failures}")
    if total_runs:
        pct = 100 * (total_runs - total_failures) / total_runs
        print(f"Actual pass rate: {pct:.1f}%")
    print()

    for section, runs, failures in by_section:
        if not failures:
            continue
        print(f"\n--- {section} ({len(failures)}/{len(runs)} failed) ---")
        for r in failures:
            status = "TIMEOUT" if r["timed_out"] else f"exit {r['exit_code']}"
            print(f"  [{r['sr_id']}] {r['slug']}: {status}")
            print(f"    cmd: {r['command'][:80]}{'...' if len(r['command'])>80 else ''}")
            if r["stderr_preview"]:
                print(f"    stderr: {r['stderr_preview'][:120]}...")
            print()

    if total_failures == 0:
        print("\nNo actual CLI failures found in logs.")
    else:
        print("\n" + "=" * 80)
        print("NOTE: Tests may still PASS because many use may_fail=True, which suppresses")
        print("assertions on CLI failures. Check test files for may_fail usage.")
        print("=" * 80)


if __name__ == "__main__":
    main()
