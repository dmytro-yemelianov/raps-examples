#!/bin/bash
# Section 09 — ACC Modules: Assets, Submittals, Checklists
# Runs: SR-160 through SR-177
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "09-acc-modules" "ACC Modules: Assets, Submittals, Checklists"

# ── Asset atomics ────────────────────────────────────────────────

# SR-160: List assets
run_sample "SR-160" "acc-asset-list" \
  "raps acc asset list --project \$PROJECT_ID" \
  "Expected: Lists assets" \
  "Review: List output"

# SR-161: Create an asset
run_sample "SR-161" "acc-asset-create" \
  "raps acc asset create --project \$PROJECT_ID --name \"HVAC Unit AHU-01\" --category \"Mechanical\"" \
  "Expected: Creates asset" \
  "Review: Exit 0; contains asset ID"

# SR-162: Get asset details
run_sample "SR-162" "acc-asset-get" \
  "raps acc asset get --project \$PROJECT_ID --asset \$ASSET_ID" \
  "Expected: Shows details" \
  "Review: Contains name, category, status"

# SR-163: Update an asset
run_sample "SR-163" "acc-asset-update" \
  "raps acc asset update --project \$PROJECT_ID --asset \$ASSET_ID --status \"installed\"" \
  "Expected: Updates asset" \
  "Review: Exit 0"

# SR-164: Delete an asset
run_sample "SR-164" "acc-asset-delete" \
  "raps acc asset delete --project \$PROJECT_ID --asset \$ASSET_ID --yes" \
  "Expected: Deletes asset" \
  "Review: Exit 0"

# ── Submittal atomics ────────────────────────────────────────────

# SR-165: List submittals
run_sample "SR-165" "acc-submittal-list" \
  "raps acc submittal list --project \$PROJECT_ID" \
  "Expected: Lists submittals" \
  "Review: List output"

# SR-166: Create a submittal
run_sample "SR-166" "acc-submittal-create" \
  "raps acc submittal create --project \$PROJECT_ID --title \"Concrete mix design for Level 5\" --spec-section \"03 30 00\"" \
  "Expected: Creates submittal" \
  "Review: Exit 0; contains submittal ID"

# SR-167: Get submittal details
run_sample "SR-167" "acc-submittal-get" \
  "raps acc submittal get --project \$PROJECT_ID --submittal \$SUBMITTAL_ID" \
  "Expected: Shows details" \
  "Review: Contains title, spec section, status"

# SR-168: Update a submittal
run_sample "SR-168" "acc-submittal-update" \
  "raps acc submittal update --project \$PROJECT_ID --submittal \$SUBMITTAL_ID --status \"approved\"" \
  "Expected: Updates submittal" \
  "Review: Exit 0"

# SR-169: Delete a submittal
run_sample "SR-169" "acc-submittal-delete" \
  "raps acc submittal delete --project \$PROJECT_ID --submittal \$SUBMITTAL_ID --yes" \
  "Expected: Deletes submittal" \
  "Review: Exit 0"

# ── Checklist atomics ────────────────────────────────────────────

# SR-170: List checklists
run_sample "SR-170" "acc-checklist-list" \
  "raps acc checklist list --project \$PROJECT_ID" \
  "Expected: Lists checklists" \
  "Review: List output"

# SR-171: Create a checklist
run_sample "SR-171" "acc-checklist-create" \
  "raps acc checklist create --project \$PROJECT_ID --name \"Pre-pour inspection - Level 3\" --template \$TEMPLATE_ID" \
  "Expected: Creates checklist" \
  "Review: Exit 0; contains checklist ID"

# SR-172: Get checklist details
run_sample "SR-172" "acc-checklist-get" \
  "raps acc checklist get --project \$PROJECT_ID --checklist \$CHECKLIST_ID" \
  "Expected: Shows details" \
  "Review: Contains name, template, status"

# SR-173: Update a checklist
run_sample "SR-173" "acc-checklist-update" \
  "raps acc checklist update --project \$PROJECT_ID --checklist \$CHECKLIST_ID --status \"completed\"" \
  "Expected: Updates checklist" \
  "Review: Exit 0"

# SR-174: List checklist templates
run_sample "SR-174" "acc-checklist-templates" \
  "raps acc checklist templates --project \$PROJECT_ID" \
  "Expected: Lists checklist templates" \
  "Review: Contains template names and IDs"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-175: Facilities manager tracks equipment
lifecycle_start "SR-175" "asset-tracking-lifecycle" "Facilities manager tracks equipment"
lifecycle_step 1 "raps acc asset create --project \$PID --name \"Chiller CH-01\" --category \"Mechanical\""
lifecycle_step 2 "raps acc asset create --project \$PID --name \"Chiller CH-02\" --category \"Mechanical\""
lifecycle_step 3 "raps acc asset list --project \$PID"
lifecycle_step 4 "raps acc asset update --project \$PID --asset \$CH01 --status \"delivered\""
lifecycle_step 5 "raps acc asset update --project \$PID --asset \$CH01 --status \"installed\""
lifecycle_step 6 "raps acc asset get --project \$PID --asset \$CH01"
lifecycle_step 7 "raps acc asset delete --project \$PID --asset \$CH02 --yes"
lifecycle_end

# SR-176: GC submits shop drawings
lifecycle_start "SR-176" "submittal-review-lifecycle" "GC submits shop drawings"
lifecycle_step 1 "raps acc submittal create --project \$PID --title \"Structural steel shop drawings\" --spec-section \"05 12 00\""
lifecycle_step 2 "raps acc submittal get --project \$PID --submittal \$ID"
lifecycle_step 3 "raps acc submittal update --project \$PID --submittal \$ID --reviewer \$ARCHITECT --status \"in_review\""
lifecycle_step 4 "raps acc submittal update --project \$PID --submittal \$ID --status \"revise_resubmit\""
lifecycle_step 5 "raps acc submittal update --project \$PID --submittal \$ID --status \"approved\""
lifecycle_step 6 "raps acc submittal delete --project \$PID --submittal \$ID --yes"
lifecycle_end

# SR-177: Inspector completes inspection
lifecycle_start "SR-177" "checklist-inspection-lifecycle" "Inspector completes inspection"
lifecycle_step 1 "raps acc checklist templates --project \$PID"
lifecycle_step 2 "raps acc checklist create --project \$PID --name \"Fire stopping inspection B3\" --template \$TPL"
lifecycle_step 3 "raps acc checklist get --project \$PID --checklist \$ID"
lifecycle_step 4 "raps acc checklist update --project \$PID --checklist \$ID --status \"in_progress\""
lifecycle_step 5 "raps acc checklist update --project \$PID --checklist \$ID --status \"completed\""
lifecycle_step 6 "raps acc checklist get --project \$PID --checklist \$ID"
lifecycle_end

section_end
