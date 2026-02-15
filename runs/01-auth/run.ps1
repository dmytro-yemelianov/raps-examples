# Section 01 — Authentication
# Runs: SR-010 through SR-024
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "01-auth" -Title "Authentication"

# --- Pre-seed demo environment variables (override with real values) ---
if (-not $env:EXTERNAL_TOKEN) { $env:EXTERNAL_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.demo-token-for-testing" }

# -- Atomic commands ---------------------------------------------------

# SR-010: Test 2-legged auth (client credentials)
Invoke-Sample -Id "SR-010" -Slug "auth-test-2leg" `
  -Command "raps auth test" `
  -Expects "Expected: 2-legged token obtained successfully" `
  -Review "Review: Exit code 0; output confirms valid credentials"

# SR-011: Interactive 3-legged login (browser-based)
Invoke-Sample -Id "SR-011" -Slug "auth-login-3leg-browser" `
  -Command "raps auth login" `
  -Expects "Expected: Browser opens for OAuth consent; token stored" `
  -Review "Review: Exit code 0; callback received; token persisted"

# SR-012: Device code flow login
Invoke-Sample -Id "SR-012" -Slug "auth-login-device-code" `
  -Command "raps auth login --device" `
  -Expects "Expected: Device code displayed; user authorizes in browser" `
  -Review "Review: Exit code 0; token stored after device authorization"

# SR-013: Direct token injection
Invoke-Sample -Id "SR-013" -Slug "auth-login-token-direct" `
  -Command "raps auth login --token 'eyJ...'" `
  -Expects "Expected: Provided token stored directly" `
  -Review "Review: Exit code 0; token persisted without exchange"

# SR-014: Refresh token login with explicit expiry
Invoke-Sample -Id "SR-014" -Slug "auth-login-refresh-token" `
  -Command "raps auth login --refresh-token 'rt_...' --expires-in 3600" `
  -Expects "Expected: Refresh token exchanged for access token" `
  -Review "Review: Exit code 0; access token valid for 3600s"

# SR-015: Check auth status
Invoke-Sample -Id "SR-015" -Slug "auth-status" `
  -Command "raps auth status" `
  -Expects "Expected: Current auth state displayed" `
  -Review "Review: Shows token type, expiry, and profile"

# SR-016: Display authenticated user identity
Invoke-Sample -Id "SR-016" -Slug "auth-whoami" `
  -Command "raps auth whoami" `
  -Expects "Expected: User identity information returned" `
  -Review "Review: Shows user ID, email, and name"

# SR-017: Inspect token details
Invoke-Sample -Id "SR-017" -Slug "auth-inspect" `
  -Command "raps auth inspect" `
  -Expects "Expected: Token claims and metadata shown" `
  -Review "Review: Displays scopes, issuer, expiry timestamp"

# SR-018: Inspect token with expiry warning threshold
Invoke-Sample -Id "SR-018" -Slug "auth-inspect-warn" `
  -Command "raps auth inspect --warn-expiry-seconds 7200" `
  -Expects "Expected: Token inspected with 2-hour warning threshold" `
  -Review "Review: Warning emitted if token expires within 7200s"

# SR-019: Logout and clear stored token
Invoke-Sample -Id "SR-019" -Slug "auth-logout" `
  -Command "raps auth logout" `
  -Expects "Expected: Stored token removed" `
  -Review "Review: Exit code 0; subsequent auth commands require re-login"

# SR-020: Login using default profile
Invoke-Sample -Id "SR-020" -Slug "auth-login-default-profile" `
  -Command "raps auth login --default" `
  -Expects "Expected: Login using default profile credentials" `
  -Review "Review: Exit code 0; default profile activated"

# -- Lifecycles --------------------------------------------------------

# SR-021: Full 2-legged auth cycle
Start-Lifecycle -Id "SR-021" -Slug "auth-lifecycle-2leg" -Description "Full 2-legged auth cycle"
Invoke-LifecycleStep -StepNum 1 -Command "raps auth test"
Invoke-LifecycleStep -StepNum 2 -Command "raps auth status"
Invoke-LifecycleStep -StepNum 3 -Command "raps auth inspect"
Invoke-LifecycleStep -StepNum 4 -Command "raps auth logout"
Invoke-LifecycleStep -StepNum 5 -Command "raps auth test"
End-Lifecycle

# SR-022: Full 3-legged auth cycle
Start-Lifecycle -Id "SR-022" -Slug "auth-lifecycle-3leg" -Description "Full 3-legged auth cycle"
Invoke-LifecycleStep -StepNum 1 -Command "raps auth login"
Invoke-LifecycleStep -StepNum 2 -Command "raps auth whoami"
Invoke-LifecycleStep -StepNum 3 -Command "raps auth status"
Invoke-LifecycleStep -StepNum 4 -Command "raps auth inspect --warn-expiry-seconds 86400"
Invoke-LifecycleStep -StepNum 5 -Command "raps auth logout"
End-Lifecycle

# SR-023: Device code auth cycle
Start-Lifecycle -Id "SR-023" -Slug "auth-lifecycle-device" -Description "Device code auth cycle"
Invoke-LifecycleStep -StepNum 1 -Command "raps auth login --device"
Invoke-LifecycleStep -StepNum 2 -Command "raps auth test"
Invoke-LifecycleStep -StepNum 3 -Command "raps auth whoami"
Invoke-LifecycleStep -StepNum 4 -Command "raps auth logout"
End-Lifecycle

# SR-024: Token injection cycle
Start-Lifecycle -Id "SR-024" -Slug "auth-lifecycle-token-injection" -Description "Token injection cycle"
Invoke-LifecycleStep -StepNum 1 -Command "raps auth login --token `"$env:EXTERNAL_TOKEN`" --expires-in 1800"
Invoke-LifecycleStep -StepNum 2 -Command "raps auth test"
Invoke-LifecycleStep -StepNum 3 -Command "raps auth inspect"
Invoke-LifecycleStep -StepNum 4 -Command "raps auth logout"
End-Lifecycle

End-Section
