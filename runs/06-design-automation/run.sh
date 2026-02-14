#!/bin/bash
# Section 06 — Design Automation
# Runs: SR-110 through SR-121
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "06-design-automation" "Design Automation"

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

# SR-112: Create an appbundle
run_sample "SR-112" "da-appbundle-create" \
  "raps da appbundle-create --name \"CountWalls\" --engine \"Autodesk.Revit+2025\" --bundle ./plugins/countwalls.zip" \
  "Expected: Creates appbundle" \
  "Review: Exit 0; contains ID"

# SR-113: Delete an appbundle
run_sample "SR-113" "da-appbundle-delete" \
  "raps da appbundle-delete --name \"CountWalls\"" \
  "Expected: Deletes appbundle" \
  "Review: Exit 0; gone from list"

# ── Activity atomics ─────────────────────────────────────────────

# SR-114: List activities
run_sample "SR-114" "da-activities-list" \
  "raps da activities" \
  "Expected: Lists activities" \
  "Review: Contains activity IDs"

# SR-115: Create an activity
run_sample "SR-115" "da-activity-create" \
  "raps da activity-create --name \"CountWallsActivity\" --engine \"Autodesk.Revit+2025\" --appbundle \"CountWalls\" --command-line \"...\"" \
  "Expected: Creates activity" \
  "Review: Exit 0; contains activity ID"

# SR-116: Delete an activity
run_sample "SR-116" "da-activity-delete" \
  "raps da activity-delete --name \"CountWallsActivity\"" \
  "Expected: Deletes activity" \
  "Review: Exit 0"

# ── Work item atomics ────────────────────────────────────────────

# SR-117: Submit a work item
run_sample "SR-117" "da-run" \
  "raps da run --activity \"CountWallsActivity\" --input-url \$SIGNED_URL --output-url \$OUTPUT_URL" \
  "Expected: Submits workitem" \
  "Review: Exit 0; contains work item ID"

# SR-118: List work items
run_sample "SR-118" "da-workitems" \
  "raps da workitems" \
  "Expected: Lists work items" \
  "Review: Contains IDs and statuses"

# SR-119: Show work item status
run_sample "SR-119" "da-status" \
  "raps da status --id \$WORKITEM_ID" \
  "Expected: Shows status" \
  "Review: Contains status field"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-120: Register and test a Revit plugin
lifecycle_start "SR-120" "da-appbundle-lifecycle" "Register and test a Revit plugin"
lifecycle_step 1 "raps da engines"
lifecycle_step 2 "raps da appbundle-create --name \"ExtractData\" --engine \"Autodesk.Revit+2025\" --bundle ./plugin.zip"
lifecycle_step 3 "raps da appbundles"
lifecycle_step 4 "raps da activity-create --name \"ExtractAct\" --engine \"Autodesk.Revit+2025\" --appbundle \"ExtractData\" --command-line \"...\""
lifecycle_step 5 "raps da activities"
lifecycle_step 6 "raps da activity-delete --name \"ExtractAct\""
lifecycle_step 7 "raps da appbundle-delete --name \"ExtractData\""
lifecycle_end

# SR-121: Run and monitor a DA job
lifecycle_start "SR-121" "da-workitem-lifecycle" "Run and monitor a DA job"
lifecycle_step 1 "raps object upload --bucket da-test --file ./model.rvt"
lifecycle_step 2 "raps object signed-url --bucket da-test --key model.rvt"
lifecycle_step 3 "raps da run --activity \"ExtractAct\" --input-url \$INPUT_URL --output-url \$OUTPUT_URL"
lifecycle_step 4 "raps da status --id \$WORKITEM_ID"
lifecycle_step 5 "raps da workitems"
lifecycle_step 6 "raps object download --bucket da-test --key output.json --output ./results/"
lifecycle_end

section_end
