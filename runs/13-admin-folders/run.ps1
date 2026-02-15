# Section 13 — Admin: Folder Permissions & Operations
# Runs: SR-220 through SR-228
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "13-admin-folders" -Title "Admin: Folder Permissions & Operations"

# -- Atomic commands -------------------------------------------------------

# SR-220: Grant folder rights dry-run
Invoke-Sample -Id "SR-220" -Slug "admin-folder-rights-dryrun" `
  -Command "raps admin folder rights user@company.com -a $env:ACCT -l view-download-upload --folder `"Plans`" -f `"Tower`" --dry-run" `
  -Expects "Expected: Shows which projects and folders would be affected" `
  -Review "Review: Lists matched projects; no actual changes"

# SR-221: Grant folder rights execute
Invoke-Sample -Id "SR-221" -Slug "admin-folder-rights-execute" `
  -Command "raps admin folder rights user@company.com -a $env:ACCT -l view-download-upload --folder `"Plans`" -f `"Tower`" -y" `
  -Expects "Expected: Grants folder permissions across matching projects" `
  -Review "Review: Exit 0; permissions applied"

# SR-222: Grant folder rights from project-ids file
Invoke-Sample -Id "SR-222" -Slug "admin-folder-rights-from-file" `
  -Command "raps admin folder rights user@company.com -a $env:ACCT -l folder-control --project-ids ./projects.txt -y" `
  -Expects "Expected: Grants folder permissions to projects in file" `
  -Review "Review: Exit 0; permissions applied to each project"

# SR-223: List companies in account
Invoke-Sample -Id "SR-223" -Slug "admin-company-list" `
  -Command "raps admin company-list -a $env:ACCOUNT_ID" `
  -Expects "Expected: Lists all companies in the account" `
  -Review "Review: Contains company names and IDs"

# SR-224: List completed operations
Invoke-Sample -Id "SR-224" -Slug "admin-operation-list" `
  -Command "raps admin operation list --status completed --limit 5" `
  -Expects "Expected: Lists recent completed operations" `
  -Review "Review: Contains operation IDs and statuses"

# SR-225: Check operation status
Invoke-Sample -Id "SR-225" -Slug "admin-operation-status" `
  -Command "raps admin operation status $env:OPERATION_ID" `
  -Expects "Expected: Shows detailed operation status" `
  -Review "Review: Contains progress, affected items, and timing"

# SR-226: Resume a paused operation
Invoke-Sample -Id "SR-226" -Slug "admin-operation-resume" `
  -Command "raps admin operation resume $env:OPERATION_ID --concurrency 3" `
  -Expects "Expected: Resumes the operation with specified concurrency" `
  -Review "Review: Exit 0; operation status changes to running"

# SR-227: Cancel an operation
Invoke-Sample -Id "SR-227" -Slug "admin-operation-cancel" `
  -Command "raps admin operation cancel $env:OPERATION_ID -y" `
  -Expects "Expected: Cancels the operation" `
  -Review "Review: Exit 0; operation status is cancelled"

# -- Lifecycles ------------------------------------------------------------

# SR-228: Grant, verify, restrict folder access
Start-Lifecycle -Id "SR-228" -Slug "folder-permissions-lifecycle" -Description "Grant, verify, restrict folder access"
Invoke-LifecycleStep -StepNum 1 -Command "raps admin folder rights user@co.com -a $env:ACCT -l view-download-upload-edit --folder `"Plans`" -f `"Active`" --dry-run"
Invoke-LifecycleStep -StepNum 2 -Command "raps admin folder rights user@co.com -a $env:ACCT -l view-download-upload-edit --folder `"Plans`" -f `"Active`" -y"
Invoke-LifecycleStep -StepNum 3 -Command "raps admin operation list --limit 1"
Invoke-LifecycleStep -StepNum 4 -Command "raps admin operation status $env:OP_ID"
Invoke-LifecycleStep -StepNum 5 -Command "raps admin folder rights user@co.com -a $env:ACCT -l view-only --folder `"Plans`" -f `"Active`" -y"
Invoke-LifecycleStep -StepNum 6 -Command "raps admin operation status $env:OP2_ID"
End-Lifecycle

End-Section
