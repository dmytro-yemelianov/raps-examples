#!/bin/bash
# Section 14 — Reality Capture
# Runs: SR-230 through SR-238
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "14-reality-capture" "Reality Capture"

# ── Atomic commands ──────────────────────────────────────────────

# SR-230: List reality capture jobs
run_sample "SR-230" "reality-list" \
  "raps reality list" \
  "Expected: Lists all reality capture jobs" \
  "Review: Contains job IDs, names, and statuses"

# SR-231: List supported output formats
run_sample "SR-231" "reality-formats" \
  "raps reality formats" \
  "Expected: Lists supported output formats" \
  "Review: Contains format names (obj, rcp, etc.)"

# SR-232: Create a reality capture job
run_sample "SR-232" "reality-create" \
  "raps reality create --name \"Site Survey 2026-02\" --format obj" \
  "Expected: Creates a new reality capture job" \
  "Review: Exit 0; output contains job ID"

# SR-233: Upload photos to a job
run_sample "SR-233" "reality-upload" \
  "raps reality upload --job \$JOB_ID --photos ./site-photos/" \
  "Expected: Uploads photos to the reality capture job" \
  "Review: Exit 0; shows uploaded photo count"

# SR-234: Start processing a job
run_sample "SR-234" "reality-process" \
  "raps reality process --job \$JOB_ID" \
  "Expected: Starts photogrammetry processing" \
  "Review: Exit 0; job status changes to processing"

# SR-235: Check job status
run_sample "SR-235" "reality-status" \
  "raps reality status --job \$JOB_ID" \
  "Expected: Shows current job status and progress" \
  "Review: Contains status, progress percentage, and timing"

# SR-236: Download job results
run_sample "SR-236" "reality-result" \
  "raps reality result --job \$JOB_ID --output ./results/" \
  "Expected: Downloads processed output files" \
  "Review: Exit 0; output files exist at specified path"

# SR-237: Delete a reality capture job
run_sample "SR-237" "reality-delete" \
  "raps reality delete --job \$JOB_ID --yes" \
  "Expected: Deletes the reality capture job" \
  "Review: Exit 0; job no longer appears in list"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-238: Capture and process construction site
lifecycle_start "SR-238" "reality-capture-lifecycle" "Capture and process construction site"
lifecycle_step 1 "raps reality formats"
lifecycle_step 2 "raps reality create --name \"Foundation Survey\" --format obj"
lifecycle_step 3 "raps reality upload --job \$JID --photos ./site-photos/"
lifecycle_step 4 "raps reality process --job \$JID"
lifecycle_step 5 "raps reality status --job \$JID"
lifecycle_step 6 "raps reality result --job \$JID --output ./survey-results/"
lifecycle_step 7 "raps reality list"
lifecycle_step 8 "raps reality delete --job \$JID --yes"
lifecycle_end

section_end
