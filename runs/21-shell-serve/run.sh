#!/bin/bash
# Section 21 — Shell, Serve, Completions
# Runs: SR-300 through SR-305
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "21-shell-serve" "Shell, Serve, Completions"

# ── Atomic commands ──────────────────────────────────────────────

# SR-300: Interactive shell (long-running; auto-exit)
run_sample "SR-300" "shell-interactive" \
  "timeout 3 raps shell <<< \"exit\" || true" \
  "Expected: Starts REPL" \
  "Review: Prompt appears; exit quits"

# SR-301: MCP server (long-running; auto-kill)
run_sample "SR-301" "serve-mcp" \
  "timeout 3 raps serve || true" \
  "Expected: Starts MCP server" \
  "Review: Server starts; timeout exits cleanly"

# SR-302: Bash completions
run_sample "SR-302" "completions-bash" \
  "raps completions bash" \
  "Expected: Outputs bash completions" \
  "Review: Valid bash completion script"

# SR-303: PowerShell completions
run_sample "SR-303" "completions-powershell" \
  "raps completions powershell" \
  "Expected: Outputs PowerShell completions" \
  "Review: Valid PowerShell completion script"

# SR-304: Zsh completions
run_sample "SR-304" "completions-zsh" \
  "raps completions zsh" \
  "Expected: Outputs zsh completions" \
  "Review: Valid zsh completion script"

# SR-305: Fish completions
run_sample "SR-305" "completions-fish" \
  "raps completions fish" \
  "Expected: Outputs fish completions" \
  "Review: Valid fish completion script"

section_end
