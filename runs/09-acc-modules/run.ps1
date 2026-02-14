# Section 09 — ACC Modules: Assets, Submittals, Checklists
# Runs: SR-160 through SR-177
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "09-acc-modules" -Title "ACC Modules: Assets, Submittals, Checklists"

# -- Asset atomics -----------------------------------------------------

# SR-160: List assets
Invoke-Sample -Id "SR-160" -Slug "acc-asset-list" `
  -Command "raps acc asset list --project $env:PROJECT_ID" `
  -Expects "Expected: Lists assets" `
  -Review "Review: List output"

# SR-161: Create an asset
Invoke-Sample -Id "SR-161" -Slug "acc-asset-create" `
  -Command "raps acc asset create --project $env:PROJECT_ID --name `"HVAC Unit AHU-01`" --category `"Mechanical`"" `
  -Expects "Expected: Creates asset" `
  -Review "Review: Exit 0; contains asset ID"

# SR-162: Get asset details
Invoke-Sample -Id "SR-162" -Slug "acc-asset-get" `
  -Command "raps acc asset get --project $env:PROJECT_ID --asset $env:ASSET_ID" `
  -Expects "Expected: Shows details" `
  -Review "Review: Contains name, category, status"

# SR-163: Update an asset
Invoke-Sample -Id "SR-163" -Slug "acc-asset-update" `
  -Command "raps acc asset update --project $env:PROJECT_ID --asset $env:ASSET_ID --status `"installed`"" `
  -Expects "Expected: Updates asset" `
  -Review "Review: Exit 0"

# SR-164: Delete an asset
Invoke-Sample -Id "SR-164" -Slug "acc-asset-delete" `
  -Command "raps acc asset delete --project $env:PROJECT_ID --asset $env:ASSET_ID --yes" `
  -Expects "Expected: Deletes asset" `
  -Review "Review: Exit 0"

# -- Submittal atomics -------------------------------------------------

# SR-165: List submittals
Invoke-Sample -Id "SR-165" -Slug "acc-submittal-list" `
  -Command "raps acc submittal list --project $env:PROJECT_ID" `
  -Expects "Expected: Lists submittals" `
  -Review "Review: List output"

# SR-166: Create a submittal
Invoke-Sample -Id "SR-166" -Slug "acc-submittal-create" `
  -Command "raps acc submittal create --project $env:PROJECT_ID --title `"Concrete mix design for Level 5`" --spec-section `"03 30 00`"" `
  -Expects "Expected: Creates submittal" `
  -Review "Review: Exit 0; contains submittal ID"

# SR-167: Get submittal details
Invoke-Sample -Id "SR-167" -Slug "acc-submittal-get" `
  -Command "raps acc submittal get --project $env:PROJECT_ID --submittal $env:SUBMITTAL_ID" `
  -Expects "Expected: Shows details" `
  -Review "Review: Contains title, spec section, status"

# SR-168: Update a submittal
Invoke-Sample -Id "SR-168" -Slug "acc-submittal-update" `
  -Command "raps acc submittal update --project $env:PROJECT_ID --submittal $env:SUBMITTAL_ID --status `"approved`"" `
  -Expects "Expected: Updates submittal" `
  -Review "Review: Exit 0"

# SR-169: Delete a submittal
Invoke-Sample -Id "SR-169" -Slug "acc-submittal-delete" `
  -Command "raps acc submittal delete --project $env:PROJECT_ID --submittal $env:SUBMITTAL_ID --yes" `
  -Expects "Expected: Deletes submittal" `
  -Review "Review: Exit 0"

# -- Checklist atomics -------------------------------------------------

# SR-170: List checklists
Invoke-Sample -Id "SR-170" -Slug "acc-checklist-list" `
  -Command "raps acc checklist list --project $env:PROJECT_ID" `
  -Expects "Expected: Lists checklists" `
  -Review "Review: List output"

# SR-171: Create a checklist
Invoke-Sample -Id "SR-171" -Slug "acc-checklist-create" `
  -Command "raps acc checklist create --project $env:PROJECT_ID --name `"Pre-pour inspection - Level 3`" --template $env:TEMPLATE_ID" `
  -Expects "Expected: Creates checklist" `
  -Review "Review: Exit 0; contains checklist ID"

# SR-172: Get checklist details
Invoke-Sample -Id "SR-172" -Slug "acc-checklist-get" `
  -Command "raps acc checklist get --project $env:PROJECT_ID --checklist $env:CHECKLIST_ID" `
  -Expects "Expected: Shows details" `
  -Review "Review: Contains name, template, status"

