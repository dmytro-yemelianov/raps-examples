#!/bin/bash
# Section 06 — Design Automation
# Runs: SR-110 through SR-121
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "06-design-automation" "Design Automation"
require_2leg_auth || { section_end; exit 0; }

# --- Pre-seed demo environment variables (override with real values) ---
: "${SIGNED_URL:=https://developer.api.autodesk.com/oss/v2/buckets/demo/objects/model.rvt?token=demo}"
: "${INPUT_URL:=https://developer.api.autodesk.com/oss/v2/buckets/demo/objects/input.rvt?token=demo}"
: "${OUTPUT_URL:=https://developer.api.autodesk.com/oss/v2/buckets/demo/objects/output.json?token=demo}"
: "${WORKITEM_ID:=demo-workitem-001}"

# ── Engine & AppBundle atomics ────────────────────────────────────

# SR-110: List DA engines
run_sample "SR-110" "da-engines" \
  "raps da engines" \
  "Expected: Lists DA engines" \
  "Review: Contains engine names/versions"

# SR-111: List appbundles
run_sample "SR-111" "da-appbundles-list" \
  "raps da appbundles" \
  "Expected: Lists appbundles" \
  "Review: List output"

# SR-112: Create an appbundle (DA nickname defaults to "default")
run_sample "SR-112" "da-appbundle-create" \
  "raps da appbundle create sr-test-bundle --engine \"Autodesk.Revit+2025\" --description \"RAPS test bundle\" || true" \
  "Expected: Appbundle created or error (no DA nickname)" \
  "Review: 200 with bundle details or 4xx error"

# SR-113: Delete an appbundle
run_sample "SR-113" "da-appbundle-delete" \
  "raps da appbundle delete sr-test-bundle || true" \
  "Expected: Appbundle deleted or 404" \
  "Review: Exit 0 (deleted) or non-zero (not found)"

# ── Activity atomics ─────────────────────────────────────────────

# SR-114: List activities
run_sample "SR-114" "da-activities-list" \
  "raps da activities" \
  "Expected: Lists activities" \
  "Review: Contains activity IDs"

# SR-115: Create an activity
run_sample "SR-115" "da-activity-create" \
  "raps da activity create sr-test-activity --engine \"Autodesk.Revit+2025\" --command-line '\$(engine.path)\\\\revitcoreconsole.exe /i \$(args[input].path)' --appbundles \"sr-test-bundle\" || true" \
  "Expected: Activity created or error" \
  "Review: 200 with activity details or 4xx error"

# SR-116: Delete an activity
run_sample "SR-116" "da-activity-delete" \
  "raps da activity delete sr-test-activity || true" \
  "Expected: Activity deleted or 404" \
  "Review: Exit 0 (deleted) or non-zero (not found)"

# ── Work item atomics ────────────────────────────────────────────

# SR-117: Submit a work item
run_sample "SR-117" "da-run" \
  "raps da run sr-test-activity --input \"$INPUT_URL\" --output \"$OUTPUT_URL\" || true" \
  "Expected: Work item submitted or error (no activity)" \
  "Review: Returns work item ID or 4xx error"

# SR-118: List work items (fixed: now includes startAfterTime param)
run_sample "SR-118" "da-workitems" \
  "raps da workitems || true" \
  "Expected: Lists recent work items (past 24h)" \
  "Review: Contains work item IDs and statuses"

# SR-119: Show work item status
run_sample "SR-119" "da-status" \
  "raps da status $WORKITEM_ID || true" \
  "Expected: Work item status or 404 for dummy ID" \
  "Review: Shows status, progress, or 404 error"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-120: Register and test a Revit plugin
lifecycle_start "SR-120" "da-appbundle-lifecycle" "AppBundle create → list → delete"
lifecycle_step 1 "raps da appbundle create sr-lifecycle-bundle --engine \"Autodesk.Revit+2025\""
lifecycle_step 2 "raps da appbundles"
lifecycle_step 3 "raps da appbundle delete sr-lifecycle-bundle"
lifecycle_end

# SR-121: Run and monitor a DA job
lifecycle_start "SR-121" "da-workitem-lifecycle" "Activity create → run → status → cleanup"
lifecycle_step 1 "raps da activity create sr-lifecycle-activity --engine \"Autodesk.Revit+2025\" --command-line 'test' --appbundles \"sr-lifecycle-bundle\""
lifecycle_step 2 "raps da run sr-lifecycle-activity --input \"$INPUT_URL\" --output \"$OUTPUT_URL\""
lifecycle_step 3 "raps da workitems"
lifecycle_step 4 "raps da activity delete sr-lifecycle-activity"
lifecycle_end

section_end
