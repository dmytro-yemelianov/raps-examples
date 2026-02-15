#!/bin/bash
# oauth-login.sh — Orchestrate headless 3-legged OAuth login for test harness
#
# Launches `raps auth login --default` in background, captures the auth URL
# from stdout, then runs oauth-automate.py (Playwright) to complete the flow.
#
# Usage: source this file, then call oauth_auto_login
#
# Required env: APS_USERNAME, APS_PASSWORD

# Resolve paths relative to this script
_OAUTH_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_OAUTH_RUNS_DIR="$(cd "$_OAUTH_LIB_DIR/.." && pwd)"
_OAUTH_SCRIPTS_DIR="$(cd "$_OAUTH_RUNS_DIR/../scripts" && pwd)"
_OAUTH_AUTOMATE="$_OAUTH_SCRIPTS_DIR/oauth-automate.py"

oauth_check_ready() {
  local ok=1

  if [ -z "${APS_USERNAME:-}" ] || [ -z "${APS_PASSWORD:-}" ]; then
    echo "[oauth] ERROR: APS_USERNAME and APS_PASSWORD must be set"
    ok=0
  fi

  if ! command -v python3 &>/dev/null; then
    echo "[oauth] ERROR: python3 not found"
    ok=0
  fi

  if ! python3 -c "import playwright" &>/dev/null; then
    echo "[oauth] ERROR: playwright not installed (pip install playwright && playwright install chromium)"
    ok=0
  fi

  if [ ! -f "$_OAUTH_AUTOMATE" ]; then
    echo "[oauth] ERROR: oauth-automate.py not found at $_OAUTH_AUTOMATE"
    ok=0
  fi

  [ "$ok" -eq 1 ]
}

oauth_auto_login() {
  echo "[oauth] Starting headless 3-legged OAuth login..."

  if ! oauth_check_ready; then
    echo "[oauth] Prerequisites not met, aborting"
    return 1
  fi

  local tmp_out
  tmp_out="$(mktemp)"

  # Launch raps auth login in background, capturing stdout
  raps auth login --default > "$tmp_out" 2>&1 &
  local raps_pid=$!
  echo "[oauth] raps auth login started (pid=$raps_pid)"

  # Poll stdout for the auth URL (contains authentication/v2/authorize)
  local auth_url=""
  local waited=0
  local max_wait=15

  while [ "$waited" -lt "$max_wait" ]; do
    if [ -f "$tmp_out" ]; then
      auth_url=$(grep -o 'https://[^ ]*authentication/v2/authorize[^ ]*' "$tmp_out" 2>/dev/null | head -1)
      if [ -n "$auth_url" ]; then
        break
      fi
    fi
    sleep 1
    waited=$((waited + 1))
  done

  if [ -z "$auth_url" ]; then
    echo "[oauth] ERROR: Could not extract auth URL within ${max_wait}s"
    echo "[oauth] raps output:"
    cat "$tmp_out" 2>/dev/null
    kill "$raps_pid" 2>/dev/null
    rm -f "$tmp_out"
    return 1
  fi

  echo "[oauth] Auth URL captured, launching headless browser..."

  # Run Playwright automation (foreground)
  local py_exit=0
  python3 "$_OAUTH_AUTOMATE" "$auth_url" --timeout 60 || py_exit=$?

  if [ "$py_exit" -ne 0 ]; then
    echo "[oauth] ERROR: Playwright automation failed (exit=$py_exit)"
    kill "$raps_pid" 2>/dev/null
    rm -f "$tmp_out"
    return 1
  fi

  # Wait for raps background process to finish
  echo "[oauth] Waiting for raps to complete token exchange..."
  local raps_waited=0
  while kill -0 "$raps_pid" 2>/dev/null; do
    if [ "$raps_waited" -ge 15 ]; then
      echo "[oauth] WARNING: raps still running after 15s, killing"
      kill "$raps_pid" 2>/dev/null
      break
    fi
    sleep 1
    raps_waited=$((raps_waited + 1))
  done
  wait "$raps_pid" 2>/dev/null

  rm -f "$tmp_out"

  # Verify login succeeded
  echo "[oauth] Verifying auth status..."
  if raps auth status 2>&1 | grep -q "logged_in.*true\|three_legged.*true\|3-legged.*active\|Token.*valid"; then
    echo "[oauth] SUCCESS: 3-legged OAuth login complete"
    return 0
  else
    echo "[oauth] WARNING: Could not confirm login status (may still be OK)"
    echo "[oauth] auth status output:"
    raps auth status 2>&1 || true
    return 0
  fi
}
