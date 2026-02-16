#!/bin/bash
# Section 09 — ACC Modules: Assets, Submittals, Checklists
# Runs: SR-160 through SR-177
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "09-acc-modules" "ACC Modules: Assets, Submittals, Checklists"
require_3leg_auth || { section_end; exit 0; }

# --- Pre-seed demo environment variables (override with real values) ---
: "${PROJECT_ID:=${RAPS_PROJECT_ID:-demo-project-001}}"
: "${CATEGORY_ID:=cat-demo-001}"
: "${ASSET_ID:=ast-demo-001}"
: "${STATUS_ID:=st-demo-001}"
: "${SUBMITTAL_ID:=sub-demo-001}"
: "${CHECKLIST_ID:=chk-demo-001}"
: "${TEMPLATE_ID:=tpl-demo-001}"
: "${PID:=${RAPS_PROJECT_ID:-demo-project-001}}"
: "${MECH_CAT:=cat-mechanical-001}"
: "${CH01:=ast-chiller-01}"
: "${CH02:=ast-chiller-02}"
: "${DELIVERED_STATUS:=st-delivered-001}"
: "${INSTALLED_STATUS:=st-installed-001}"
: "${TPL:=tpl-demo-001}"
: "${FOLDER_ID:=urn:adsk.wipprod:fs.folder:co.demo-folder-001}"

# ── Asset atomics ────────────────────────────────────────────────

# SR-160: List assets
run_sample "SR-160" "acc-asset-list" \
  "raps acc asset list $PROJECT_ID || true" \
  "Expected: Lists assets" \
  "Review: List output"

# SR-161: Create an asset
run_sample "SR-161" "acc-asset-create" \
  "raps acc asset create $PROJECT_ID --category-id $CATEGORY_ID --description \"HVAC Unit AHU-01\" || true" \
  "Expected: Creates asset" \
  "Review: Exit 0; contains asset ID"

# SR-162: Get asset details
run_sample "SR-162" "acc-asset-get" \
  "raps acc asset get $PROJECT_ID $ASSET_ID || true" \
  "Expected: Shows details" \
  "Review: Contains name, category, status"

# SR-163: Update an asset
run_sample "SR-163" "acc-asset-update" \
  "raps acc asset update $PROJECT_ID $ASSET_ID --status-id $STATUS_ID || true" \
  "Expected: Updates asset" \
  "Review: Exit 0"

# SR-164: Delete an asset
run_sample "SR-164" "acc-asset-delete" \
  "raps acc asset delete $PROJECT_ID $ASSET_ID --yes || true" \
  "Expected: Deletes asset" \
  "Review: Exit 0"

# ── Submittal atomics ────────────────────────────────────────────

# SR-165: List submittals
run_sample "SR-165" "acc-submittal-list" \
  "raps acc submittal list $PROJECT_ID || true" \
  "Expected: Lists submittals" \
  "Review: List output"

# SR-166: Create a submittal
run_sample "SR-166" "acc-submittal-create" \
  "raps acc submittal create $PROJECT_ID --title \"Concrete mix design for Level 5\" --spec-section \"03 30 00\" || true" \
  "Expected: Creates submittal" \
  "Review: Exit 0; contains submittal ID"

# SR-167: Get submittal details
run_sample "SR-167" "acc-submittal-get" \
  "raps acc submittal get $PROJECT_ID $SUBMITTAL_ID || true" \
  "Expected: Shows details" \
  "Review: Contains title, spec section, status"

# SR-168: Update a submittal
run_sample "SR-168" "acc-submittal-update" \
  "raps acc submittal update $PROJECT_ID $SUBMITTAL_ID --status \"approved\" || true" \
  "Expected: Updates submittal" \
  "Review: Exit 0"

# SR-169: Delete a submittal
run_sample "SR-169" "acc-submittal-delete" \
  "raps acc submittal delete $PROJECT_ID $SUBMITTAL_ID --yes || true" \
  "Expected: Deletes submittal" \
  "Review: Exit 0"

