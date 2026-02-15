#!/bin/bash
# Section 08 — ACC RFIs
# Runs: SR-150 through SR-155
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "08-acc-rfi" "ACC RFIs"

# --- Pre-seed demo environment variables (override with real values) ---
: "${PROJECT_ID:=b.demo-project-001}"
: "${RFI_ID:=rfi-demo-001}"
: "${ID:=rfi-demo-001}"
: "${USER_ID:=demo-user-001}"
: "${STRUCT_ENG:=demo-struct-eng-001}"

# ── RFI atomics ──────────────────────────────────────────────────

# SR-150: List RFIs
run_sample "SR-150" "rfi-list" \
  "raps rfi list \$PROJECT_ID" \
  "Expected: Lists RFIs" \
  "Review: Contains numbers, titles, statuses"

# SR-151: Create an RFI
run_sample "SR-151" "rfi-create" \
  "raps rfi create \$PROJECT_ID --title \"Clarification on MEP routing at Level 3\" --question \"Conflict between HVAC duct and structural beam at grid C-4\"" \
  "Expected: Creates RFI" \
  "Review: Exit 0; contains RFI ID"

# SR-152: Get RFI details
run_sample "SR-152" "rfi-get" \
  "raps rfi get \$PROJECT_ID \$RFI_ID" \
  "Expected: Shows details" \
  "Review: Contains title, status, dates"

# SR-153: Update an RFI
run_sample "SR-153" "rfi-update" \
  "raps rfi update \$PROJECT_ID \$RFI_ID --assigned-to \$USER_ID --priority \"high\"" \
  "Expected: Updates RFI" \
  "Review: Exit 0"

# SR-154: Delete an RFI
run_sample "SR-154" "rfi-delete" \
  "raps rfi delete \$PROJECT_ID \$RFI_ID --yes" \
  "Expected: Deletes RFI" \
  "Review: Exit 0"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-155: Architect raises and resolves an RFI
lifecycle_start "SR-155" "rfi-full-lifecycle" "Architect raises and resolves an RFI"
lifecycle_step 1 "raps rfi create \$PROJECT_ID --title \"Beam depth at grid D-7\""
lifecycle_step 2 "raps rfi list \$PROJECT_ID"
lifecycle_step 3 "raps rfi get \$PROJECT_ID \$ID"
lifecycle_step 4 "raps rfi update \$PROJECT_ID \$ID --assigned-to \$STRUCT_ENG --priority \"high\""
lifecycle_step 5 "raps rfi update \$PROJECT_ID \$ID --status \"answered\" --answer \"Use W14x30, see SK-204\""
lifecycle_step 6 "raps rfi get \$PROJECT_ID \$ID"
lifecycle_step 7 "raps rfi delete \$PROJECT_ID \$ID --yes"
lifecycle_end

section_end
