# Section 05 — Model Derivative / Translation
# Runs: SR-090 through SR-101
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "05-model-derivative" -Title "Model Derivative / Translation"

# -- Atomic commands ---------------------------------------------------

# SR-090: Start a translation job
Invoke-Sample -Id "SR-090" -Slug "translate-start" `
  -Command "raps translate start --urn $env:OBJECT_URN --format svf2" `
  -Expects "Expected: Starts a model translation job to SVF2 format" `
  -Review "Review: Exit 0; output contains translation job URN and status"

# SR-091: Check translation status
Invoke-Sample -Id "SR-091" -Slug "translate-status" `
  -Command "raps translate status --urn $env:OBJECT_URN" `
  -Expects "Expected: Reports current translation progress" `
  -Review "Review: Contains progress percentage and status (pending/inprogress/success/failed)"

# SR-092: Get translation manifest
Invoke-Sample -Id "SR-092" -Slug "translate-manifest" `
  -Command "raps translate manifest --urn $env:OBJECT_URN" `
  -Expects "Expected: Shows the translation manifest with derivative tree" `
  -Review "Review: Contains derivative URN, output formats, and bubble structure"

# SR-093: List available derivatives
Invoke-Sample -Id "SR-093" -Slug "translate-derivatives" `
  -Command "raps translate derivatives --urn $env:OBJECT_URN" `
  -Expects "Expected: Lists all available derivative outputs for the model" `
  -Review "Review: Contains derivative types (SVF, thumbnail, metadata) and roles"

# SR-094: Download derivatives
Invoke-Sample -Id "SR-094" -Slug "translate-download" `
  -Command "raps translate download --urn $env:OBJECT_URN --output ./derivatives/" `
  -Expects "Expected: Downloads derivative files to the specified directory" `
  -Review "Review: Files exist at output path; directory contains derivative assets"

# SR-095: List translation presets
Invoke-Sample -Id "SR-095" -Slug "translate-preset-list" `
  -Command "raps translate preset list" `
  -Expects "Expected: Lists all saved translation presets" `
  -Review "Review: Table or list with preset names and target formats"

# SR-096: Create a translation preset
Invoke-Sample -Id "SR-096" -Slug "translate-preset-create" `
  -Command "raps translate preset create --name 'svf2-default' --format svf2" `
  -Expects "Expected: Creates a reusable translation preset" `
  -Review "Review: Exit 0; output confirms preset saved with name and format"

# SR-097: Show a translation preset
Invoke-Sample -Id "SR-097" -Slug "translate-preset-show" `
  -Command "raps translate preset show --name 'svf2-default'" `
  -Expects "Expected: Displays details of the specified preset" `
  -Review "Review: Contains preset name, target format, and configuration"

# SR-098: Use a preset for translation
Invoke-Sample -Id "SR-098" -Slug "translate-preset-use" `
  -Command "raps translate preset use --name 'svf2-default' --urn $env:OBJECT_URN" `
  -Expects "Expected: Starts a translation using the saved preset configuration" `
  -Review "Review: Exit 0; translation job started with preset settings"

# SR-099: Delete a translation preset
Invoke-Sample -Id "SR-099" -Slug "translate-preset-delete" `
  -Command "raps translate preset delete --name 'svf2-default'" `
  -Expects "Expected: Deletes the specified preset" `
  -Review "Review: Exit 0; preset no longer appears in list"

# -- Lifecycles --------------------------------------------------------

# SR-100: Full translation pipeline (upload and translate a model)
Start-Lifecycle -Id "SR-100" -Slug "translate-full-pipeline" -Description "Upload and translate a model"
Invoke-LifecycleStep -StepNum 1 -Command "raps bucket create --name translate-test --policy transient"
Invoke-LifecycleStep -StepNum 2 -Command "raps object upload --bucket translate-test --file ./test-data/sample.rvt"
Invoke-LifecycleStep -StepNum 3 -Command "raps translate start --urn $env:URN --format svf2"
Invoke-LifecycleStep -StepNum 4 -Command "raps translate status --urn $env:URN"
Invoke-LifecycleStep -StepNum 5 -Command "raps translate manifest --urn $env:URN"
Invoke-LifecycleStep -StepNum 6 -Command "raps translate derivatives --urn $env:URN"
Invoke-LifecycleStep -StepNum 7 -Command "raps translate download --urn $env:URN --output ./output/"
Invoke-LifecycleStep -StepNum 8 -Command "raps bucket delete --name translate-test --yes"
End-Lifecycle

# SR-101: Preset CRUD + use lifecycle
Start-Lifecycle -Id "SR-101" -Slug "translate-preset-lifecycle" -Description "Preset CRUD + use"
Invoke-LifecycleStep -StepNum 1 -Command "raps translate preset create --name 'ifc-to-svf' --format svf2"
Invoke-LifecycleStep -StepNum 2 -Command "raps translate preset list"
Invoke-LifecycleStep -StepNum 3 -Command "raps translate preset show --name 'ifc-to-svf'"
Invoke-LifecycleStep -StepNum 4 -Command "raps translate preset use --name 'ifc-to-svf' --urn $env:URN"
Invoke-LifecycleStep -StepNum 5 -Command "raps translate preset delete --name 'ifc-to-svf'"
End-Lifecycle

End-Section