# ── Checklist atomics ────────────────────────────────────────────

# SR-170: List checklists
run_sample "SR-170" "acc-checklist-list" \
  "raps acc checklist list $PROJECT_ID || true" \
  "Expected: Lists checklists" \
  "Review: List output"

# SR-171: Create a checklist
run_sample "SR-171" "acc-checklist-create" \
  "raps acc checklist create $PROJECT_ID --title \"Pre-pour inspection - Level 3\" --template-id $TEMPLATE_ID || true" \
  "Expected: Creates checklist" \
  "Review: Exit 0; contains checklist ID"

# SR-172: Get checklist details
run_sample "SR-172" "acc-checklist-get" \
  "raps acc checklist get $PROJECT_ID $CHECKLIST_ID || true" \
  "Expected: Shows details" \
  "Review: Contains name, template, status"

# SR-173: Update a checklist
run_sample "SR-173" "acc-checklist-update" \
  "raps acc checklist update $PROJECT_ID $CHECKLIST_ID --status \"completed\" || true" \
  "Expected: Updates checklist" \
  "Review: Exit 0"

# SR-174: List checklist templates
run_sample "SR-174" "acc-checklist-templates" \
  "raps acc checklist templates $PROJECT_ID || true" \
  "Expected: Lists checklist templates" \
  "Review: Contains template names and IDs"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-175: Facilities manager tracks equipment
lifecycle_start "SR-175" "asset-tracking-lifecycle" "Facilities manager tracks equipment"
lifecycle_step 1 "raps acc asset create $PID --category-id $MECH_CAT --description \"Chiller CH-01\" || true"
lifecycle_step 2 "raps acc asset create $PID --category-id $MECH_CAT --description \"Chiller CH-02\" || true"
lifecycle_step 3 "raps acc asset list $PID || true"
lifecycle_step 4 "raps acc asset update $PID $CH01 --status-id $DELIVERED_STATUS || true"
lifecycle_step 5 "raps acc asset update $PID $CH01 --status-id $INSTALLED_STATUS || true"
lifecycle_step 6 "raps acc asset get $PID $CH01 || true"
lifecycle_step 7 "raps acc asset delete $PID $CH02 --yes || true"
lifecycle_end

# SR-176: GC submits shop drawings
lifecycle_start "SR-176" "submittal-review-lifecycle" "GC submits shop drawings"
lifecycle_step 1 "raps acc submittal create $PID --title \"Structural steel shop drawings\" --spec-section \"05 12 00\" || true"
lifecycle_step 2 "raps acc submittal get $PID $SUBMITTAL_ID || true"
lifecycle_step 3 "raps acc submittal update $PID $SUBMITTAL_ID --status \"in_review\" || true"
lifecycle_step 4 "raps acc submittal update $PID $SUBMITTAL_ID --status \"revise_resubmit\" || true"
lifecycle_step 5 "raps acc submittal update $PID $SUBMITTAL_ID --status \"approved\" || true"
lifecycle_step 6 "raps acc submittal delete $PID $SUBMITTAL_ID --yes || true"
lifecycle_end

# SR-177: Inspector completes inspection
lifecycle_start "SR-177" "checklist-inspection-lifecycle" "Inspector completes inspection"
lifecycle_step 1 "raps acc checklist templates $PID || true"
lifecycle_step 2 "raps acc checklist create $PID --title \"Fire stopping inspection B3\" --template-id $TPL || true"
lifecycle_step 3 "raps acc checklist get $PID $CHECKLIST_ID || true"
lifecycle_step 4 "raps acc checklist update $PID $CHECKLIST_ID --status \"in_progress\" || true"
lifecycle_step 5 "raps acc checklist update $PID $CHECKLIST_ID --status \"completed\" || true"
lifecycle_step 6 "raps acc checklist get $PID $CHECKLIST_ID || true"
lifecycle_end

section_end
