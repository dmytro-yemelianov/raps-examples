#!/bin/bash
# Section 05 — Model Derivative / Translation
# Runs: SR-090 through SR-101
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "05-model-derivative" "Model Derivative / Translation"

# --- Pre-seed demo environment variables (override with real values) ---
: "${OBJECT_URN:=dXJuOmFkc2sub2JqZWN0czpvcy5vYmplY3Q6ZGVtby1idWNrZXQvc2FtcGxlLmlmYw}"
: "${URN:=dXJuOmFkc2sub2JqZWN0czpvcy5vYmplY3Q6ZGVtby1idWNrZXQvc2FtcGxlLmlmYw}"
: "${ITEM_ID:=urn:adsk.wipprod:dm.lineage:demo-item-001}"
: "${FOLDER_ID:=urn:adsk.wipprod:fs.folder:co.demo-folder-001}"

# ── Atomic commands ──────────────────────────────────────────────

# SR-090: Start a translation job
run_sample "SR-090" "translate-start" \
  "raps translate start \$OBJECT_URN -f svf2" \
  "Expected: Starts a model translation job to SVF2 format" \
  "Review: Exit 0; output contains translation job URN and status"

# SR-091: Check translation status
run_sample "SR-091" "translate-status" \
  "raps translate status \$OBJECT_URN" \
  "Expected: Reports current translation progress" \
  "Review: Contains progress percentage and status (pending/inprogress/success/failed)"

# SR-092: Get translation manifest
run_sample "SR-092" "translate-manifest" \
  "raps translate manifest \$OBJECT_URN" \
  "Expected: Shows the translation manifest with derivative tree" \
  "Review: Contains derivative URN, output formats, and bubble structure"

# SR-093: List available derivatives
run_sample "SR-093" "translate-derivatives" \
  "raps translate derivatives \$OBJECT_URN" \
  "Expected: Lists all available derivative outputs for the model" \
  "Review: Contains derivative types (SVF, thumbnail, metadata) and roles"

# SR-094: Download derivatives
run_sample "SR-094" "translate-download" \
  "raps translate download \$OBJECT_URN -o ./derivatives/" \
  "Expected: Downloads derivative files to the specified directory" \
  "Review: Files exist at output path; directory contains derivative assets"

# SR-095: List translation presets
run_sample "SR-095" "translate-preset-list" \
  "raps translate preset list" \
  "Expected: Lists all saved translation presets" \
  "Review: Table or list with preset names and target formats"

# SR-096: Create a translation preset
run_sample "SR-096" "translate-preset-create" \
  "raps translate preset create --name \"svf2-default\" --format svf2" \
  "Expected: Creates a reusable translation preset" \
  "Review: Exit 0; output confirms preset saved with name and format"

# SR-097: Show a translation preset
run_sample "SR-097" "translate-preset-show" \
  "raps translate preset show --name \"svf2-default\"" \
  "Expected: Displays details of the specified preset" \
  "Review: Contains preset name, target format, and configuration"

# SR-098: Use a preset for translation
run_sample "SR-098" "translate-preset-use" \
  "raps translate preset use --name \"svf2-default\" \$OBJECT_URN" \
  "Expected: Starts a translation using the saved preset configuration" \
  "Review: Exit 0; translation job started with preset settings"

# SR-099: Delete a translation preset
run_sample "SR-099" "translate-preset-delete" \
  "raps translate preset delete --name \"svf2-default\"" \
  "Expected: Deletes the specified preset" \
  "Review: Exit 0; preset no longer appears in list"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-100: Full translation pipeline (upload and translate a model)
lifecycle_start "SR-100" "translate-full-pipeline" "Upload and translate a model"
lifecycle_step 1 "raps bucket create"
lifecycle_step 2 "raps object upload translate-test ./test-data/sample.rvt"
lifecycle_step 3 "raps translate start \$URN -f svf2"
lifecycle_step 4 "raps translate status \$URN"
lifecycle_step 5 "raps translate manifest \$URN"
lifecycle_step 6 "raps translate derivatives \$URN"
lifecycle_step 7 "raps translate download \$URN -o ./output/"
lifecycle_step 8 "raps bucket delete translate-test"
lifecycle_end

# SR-101: Preset CRUD + use lifecycle
lifecycle_start "SR-101" "translate-preset-lifecycle" "Preset CRUD + use"
lifecycle_step 1 "raps translate preset create --name \"ifc-to-svf\" --format svf2"
lifecycle_step 2 "raps translate preset list"
lifecycle_step 3 "raps translate preset show --name \"ifc-to-svf\""
lifecycle_step 4 "raps translate preset use --name \"ifc-to-svf\" \$URN"
lifecycle_step 5 "raps translate preset delete --name \"ifc-to-svf\""
lifecycle_end

section_end
