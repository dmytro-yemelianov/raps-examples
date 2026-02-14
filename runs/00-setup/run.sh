#!/bin/bash
# Section 00 — Setup & Prerequisites
# Runs: SR-001 through SR-003
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "00-setup" "Setup & Prerequisites"

# SR-001: Verify APS environment variables are configured
run_sample "SR-001" "setup-env-file" \
  "env | grep -E '^APS_(CLIENT_ID|CLIENT_SECRET|CALLBACK_URL)='" \
  "Expected: Environment variables are set" \
  "Review: All 3 vars present and non-empty"

# SR-002: Verify raps-mock is running (if targeting mock)
run_sample "SR-002" "setup-mock-server" \
  "echo 'Verify raps-mock is running on port 3000'" \
  "Expected: Server listening on port 3000" \
  "Review: curl http://localhost:3000/health returns 200"

# SR-003: Generate test files for subsequent sections
run_sample "SR-003" "setup-generate-test-files" \
  "raps generate files --count 5 --output ./test-data --complexity medium" \
  "Expected: Generates 5 files of each type in ./test-data/" \
  "Review: Directory contains IFC, RVT, DWG, NWD, PDF files; exit code 0"

section_end
