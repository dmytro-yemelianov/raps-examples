#!/bin/bash
# Section 11 — Admin: Bulk User Management
# Runs: SR-190 through SR-206
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "11-admin-users" "Admin: Bulk User Management"

# --- Pre-seed demo environment variables (override with real values) ---
: "${ACCOUNT_ID:=demo-account-001}"
: "${PROJECT_ID:=b.demo-project-001}"
: "${ROLE_ID:=role-demo-001}"
: "${USER_ID:=demo-user-001}"
: "${NEW_ROLE_ID:=role-demo-002}"
: "${ACCT:=demo-account-001}"
: "${OLD_PROJECT:=b.demo-old-project-001}"

# ── Atomic commands ──────────────────────────────────────────────

# SR-190: List all users in account
run_sample "SR-190" "admin-user-list-account" \
  "raps admin user list -a \$ACCOUNT_ID" \
  "Expected: Lists all users in account" \
  "Review: Contains emails, roles, statuses"

# SR-191: List users in project
run_sample "SR-191" "admin-user-list-project" \
  "raps admin user list -a \$ACCOUNT_ID -p \$PROJECT_ID" \
  "Expected: Lists users in project" \
  "Review: Contains emails and roles"

# SR-192: List users with filters
run_sample "SR-192" "admin-user-list-filtered" \
  "raps admin user list -a \$ACCOUNT_ID --role \"project_admin\" --status \"active\" --search \"john\"" \
  "Expected: Filtered user list" \
  "Review: All results match filters"

# SR-193: Bulk add user dry-run
run_sample "SR-193" "admin-user-add-bulk-dryrun" \
  "raps admin user add user@company.com -a \$ACCOUNT_ID -r \"project_admin\" -f \"Tower\" --dry-run" \
  "Expected: Shows which projects affected" \
  "Review: Lists matched projects; no actual changes"

# SR-194: Bulk add user execute
run_sample "SR-194" "admin-user-add-bulk-execute" \
  "raps admin user add user@company.com -a \$ACCOUNT_ID -r \"project_admin\" -f \"Tower\" -y" \
  "Expected: Adds user to matching projects" \
  "Review: Exit 0; summary shows projects added"

# SR-195: Add user from project-ids file
run_sample "SR-195" "admin-user-add-from-file" \
  "raps admin user add user@company.com -a \$ACCOUNT_ID -r \"viewer\" --project-ids ./project-ids.txt -y" \
  "Expected: Adds user to projects in file" \
  "Review: Exit 0; added to each project"

# SR-196: Bulk remove user dry-run
run_sample "SR-196" "admin-user-remove-bulk-dryrun" \
  "raps admin user remove user@company.com -a \$ACCOUNT_ID -f \"Old Project\" --dry-run" \
  "Expected: Shows projects user would be removed from" \
  "Review: Lists matched projects"

# SR-197: Bulk update user role dry-run
run_sample "SR-197" "admin-user-update-bulk-dryrun" \
  "raps admin user update user@company.com -a \$ACCOUNT_ID -r \"viewer\" --from-role \"project_admin\" -f \"Archive\" --dry-run" \
  "Expected: Shows role change preview" \
  "Review: Lists projects where role would change"

# SR-198: Update user roles from CSV
run_sample "SR-198" "admin-user-update-from-csv" \
  "raps admin user update user@company.com -a \$ACCOUNT_ID --from-csv ./role-changes.csv -y" \
  "Expected: Updates roles per CSV" \
  "Review: Exit 0; changes applied"

# SR-199: Add single user to project
run_sample "SR-199" "admin-user-add-single" \
  "raps admin user add-to-project -p \$PROJECT_ID -e \"new.user@company.com\" -r \$ROLE_ID" \
  "Expected: Adds single user" \
  "Review: Exit 0; user visible in list"

# SR-200: Update single user in project
run_sample "SR-200" "admin-user-update-single" \
  "raps admin user update-in-project -p \$PROJECT_ID -u \$USER_ID -r \$NEW_ROLE_ID" \
  "Expected: Updates user role" \
  "Review: Exit 0; role changed"

# SR-201: Remove single user from project
run_sample "SR-201" "admin-user-remove-single" \
  "raps admin user remove-from-project -p \$PROJECT_ID -u \$USER_ID -y" \
  "Expected: Removes user" \
  "Review: Exit 0; user gone"

# SR-202: Import users from CSV
run_sample "SR-202" "admin-user-import-csv" \
  "raps admin user import -p \$PROJECT_ID --from-csv ./new-users.csv" \
  "Expected: Imports users from CSV" \
  "Review: Exit 0; all CSV users in project"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-203: Account admin onboards new team member
lifecycle_start "SR-203" "new-employee-onboarding" "Account admin onboards new team member"
lifecycle_step 1 "raps admin user list -a \$ACCT --search \"newuser@company.com\""
lifecycle_step 2 "raps admin project list -a \$ACCT --status active -f \"Building\""
lifecycle_step 3 "raps admin user add newuser@company.com -a \$ACCT -r \"project_admin\" -f \"Building\" --dry-run"
lifecycle_step 4 "raps admin user add newuser@company.com -a \$ACCT -r \"project_admin\" -f \"Building\" -y"
lifecycle_step 5 "raps admin user list -a \$ACCT --search \"newuser@company.com\""
lifecycle_step 6 "raps admin folder rights newuser@company.com -a \$ACCT -l view-download-upload --folder \"Plans\" -f \"Building\" --dry-run"
lifecycle_step 7 "raps admin folder rights newuser@company.com -a \$ACCT -l view-download-upload --folder \"Plans\" -f \"Building\" -y"
lifecycle_end

# SR-204: Remove departing employee
lifecycle_start "SR-204" "employee-offboarding" "Remove departing employee"
lifecycle_step 1 "raps admin user list -a \$ACCT --search \"departing@company.com\""
lifecycle_step 2 "raps admin user remove departing@company.com -a \$ACCT --dry-run"
lifecycle_step 3 "raps admin user remove departing@company.com -a \$ACCT -y"
lifecycle_step 4 "raps admin user list -a \$ACCT --search \"departing@company.com\""
lifecycle_end

# SR-205: Downgrade stale admins to viewers
lifecycle_start "SR-205" "role-migration" "Downgrade stale admins to viewers"
lifecycle_step 1 "raps admin project list -a \$ACCT --status active -f \"2024\""
lifecycle_step 2 "raps admin user list -a \$ACCT --role \"project_admin\""
lifecycle_step 3 "raps admin user update admin1@co.com -a \$ACCT -r \"viewer\" --from-role \"project_admin\" -f \"2024\" --dry-run"
lifecycle_step 4 "raps admin user update admin1@co.com -a \$ACCT -r \"viewer\" --from-role \"project_admin\" -f \"2024\" -y"
lifecycle_step 5 "raps admin user list -a \$ACCT -p \$OLD_PROJECT --role \"project_admin\""
lifecycle_end

# SR-206: Onboard 50 users from CSV
lifecycle_start "SR-206" "csv-batch-onboarding" "Onboard 50 users from CSV"
lifecycle_step 1 "raps admin user import -p \$PROJECT_ID --from-csv ./bulk-users.csv"
lifecycle_step 2 "raps admin user list -a \$ACCT -p \$PROJECT_ID"
lifecycle_step 3 "raps admin user update user1@co.com -a \$ACCT --from-csv ./role-updates.csv -y"
lifecycle_step 4 "raps admin user list -a \$ACCT -p \$PROJECT_ID --role \"project_admin\""
lifecycle_end

section_end
