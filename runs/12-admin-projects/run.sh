#!/bin/bash
# Section 12 — Admin: Project Management
# Runs: SR-210 through SR-215
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "12-admin-projects" "Admin: Project Management"

# --- Pre-seed demo environment variables (override with real values) ---
: "${ACCOUNT_ID:=demo-account-001}"
: "${PROJECT_ID:=b.demo-project-001}"
: "${ACCT:=demo-account-001}"
: "${PID:=b.demo-project-001}"

# ── Atomic commands ──────────────────────────────────────────────

# SR-210: List all projects in account
run_sample "SR-210" "admin-project-list" \
  "raps admin project list -a \$ACCOUNT_ID" \
  "Expected: Lists all projects in the account" \
  "Review: Contains project names, IDs, and statuses"

# SR-211: List projects with filters
run_sample "SR-211" "admin-project-list-filtered" \
  "raps admin project list -a \$ACCOUNT_ID -f \"name:*Tower*\" --status active --platform acc --limit 10" \
  "Expected: Filtered project list" \
  "Review: All results match filter, status, and platform"

# SR-212: Create a project
run_sample "SR-212" "admin-project-create" \
  "raps admin project create -a \$ACCOUNT_ID --name \"Tower Phase 3\" -t \"Bridge\" --classification \"Sample\" --start-date \"2026-03-01\" --end-date \"2027-12-31\" --timezone \"America/New_York\"" \
  "Expected: Creates a new project" \
  "Review: Exit 0; output contains project ID and name"

# SR-213: Update a project
run_sample "SR-213" "admin-project-update" \
  "raps admin project update -a \$ACCOUNT_ID -p \$PROJECT_ID --name \"Tower Phase 3 - Revised\" --status active" \
  "Expected: Updates project name and status" \
  "Review: Exit 0; project reflects new name"

# SR-214: Archive a project
run_sample "SR-214" "admin-project-archive" \
  "raps admin project archive -a \$ACCOUNT_ID -p \$PROJECT_ID" \
  "Expected: Archives the project" \
  "Review: Exit 0; project status is archived"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-215: Create and manage project
lifecycle_start "SR-215" "project-lifecycle-admin" "Create and manage project"
lifecycle_step 1 "raps admin project create -a \$ACCT --name \"Bridge Retrofit\" -t \"Bridge\""
lifecycle_step 2 "raps admin project list -a \$ACCT -f \"name:*Bridge*\""
lifecycle_step 3 "raps admin user add pm@company.com -a \$ACCT -r \"project_admin\" -f \"name:*Bridge Retrofit*\" -y"
lifecycle_step 4 "raps admin project update -a \$ACCT -p \$PID --start-date \"2026-04-01\""
lifecycle_step 5 "raps admin project archive -a \$ACCT -p \$PID"
lifecycle_step 6 "raps admin project list -a \$ACCT --status active"
lifecycle_end

section_end
