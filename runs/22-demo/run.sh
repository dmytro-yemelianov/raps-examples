#!/bin/bash
# Section 22 — Demo
# Runs: SR-310 through SR-313
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "22-demo" "Demo"

# ── Atomic commands ──────────────────────────────────────────────

# SR-310: Bucket lifecycle demo (increased timeout)
RAPS_CMD_TIMEOUT=120 run_sample "SR-310" "demo-bucket-lifecycle" \
  "raps demo bucket-lifecycle --non-interactive || true" \
  "Expected: Runs bucket lifecycle demo" \
  "Review: Creates/lists/deletes buckets; may timeout on slow API"

# SR-311: Model pipeline demo
if [ -f ./test-data/sample.rvt ]; then
  RAPS_CMD_TIMEOUT=120 run_sample "SR-311" "demo-model-pipeline" \
    "raps demo model-pipeline --input ./test-data/sample.rvt --non-interactive || true" \
    "Expected: Runs model pipeline demo" \
    "Review: Uploads and translates model file"
else
  skip_sample "SR-311" "demo-model-pipeline" "missing ./test-data/sample.rvt (run 00-setup first)"
fi

# SR-312: Data management demo
run_sample "SR-312" "demo-data-management" \
  "raps demo data-management --non-interactive --export ./dm-report.json" \
  "Expected: Runs data management demo" \
  "Review: Exit 0; exports report to JSON"

# SR-313: Batch processing demo
if [ -d ./test-data ]; then
  RAPS_CMD_TIMEOUT=120 run_sample "SR-313" "demo-batch-processing" \
    "raps demo batch-processing --input ./test-data/ --non-interactive || true" \
    "Expected: Processes test files in batch" \
    "Review: Iterates over test files; may fail on API errors"
else
  skip_sample "SR-313" "demo-batch-processing" "missing ./test-data/ (run 00-setup first)"
fi

section_end
