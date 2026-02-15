# Section 16 — Templates
# Runs: SR-250 through SR-255
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "16-templates" -Title "Templates"

# --- Pre-seed demo environment variables (override with real values) ---
if (-not $env:ACCOUNT_ID) { $env:ACCOUNT_ID = "demo-account-001" }
if (-not $env:TEMPLATE_ID) { $env:TEMPLATE_ID = "tpl-demo-001" }
if (-not $env:ACCT) { $env:ACCT = "demo-account-001" }
if (-not $env:TPL_ID) { $env:TPL_ID = "tpl-demo-001" }

# -- Atomic commands -------------------------------------------------------

# SR-250: List templates
Invoke-Sample -Id "SR-250" -Slug "template-list" `
  -Command "raps template list -a $env:ACCOUNT_ID" `
  -Expects "Expected: Lists templates" `
  -Review "Review: Contains template names and IDs"

# SR-251: Create a template
Invoke-Sample -Id "SR-251" -Slug "template-create" `
  -Command "raps template create -a $env:ACCOUNT_ID --name `"Standard Building Template`"" `
  -Expects "Expected: Creates template" `
  -Review "Review: Exit 0; contains template ID"

# SR-252: Get template details
Invoke-Sample -Id "SR-252" -Slug "template-info" `
  -Command "raps template info $env:TEMPLATE_ID -a $env:ACCOUNT_ID" `
  -Expects "Expected: Shows template details" `
  -Review "Review: Contains name, ID, and configuration"

# SR-253: Update a template
Invoke-Sample -Id "SR-253" -Slug "template-update" `
  -Command "raps template update $env:TEMPLATE_ID -a $env:ACCOUNT_ID --name `"Standard Building Template v2`"" `
  -Expects "Expected: Updates template" `
  -Review "Review: Exit 0; name changed"

# SR-254: Archive a template
Invoke-Sample -Id "SR-254" -Slug "template-archive" `
  -Command "raps template archive $env:TEMPLATE_ID -a $env:ACCOUNT_ID" `
  -Expects "Expected: Archives template" `
  -Review "Review: Exit 0; template no longer active"

# -- Lifecycles ------------------------------------------------------------

# SR-255: Admin manages templates
Start-Lifecycle -Id "SR-255" -Slug "template-management-lifecycle" -Description "Admin manages templates"
Invoke-LifecycleStep -StepNum 1 -Command "raps template create -a $env:ACCT --name `"Healthcare Template`""
Invoke-LifecycleStep -StepNum 2 -Command "raps template list -a $env:ACCT"
Invoke-LifecycleStep -StepNum 3 -Command "raps template info $env:TPL_ID -a $env:ACCT"
Invoke-LifecycleStep -StepNum 4 -Command "raps template update $env:TPL_ID -a $env:ACCT --name `"Healthcare Template 2026`""
Invoke-LifecycleStep -StepNum 5 -Command "raps template archive $env:TPL_ID -a $env:ACCT"
Invoke-LifecycleStep -StepNum 6 -Command "raps template list -a $env:ACCT"
End-Lifecycle

End-Section
