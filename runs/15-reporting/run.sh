#!/bin/bash
# Section 15 — Portfolio Reports
# Runs: SR-240 through SR-244
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "15-reporting" "Portfolio Reports"

# ── Atomic commands ──────────────────────────────────────────────

# SR-240: RFI summary report
run_sample "SR-240" "report-rfi-summary" \
  "raps report rfi-summary -a \$ACCOUNT_ID -f \"Tower\" --status open --since \"2026-01-01\"" \
  "Expected: Aggregated RFI summary" \
  "Review: Per-project RFI counts"

# SR-241: Issues summary report
run_sample "SR-241" "report-issues-summary" \
  "raps report issues-summary -a \$ACCOUNT_ID -f \"Phase 2\" --status open" \
  "Expected: Aggregated issue summary" \
  "Review: Per-project issue counts"

# SR-242: Submittals summary report
run_sample "SR-242" "report-submittals-summary" \
  "raps report submittals-summary -a \$ACCOUNT_ID" \
  "Expected: Submittal summary" \
  "Review: Per-project counts by status"

# SR-243: Checklists summary report
run_sample "SR-243" "report-checklists-summary" \
  "raps report checklists-summary -a \$ACCOUNT_ID --status \"in_progress\"" \
  "Expected: Checklist summary" \
  "Review: Per-project completion stats"

# SR-244: Assets summary report
run_sample "SR-244" "report-assets-summary" \
  "raps report assets-summary -a \$ACCOUNT_ID -f \"Hospital\"" \
  "Expected: Asset summary" \
  "Review: Per-project counts by category"

section_end
