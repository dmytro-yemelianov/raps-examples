#!/bin/bash
# Section 18 — Pipelines
# Runs: SR-270 through SR-273
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "18-pipelines" "Pipelines"

# ── Atomic commands ──────────────────────────────────────────────

# SR-270: Generate sample pipeline YAML
run_sample "SR-270" "pipeline-sample" \
  "raps pipeline sample -o ./sample-pipeline.yaml" \
  "Expected: Generates sample YAML" \
  "Review: File created with valid pipeline structure"

# SR-271: Validate pipeline file
run_sample "SR-271" "pipeline-validate" \
  "raps pipeline validate ./sample-pipeline.yaml" \
  "Expected: Validates structure" \
  "Review: Exit 0; reports valid or lists errors"

# SR-272: Run a pipeline
run_sample "SR-272" "pipeline-run" \
  "raps pipeline run ./sample-pipeline.yaml" \
  "Expected: Executes pipeline" \
  "Review: Exit 0; shows step-by-step progress"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-273: DevOps creates and runs pipeline
lifecycle_start "SR-273" "pipeline-author-and-run" "DevOps creates and runs pipeline"
lifecycle_step 1 "raps pipeline sample -o ./my-pipeline.yaml"
lifecycle_step 2 "raps pipeline validate ./my-pipeline.yaml"
lifecycle_step 3 "raps pipeline run ./my-pipeline.yaml"
lifecycle_end

section_end
