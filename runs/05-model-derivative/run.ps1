# Section 05 — Model Derivative / Translation
# Runs: SR-090 through SR-101
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "05-model-derivative" -Title "Model Derivative / Translation"

# --- Pre-seed demo environment variables (override with real values) ---
if (-not $env:OBJECT_URN) { $env:OBJECT_URN = "dXJuOmFkc2sub2JqZWN0czpvcy5vYmplY3Q6ZGVtby1idWNrZXQvc2FtcGxlLmlmYw" }
if (-not $env:URN) { $env:URN = "dXJuOmFkc2sub2JqZWN0czpvcy5vYmplY3Q6ZGVtby1idWNrZXQvc2FtcGxlLmlmYw" }
if (-not $env:ITEM_ID) { $env:ITEM_ID = "urn:adsk.wipprod:dm.lineage:demo-item-001" }
if (-not $env:FOLDER_ID) { $env:FOLDER_ID = "urn:adsk.wipprod:fs.folder:co.demo-folder-001" }

# -- Atomic commands ---------------------------------------------------

# SR-090: Start a translation job
Invoke-Sample -Id "SR-090" -Slug "translate-start" `
  -Command "raps translate start $env:OBJECT_URN -f svf2" `
  -Expects "Expected: Starts a model translation job to SVF2 format" `
  -Review "Review: Exit 0; output contains translation job URN and status"

# SR-091: Check translation status
Invoke-Sample -Id "SR-091" -Slug "translate-status" `
  -Command "raps translate status $env:OBJECT_URN" `
  -Expects "Expected: Reports current translation progress" `
  -Review "Review: Contains progress percentage and status (pending/inprogress/success/failed)"

# SR-092: Get translation manifest
Invoke-Sample -Id "SR-092" -Slug "translate-manifest" `
  -Command "raps translate manifest $env:OBJECT_URN" `
  -Expects "Expected: Shows the translation manifest with derivative tree" `
  -Review "Review: Contains derivative URN, output formats, and bubble structure"

# SR-093: List available derivatives
Invoke-Sample -Id "SR-093" -Slug "translate-derivatives" `
  -Command "raps translate derivatives $env:OBJECT_URN" `
  -Expects "Expected: Lists all available derivative outputs for the model" `
  -Review "Review: Contains derivative types (SVF, thumbnail, metadata) and roles"

# SR-094: Download derivatives
Invoke-Sample -Id "SR-094" -Slug "translate-download" `
  -Command "raps translate download $env:OBJECT_URN -o ./derivatives/" `
  -Expects "Expected: Downloads derivative files to the specified directory" `
  -Review "Review: Files exist at output path; directory contains derivative assets"

# SR-095: List translation presets
Invoke-Sample -Id "SR-095" -Slug "translate-preset-list" `
  -Command "raps translate preset list" `
  -Expects "Expected: Lists all saved translation presets" `
  -Review "Review: Table or list with preset names and target formats"

# SR-096: Create a translation preset
Invoke-Sample -Id "SR-096" -Slug "translate-preset-create" `
  -Command "raps translate preset create 'svf2-default' -f svf2" `
  -Expects "Expected: Creates a reusable translation preset" `
  -Review "Review: Exit 0; output confirms preset saved with name and format"

# SR-097: Show a translation preset
Invoke-Sample -Id "SR-097" -Slug "translate-preset-show" `
  -Command "raps translate preset show 'svf2-default'" `
  -Expects "Expected: Displays details of the specified preset" `
  -Review "Review: Contains preset name, target format, and configuration"

# SR-098: Use a preset for translation
Invoke-Sample -Id "SR-098" -Slug "translate-preset-use" `
  -Command "raps translate preset use $env:OBJECT_URN 'svf2-default'" `
  -Expects "Expected: Starts a translation using the saved preset configuration" `
  -Review "Review: Exit 0; translation job started with preset settings"

# SR-099: Delete a translation preset
Invoke-Sample -Id "SR-099" -Slug "translate-preset-delete" `
  -Command "raps translate preset delete 'svf2-default'" `
  -Expects "Expected: Deletes the specified preset" `
  -Review "Review: Exit 0; preset no longer appears in list"

# -- Lifecycles --------------------------------------------------------

# SR-100: Full translation pipeline (upload and translate a model)
Start-Lifecycle -Id "SR-100" -Slug "translate-full-pipeline" -Description "Upload and translate a model"
Invoke-LifecycleStep -StepNum 1 -Command "raps bucket create"
Invoke-LifecycleStep -StepNum 2 -Command "raps object upload translate-test ./test-data/sample.rvt"
Invoke-LifecycleStep -StepNum 3 -Command "raps translate start $env:URN -f svf2"
Invoke-LifecycleStep -StepNum 4 -Command "raps translate status $env:URN"
Invoke-LifecycleStep -StepNum 5 -Command "raps translate manifest $env:URN"
Invoke-LifecycleStep -StepNum 6 -Command "raps translate derivatives $env:URN"
Invoke-LifecycleStep -StepNum 7 -Command "raps translate download $env:URN -o ./output/"
Invoke-LifecycleStep -StepNum 8 -Command "raps bucket delete translate-test"
End-Lifecycle

# SR-101: Preset CRUD + use lifecycle
Start-Lifecycle -Id "SR-101" -Slug "translate-preset-lifecycle" -Description "Preset CRUD + use"
Invoke-LifecycleStep -StepNum 1 -Command "raps translate preset create 'ifc-to-svf' -f svf2"
Invoke-LifecycleStep -StepNum 2 -Command "raps translate preset list"
Invoke-LifecycleStep -StepNum 3 -Command "raps translate preset show 'ifc-to-svf'"
Invoke-LifecycleStep -StepNum 4 -Command "raps translate preset use $env:URN 'ifc-to-svf'"
Invoke-LifecycleStep -StepNum 5 -Command "raps translate preset delete 'ifc-to-svf'"
End-Lifecycle

End-Section
