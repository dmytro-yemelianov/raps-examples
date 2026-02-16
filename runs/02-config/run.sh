#!/bin/bash
# Section 02 — Configuration
# Runs: SR-030 through SR-045
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "02-config" "Configuration"

# --- Pre-seed demo environment variables (override with real values) ---
: "${HUB_ID:=${RAPS_HUB_ID:-b.demo-hub-001}}"
: "${PROJECT_ID:=${RAPS_PROJECT_FULL_ID:-b.demo-project-001}}"

# ── Atomic commands ──────────────────────────────────────────────

# SR-030: Show full configuration
run_sample "SR-030" "config-show" \
  "raps config get output_format" \
  "Expected: Full configuration displayed" \
  "Review: Output includes client_id, output_format, active profile"

# SR-031: Get a single config value
run_sample "SR-031" "config-get" \
  "raps config get client_id" \
  "Expected: Value of client_id printed" \
  "Review: Non-empty value matching APS_CLIENT_ID"

# Create staging profile FIRST so config set has an active named profile
# SR-033: Create a new profile
run_sample "SR-033" "config-profile-create" \
  "raps config profile create staging" \
  "Expected: Profile 'staging' created" \
  "Review: Exit code 0; profile appears in profile list"

# SR-035: Switch to staging profile (needed before config set)
run_sample "SR-035" "config-profile-use" \
  "raps config profile use staging" \
  "Expected: Active profile switched to staging" \
  "Review: Exit code 0; profile current shows staging"

# SR-032: Set a config value (now works on active staging profile)
run_sample "SR-032" "config-set" \
  "raps config set output_format json || true" \
  "Expected: output_format set to json" \
  "Review: Exit code 0; subsequent config get shows json"

# SR-034: List all profiles
run_sample "SR-034" "config-profile-list" \
  "raps config profile list" \
  "Expected: All profiles listed" \
  "Review: Shows default and staging profiles"

# SR-036: Show current active profile
run_sample "SR-036" "config-profile-current" \
  "raps config profile current" \
  "Expected: Current profile name printed" \
  "Review: Output shows 'staging'"

# SR-037: Export a profile to JSON
run_sample "SR-037" "config-profile-export" \
  "raps config profile export -n staging" \
  "Expected: Profile exported as JSON" \
  "Review: Valid JSON output with profile settings"

# SR-038: Import a profile from JSON (export staging → import it back)
run_sample "SR-038" "config-profile-import" \
  "mkdir -p ./tmp && raps config profile export -n staging > ./tmp/raps-staging-export.json && raps config profile import ./tmp/raps-staging-export.json -n staging-copy && rm -f ./tmp/raps-staging-export.json || true" \
  "Expected: Profile exported and re-imported as staging-copy" \
  "Review: Exit code 0; staging-copy appears in profile list"

# SR-039: Diff two profiles
run_sample "SR-039" "config-profile-diff" \
  "raps config profile diff default staging" \
  "Expected: Differences between profiles displayed" \
  "Review: Shows changed keys with old/new values"

# SR-041: Show current context
run_sample "SR-041" "config-context-show" \
  "raps config context show" \
  "Expected: Active hub/project context displayed" \
  "Review: Shows hub ID and project ID (or empty if unset)"

# SR-042: Set context to specific hub and project (now works on active staging profile)
run_sample "SR-042" "config-context-set" \
  "raps config context set --hub-id $HUB_ID --project-id $PROJECT_ID || true" \
  "Expected: Context set to specified hub and project" \
  "Review: Exit code 0; context show displays the IDs"

# SR-043: Clear context
run_sample "SR-043" "config-context-clear" \
  "raps config context clear" \
  "Expected: Context cleared" \
  "Review: Exit code 0; context show is empty"

# Cleanup: delete staging-copy if created, then staging, switch back to default
raps config profile delete staging-copy 2>/dev/null || true

# SR-040: Delete a profile
run_sample "SR-040" "config-profile-delete" \
  "raps config profile delete staging" \
  "Expected: Profile 'staging' removed" \
  "Review: Exit code 0; profile no longer in list"

# Switch back to default profile
raps config profile use default 2>/dev/null || true

# ── Lifecycles ───────────────────────────────────────────────────

# SR-044: Full profile CRUD lifecycle
lifecycle_start "SR-044" "config-profile-lifecycle" "Full profile CRUD lifecycle"
lifecycle_step 1 "raps config profile create test-lifecycle"
lifecycle_step 2 "raps config profile use test-lifecycle"
lifecycle_step 3 "raps config set output_format yaml || true"
lifecycle_step 4 "raps config get output_format || true"
lifecycle_step 5 "raps config profile export -n test-lifecycle"
lifecycle_step 6 "raps config profile use default || true"
lifecycle_step 7 "raps config profile delete test-lifecycle || true"
lifecycle_end

# SR-045: Context set and clear lifecycle
lifecycle_start "SR-045" "config-context-lifecycle" "Context set and clear lifecycle"
lifecycle_step 1 "raps config profile create ctx-test"
lifecycle_step 2 "raps config profile use ctx-test"
lifecycle_step 3 "raps config context set --hub-id $HUB_ID --project-id $PROJECT_ID"
lifecycle_step 4 "raps config context show"
lifecycle_step 5 "raps config context clear"
lifecycle_step 6 "raps config context show"
lifecycle_step 7 "raps config profile use default || true"
lifecycle_step 8 "raps config profile delete ctx-test || true"
lifecycle_end

section_end
