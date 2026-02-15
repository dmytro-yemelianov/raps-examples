# Section 15 — Portfolio Reports
# Runs: SR-240 through SR-244
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "15-reporting" -Title "Portfolio Reports"

# --- Pre-seed demo environment variables (override with real values) ---
if (-not $env:ACCOUNT_ID) { $env:ACCOUNT_ID = "demo-account-001" }

# -- Atomic commands -------------------------------------------------------

# SR-240: RFI summary report
Invoke-Sample -Id "SR-240" -Slug "report-rfi-summary" `
  -Command "raps report rfi-summary -a $env:ACCOUNT_ID -f `"Tower`" --status open --since `"2026-01-01`"" `
  -Expects "Expected: Aggregated RFI summary" `
  -Review "Review: Per-project RFI counts"

# SR-241: Issues summary report
Invoke-Sample -Id "SR-241" -Slug "report-issues-summary" `
  -Command "raps report issues-summary -a $env:ACCOUNT_ID -f `"Phase 2`" --status open" `
  -Expects "Expected: Aggregated issue summary" `
  -Review "Review: Per-project issue counts"

# SR-242: Submittals summary report
Invoke-Sample -Id "SR-242" -Slug "report-submittals-summary" `
  -Command "raps report submittals-summary -a $env:ACCOUNT_ID" `
  -Expects "Expected: Submittal summary" `
  -Review "Review: Per-project counts by status"

# SR-243: Checklists summary report
Invoke-Sample -Id "SR-243" -Slug "report-checklists-summary" `
  -Command "raps report checklists-summary -a $env:ACCOUNT_ID --status `"in_progress`"" `
  -Expects "Expected: Checklist summary" `
  -Review "Review: Per-project completion stats"

# SR-244: Assets summary report
Invoke-Sample -Id "SR-244" -Slug "report-assets-summary" `
  -Command "raps report assets-summary -a $env:ACCOUNT_ID -f `"Hospital`"" `
  -Expects "Expected: Asset summary" `
  -Review "Review: Per-project counts by category"

End-Section
