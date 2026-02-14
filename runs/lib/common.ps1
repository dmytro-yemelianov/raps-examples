# common.ps1 — Shared helpers for sample run scripts (PowerShell/Windows)
#
# Provides: Start-Section, End-Section, Invoke-Sample, Start-Lifecycle,
#           Invoke-LifecycleStep, End-Lifecycle, logging, mock-aware command routing
#
# Usage: . "$PSScriptRoot\..\lib\common.ps1"

$ErrorActionPreference = "Continue"

# --- Directories ---
$script:RunsDir = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$script:LogsRoot = if ($env:LOGS_ROOT) { $env:LOGS_ROOT } else { Join-Path (Split-Path -Parent $script:RunsDir) "logs" }
$script:RunTimestamp = if ($env:RUN_TIMESTAMP) { $env:RUN_TIMESTAMP } else { Get-Date -Format "yyyy-MM-dd-HH-mm" }
$script:LogDir = Join-Path $script:LogsRoot $script:RunTimestamp
New-Item -ItemType Directory -Force -Path $script:LogDir | Out-Null

# --- Target (real or mock) ---
$script:RapsTarget = if ($env:RAPS_TARGET) { $env:RAPS_TARGET } else { "real" }
$script:MockPort = if ($env:MOCK_PORT) { $env:MOCK_PORT } else { "3000" }
$script:MockBaseUrl = "http://localhost:$script:MockPort"

# --- State ---
$script:CurrentSection = ""
$script:CurrentSectionLog = ""
$script:CurrentSectionJson = ""
$script:SectionRunCount = 0
$script:SectionOkCount = 0
$script:SectionFailCount = 0
$script:LifecycleId = ""
$script:LifecycleStepNum = 0

# --- Helpers ---

function Get-RapsCmd {
    param([string]$Command)
    if ($script:RapsTarget -eq "mock") {
        return "$Command --base-url $script:MockBaseUrl"
    }
    return $Command
}

function Write-Log {
    param([string]$Message)
    $Message | Tee-Object -FilePath $script:CurrentSectionLog -Append
}

function Initialize-JsonLog {
    param([string]$Name, [string]$Title)
    $obj = @{
        section   = $Name
        title     = $Title
        target    = $script:RapsTarget
        timestamp = (Get-Date -Format "o")
        runs      = @()
    }
    $obj | ConvertTo-Json -Depth 10 | Set-Content -Path $script:CurrentSectionJson -Encoding UTF8
}

function Add-JsonRun {
    param([string]$Id, [string]$Slug, [string]$Command, [int]$ExitCode, [double]$Duration)
    $data = Get-Content -Path $script:CurrentSectionJson -Raw | ConvertFrom-Json
    $run = @{
        id               = $Id
        slug             = $Slug
        command          = $Command
        exit_code        = $ExitCode
        duration_seconds = $Duration
        target           = $script:RapsTarget
    }
    $data.runs += [PSCustomObject]$run
    $data | ConvertTo-Json -Depth 10 | Set-Content -Path $script:CurrentSectionJson -Encoding UTF8
}

# --- Section ---

function Start-Section {
    param([string]$Name, [string]$Title)
    $script:CurrentSection = $Name
    $script:CurrentSectionLog = Join-Path $script:LogDir "$Name.log"
    $script:CurrentSectionJson = Join-Path $script:LogDir "$Name.json"
    $script:SectionRunCount = 0
    $script:SectionOkCount = 0
    $script:SectionFailCount = 0

    Initialize-JsonLog -Name $Name -Title $Title

    Write-Log ""
    Write-Log "========================================"
    Write-Log "  $Title"
    Write-Log "  Target: $script:RapsTarget"
    Write-Log "========================================"
    Write-Log ""
}

function End-Section {
    Write-Log ""
    Write-Log "----------------------------------------"
    Write-Log "Section $($script:CurrentSection): $($script:SectionRunCount) runs ($($script:SectionOkCount) ok, $($script:SectionFailCount) fail)"
    Write-Log "Log:  $script:CurrentSectionLog"
    Write-Log "JSON: $script:CurrentSectionJson"
    Write-Log ""
}

# --- Run a single sample ---

function Invoke-Sample {
    param(
        [string]$Id,
        [string]$Slug,
        [string]$Command,
        [string]$Expects,
        [string]$Review
    )
    $script:SectionRunCount++

    $actualCmd = Get-RapsCmd -Command $Command

    Write-Log "[$Id] $Slug"
    Write-Log "  Command:  $actualCmd"
    Write-Log "  Expects:  $Expects"
    Write-Log "  Review:   $Review"

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $exitCode = 0

    try {
        $output = Invoke-Expression $actualCmd 2>&1
        $output | Out-File -FilePath $script:CurrentSectionLog -Append -Encoding UTF8
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) { $exitCode = 0 }
    }
    catch {
        $exitCode = 1
        $_.Exception.Message | Out-File -FilePath $script:CurrentSectionLog -Append -Encoding UTF8
    }

    $sw.Stop()
    $duration = [math]::Round($sw.Elapsed.TotalSeconds, 3)

    if ($exitCode -eq 0) {
        Write-Log "  Exit: $exitCode ($($duration)s)"
        $script:SectionOkCount++
    }
    else {
        Write-Log "  EXIT: $exitCode ($($duration)s)"
        $script:SectionFailCount++
    }
    Write-Log ""

    Add-JsonRun -Id $Id -Slug $Slug -Command $actualCmd -ExitCode $exitCode -Duration $duration
}

# --- Lifecycle helpers ---

function Start-Lifecycle {
    param([string]$Id, [string]$Slug, [string]$Description)
    $script:LifecycleId = $Id
    $script:LifecycleStepNum = 0
    Write-Log "[$Id] Lifecycle: $Slug"
    Write-Log "  $Description"
}

function Invoke-LifecycleStep {
    param([int]$StepNum, [string]$Command)
    $script:LifecycleStepNum++

    $actualCmd = Get-RapsCmd -Command $Command

    Write-Log "  Step $($StepNum): $actualCmd"

    $exitCode = 0
    try {
        $output = Invoke-Expression $actualCmd 2>&1
        $output | Out-File -FilePath $script:CurrentSectionLog -Append -Encoding UTF8
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) { $exitCode = 0 }
    }
    catch {
        $exitCode = 1
    }

    if ($exitCode -eq 0) {
        Write-Log "    -> exit $exitCode"
    }
    else {
        Write-Log "    -> EXIT $exitCode"
    }
}

function End-Lifecycle {
    Write-Log "  Lifecycle $($script:LifecycleId) complete ($($script:LifecycleStepNum) steps)"
    Write-Log ""
    $script:LifecycleId = ""
    $script:LifecycleStepNum = 0
    $script:SectionRunCount++
    $script:SectionOkCount++
}
