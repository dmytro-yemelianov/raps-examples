#!/bin/bash
# Section 16 — Templates
# Runs: SR-250 through SR-255
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "16-templates" "Templates"
require_3leg_auth || { section_end; exit 0; }

# --- Pre-seed demo environment variables (override with real values) ---
: "${ACCOUNT_ID:=${RAPS_ACCOUNT_ID:-demo-account-001}}"
: "${TEMPLATE_ID:=tpl-demo-001}"
: "${ACCT:=${RAPS_ACCOUNT_ID:-demo-account-001}}"
: "${TPL_ID:=tpl-demo-001}"

# ── Atomic commands ──────────────────────────────────────────────

# SR-250: List templates
run_sample "SR-250" "template-list" \
  "raps template list -a $ACCOUNT_ID || true" \
  "Expected: Lists templates" \
  "Review: Contains template names and IDs"

# SR-251: Create a template
run_sample "SR-251" "template-create" \
  "raps template create -a $ACCOUNT_ID --name \"Standard Building Template\" || true" \
  "Expected: Creates template" \
  "Review: Exit 0; contains template ID"

# SR-252: Get template details
run_sample "SR-252" "template-info" \
  "raps template info $TEMPLATE_ID -a $ACCOUNT_ID || true" \
  "Expected: Shows template details" \
  "Review: Contains name, ID, and configuration"

# SR-253: Update a template
run_sample "SR-253" "template-update" \
  "raps template update $TEMPLATE_ID -a $ACCOUNT_ID --name \"Standard Building Template v2\" || true" \
  "Expected: Updates template" \
  "Review: Exit 0; name changed"

# SR-254: Archive a template
run_sample "SR-254" "template-archive" \
  "raps template archive $TEMPLATE_ID -a $ACCOUNT_ID || true" \
  "Expected: Archives template" \
  "Review: Exit 0; template no longer active"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-255: Admin manages templates
lifecycle_start "SR-255" "template-management-lifecycle" "Admin manages templates"
lifecycle_step 1 "raps template create -a $ACCT --name \"Healthcare Template\"" || true
lifecycle_step 2 "raps template list -a $ACCT" || true
lifecycle_step 3 "raps template info $TPL_ID -a $ACCT" || true
lifecycle_step 4 "raps template update $TPL_ID -a $ACCT --name \"Healthcare Template 2026\"" || true
lifecycle_step 5 "raps template archive $TPL_ID -a $ACCT" || true
lifecycle_step 6 "raps template list -a $ACCT" || true
lifecycle_end

section_end