# SR-173: Update a checklist
Invoke-Sample -Id "SR-173" -Slug "acc-checklist-update" `
  -Command "raps acc checklist update --project $env:PROJECT_ID --checklist $env:CHECKLIST_ID --status `"completed`"" `
  -Expects "Expected: Updates checklist" `
  -Review "Review: Exit 0"

# SR-174: List checklist templates
Invoke-Sample -Id "SR-174" -Slug "acc-checklist-templates" `
  -Command "raps acc checklist templates --project $env:PROJECT_ID" `
  -Expects "Expected: Lists checklist templates" `
  -Review "Review: Contains template names and IDs"

# -- Lifecycles --------------------------------------------------------

# SR-175: Facilities manager tracks equipment
Start-Lifecycle -Id "SR-175" -Slug "asset-tracking-lifecycle" -Description "Facilities manager tracks equipment"
Invoke-LifecycleStep -StepNum 1 -Command "raps acc asset create --project $env:PID --name `"Chiller CH-01`" --category `"Mechanical`""
Invoke-LifecycleStep -StepNum 2 -Command "raps acc asset create --project $env:PID --name `"Chiller CH-02`" --category `"Mechanical`""
Invoke-LifecycleStep -StepNum 3 -Command "raps acc asset list --project $env:PID"
Invoke-LifecycleStep -StepNum 4 -Command "raps acc asset update --project $env:PID --asset $env:CH01 --status `"delivered`""
Invoke-LifecycleStep -StepNum 5 -Command "raps acc asset update --project $env:PID --asset $env:CH01 --status `"installed`""
Invoke-LifecycleStep -StepNum 6 -Command "raps acc asset get --project $env:PID --asset $env:CH01"
Invoke-LifecycleStep -StepNum 7 -Command "raps acc asset delete --project $env:PID --asset $env:CH02 --yes"
End-Lifecycle

# SR-176: GC submits shop drawings
Start-Lifecycle -Id "SR-176" -Slug "submittal-review-lifecycle" -Description "GC submits shop drawings"
Invoke-LifecycleStep -StepNum 1 -Command "raps acc submittal create --project $env:PID --title `"Structural steel shop drawings`" --spec-section `"05 12 00`""
Invoke-LifecycleStep -StepNum 2 -Command "raps acc submittal get --project $env:PID --submittal $env:ID"
Invoke-LifecycleStep -StepNum 3 -Command "raps acc submittal update --project $env:PID --submittal $env:ID --reviewer $env:ARCHITECT --status `"in_review`""
Invoke-LifecycleStep -StepNum 4 -Command "raps acc submittal update --project $env:PID --submittal $env:ID --status `"revise_resubmit`""
Invoke-LifecycleStep -StepNum 5 -Command "raps acc submittal update --project $env:PID --submittal $env:ID --status `"approved`""
Invoke-LifecycleStep -StepNum 6 -Command "raps acc submittal delete --project $env:PID --submittal $env:ID --yes"
End-Lifecycle

# SR-177: Inspector completes inspection
Start-Lifecycle -Id "SR-177" -Slug "checklist-inspection-lifecycle" -Description "Inspector completes inspection"
Invoke-LifecycleStep -StepNum 1 -Command "raps acc checklist templates --project $env:PID"
Invoke-LifecycleStep -StepNum 2 -Command "raps acc checklist create --project $env:PID --name `"Fire stopping inspection B3`" --template $env:TPL"
Invoke-LifecycleStep -StepNum 3 -Command "raps acc checklist get --project $env:PID --checklist $env:ID"
Invoke-LifecycleStep -StepNum 4 -Command "raps acc checklist update --project $env:PID --checklist $env:ID --status `"in_progress`""
Invoke-LifecycleStep -StepNum 5 -Command "raps acc checklist update --project $env:PID --checklist $env:ID --status `"completed`""
Invoke-LifecycleStep -StepNum 6 -Command "raps acc checklist get --project $env:PID --checklist $env:ID"
End-Lifecycle

End-Section
