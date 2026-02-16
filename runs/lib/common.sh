#!/bin/bash
# common.sh — Shared helpers for sample run scripts (Bash/Linux)
#
# Provides: section_start, section_end, run_sample, lifecycle_start,
#           lifecycle_step, lifecycle_end, logging, mock-aware command routing
#
# Usage: source "$SCRIPT_DIR/../lib/common.sh"

set -euo pipefail

# --- OAuth automation (optional) ---
source "$(dirname "${BASH_SOURCE[0]}")/oauth-login.sh" 2>/dev/null || true

# --- Auto-discover real IDs (hubs, projects, accounts) ---
source "$(dirname "${BASH_SOURCE[0]}")/discover-ids.sh" 2>/dev/null || true

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
SECTION_SKIP_COUNT=0
LIFECYCLE_ID=""
LIFECYCLE_STEP_NUM=0

# --- Auth state (cached, checked once) ---
_AUTH_2LEG=""
_AUTH_3LEG=""

has_2leg_auth() {
  if [ -z "$_AUTH_2LEG" ]; then
    if [ "$RAPS_TARGET" = "mock" ]; then
      _AUTH_2LEG=yes
    elif raps auth test --quiet 2>/dev/null; then
      _AUTH_2LEG=yes
    else
      _AUTH_2LEG=no
    fi
  fi
  [ "$_AUTH_2LEG" = "yes" ]
}

has_3leg_auth() {
  if [ -z "$_AUTH_3LEG" ]; then
    if [ "$RAPS_TARGET" = "mock" ]; then
      _AUTH_3LEG=yes
    elif raps auth status --quiet 2>/dev/null | grep -q '"logged_in": true\|logged_in.*true'; then
      _AUTH_3LEG=yes
    else
      _AUTH_3LEG=no
    fi
  fi
  [ "$_AUTH_3LEG" = "yes" ]
}

# Guard: call at top of section. If auth missing, logs skip and returns 1.
require_2leg_auth() {
  if ! has_2leg_auth; then
    log_line "  ${YELLOW}SKIPPED: 2-legged auth not available${RESET}"
    return 1
  fi
}

require_3leg_auth() {
  if ! has_3leg_auth; then
    log_line "  ${YELLOW}SKIPPED: 3-legged auth not available (run: raps auth login --default)${RESET}"
    return 1
  fi
}

# Save 3-legged token so it can be restored after destructive auth operations.
# Reads raw token from Windows Credential Manager via PowerShell (Rust keyring stores UTF-16).
# Exported so child processes (bash sub-scripts) also see it.
save_auth() {
  export _RAPS_SAVED_3LEG_TOKEN
  local script_dir
  script_dir="$(dirname "${BASH_SOURCE[0]}")"
  _RAPS_SAVED_3LEG_TOKEN=$(powershell -ExecutionPolicy Bypass -File "$(win_path "$script_dir/read-token.ps1")" 2>/dev/null || echo "")
}

# Restore auth after destructive operations (logout).
# Re-verifies 2-leg (always available with env vars) and restores saved 3-leg token.
restore_auth() {
  _AUTH_2LEG=""
  _AUTH_3LEG=""
  # 2-leg always works if env vars are set
  has_2leg_auth || true
  # Restore saved 3-leg token if available
  if [ -n "${_RAPS_SAVED_3LEG_TOKEN:-}" ]; then
    raps auth login --token "$_RAPS_SAVED_3LEG_TOKEN" &>/dev/null || true
    _AUTH_3LEG=""
    has_3leg_auth || true
    return
  fi
  # Fallback: try oauth_auto_login
  if type oauth_auto_login &>/dev/null; then
    oauth_auto_login 2>/dev/null || true
    _AUTH_3LEG=""
    has_3leg_auth || true
  fi
}

# Clear cached 3-leg auth state so it gets re-checked on next use.
recheck_3leg_auth() {
  _AUTH_3LEG=""
}

