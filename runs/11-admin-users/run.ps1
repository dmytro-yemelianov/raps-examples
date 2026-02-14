# Section 11 — Admin: Bulk User Management
# Runs: SR-190 through SR-206
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "11-admin-users" -Title "Admin: Bulk User Management"

# -- Atomic commands -------------------------------------------------------

# SR-190: List all users in account
Invoke-Sample -Id "SR-190" -Slug "admin-user-list-account" `
  -Command "raps admin user list --account $env:ACCOUNT_ID" `
  -Expects "Expected: Lists all users in account" `
  -Review "Review: Contains emails, roles, statuses"

# SR-191: List users in project
Invoke-Sample -Id "SR-191" -Slug "admin-user-list-project" `
  -Command "raps admin user list --project $env:PROJECT_ID" `
  -Expects "Expected: Lists users in project" `
  -Review "Review: Contains emails and roles"

# SR-192: List users with filters
Invoke-Sample -Id "SR-192" -Slug "admin-user-list-filtered" `
  -Command "raps admin user list --account $env:ACCOUNT_ID --role `"project_admin`" --status `"active`" --search `"john`"" `
  -Expects "Expected: Filtered user list" `
  -Review "Review: All results match filters"

# SR-193: Bulk add user dry-run
Invoke-Sample -Id "SR-193" -Slug "admin-user-add-bulk-dryrun" `
  -Command "raps admin user add user@company.com --account $env:ACCOUNT_ID --role `"project_admin`" --filter `"Tower`" --concurrency 5 --dry-run" `
  -Expects "Expected: Shows which projects affected" `
  -Review "Review: Lists matched projects; no actual changes"

# SR-194: Bulk add user execute
Invoke-Sample -Id "SR-194" -Slug "admin-user-add-bulk-execute" `
  -Command "raps admin user add user@company.com --account $env:ACCOUNT_ID --role `"project_admin`" --filter `"Tower`" --concurrency 5 --yes" `
  -Expects "Expected: Adds user to matching projects" `
  -Review "Review: Exit 0; summary shows projects added"

# SR-195: Add user from project-ids file
Invoke-Sample -Id "SR-195" -Slug "admin-user-add-from-file" `
  -Command "raps admin user add user@company.com --account $env:ACCOUNT_ID --role `"viewer`" --project-ids ./project-ids.txt --yes" `
  -Expects "Expected: Adds user to projects in file" `
  -Review "Review: Exit 0; added to each project"

# SR-196: Bulk remove user dry-run
Invoke-Sample -Id "SR-196" -Slug "admin-user-remove-bulk-dryrun" `
  -Command "raps admin user remove user@company.com --account $env:ACCOUNT_ID --filter `"Old Project`" --dry-run" `
  -Expects "Expected: Shows projects user would be removed from" `
  -Review "Review: Lists matched projects"

# SR-197: Bulk update user role dry-run
Invoke-Sample -Id "SR-197" -Slug "admin-user-update-bulk-dryrun" `
  -Command "raps admin user update user@company.com --account $env:ACCOUNT_ID --role `"viewer`" --from-role `"project_admin`" --filter `"Archive`" --dry-run" `
  -Expects "Expected: Shows role change preview" `
  -Review "Review: Lists projects where role would change"

# SR-198: Update user roles from CSV
Invoke-Sample -Id "SR-198" -Slug "admin-user-update-from-csv" `
  -Command "raps admin user update user@company.com --account $env:ACCOUNT_ID --from-csv ./role-changes.csv --yes" `
  -Expects "Expected: Updates roles per CSV" `
  -Review "Review: Exit 0; changes applied"

# SR-199: Add single user to project
Invoke-Sample -Id "SR-199" -Slug "admin-user-add-single" `
  -Command "raps admin user add-to-project --project $env:PROJECT_ID --email `"new.user@company.com`" --role-id $env:ROLE_ID" `
  -Expects "Expected: Adds single user" `
  -Review "Review: Exit 0; user visible in list"

# SR-200: Update single user in project
Invoke-Sample -Id "SR-200" -Slug "admin-user-update-single" `
  -Command "raps admin user update-in-project --project $env:PROJECT_ID --user-id $env:USER_ID --role-id $env:NEW_ROLE_ID" `
  -Expects "Expected: Updates user role" `
  -Review "Review: Exit 0; role changed"

