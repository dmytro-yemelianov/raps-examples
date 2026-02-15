# Section 14 — Reality Capture
# Runs: SR-230 through SR-238
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "14-reality-capture" -Title "Reality Capture"

# -- Atomic commands -------------------------------------------------------

# SR-230: List reality capture jobs
Invoke-Sample -Id "SR-230" -Slug "reality-list" `
  -Command "raps reality list" `
  -Expects "Expected: Lists all reality capture jobs" `
  -Review "Review: Contains job IDs, names, and statuses"

# SR-231: List supported output formats
Invoke-Sample -Id "SR-231" -Slug "reality-formats" `
  -Command "raps reality formats" `
  -Expects "Expected: Lists supported output formats" `
  -Review "Review: Contains format names (obj, rcp, etc.)"

# SR-232: Create a reality capture job
Invoke-Sample -Id "SR-232" -Slug "reality-create" `
  -Command "raps reality create --name `"Site Survey 2026-02`" -f obj" `
  -Expects "Expected: Creates a new reality capture job" `
  -Review "Review: Exit 0; output contains job ID"

# SR-233: Upload photos to a job
Invoke-Sample -Id "SR-233" -Slug "reality-upload" `
  -Command "raps reality upload $env:JOB_ID ./site-photos/*" `
  -Expects "Expected: Uploads photos to the reality capture job" `
  -Review "Review: Exit 0; shows uploaded photo count"

# SR-234: Start processing a job
Invoke-Sample -Id "SR-234" -Slug "reality-process" `
  -Command "raps reality process $env:JOB_ID" `
  -Expects "Expected: Starts photogrammetry processing" `
  -Review "Review: Exit 0; job status changes to processing"

# SR-235: Check job status
Invoke-Sample -Id "SR-235" -Slug "reality-status" `
  -Command "raps reality status $env:JOB_ID" `
  -Expects "Expected: Shows current job status and progress" `
  -Review "Review: Contains status, progress percentage, and timing"

# SR-236: Download job results
Invoke-Sample -Id "SR-236" -Slug "reality-result" `
  -Command "raps reality result $env:JOB_ID" `
  -Expects "Expected: Gets download link for processed output" `
  -Review "Review: Exit 0; returns download URL"

# SR-237: Delete a reality capture job
Invoke-Sample -Id "SR-237" -Slug "reality-delete" `
  -Command "raps reality delete $env:JOB_ID" `
  -Expects "Expected: Deletes the reality capture job" `
  -Review "Review: Exit 0; job no longer appears in list"

# -- Lifecycles ------------------------------------------------------------

# SR-238: Capture and process construction site
Start-Lifecycle -Id "SR-238" -Slug "reality-capture-lifecycle" -Description "Capture and process construction site"
Invoke-LifecycleStep -StepNum 1 -Command "raps reality formats"
Invoke-LifecycleStep -StepNum 2 -Command "raps reality create --name `"Foundation Survey`" -f obj"
Invoke-LifecycleStep -StepNum 3 -Command "raps reality upload $env:JID ./site-photos/*"
Invoke-LifecycleStep -StepNum 4 -Command "raps reality process $env:JID"
Invoke-LifecycleStep -StepNum 5 -Command "raps reality status $env:JID"
Invoke-LifecycleStep -StepNum 6 -Command "raps reality result $env:JID"
Invoke-LifecycleStep -StepNum 7 -Command "raps reality list"
Invoke-LifecycleStep -StepNum 8 -Command "raps reality delete $env:JID"
End-Lifecycle

End-Section
