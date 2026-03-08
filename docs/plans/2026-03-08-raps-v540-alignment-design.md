# Design: Align raps-examples to RAPS v5.4.0

**Date:** 2026-03-08
**Status:** Approved

## Context

RAPS reached v5.4.0 with four feature PRs since the last raps-examples update. This document
captures the alignment plan: which new CLI commands need test coverage, where to add them, and
which SR-IDs to assign.

## New commands requiring coverage

| PR | Commands |
|----|----------|
| #232 | `raps logs show/path/clear/follow`, `--log-file` global flag |
| #233 | `raps pipeline diff`, `raps translate timeline`, `raps acc export` |
| #234 | `raps snapshot create/diff/list` |
| #235 | `raps object audit`, `raps object tag set/get/delete/search`, `raps lint` |

`raps config wizard` (PR #234) is intentionally excluded — it requires an interactive TTY and
cannot be driven by subprocess in this framework.

## Approach: Hybrid (atomics + selective lifecycles)

Atomics for every new command. Lifecycle tests only where the feature has a meaningful multi-step
flow:

- `raps object tag`: set → get → search → delete lifecycle
- `raps snapshot`: create → list → diff lifecycle
- `raps logs`: clear → show → path lifecycle

One-shot commands (`raps lint`, `raps acc export`, `raps translate timeline`, `raps pipeline diff`)
get atomic tests only.

## SR-ID assignments (natural per-section ranges)

### test_02_config.py — SR-046–049

| SR-ID | Command | Auth |
|-------|---------|------|
| SR-046 | `raps snapshot create <bucket>` | 2-leg |
| SR-047 | `raps snapshot list` | None |
| SR-048 | `raps snapshot diff <old> <new>` | None |
| SR-049 | snapshot lifecycle (create → list → diff) | 2-leg |

### test_03_storage.py — SR-067–072

| SR-ID | Command | Auth |
|-------|---------|------|
| SR-067 | `raps object audit <bucket>` | 2-leg |
| SR-068 | `raps object tag set <bucket> <key> attr=val` | 2-leg |
| SR-069 | `raps object tag get <bucket> <key>` | 2-leg |
| SR-070 | `raps object tag delete <bucket> <key> <attr>` | 2-leg |
| SR-071 | `raps object tag search <bucket> attr=val` | 2-leg |
| SR-072 | tag lifecycle (set → get → search → delete) | 2-leg |

### test_05_model_derivative.py — SR-102

| SR-ID | Command | Auth |
|-------|---------|------|
| SR-102 | `raps translate timeline <urn>` | 2-leg |

### test_09_acc_modules.py — SR-178

| SR-ID | Command | Auth |
|-------|---------|------|
| SR-178 | `raps acc export <project-id>` | 3-leg |

### test_18_pipelines.py — SR-274

| SR-ID | Command | Auth |
|-------|---------|------|
| SR-274 | `raps pipeline diff <file1> <file2>` | 2-leg |

### tests/test_23_logs.py (new file) — SR-310–313

| SR-ID | Command | Auth |
|-------|---------|------|
| SR-310 | `raps logs path` | None |
| SR-311 | `raps logs show` | None |
| SR-312 | `raps logs clear -y` | None |
| SR-313 | logs lifecycle (clear → show → path) | None |

### test_99_cross_cutting.py — SR-560–561

| SR-ID | Command | Auth |
|-------|---------|------|
| SR-560 | `--log-file` global flag passthrough | None |
| SR-561 | `raps lint` on a sample pipeline YAML | None |

## Delta

+18 tests across 6 modified files + 1 new file. Total: 263 → ~281 tests across 26 sections.

## README updates

- Section table: add row for section 23 (Logs, 4 tests, None)
- Update total test count (263 → 281)
- Update section count (25 → 26)
