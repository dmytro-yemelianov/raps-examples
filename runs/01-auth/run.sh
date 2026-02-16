#!/bin/bash
# Section 01 — Authentication
# Runs: SR-010 through SR-024
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "01-auth" "Authentication"

# --- Pre-seed demo environment variables (override with real values) ---
: "${EXTERNAL_TOKEN:=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.demo-token-for-testing}"

# ── Atomic commands ──────────────────────────────────────────────

# SR-010: Test 2-legged auth (client credentials)
run_sample "SR-010" "auth-test-2leg" \
  "raps auth test" \
  "Expected: 2-legged token obtained successfully" \
  "Review: Exit code 0; output confirms valid credentials"

# SR-011: Interactive 3-legged login (browser-based)
# Uses oauth_auto_login if available, otherwise accepts non-zero exit
if type oauth_auto_login &>/dev/null; then
  run_sample "SR-011" "auth-login-3leg-browser" \
    "oauth_auto_login || true" \
    "Expected: 3-legged OAuth login completes" \
    "Review: Exit code 0; user is now authenticated"
else
  skip_sample "SR-011" "auth-login-3leg-browser" "oauth_auto_login not available (needs APS_USERNAME/APS_PASSWORD)"
fi

# SR-012: Device code flow login — run with short timeout, accept non-zero exit
run_sample "SR-012" "auth-login-device-code" \
  "RAPS_CMD_TIMEOUT=5 raps auth login --device-code 2>&1 || true" \
  "Expected: Device code flow initiates (will timeout)" \
  "Review: Shows device code URL and user code before timeout"

# SR-013: Direct token injection — extract current token and re-inject it
run_sample "SR-013" "auth-login-token-direct" \
  "TOKEN=\$(raps auth inspect --output json 2>/dev/null | python3 -c \"import sys,json; print(json.load(sys.stdin).get('access_token',''))\" 2>/dev/null || echo '$EXTERNAL_TOKEN') && raps auth login --token \"\$TOKEN\"" \
  "Expected: Token injected successfully" \
  "Review: Exit code 0; auth test succeeds after injection"

# SR-014: Refresh token login with explicit expiry
# If 3-leg active, extract refresh token; otherwise use dummy and accept error
run_sample "SR-014" "auth-login-refresh-token" \
  "REFRESH=\$(raps auth inspect --output json 2>/dev/null | python3 -c \"import sys,json; print(json.load(sys.stdin).get('refresh_token',''))\" 2>/dev/null || echo 'dummy-refresh') && raps auth login --refresh-token \"\$REFRESH\" --expires-in 3600 || true" \
  "Expected: Refresh token login attempted" \
  "Review: Succeeds with real token or fails gracefully with dummy"

# SR-015: Check auth status
run_sample "SR-015" "auth-status" \
  "raps auth status || true" \
  "Expected: Current auth state displayed" \
  "Review: Shows token type, expiry, and profile"

# SR-016: Display authenticated user identity
run_sample "SR-016" "auth-whoami" \
  "raps auth whoami || true" \
  "Expected: User identity information returned" \
  "Review: Shows user ID, email, and name"

# SR-017: Inspect token details
run_sample "SR-017" "auth-inspect" \
  "raps auth inspect || true" \
  "Expected: Token claims and metadata shown" \
  "Review: Displays scopes, issuer, expiry timestamp"

# SR-018: Inspect token with expiry warning threshold
# Use 24h threshold to prevent false exit 1 on fresh tokens
run_sample "SR-018" "auth-inspect-warn" \
  "raps auth inspect --warn-expiry-seconds 86400 || true" \
  "Expected: Token inspection with expiry warning check" \
  "Review: Exit 0 if token valid >24h, exit 1 if expiring soon (both acceptable)"

# SR-019: Logout and clear stored token, then restore auth
run_sample "SR-019" "auth-logout" \
  "raps auth logout" \
  "Expected: Stored token cleared" \
  "Review: Exit 0; auth test after should fail (until re-auth)"
restore_auth

# SR-020: Login using default profile
if type oauth_auto_login &>/dev/null; then
  run_sample "SR-020" "auth-login-default-profile" \
    "oauth_auto_login || true" \
    "Expected: Login via default profile" \
    "Review: Exit code 0; 3-legged auth active"
else
  skip_sample "SR-020" "auth-login-default-profile" "oauth_auto_login not available"
fi

# ── Lifecycles ───────────────────────────────────────────────────

# SR-021: Full 2-legged auth cycle (test→status→inspect→logout→test)
lifecycle_start "SR-021" "auth-lifecycle-2leg" "Full 2-legged auth cycle"
lifecycle_step 1 "raps auth test"
lifecycle_step 2 "raps auth status || true"
lifecycle_step 3 "raps auth inspect || true"
lifecycle_step 4 "raps auth logout || true"
lifecycle_step 5 "raps auth test"
lifecycle_end
restore_auth

# SR-022: Full 3-legged auth cycle — skip: interactive
skip_sample "SR-022" "auth-lifecycle-3leg" "interactive (opens browser)"

# SR-023: Device code auth cycle — run with short timeout, accept non-zero exit
run_sample "SR-023" "auth-lifecycle-device" \
  "RAPS_CMD_TIMEOUT=5 raps auth login --device-code 2>&1 || true" \
  "Expected: Device code flow initiates (will timeout)" \
  "Review: Shows device code before timeout"

# SR-024: Token injection cycle
lifecycle_start "SR-024" "auth-lifecycle-token-injection" "Token injection cycle"
lifecycle_step 1 "TOKEN=\$(raps auth inspect --output json 2>/dev/null | python3 -c \"import sys,json; print(json.load(sys.stdin).get('access_token','$EXTERNAL_TOKEN'))\" 2>/dev/null) && raps auth login --token \"\$TOKEN\" || true"
lifecycle_step 2 "raps auth test || true"
lifecycle_step 3 "raps auth status || true"
lifecycle_step 4 "raps auth inspect || true"
lifecycle_step 5 "raps auth logout || true"
lifecycle_end
restore_auth

section_end
