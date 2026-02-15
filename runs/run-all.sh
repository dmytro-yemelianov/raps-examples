#!/bin/bash
# run-all.sh — Master orchestrator for all sample run sections
#
# Usage:
#   ./run-all.sh                    # Run all sections against real APS
#   RAPS_TARGET=mock ./run-all.sh   # Run all sections against raps-mock
#   ./run-all.sh 01-auth 03-storage # Run specific sections only
#   ./run-all.sh --auto-login       # Auto-login 3-legged OAuth first (needs APS_USERNAME/APS_PASSWORD)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export RUN_TIMESTAMP="${RUN_TIMESTAMP:-$(date +%Y-%m-%d-%H-%M)}"
export LOGS_ROOT="${LOGS_ROOT:-$SCRIPT_DIR/../logs}"
export RAPS_TARGET="${RAPS_TARGET:-real}"

LOG_DIR="$LOGS_ROOT/$RUN_TIMESTAMP"
mkdir -p "$LOG_DIR"

# --- Optional: headless 3-legged OAuth auto-login ---
if [ "${1:-}" = "--auto-login" ]; then
  shift
  source "$SCRIPT_DIR/lib/oauth-login.sh"
  oauth_auto_login
fi

echo "========================================"
echo "RAPS CLI Sample Runs"
echo "========================================"
echo ""
echo "Target:    $RAPS_TARGET"
echo "Timestamp: $RUN_TIMESTAMP"
echo "Logs:      $LOG_DIR"
echo ""

ALL_SECTIONS=(
  00-setup
  01-auth
  02-config
  03-storage
  04-data-management
  05-model-derivative
  06-design-automation
  07-acc-issues
  08-acc-rfi
  09-acc-modules
  10-webhooks
  11-admin-users
  12-admin-projects
  13-admin-folders
  14-reality-capture
  15-reporting
  16-templates
  17-plugins
  18-pipelines
  19-api-raw
  20-generation
  21-shell-serve
  22-demo
  30-workflows
  99-cross-cutting
)

if [ $# -gt 0 ]; then
  SECTIONS=("$@")
else
  SECTIONS=("${ALL_SECTIONS[@]}")
fi

TOTAL=0
PASSED=0
FAILED=0
SKIPPED=0

for section in "${SECTIONS[@]}"; do
  SECTION_SCRIPT="$SCRIPT_DIR/$section/run.sh"

  if [ -f "$SECTION_SCRIPT" ]; then
    echo "--- Running: $section ---"
    if bash "$SECTION_SCRIPT"; then
      echo "  OK: $section"
      PASSED=$((PASSED + 1))
    else
      echo "  FAIL: $section"
      FAILED=$((FAILED + 1))
    fi
    TOTAL=$((TOTAL + 1))
  else
    echo "  SKIP: $section (no run.sh)"
    SKIPPED=$((SKIPPED + 1))
  fi
done

echo ""
echo "========================================"
echo "Sample Runs Complete"
echo "========================================"
echo "Sections:  $TOTAL run, $PASSED ok, $FAILED fail, $SKIPPED skip"
echo "Logs:      $LOG_DIR"
echo ""
echo "Review:"
echo "  cat $LOG_DIR/<section>.log"
echo "  cat $LOG_DIR/<section>.json | python3 -m json.tool"

if [ "$FAILED" -gt 0 ]; then
  exit 1
fi
