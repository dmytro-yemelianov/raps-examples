# Section 02 — Configuration
# Runs: SR-030 through SR-045
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "02-config" -Title "Configuration"

# --- Pre-seed demo environment variables (override with real values) ---
if (-not $env:HUB_ID) { $env:HUB_ID = "b.demo-hub-001" }
if (-not $env:PROJECT_ID) { $env:PROJECT_ID = "b.demo-project-001" }

# -- Atomic commands ---------------------------------------------------

# SR-030: Show full configuration
Invoke-Sample -Id "SR-030" -Slug "config-show" `
  -Command "raps config get output_format" `
  -Expects "Expected: Full configuration displayed" `
  -Review "Review: Output includes client_id, output_format, active profile"

# SR-031: Get a single config value
Invoke-Sample -Id "SR-031" -Slug "config-get" `
  -Command "raps config get client_id" `
  -Expects "Expected: Value of client_id printed" `
  -Review "Review: Non-empty value matching APS_CLIENT_ID"

# SR-032: Set a config value
Invoke-Sample -Id "SR-032" -Slug "config-set" `
  -Command "raps config set output_format json" `
  -Expects "Expected: output_format updated to json" `
  -Review "Review: Exit code 0; subsequent config show reflects change"

# SR-033: Create a new profile
Invoke-Sample -Id "SR-033" -Slug "config-profile-create" `
  -Command "raps config profile create staging" `
  -Expects "Expected: Profile 'staging' created" `
  -Review "Review: Exit code 0; profile appears in profile list"

# SR-034: List all profiles
Invoke-Sample -Id "SR-034" -Slug "config-profile-list" `
  -Command "raps config profile list" `
  -Expects "Expected: All profiles listed" `
  -Review "Review: Shows default and staging profiles"

# SR-035: Switch to a profile
Invoke-Sample -Id "SR-035" -Slug "config-profile-use" `
  -Command "raps config profile use staging" `
  -Expects "Expected: Active profile switched to staging" `
  -Review "Review: Exit code 0; profile current shows staging"

# SR-036: Show current active profile
Invoke-Sample -Id "SR-036" -Slug "config-profile-current" `
  -Command "raps config profile current" `
  -Expects "Expected: Current profile name printed" `
  -Review "Review: Output shows 'staging'"

# SR-037: Export a profile to JSON
Invoke-Sample -Id "SR-037" -Slug "config-profile-export" `
  -Command "raps config profile export -n staging" `
  -Expects "Expected: Profile exported as JSON" `
  -Review "Review: Valid JSON output with profile settings"

# SR-038: Import a profile from JSON file
Invoke-Sample -Id "SR-038" -Slug "config-profile-import" `
  -Command "raps config profile import ./staging-profile.json" `
  -Expects "Expected: Profile imported from file" `
  -Review "Review: Exit code 0; imported profile appears in list"

# SR-039: Diff two profiles
Invoke-Sample -Id "SR-039" -Slug "config-profile-diff" `
  -Command "raps config profile diff default staging" `
  -Expects "Expected: Differences between profiles displayed" `
  -Review "Review: Shows changed keys with old/new values"

# SR-040: Delete a profile
Invoke-Sample -Id "SR-040" -Slug "config-profile-delete" `
  -Command "raps config profile delete staging" `
  -Expects "Expected: Profile 'staging' removed" `
  -Review "Review: Exit code 0; profile no longer in list"

# SR-041: Show current context
Invoke-Sample -Id "SR-041" -Slug "config-context-show" `
  -Command "raps config context show" `
  -Expects "Expected: Active hub/project context displayed" `
  -Review "Review: Shows hub ID and project ID (or empty if unset)"

# SR-042: Set context to specific hub and project
Invoke-Sample -Id "SR-042" -Slug "config-context-set" `
  -Command "raps config context set hub_id $env:HUB_ID; raps config context set project_id $env:PROJECT_ID" `
  -Expects "Expected: Context bound to specified hub and project" `
  -Review "Review: Exit code 0; context show reflects new values"

# SR-043: Clear context
Invoke-Sample -Id "SR-043" -Slug "config-context-clear" `
  -Command "raps config context clear" `
  -Expects "Expected: Context cleared" `
  -Review "Review: Exit code 0; context show returns empty"

# -- Lifecycles --------------------------------------------------------

# SR-044: Full profile CRUD lifecycle
Start-Lifecycle -Id "SR-044" -Slug "config-profile-lifecycle" -Description "Full profile CRUD"
Invoke-LifecycleStep -StepNum 1  -Command "raps config profile create test-profile"
Invoke-LifecycleStep -StepNum 2  -Command "raps config profile list"
Invoke-LifecycleStep -StepNum 3  -Command "raps config profile use test-profile"
Invoke-LifecycleStep -StepNum 4  -Command "raps config profile current"
Invoke-LifecycleStep -StepNum 5  -Command "raps config set output_format yaml"
Invoke-LifecycleStep -StepNum 6  -Command "raps config profile export -n test-profile"
Invoke-LifecycleStep -StepNum 7  -Command "raps config profile diff default test-profile"
Invoke-LifecycleStep -StepNum 8  -Command "raps config profile use default"
Invoke-LifecycleStep -StepNum 9  -Command "raps config profile delete test-profile"
Invoke-LifecycleStep -StepNum 10 -Command "raps config profile list"
End-Lifecycle

# SR-045: Context set and clear lifecycle
Start-Lifecycle -Id "SR-045" -Slug "config-context-lifecycle" -Description "Context set and clear"
Invoke-LifecycleStep -StepNum 1 -Command "raps config context clear"
Invoke-LifecycleStep -StepNum 2 -Command "raps config context show"
Invoke-LifecycleStep -StepNum 3 -Command "raps config context set hub_id $env:HUB_ID; raps config context set project_id $env:PROJECT_ID"
Invoke-LifecycleStep -StepNum 4 -Command "raps config context show"
Invoke-LifecycleStep -StepNum 5 -Command "raps hub list"
Invoke-LifecycleStep -StepNum 6 -Command "raps config context clear"
Invoke-LifecycleStep -StepNum 7 -Command "raps config context show"
End-Lifecycle

End-Section