# --- Colors (disabled if NO_COLOR set) ---
if [ -z "${NO_COLOR:-}" ]; then
  GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[0;33m'
  CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
else
  GREEN=''; RED=''; YELLOW=''; CYAN=''; BOLD=''; RESET=''
fi

# --- Helpers ---

# Convert Git Bash /c/ paths to C:/ for python3 on Windows
win_path() {
  local p="$1"
  if [[ "$p" =~ ^/([a-zA-Z])/ ]]; then
    echo "${BASH_REMATCH[1]^}:/${p:3}"
  else
    echo "$p"
  fi
}

# Per-command timeout (seconds); 0 = no timeout
RAPS_CMD_TIMEOUT="${RAPS_CMD_TIMEOUT:-30}"

raps_cmd() {
  local cmd="$1"
  if [ "$RAPS_TARGET" = "mock" ]; then
    echo "$cmd --base-url $MOCK_BASE_URL"
  else
    echo "$cmd"
  fi
}

# Run a command with timeout; sets _CMD_EXIT to exit code
# Uses eval (to preserve shell variables) in a subshell with a watchdog timer.
run_with_timeout() {
  local cmd="$1" logfile="$2"
  local timeout_sec="${RAPS_CMD_TIMEOUT:-0}"

  if [ "$timeout_sec" -gt 0 ] 2>/dev/null; then
    # Run eval in a subshell in the background so we can enforce a timeout
    ( eval "$cmd" ) >> "$logfile" 2>&1 &
    local pid=$!
    local waited=0
    while kill -0 "$pid" 2>/dev/null; do
      if [ "$waited" -ge "$timeout_sec" ]; then
        kill "$pid" 2>/dev/null
        wait "$pid" 2>/dev/null
        echo "  TIMEOUT after ${timeout_sec}s" >> "$logfile"
        _CMD_EXIT=124
        return
      fi
      sleep 1
      waited=$((waited + 1))
    done
    wait "$pid"
    _CMD_EXIT=$?
  else
    eval "$cmd" >> "$logfile" 2>&1
    _CMD_EXIT=$?
  fi
}

log_line() {
  local msg="$1"
  echo -e "$msg" | tee -a "$CURRENT_SECTION_LOG"
}

_JSON_SECTION_NAME=""
_JSON_SECTION_TITLE=""
_JSON_TIMESTAMP=""
_JSON_RUNS=()

json_init() {
  local name="$1" title="$2"
  _JSON_SECTION_NAME="$name"
  _JSON_SECTION_TITLE="$title"
  _JSON_TIMESTAMP="$(date -Iseconds)"
  _JSON_RUNS=()
}

json_append_run() {
  local id="$1" slug="$2" command="$3" exit_code="$4" duration="$5"
  # Escape backslashes, double quotes, and control characters for JSON
  local escaped_cmd
  escaped_cmd=$(printf '%s' "$command" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g')
  local escaped_slug
  escaped_slug=$(printf '%s' "$slug" | sed 's/\\/\\\\/g; s/"/\\"/g')
  _JSON_RUNS+=("$(printf '    {\n      "id": "%s",\n      "slug": "%s",\n      "command": "%s",\n      "exit_code": %s,\n      "duration_seconds": %s,\n      "target": "%s"\n    }' \
    "$id" "$escaped_slug" "$escaped_cmd" "$exit_code" "$duration" "$RAPS_TARGET")")
}

# Write accumulated JSON runs to disk. Called at start of section_end().
json_finalize() {
  {
    printf '{\n  "section": "%s",\n  "title": "%s",\n  "target": "%s",\n  "timestamp": "%s",\n  "runs": [\n' \
      "$_JSON_SECTION_NAME" "$_JSON_SECTION_TITLE" "$RAPS_TARGET" "$_JSON_TIMESTAMP"
    local i
    for (( i=0; i<${#_JSON_RUNS[@]}; i++ )); do
      if (( i > 0 )); then
        printf ',\n'
      fi
      printf '%s' "${_JSON_RUNS[$i]}"
    done
    printf '\n  ]\n}\n'
  } > "$CURRENT_SECTION_JSON"
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
  SECTION_SKIP_COUNT=0

  json_init "$name" "$title"

  log_line ""
  log_line "${BOLD}========================================${RESET}"
  log_line "${BOLD}  $title${RESET}"
  log_line "${BOLD}  Target: $RAPS_TARGET${RESET}"
  log_line "${BOLD}========================================${RESET}"
  log_line ""
}

section_end() {
  json_finalize
  log_line ""
  log_line "----------------------------------------"
  local summary="$SECTION_RUN_COUNT runs ($SECTION_OK_COUNT ok, $SECTION_FAIL_COUNT fail"
  if [ "$SECTION_SKIP_COUNT" -gt 0 ]; then
    summary="$summary, $SECTION_SKIP_COUNT skip"
  fi
  summary="$summary)"
  log_line "Section $CURRENT_SECTION: $summary"
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
  run_with_timeout "$actual_cmd" "$CURRENT_SECTION_LOG"
  exit_code=$_CMD_EXIT
  set -e

  local end_time
  end_time=$(date +%s.%N 2>/dev/null || date +%s)
  duration=$(awk "BEGIN {printf \"%.2f\", $end_time - $start_time}" 2>/dev/null || echo "0")

  if [ "$exit_code" -eq 0 ]; then
    log_line "  ${GREEN}Exit: $exit_code (${duration}s)${RESET}"
    SECTION_OK_COUNT=$((SECTION_OK_COUNT + 1))
  elif [ "$exit_code" -eq 124 ]; then
    log_line "  ${RED}TIMEOUT (${RAPS_CMD_TIMEOUT}s)${RESET}"
    SECTION_FAIL_COUNT=$((SECTION_FAIL_COUNT + 1))
  else
    log_line "  ${RED}Exit: $exit_code (${duration}s)${RESET}"
    SECTION_FAIL_COUNT=$((SECTION_FAIL_COUNT + 1))
  fi
  log_line ""

  json_append_run "$id" "$slug" "$actual_cmd" "$exit_code" "$duration"
}

# Skip a sample (counted as skip, not fail)
skip_sample() {
  local id="$1" slug="$2" reason="${3:-skipped}"
  SECTION_RUN_COUNT=$((SECTION_RUN_COUNT + 1))
  SECTION_SKIP_COUNT=$((SECTION_SKIP_COUNT + 1))
  log_line "${CYAN}[$id]${RESET} $slug"
  log_line "  ${YELLOW}SKIP: $reason${RESET}"
  log_line ""
  json_append_run "$id" "$slug" "(skipped: $reason)" "0" "0"
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
  run_with_timeout "$actual_cmd" "$CURRENT_SECTION_LOG"
  local exit_code=$_CMD_EXIT
  set -e

  if [ "$exit_code" -eq 0 ]; then
    log_line "    ${GREEN}-> exit $exit_code${RESET}"
  elif [ "$exit_code" -eq 124 ]; then
    log_line "    ${RED}-> TIMEOUT${RESET}"
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