# SR-201: Remove single user from project
Invoke-Sample -Id "SR-201" -Slug "admin-user-remove-single" `
  -Command "raps admin user remove-from-project --project $env:PROJECT_ID --user-id $env:USER_ID --yes" `
  -Expects "Expected: Removes user" `
  -Review "Review: Exit 0; user gone"

# SR-202: Import users from CSV
Invoke-Sample -Id "SR-202" -Slug "admin-user-import-csv" `
  -Command "raps admin user import --project $env:PROJECT_ID --from-csv ./new-users.csv" `
  -Expects "Expected: Imports users from CSV" `
  -Review "Review: Exit 0; all CSV users in project"

# -- Lifecycles ------------------------------------------------------------

# SR-203: Account admin onboards new team member
Start-Lifecycle -Id "SR-203" -Slug "new-employee-onboarding" -Description "Account admin onboards new team member"
Invoke-LifecycleStep -StepNum 1 -Command "raps admin user list --account $env:ACCT --search `"newuser@company.com`""
Invoke-LifecycleStep -StepNum 2 -Command "raps admin project list --account $env:ACCT --status active --filter `"Building`""
Invoke-LifecycleStep -StepNum 3 -Command "raps admin user add newuser@company.com --account $env:ACCT --role `"project_admin`" --filter `"Building`" --dry-run"
Invoke-LifecycleStep -StepNum 4 -Command "raps admin user add newuser@company.com --account $env:ACCT --role `"project_admin`" --filter `"Building`" --yes"
Invoke-LifecycleStep -StepNum 5 -Command "raps admin user list --account $env:ACCT --search `"newuser@company.com`""
Invoke-LifecycleStep -StepNum 6 -Command "raps admin folder rights newuser@company.com --account $env:ACCT --level view-download-upload --folder `"Plans`" --filter `"Building`" --dry-run"
Invoke-LifecycleStep -StepNum 7 -Command "raps admin folder rights newuser@company.com --account $env:ACCT --level view-download-upload --folder `"Plans`" --filter `"Building`" --yes"
End-Lifecycle

# SR-204: Remove departing employee
Start-Lifecycle -Id "SR-204" -Slug "employee-offboarding" -Description "Remove departing employee"
Invoke-LifecycleStep -StepNum 1 -Command "raps admin user list --account $env:ACCT --search `"departing@company.com`""
Invoke-LifecycleStep -StepNum 2 -Command "raps admin user remove departing@company.com --account $env:ACCT --dry-run"
Invoke-LifecycleStep -StepNum 3 -Command "raps admin user remove departing@company.com --account $env:ACCT --yes"
Invoke-LifecycleStep -StepNum 4 -Command "raps admin user list --account $env:ACCT --search `"departing@company.com`""
End-Lifecycle

# SR-205: Downgrade stale admins to viewers
Start-Lifecycle -Id "SR-205" -Slug "role-migration" -Description "Downgrade stale admins to viewers"
Invoke-LifecycleStep -StepNum 1 -Command "raps admin project list --account $env:ACCT --status active --filter `"2024`""
Invoke-LifecycleStep -StepNum 2 -Command "raps admin user list --account $env:ACCT --role `"project_admin`""
Invoke-LifecycleStep -StepNum 3 -Command "raps admin user update admin1@co.com --account $env:ACCT --role `"viewer`" --from-role `"project_admin`" --filter `"2024`" --dry-run"
Invoke-LifecycleStep -StepNum 4 -Command "raps admin user update admin1@co.com --account $env:ACCT --role `"viewer`" --from-role `"project_admin`" --filter `"2024`" --yes"
Invoke-LifecycleStep -StepNum 5 -Command "raps admin user list --project $env:OLD_PROJECT --role `"project_admin`""
End-Lifecycle

# SR-206: Onboard 50 users from CSV
Start-Lifecycle -Id "SR-206" -Slug "csv-batch-onboarding" -Description "Onboard 50 users from CSV"
Invoke-LifecycleStep -StepNum 1 -Command "raps admin user import --project $env:PROJECT_ID --from-csv ./bulk-users.csv"
Invoke-LifecycleStep -StepNum 2 -Command "raps admin user list --project $env:PROJECT_ID"
Invoke-LifecycleStep -StepNum 3 -Command "raps admin user update user1@co.com --account $env:ACCT --from-csv ./role-updates.csv --yes"
Invoke-LifecycleStep -StepNum 4 -Command "raps admin user list --project $env:PROJECT_ID --role `"project_admin`""
End-Lifecycle

End-Section
