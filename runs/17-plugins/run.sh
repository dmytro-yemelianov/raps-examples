#!/bin/bash
# Section 17 — Plugins
# Runs: SR-260 through SR-266
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "17-plugins" "Plugins"

# ── Atomic commands ──────────────────────────────────────────────

# SR-260: List plugins
run_sample "SR-260" "plugin-list" \
  "raps plugin list" \
  "Expected: Lists plugins" \
  "Review: Contains plugin names and statuses"

# SR-261: Enable a plugin
run_sample "SR-261" "plugin-enable" \
  "raps plugin enable my-plugin" \
  "Expected: Enables plugin" \
  "Review: Exit 0; plugin shown as enabled"

# SR-262: Disable a plugin
run_sample "SR-262" "plugin-disable" \
  "raps plugin disable my-plugin" \
  "Expected: Disables plugin" \
  "Review: Exit 0; plugin shown as disabled"

# SR-263: List aliases
run_sample "SR-263" "plugin-alias-list" \
  "raps plugin alias list" \
  "Expected: Lists aliases" \
  "Review: Contains alias names and target commands"

# SR-264: Add an alias
run_sample "SR-264" "plugin-alias-add" \
  "raps plugin alias add \"bl\" \"bucket list\"" \
  "Expected: Creates alias" \
  "Review: Exit 0; alias registered"

# SR-265: Remove an alias
run_sample "SR-265" "plugin-alias-remove" \
  "raps plugin alias remove \"bl\"" \
  "Expected: Removes alias" \
  "Review: Exit 0; alias no longer listed"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-266: Developer sets up aliases
lifecycle_start "SR-266" "alias-power-user-lifecycle" "Developer sets up aliases"
lifecycle_step 1 "raps plugin alias add \"bl\" \"bucket list\""
lifecycle_step 2 "raps plugin alias add \"ol\" \"object list\""
lifecycle_step 3 "raps plugin alias add \"ts\" \"translate status\""
lifecycle_step 4 "raps plugin alias list"
lifecycle_step 5 "raps plugin alias list | grep bl"
lifecycle_step 6 "raps plugin alias remove \"bl\""
lifecycle_step 7 "raps plugin alias list"
lifecycle_end

section_end
