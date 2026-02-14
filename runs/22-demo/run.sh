#!/bin/bash
# Section 22 — Demo
# Runs: SR-310 through SR-313
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "22-demo" "Demo"

# ── Atomic commands ──────────────────────────────────────────────

# SR-310: Bucket lifecycle demo
run_sample "SR-310" "demo-bucket-lifecycle" \
  "raps demo bucket-lifecycle --prefix \"demo\" --skip-cleanup" \
  "Expected: Runs bucket lifecycle demo" \
  "Review: Exit 0; creates, lists, and manages demo buckets"

# SR-311: Model pipeline demo
run_sample "SR-311" "demo-model-pipeline" \
  "raps demo model-pipeline --file ./test-data/sample.rvt --format svf2 --keep-bucket" \
  "Expected: Runs model pipeline demo" \
  "Review: Exit 0; uploads, translates, and verifies model"

# SR-312: Data management demo
run_sample "SR-312" "demo-data-management" \
  "raps demo data-management --non-interactive --export ./dm-report.json" \
  "Expected: Runs data management demo" \
  "Review: Exit 0; exports report to JSON"

# SR-313: Batch processing demo
run_sample "SR-313" "demo-batch-processing" \
  "raps demo batch-processing --input ./test-data/ --max-parallel 3 --format svf2 --skip-cleanup" \
  "Expected: Runs batch processing demo" \
  "Review: Exit 0; processes multiple files in parallel"

section_end
