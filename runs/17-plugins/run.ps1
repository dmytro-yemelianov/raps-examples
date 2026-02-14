# Section 17 — Plugins
# Runs: SR-260 through SR-266
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "17-plugins" -Title "Plugins"

# -- Atomic commands -------------------------------------------------------

# SR-260: List plugins
Invoke-Sample -Id "SR-260" -Slug "plugin-list" `
  -Command "raps plugin list" `
  -Expects "Expected: Lists plugins" `
  -Review "Review: Contains plugin names and statuses"

# SR-261: Enable a plugin
Invoke-Sample -Id "SR-261" -Slug "plugin-enable" `
  -Command "raps plugin enable my-plugin" `
  -Expects "Expected: Enables plugin" `
  -Review "Review: Exit 0; plugin shown as enabled"

# SR-262: Disable a plugin
Invoke-Sample -Id "SR-262" -Slug "plugin-disable" `
  -Command "raps plugin disable my-plugin" `
  -Expects "Expected: Disables plugin" `
  -Review "Review: Exit 0; plugin shown as disabled"

# SR-263: List aliases
Invoke-Sample -Id "SR-263" -Slug "plugin-alias-list" `
  -Command "raps plugin alias list" `
  -Expects "Expected: Lists aliases" `
  -Review "Review: Contains alias names and target commands"

# SR-264: Add an alias
Invoke-Sample -Id "SR-264" -Slug "plugin-alias-add" `
  -Command "raps plugin alias add `"bl`" `"bucket list`"" `
  -Expects "Expected: Creates alias" `
  -Review "Review: Exit 0; alias registered"

# SR-265: Remove an alias
Invoke-Sample -Id "SR-265" -Slug "plugin-alias-remove" `
  -Command "raps plugin alias remove `"bl`"" `
  -Expects "Expected: Removes alias" `
  -Review "Review: Exit 0; alias no longer listed"

# -- Lifecycles ------------------------------------------------------------

# SR-266: Developer sets up aliases
Start-Lifecycle -Id "SR-266" -Slug "alias-power-user-lifecycle" -Description "Developer sets up aliases"
Invoke-LifecycleStep -StepNum 1 -Command "raps plugin alias add `"bl`" `"bucket list`""
Invoke-LifecycleStep -StepNum 2 -Command "raps plugin alias add `"ol`" `"object list`""
Invoke-LifecycleStep -StepNum 3 -Command "raps plugin alias add `"ts`" `"translate status`""
Invoke-LifecycleStep -StepNum 4 -Command "raps plugin alias list"
Invoke-LifecycleStep -StepNum 5 -Command "raps bl"
Invoke-LifecycleStep -StepNum 6 -Command "raps plugin alias remove `"bl`""
Invoke-LifecycleStep -StepNum 7 -Command "raps plugin alias list"
End-Lifecycle

End-Section
