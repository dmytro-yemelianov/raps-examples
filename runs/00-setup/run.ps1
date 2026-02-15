# Section 00 — Setup & Prerequisites
# Runs: SR-001 through SR-003
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "00-setup" -Title "Setup & Prerequisites"

# SR-001: Verify APS environment variables are configured
Invoke-Sample -Id "SR-001" -Slug "setup-env-file" `
  -Command "Get-ChildItem env:APS_CLIENT_ID,env:APS_CLIENT_SECRET,env:APS_CALLBACK_URL" `
  -Expects "Expected: Environment variables are set" `
  -Review "Review: All 3 vars present and non-empty"

# SR-002: Verify raps-mock is running (if targeting mock)
Invoke-Sample -Id "SR-002" -Slug "setup-mock-server" `
  -Command "Write-Output 'Verify raps-mock is running on port 3000'" `
  -Expects "Expected: Server listening on port 3000" `
  -Review "Review: Invoke-WebRequest http://localhost:3000/health returns 200"

# SR-003: Generate test files for subsequent sections
Invoke-Sample -Id "SR-003" -Slug "setup-generate-test-files" `
  -Command "raps generate files -c 5 -o ./test-data --complexity medium" `
  -Expects "Expected: Generates 5 files of each type in ./test-data/" `
  -Review "Review: Directory contains IFC, RVT, DWG, NWD, PDF files; exit code 0"

End-Section
