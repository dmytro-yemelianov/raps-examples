# Section 08 — ACC RFIs
# Runs: SR-150 through SR-155
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "08-acc-rfi" -Title "ACC RFIs"

# -- RFI atomics -------------------------------------------------------

# SR-150: List RFIs
Invoke-Sample -Id "SR-150" -Slug "rfi-list" `
  -Command "raps rfi list --project $env:PROJECT_ID" `
  -Expects "Expected: Lists RFIs" `
  -Review "Review: Contains numbers, titles, statuses"

# SR-151: Create an RFI
Invoke-Sample -Id "SR-151" -Slug "rfi-create" `
  -Command "raps rfi create --project $env:PROJECT_ID --title `"Clarification on MEP routing at Level 3`" --description `"Conflict between HVAC duct and structural beam at grid C-4`"" `
  -Expects "Expected: Creates RFI" `
  -Review "Review: Exit 0; contains RFI ID"

# SR-152: Get RFI details
Invoke-Sample -Id "SR-152" -Slug "rfi-get" `
  -Command "raps rfi get --project $env:PROJECT_ID --rfi $env:RFI_ID" `
  -Expects "Expected: Shows details" `
  -Review "Review: Contains title, status, dates"

# SR-153: Update an RFI
Invoke-Sample -Id "SR-153" -Slug "rfi-update" `
  -Command "raps rfi update --project $env:PROJECT_ID --rfi $env:RFI_ID --assignee $env:USER_ID --priority `"high`"" `
  -Expects "Expected: Updates RFI" `
  -Review "Review: Exit 0"

# SR-154: Delete an RFI
Invoke-Sample -Id "SR-154" -Slug "rfi-delete" `
  -Command "raps rfi delete --project $env:PROJECT_ID --rfi $env:RFI_ID --yes" `
  -Expects "Expected: Deletes RFI" `
  -Review "Review: Exit 0"

# -- Lifecycles --------------------------------------------------------

# SR-155: Architect raises and resolves an RFI
Start-Lifecycle -Id "SR-155" -Slug "rfi-full-lifecycle" -Description "Architect raises and resolves an RFI"
Invoke-LifecycleStep -StepNum 1 -Command "raps rfi create --project $env:PROJECT_ID --title `"Beam depth at grid D-7`""
Invoke-LifecycleStep -StepNum 2 -Command "raps rfi list --project $env:PROJECT_ID"
Invoke-LifecycleStep -StepNum 3 -Command "raps rfi get --project $env:PROJECT_ID --rfi $env:ID"
Invoke-LifecycleStep -StepNum 4 -Command "raps rfi update --project $env:PROJECT_ID --rfi $env:ID --assignee $env:STRUCT_ENG --priority `"high`""
Invoke-LifecycleStep -StepNum 5 -Command "raps rfi update --project $env:PROJECT_ID --rfi $env:ID --status `"answered`" --response `"Use W14x30, see SK-204`""
Invoke-LifecycleStep -StepNum 6 -Command "raps rfi get --project $env:PROJECT_ID --rfi $env:ID"
Invoke-LifecycleStep -StepNum 7 -Command "raps rfi delete --project $env:PROJECT_ID --rfi $env:ID --yes"
End-Lifecycle

End-Section
