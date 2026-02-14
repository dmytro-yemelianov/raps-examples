# Section 21 — Shell, Serve, Completions
# Runs: SR-300 through SR-305
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "21-shell-serve" -Title "Shell, Serve, Completions"

# -- Atomic commands -------------------------------------------------------

# SR-300: Interactive shell (long-running; auto-exit)
Invoke-Sample -Id "SR-300" -Slug "shell-interactive" `
  -Command "echo `"exit`" | raps shell" `
  -Expects "Expected: Starts REPL" `
  -Review "Review: Prompt appears; exit quits"

# SR-301: MCP server (long-running; auto-kill)
Invoke-Sample -Id "SR-301" -Slug "serve-mcp" `
  -Command "Start-Process raps -ArgumentList `"serve`" -PassThru | ForEach-Object { Start-Sleep 2; Stop-Process -Id `$_.Id -Force }" `
  -Expects "Expected: Starts MCP server" `
  -Review "Review: Server starts; process killed after 2s"

# SR-302: Bash completions
Invoke-Sample -Id "SR-302" -Slug "completions-bash" `
  -Command "raps completions bash" `
  -Expects "Expected: Outputs bash completions" `
  -Review "Review: Valid bash completion script"

# SR-303: PowerShell completions
Invoke-Sample -Id "SR-303" -Slug "completions-powershell" `
  -Command "raps completions powershell" `
  -Expects "Expected: Outputs PowerShell completions" `
  -Review "Review: Valid PowerShell completion script"

# SR-304: Zsh completions
Invoke-Sample -Id "SR-304" -Slug "completions-zsh" `
  -Command "raps completions zsh" `
  -Expects "Expected: Outputs zsh completions" `
  -Review "Review: Valid zsh completion script"

# SR-305: Fish completions
Invoke-Sample -Id "SR-305" -Slug "completions-fish" `
  -Command "raps completions fish" `
  -Expects "Expected: Outputs fish completions" `
  -Review "Review: Valid fish completion script"

End-Section
