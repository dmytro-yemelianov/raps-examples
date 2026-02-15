# Section 12 — Admin: Project Management
# Runs: SR-210 through SR-215
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "12-admin-projects" -Title "Admin: Project Management"

# --- Pre-seed demo environment variables (override with real values) ---
if (-not $env:ACCOUNT_ID) { $env:ACCOUNT_ID = "demo-account-001" }
if (-not $env:PROJECT_ID) { $env:PROJECT_ID = "b.demo-project-001" }
if (-not $env:ACCT) { $env:ACCT = "demo-account-001" }
if (-not $env:PID) { $env:PID = "b.demo-project-001" }

# -- Atomic commands -------------------------------------------------------

# SR-210: List all projects in account
Invoke-Sample -Id "SR-210" -Slug "admin-project-list" `
  -Command "raps admin project list -a $env:ACCOUNT_ID" `
  -Expects "Expected: Lists all projects in the account" `
  -Review "Review: Contains project names, IDs, and statuses"

# SR-211: List projects with filters
Invoke-Sample -Id "SR-211" -Slug "admin-project-list-filtered" `
  -Command "raps admin project list -a $env:ACCOUNT_ID -f `"name:*Tower*`" --status active --platform acc --limit 10" `
  -Expects "Expected: Filtered project list" `
  -Review "Review: All results match filter, status, and platform"

# SR-212: Create a project
Invoke-Sample -Id "SR-212" -Slug "admin-project-create" `
  -Command "raps admin project create -a $env:ACCOUNT_ID --name `"Tower Phase 3`" -t `"Bridge`" --classification `"Sample`" --start-date `"2026-03-01`" --end-date `"2027-12-31`" --timezone `"America/New_York`"" `
  -Expects "Expected: Creates a new project" `
  -Review "Review: Exit 0; output contains project ID and name"

# SR-213: Update a project
Invoke-Sample -Id "SR-213" -Slug "admin-project-update" `
  -Command "raps admin project update -a $env:ACCOUNT_ID -p $env:PROJECT_ID --name `"Tower Phase 3 - Revised`" --status active" `
  -Expects "Expected: Updates project name and status" `
  -Review "Review: Exit 0; project reflects new name"

# SR-214: Archive a project
Invoke-Sample -Id "SR-214" -Slug "admin-project-archive" `
  -Command "raps admin project archive -a $env:ACCOUNT_ID -p $env:PROJECT_ID" `
  -Expects "Expected: Archives the project" `
  -Review "Review: Exit 0; project status is archived"

# -- Lifecycles ------------------------------------------------------------

# SR-215: Create and manage project
Start-Lifecycle -Id "SR-215" -Slug "project-lifecycle-admin" -Description "Create and manage project"
Invoke-LifecycleStep -StepNum 1 -Command "raps admin project create -a $env:ACCT --name `"Bridge Retrofit`" -t `"Bridge`""
Invoke-LifecycleStep -StepNum 2 -Command "raps admin project list -a $env:ACCT -f `"name:*Bridge*`""
Invoke-LifecycleStep -StepNum 3 -Command "raps admin user add pm@company.com -a $env:ACCT -r `"project_admin`" -f `"name:*Bridge Retrofit*`" -y"
Invoke-LifecycleStep -StepNum 4 -Command "raps admin project update -a $env:ACCT -p $env:PID --start-date `"2026-04-01`""
Invoke-LifecycleStep -StepNum 5 -Command "raps admin project archive -a $env:ACCT -p $env:PID"
Invoke-LifecycleStep -StepNum 6 -Command "raps admin project list -a $env:ACCT --status active"
End-Lifecycle

End-Section
