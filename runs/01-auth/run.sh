#!/bin/bash
# Section 01 — Authentication
# Runs: SR-010 through SR-024
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "01-auth" "Authentication"

# ── Atomic commands ──────────────────────────────────────────────

# SR-010: Test 2-legged auth (client credentials)
run_sample "SR-010" "auth-test-2leg" \
  "raps auth test" \
  "Expected: 2-legged token obtained successfully" \
  "Review: Exit code 0; output confirms valid credentials"

# SR-011: Interactive 3-legged login (browser-based)
run_sample "SR-011" "auth-login-3leg-browser" \
  "raps auth login" \
  "Expected: Browser opens for OAuth consent; token stored" \
  "Review: Exit code 0; callback received; token persisted"

# SR-012: Device code flow login
run_sample "SR-012" "auth-login-device-code" \
  "raps auth login --device-code" \
  "Expected: Device code displayed; user authorizes in browser" \
  "Review: Exit code 0; token stored after device authorization"

# SR-013: Direct token injection
run_sample "SR-013" "auth-login-token-direct" \
  "raps auth login --token \"eyJ...\"" \
  "Expected: Provided token stored directly" \
  "Review: Exit code 0; token persisted without exchange"

# SR-014: Refresh token login with explicit expiry
run_sample "SR-014" "auth-login-refresh-token" \
  "raps auth login --refresh-token \"rt_...\" --expires-in 3600" \
  "Expected: Refresh token exchanged for access token" \
  "Review: Exit code 0; access token valid for 3600s"

# SR-015: Check auth status
run_sample "SR-015" "auth-status" \
  "raps auth status" \
  "Expected: Current auth state displayed" \
  "Review: Shows token type, expiry, and profile"

# SR-016: Display authenticated user identity
run_sample "SR-016" "auth-whoami" \
  "raps auth whoami" \
  "Expected: User identity information returned" \
  "Review: Shows user ID, email, and name"

# SR-017: Inspect token details
run_sample "SR-017" "auth-inspect" \
  "raps auth inspect" \
  "Expected: Token claims and metadata shown" \
  "Review: Displays scopes, issuer, expiry timestamp"

# SR-018: Inspect token with expiry warning threshold
run_sample "SR-018" "auth-inspect-warn" \
  "raps auth inspect --warn-expiry-seconds 7200" \
  "Expected: Token inspected with 2-hour warning threshold" \
  "Review: Warning emitted if token expires within 7200s"

# SR-019: Logout and clear stored token
run_sample "SR-019" "auth-logout" \
  "raps auth logout" \
  "Expected: Stored token removed" \
  "Review: Exit code 0; subsequent auth commands require re-login"

# SR-020: Login using default profile
run_sample "SR-020" "auth-login-default-profile" \
  "raps auth login --default" \
  "Expected: Login using default profile credentials" \
  "Review: Exit code 0; default profile activated"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-021: Full 2-legged auth cycle
lifecycle_start "SR-021" "auth-lifecycle-2leg" "Full 2-legged auth cycle"
lifecycle_step 1 "raps auth test"
lifecycle_step 2 "raps auth status"
lifecycle_step 3 "raps auth inspect"
lifecycle_step 4 "raps auth logout"
lifecycle_step 5 "raps auth test"
lifecycle_end

# SR-022: Full 3-legged auth cycle
lifecycle_start "SR-022" "auth-lifecycle-3leg" "Full 3-legged auth cycle"
lifecycle_step 1 "raps auth login"
lifecycle_step 2 "raps auth whoami"
lifecycle_step 3 "raps auth status"
lifecycle_step 4 "raps auth inspect --warn-expiry-seconds 86400"
lifecycle_step 5 "raps auth logout"
lifecycle_end

# SR-023: Device code auth cycle
lifecycle_start "SR-023" "auth-lifecycle-device" "Device code auth cycle"
lifecycle_step 1 "raps auth login --device-code"
lifecycle_step 2 "raps auth test"
lifecycle_step 3 "raps auth whoami"
lifecycle_step 4 "raps auth logout"
lifecycle_end

# SR-024: Token injection cycle
lifecycle_start "SR-024" "auth-lifecycle-token-injection" "Token injection cycle"
lifecycle_step 1 "raps auth login --token \"\$EXTERNAL_TOKEN\" --expires-in 1800"
lifecycle_step 2 "raps auth test"
lifecycle_step 3 "raps auth inspect"
lifecycle_step 4 "raps auth logout"
lifecycle_end

section_end
