#!/bin/bash
# Section 02 — Configuration
# Runs: SR-030 through SR-045
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "02-config" "Configuration"

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

# SR-032: Set a config value
run_sample "SR-032" "config-set" \
  "raps config set output_format json" \
  "Expected: output_format updated to json" \
  "Review: Exit code 0; subsequent config show reflects change"

# SR-033: Create a new profile
run_sample "SR-033" "config-profile-create" \
  "raps config profile create staging" \
  "Expected: Profile 'staging' created" \
  "Review: Exit code 0; profile appears in profile list"

# SR-034: List all profiles
run_sample "SR-034" "config-profile-list" \
  "raps config profile list" \
  "Expected: All profiles listed" \
  "Review: Shows default and staging profiles"

# SR-035: Switch to a profile
run_sample "SR-035" "config-profile-use" \
  "raps config profile use staging" \
  "Expected: Active profile switched to staging" \
  "Review: Exit code 0; profile current shows staging"

# SR-036: Show current active profile
run_sample "SR-036" "config-profile-current" \
  "raps config profile current" \
  "Expected: Current profile name printed" \
  "Review: Output shows 'staging'"

# SR-037: Export a profile to JSON
# NOTE: raps bug - clap output flag conflict, exit 101 expected
run_sample "SR-037" "config-profile-export" \
  "raps config profile export -n staging" \
  "Expected: Profile exported as JSON" \
  "Review: Valid JSON output with profile settings"

# SR-038: Import a profile from JSON file
run_sample "SR-038" "config-profile-import" \
  "raps config profile import ./staging-profile.json" \
  "Expected: Profile imported from file" \
  "Review: Exit code 0; imported profile appears in list"

# SR-039: Diff two profiles
run_sample "SR-039" "config-profile-diff" \
  "raps config profile diff default staging" \
  "Expected: Differences between profiles displayed" \
  "Review: Shows changed keys with old/new values"

# SR-040: Delete a profile
run_sample "SR-040" "config-profile-delete" \
  "raps config profile delete staging" \
  "Expected: Profile 'staging' removed" \
  "Review: Exit code 0; profile no longer in list"

# SR-041: Show current context
run_sample "SR-041" "config-context-show" \
  "raps config context show" \
  "Expected: Active hub/project context displayed" \
  "Review: Shows hub ID and project ID (or empty if unset)"

# SR-042: Set context to specific hub and project
run_sample "SR-042" "config-context-set" \
  "raps config context set hub_id \$HUB_ID && raps config context set project_id \$PROJECT_ID" \
  "Expected: Context bound to specified hub and project" \
  "Review: Exit code 0; context show reflects new values"

# SR-043: Clear context
run_sample "SR-043" "config-context-clear" \
  "raps config context clear" \
  "Expected: Context cleared" \
  "Review: Exit code 0; context show returns empty"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-044: Full profile CRUD lifecycle
lifecycle_start "SR-044" "config-profile-lifecycle" "Full profile CRUD"
lifecycle_step 1  "raps config profile create test-profile"
lifecycle_step 2  "raps config profile list"
lifecycle_step 3  "raps config profile use test-profile"
lifecycle_step 4  "raps config profile current"
lifecycle_step 5  "raps config set output_format yaml"
lifecycle_step 6  "raps config profile export -n test-profile"  # NOTE: raps bug - clap output flag conflict, exit 101 expected
lifecycle_step 7  "raps config profile diff default test-profile"
lifecycle_step 8  "raps config profile use default"
lifecycle_step 9  "raps config profile delete test-profile"
lifecycle_step 10 "raps config profile list"
lifecycle_end

# SR-045: Context set and clear lifecycle
lifecycle_start "SR-045" "config-context-lifecycle" "Context set and clear"
lifecycle_step 1 "raps config context clear"
lifecycle_step 2 "raps config context show"
lifecycle_step 3 "raps config context set hub_id \$HUB_ID && raps config context set project_id \$PROJECT_ID"
lifecycle_step 4 "raps config context show"
lifecycle_step 5 "raps hub list"
lifecycle_step 6 "raps config context clear"
lifecycle_step 7 "raps config context show"
lifecycle_end

section_end
