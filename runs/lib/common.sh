#!/bin/bash
# common.sh — Shared helpers for sample run scripts (Bash/Linux)
#
# Provides: section_start, section_end, run_sample, lifecycle_start,
#           lifecycle_step, lifecycle_end, logging, mock-aware command routing
#
# Usage: source "$SCRIPT_DIR/../lib/common.sh"

set -euo pipefail

# --- Directories ---
RUNS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGS_ROOT="${LOGS_ROOT:-$RUNS_DIR/../logs}"
RUN_TIMESTAMP="${RUN_TIMESTAMP:-$(date +%Y-%m-%d-%H-%M)}"
LOG_DIR="$LOGS_ROOT/$RUN_TIMESTAMP"
mkdir -p "$LOG_DIR"

# --- Target (real or mock) ---
RAPS_TARGET="${RAPS_TARGET:-real}"
MOCK_PORT="${MOCK_PORT:-3000}"
MOCK_BASE_URL="http://localhost:$MOCK_PORT"

# --- State ---
CURRENT_SECTION=""
CURRENT_SECTION_LOG=""
CURRENT_SECTION_JSON=""
SECTION_RUN_COUNT=0
SECTION_OK_COUNT=0
SECTION_FAIL_COUNT=0
LIFECYCLE_ID=""
LIFECYCLE_STEP_NUM=0

# --- Colors (disabled if NO_COLOR set) ---
if [ -z "${NO_COLOR:-}" ]; then
  GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[0;33m'
  CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
else
  GREEN=''; RED=''; YELLOW=''; CYAN=''; BOLD=''; RESET=''
fi

# --- Helpers ---

raps_cmd() {
  local cmd="$1"
  if [ "$RAPS_TARGET" = "mock" ]; then
    echo "$cmd --base-url $MOCK_BASE_URL"
  else
    echo "$cmd"
  fi
}

log_line() {
  local msg="$1"
  echo -e "$msg" | tee -a "$CURRENT_SECTION_LOG"
}

json_init() {
  local name="$1" title="$2"
  cat > "$CURRENT_SECTION_JSON" << EOF
{
  "section": "$name",
  "title": "$title",
  "target": "$RAPS_TARGET",
  "timestamp": "$(date -Iseconds)",
  "runs": []
}
EOF
}

json_append_run() {
  local id="$1" slug="$2" command="$3" exit_code="$4" duration="$5"
  python3 - <<PYEOF
import json, sys
path = "$CURRENT_SECTION_JSON"
with open(path, 'r') as f:
    data = json.load(f)
data['runs'].append({
    'id': '$id',
    'slug': '$slug',
    'command': $(python3 -c "import json; print(json.dumps('$command'))"),
    'exit_code': int('$exit_code'),
    'duration_seconds': float('$duration'),
    'target': '$RAPS_TARGET'
})
with open(path, 'w') as f:
    json.dump(data, f, indent=2)
PYEOF
}

# --- Section ---

section_start() {
  local name="$1" title="$2"
  CURRENT_SECTION="$name"
  CURRENT_SECTION_LOG="$LOG_DIR/${name}.log"
  CURRENT_SECTION_JSON="$LOG_DIR/${name}.json"
  SECTION_RUN_COUNT=0
  SECTION_OK_COUNT=0
  SECTION_FAIL_COUNT=0

  json_init "$name" "$title"

  log_line ""
  log_line "${BOLD}========================================${RESET}"
  log_line "${BOLD}  $title${RESET}"
  log_line "${BOLD}  Target: $RAPS_TARGET${RESET}"
  log_line "${BOLD}========================================${RESET}"
  log_line ""
}

section_end() {
  log_line ""
  log_line "----------------------------------------"
  log_line "Section $CURRENT_SECTION: $SECTION_RUN_COUNT runs ($SECTION_OK_COUNT ok, $SECTION_FAIL_COUNT fail)"
  log_line "Log:  $CURRENT_SECTION_LOG"
  log_line "JSON: $CURRENT_SECTION_JSON"
  log_line ""
}

# --- Run a single sample ---

run_sample() {
  local id="$1" slug="$2" command="$3" expects="$4" review="$5"
  SECTION_RUN_COUNT=$((SECTION_RUN_COUNT + 1))

  local actual_cmd
  actual_cmd="$(raps_cmd "$command")"

  log_line "${CYAN}[$id]${RESET} $slug"
  log_line "  Command:  $actual_cmd"
  log_line "  Expects:  $expects"
  log_line "  Review:   $review"

  local start_time exit_code=0 duration
  start_time=$(date +%s.%N 2>/dev/null || date +%s)

  set +e
  eval "$actual_cmd" >> "$CURRENT_SECTION_LOG" 2>&1
  exit_code=$?
  set -e

  local end_time
  end_time=$(date +%s.%N 2>/dev/null || date +%s)
  duration=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "0")

  if [ "$exit_code" -eq 0 ]; then
    log_line "  ${GREEN}Exit: $exit_code (${duration}s)${RESET}"
    SECTION_OK_COUNT=$((SECTION_OK_COUNT + 1))
  else
    log_line "  ${RED}Exit: $exit_code (${duration}s)${RESET}"
    SECTION_FAIL_COUNT=$((SECTION_FAIL_COUNT + 1))
  fi
  log_line ""

  json_append_run "$id" "$slug" "$actual_cmd" "$exit_code" "$duration"
}

# --- Lifecycle helpers ---

lifecycle_start() {
  local id="$1" slug="$2" desc="$3"
  LIFECYCLE_ID="$id"
  LIFECYCLE_STEP_NUM=0
  log_line "${YELLOW}[$id]${RESET} ${BOLD}Lifecycle: $slug${RESET}"
  log_line "  $desc"
}

lifecycle_step() {
  local step_num="$1" command="$2"
  LIFECYCLE_STEP_NUM=$((LIFECYCLE_STEP_NUM + 1))

  local actual_cmd
  actual_cmd="$(raps_cmd "$command")"

  log_line "  Step $step_num: $actual_cmd"

  set +e
  eval "$actual_cmd" >> "$CURRENT_SECTION_LOG" 2>&1
  local exit_code=$?
  set -e

  if [ "$exit_code" -eq 0 ]; then
    log_line "    ${GREEN}-> exit $exit_code${RESET}"
  else
    log_line "    ${RED}-> exit $exit_code${RESET}"
  fi
}

lifecycle_end() {
  log_line "  Lifecycle $LIFECYCLE_ID complete ($LIFECYCLE_STEP_NUM steps)"
  log_line ""
  LIFECYCLE_ID=""
  LIFECYCLE_STEP_NUM=0
  SECTION_RUN_COUNT=$((SECTION_RUN_COUNT + 1))
  SECTION_OK_COUNT=$((SECTION_OK_COUNT + 1))
}
