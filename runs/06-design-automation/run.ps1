# Section 06 — Design Automation
# Runs: SR-110 through SR-121
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "06-design-automation" -Title "Design Automation"

# -- Engine & AppBundle atomics ----------------------------------------

# SR-110: List DA engines
Invoke-Sample -Id "SR-110" -Slug "da-engines" `
  -Command "raps da engines" `
  -Expects "Expected: Lists DA engines" `
  -Review "Review: Contains engine names/versions"

# SR-111: List appbundles
Invoke-Sample -Id "SR-111" -Slug "da-appbundles-list" `
  -Command "raps da appbundles" `
  -Expects "Expected: Lists appbundles" `
  -Review "Review: List output"

# SR-112: Create an appbundle
Invoke-Sample -Id "SR-112" -Slug "da-appbundle-create" `
  -Command "raps da appbundle-create --name `"CountWalls`" --engine `"Autodesk.Revit+2025`" --bundle ./plugins/countwalls.zip" `
  -Expects "Expected: Creates appbundle" `
  -Review "Review: Exit 0; contains ID"

# SR-113: Delete an appbundle
Invoke-Sample -Id "SR-113" -Slug "da-appbundle-delete" `
  -Command "raps da appbundle-delete --name `"CountWalls`"" `
  -Expects "Expected: Deletes appbundle" `
  -Review "Review: Exit 0; gone from list"

# -- Activity atomics --------------------------------------------------

# SR-114: List activities
Invoke-Sample -Id "SR-114" -Slug "da-activities-list" `
  -Command "raps da activities" `
  -Expects "Expected: Lists activities" `
  -Review "Review: Contains activity IDs"

# SR-115: Create an activity
Invoke-Sample -Id "SR-115" -Slug "da-activity-create" `
  -Command "raps da activity-create --name `"CountWallsActivity`" --engine `"Autodesk.Revit+2025`" --appbundle `"CountWalls`" --command-line `"...`"" `
  -Expects "Expected: Creates activity" `
  -Review "Review: Exit 0; contains activity ID"

# SR-116: Delete an activity
Invoke-Sample -Id "SR-116" -Slug "da-activity-delete" `
  -Command "raps da activity-delete --name `"CountWallsActivity`"" `
  -Expects "Expected: Deletes activity" `
  -Review "Review: Exit 0"

# -- Work item atomics -------------------------------------------------

# SR-117: Submit a work item
Invoke-Sample -Id "SR-117" -Slug "da-run" `
  -Command "raps da run --activity `"CountWallsActivity`" --input-url $env:SIGNED_URL --output-url $env:OUTPUT_URL" `
  -Expects "Expected: Submits workitem" `
  -Review "Review: Exit 0; contains work item ID"

# SR-118: List work items
Invoke-Sample -Id "SR-118" -Slug "da-workitems" `
  -Command "raps da workitems" `
  -Expects "Expected: Lists work items" `
  -Review "Review: Contains IDs and statuses"

# SR-119: Show work item status
Invoke-Sample -Id "SR-119" -Slug "da-status" `
  -Command "raps da status --id $env:WORKITEM_ID" `
  -Expects "Expected: Shows status" `
  -Review "Review: Contains status field"

# -- Lifecycles --------------------------------------------------------

# SR-120: Register and test a Revit plugin
Start-Lifecycle -Id "SR-120" -Slug "da-appbundle-lifecycle" -Description "Register and test a Revit plugin"
Invoke-LifecycleStep -StepNum 1 -Command "raps da engines"
Invoke-LifecycleStep -StepNum 2 -Command "raps da appbundle-create --name `"ExtractData`" --engine `"Autodesk.Revit+2025`" --bundle ./plugin.zip"
Invoke-LifecycleStep -StepNum 3 -Command "raps da appbundles"
Invoke-LifecycleStep -StepNum 4 -Command "raps da activity-create --name `"ExtractAct`" --engine `"Autodesk.Revit+2025`" --appbundle `"ExtractData`" --command-line `"...`""
Invoke-LifecycleStep -StepNum 5 -Command "raps da activities"
Invoke-LifecycleStep -StepNum 6 -Command "raps da activity-delete --name `"ExtractAct`""
Invoke-LifecycleStep -StepNum 7 -Command "raps da appbundle-delete --name `"ExtractData`""
End-Lifecycle

# SR-121: Run and monitor a DA job
Start-Lifecycle -Id "SR-121" -Slug "da-workitem-lifecycle" -Description "Run and monitor a DA job"
Invoke-LifecycleStep -StepNum 1 -Command "raps object upload --bucket da-test --file ./model.rvt"
Invoke-LifecycleStep -StepNum 2 -Command "raps object signed-url --bucket da-test --key model.rvt"
Invoke-LifecycleStep -StepNum 3 -Command "raps da run --activity `"ExtractAct`" --input-url $env:INPUT_URL --output-url $env:OUTPUT_URL"
Invoke-LifecycleStep -StepNum 4 -Command "raps da status --id $env:WORKITEM_ID"
Invoke-LifecycleStep -StepNum 5 -Command "raps da workitems"
Invoke-LifecycleStep -StepNum 6 -Command "raps object download --bucket da-test --key output.json --output ./results/"
End-Lifecycle

End-Section
