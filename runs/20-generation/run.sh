#!/bin/bash
# Section 20 — Generation
# Runs: SR-290 through SR-291
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "20-generation" "Generation"

# ── Atomic commands ──────────────────────────────────────────────

# SR-290: Generate simple files
run_sample "SR-290" "generate-files-simple" \
  "raps generate files --count 1 --output ./gen-simple/ --complexity simple" \
  "Expected: Generates simple files" \
  "Review: Exit 0; files created in output directory"

# SR-291: Generate complex files
run_sample "SR-291" "generate-files-complex" \
  "raps generate files --count 10 --output ./gen-complex/ --complexity complex" \
  "Expected: Generates complex files" \
  "Review: Exit 0; 10 files created in output directory"

section_end
