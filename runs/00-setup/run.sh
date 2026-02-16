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
# Creates minimal test data that other sections depend on (SR-054, 055, 064, 065, 100, 311, 313)
run_sample "SR-003" "setup-generate-test-files" \
  "mkdir -p ./test-data && printf 'ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION((),\"2;1\");\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n' > ./test-data/sample.ifc && dd if=/dev/urandom bs=1024 count=10 of=./test-data/sample.rvt 2>/dev/null && echo 'Test data generated: sample.ifc, sample.rvt'" \
  "Expected: Generates test files in ./test-data/" \
  "Review: Directory contains sample.ifc and sample.rvt; exit code 0"

section_end
