#!/bin/bash
# Section 14 — Reality Capture
# Runs: SR-230 through SR-238
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "14-reality-capture" "Reality Capture"

# --- Pre-seed demo environment variables (override with real values) ---
: "${JOB_ID:=job-demo-001}"
: "${JID:=job-demo-001}"
: "${ID:=job-demo-001}"

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
  "raps reality create --name \"Site Survey 2026-02\" -f obj" \
  "Expected: Creates a new reality capture job" \
  "Review: Exit 0; output contains job ID"

# SR-233: Upload photos to a job
run_sample "SR-233" "reality-upload" \
  "raps reality upload \$JOB_ID ./site-photos/*" \
  "Expected: Uploads photos to the reality capture job" \
  "Review: Exit 0; shows uploaded photo count"

# SR-234: Start processing a job
run_sample "SR-234" "reality-process" \
  "raps reality process \$JOB_ID" \
  "Expected: Starts photogrammetry processing" \
  "Review: Exit 0; job status changes to processing"

# SR-235: Check job status
run_sample "SR-235" "reality-status" \
  "raps reality status \$JOB_ID" \
  "Expected: Shows current job status and progress" \
  "Review: Contains status, progress percentage, and timing"

# SR-236: Download job results
run_sample "SR-236" "reality-result" \
  "raps reality result \$JOB_ID" \
  "Expected: Gets download link for processed output" \
  "Review: Exit 0; returns download URL"

# SR-237: Delete a reality capture job
run_sample "SR-237" "reality-delete" \
  "raps reality delete \$JOB_ID" \
  "Expected: Deletes the reality capture job" \
  "Review: Exit 0; job no longer appears in list"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-238: Capture and process construction site
lifecycle_start "SR-238" "reality-capture-lifecycle" "Capture and process construction site"
lifecycle_step 1 "raps reality formats"
lifecycle_step 2 "raps reality create --name \"Foundation Survey\" -f obj"
lifecycle_step 3 "raps reality upload \$JID ./site-photos/*"
lifecycle_step 4 "raps reality process \$JID"
lifecycle_step 5 "raps reality status \$JID"
lifecycle_step 6 "raps reality result \$JID"
lifecycle_step 7 "raps reality list"
lifecycle_step 8 "raps reality delete \$JID"
lifecycle_end

section_end
