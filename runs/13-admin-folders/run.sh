#!/bin/bash
# Section 13 — Admin: Folder Permissions & Operations
# Runs: SR-220 through SR-228
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "13-admin-folders" "Admin: Folder Permissions & Operations"
require_3leg_auth || { section_end; exit 0; }

# --- Pre-seed demo environment variables (override with real values) ---
: "${ACCT:=${RAPS_ACCOUNT_ID:-demo-account-001}}"
: "${OPERATION_ID:=12345678-1234-1234-1234-123456789012}"
: "${OP_ID:=12345678-1234-1234-1234-123456789012}"
: "${OP2_ID:=12345678-1234-1234-1234-123456789013}"
: "${PID:=${RAPS_PROJECT_ID:-demo-project-001}}"

# ── Atomic commands ──────────────────────────────────────────────

# SR-220: Grant folder rights dry-run
run_sample "SR-220" "admin-folder-rights-dryrun" \
  "raps admin folder rights $TEST_USER -a $ACCT -l view-download-upload --folder \"Plans\" -f \"name:*Tower*\" --dry-run || true" \
  "Expected: Shows which projects and folders would be affected" \
  "Review: Lists matched projects; no actual changes"

# SR-221: Grant folder rights execute
run_sample "SR-221" "admin-folder-rights-execute" \
  "raps admin folder rights $TEST_USER -a $ACCT -l view-download-upload --folder \"Plans\" -f \"name:*Tower*\" -y || true" \
  "Expected: Grants folder permissions across matching projects" \
  "Review: Exit 0; permissions applied"

# SR-222: Grant folder rights from project-ids file
run_sample "SR-222" "admin-folder-rights-from-file" \
  "raps admin folder rights $TEST_USER -a $ACCT -l folder-control --project-ids ./projects.txt -y || true" \
  "Expected: Grants folder permissions to projects in file" \
  "Review: Exit 0; permissions applied to each project"

# SR-223: List companies in account
run_sample "SR-223" "admin-company-list" \
  "raps admin company-list -a $ACCT || true" \
  "Expected: Lists all companies in the account" \
  "Review: Contains company names and IDs"

# SR-224: List completed operations
run_sample "SR-224" "admin-operation-list" \
  "raps admin operation list --status completed --limit 5 || true" \
  "Expected: Lists recent completed operations" \
  "Review: Contains operation IDs and statuses"

# SR-225: Check operation status
run_sample "SR-225" "admin-operation-status" \
  "raps admin operation status $OPERATION_ID || true" \
  "Expected: Shows detailed operation status" \
  "Review: Contains progress, affected items, and timing"

# SR-226: Resume a paused operation
run_sample "SR-226" "admin-operation-resume" \
  "raps admin operation resume $OPERATION_ID --concurrency 3 || true" \
  "Expected: Resumes the operation with specified concurrency" \
  "Review: Exit 0; operation status changes to running"

# SR-227: Cancel an operation
run_sample "SR-227" "admin-operation-cancel" \
  "raps admin operation cancel $OPERATION_ID -y || true" \
  "Expected: Cancels the operation" \
  "Review: Exit 0; operation status is cancelled"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-228: Grant, verify, restrict folder access
lifecycle_start "SR-228" "folder-permissions-lifecycle" "Grant, verify, restrict folder access"
lifecycle_step 1 "raps admin folder rights $TEST_USER_FOLDER -a $ACCT -l view-download-upload-edit --folder \"Plans\" -f \"name:*Active*\" --dry-run"
lifecycle_step 2 "raps admin folder rights $TEST_USER_FOLDER -a $ACCT -l view-download-upload-edit --folder \"Plans\" -f \"name:*Active*\" -y"
lifecycle_step 3 "raps admin operation list --limit 1"
lifecycle_step 4 "raps admin operation status $OP_ID"
lifecycle_step 5 "raps admin folder rights $TEST_USER_FOLDER -a $ACCT -l view-only --folder \"Plans\" -f \"name:*Active*\" -y"
lifecycle_step 6 "raps admin operation status $OP2_ID"
lifecycle_end

section_end
