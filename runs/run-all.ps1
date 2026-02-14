# run-all.ps1 — Master orchestrator for all sample run sections (PowerShell)
#
# Usage:
#   .\run-all.ps1                              # Run all sections against real APS
#   $env:RAPS_TARGET="mock"; .\run-all.ps1     # Run all sections against raps-mock
#   .\run-all.ps1 -Sections 01-auth,03-storage # Run specific sections only
param(
    [string[]]$Sections
)

$ErrorActionPreference = "Continue"

$env:RUN_TIMESTAMP = if ($env:RUN_TIMESTAMP) { $env:RUN_TIMESTAMP } else { Get-Date -Format "yyyy-MM-dd-HH-mm" }
$env:LOGS_ROOT = if ($env:LOGS_ROOT) { $env:LOGS_ROOT } else { Join-Path (Split-Path -Parent $PSScriptRoot) "logs" }
$env:RAPS_TARGET = if ($env:RAPS_TARGET) { $env:RAPS_TARGET } else { "real" }

$LogDir = Join-Path $env:LOGS_ROOT $env:RUN_TIMESTAMP
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Write-Output "========================================"
Write-Output "RAPS CLI Sample Runs"
Write-Output "========================================"
Write-Output ""
Write-Output "Target:    $($env:RAPS_TARGET)"
Write-Output "Timestamp: $($env:RUN_TIMESTAMP)"
Write-Output "Logs:      $LogDir"
Write-Output ""

$AllSections = @(
    "00-setup"
    "01-auth"
    "02-config"
    "03-storage"
    "04-data-management"
    "05-model-derivative"
    "06-design-automation"
    "07-acc-issues"
    "08-acc-rfi"
    "09-acc-modules"
    "10-webhooks"
    "11-admin-users"
    "12-admin-projects"
    "13-admin-folders"
    "14-reality-capture"
    "15-reporting"
    "16-templates"
    "17-plugins"
    "18-pipelines"
    "19-api-raw"
    "20-generation"
    "21-shell-serve"
    "22-demo"
    "30-workflows"
    "99-cross-cutting"
)

if ($Sections.Count -gt 0) {
    $RunSections = $Sections
}
else {
    $RunSections = $AllSections
}

$Total = 0
$Passed = 0
$Failed = 0
$Skipped = 0

foreach ($section in $RunSections) {
    $sectionScript = Join-Path $PSScriptRoot "$section\run.ps1"

    if (Test-Path $sectionScript) {
        Write-Output "--- Running: $section ---"
        try {
            & $sectionScript
            Write-Output "  OK: $section"
            $Passed++
        }
        catch {
            Write-Output "  FAIL: $section"
            $Failed++
        }
        $Total++
    }
    else {
        Write-Output "  SKIP: $section (no run.ps1)"
        $Skipped++
    }
}

Write-Output ""
Write-Output "========================================"
Write-Output "Sample Runs Complete"
Write-Output "========================================"
Write-Output "Sections:  $Total run, $Passed ok, $Failed fail, $Skipped skip"
Write-Output "Logs:      $LogDir"
Write-Output ""
Write-Output "Review:"
Write-Output "  Get-Content $LogDir\<section>.log"
Write-Output "  Get-Content $LogDir\<section>.json | ConvertFrom-Json"

if ($Failed -gt 0) {
    exit 1
}
