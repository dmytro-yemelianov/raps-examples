#!/bin/bash
# Section 04 — Data Management
# Runs: SR-070 through SR-087
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "04-data-management" "Data Management"

# --- Pre-seed demo environment variables (override with real values) ---
: "${HUB_ID:=b.demo-hub-001}"
: "${PROJECT_ID:=b.demo-project-001}"
: "${FOLDER_ID:=urn:adsk.wipprod:fs.folder:co.demo-folder-001}"
: "${NEW_FOLDER_ID:=urn:adsk.wipprod:fs.folder:co.demo-folder-002}"
: "${ITEM_ID:=urn:adsk.wipprod:dm.lineage:demo-item-001}"
: "${OBJECT_URN:=dXJuOmFkc2sub2JqZWN0czpvcy5vYmplY3Q6ZGVtby1idWNrZXQvc2FtcGxlLmlmYw}"
: "${URN:=dXJuOmFkc2sub2JqZWN0czpvcy5vYmplY3Q6ZGVtby1idWNrZXQvc2FtcGxlLmlmYw}"
: "${ROOT_FOLDER:=urn:adsk.wipprod:fs.folder:co.demo-root-001}"
: "${ROOT:=urn:adsk.wipprod:fs.folder:co.demo-root-001}"
: "${PHASE1:=urn:adsk.wipprod:fs.folder:co.demo-phase1-001}"
: "${STRUCTURAL:=urn:adsk.wipprod:fs.folder:co.demo-structural-001}"
: "${MEP:=urn:adsk.wipprod:fs.folder:co.demo-mep-001}"
: "${SUBFOLDER:=urn:adsk.wipprod:fs.folder:co.demo-subfolder-001}"

# ── Atomic commands ──────────────────────────────────────────────

# SR-070: List all hubs
run_sample "SR-070" "hub-list" \
  "raps hub list" \
  "Expected: Lists all accessible BIM 360 / ACC hubs" \
  "Review: Table or list output containing hub names and IDs"

# SR-071: Get hub details
run_sample "SR-071" "hub-info" \
  "raps hub info \$HUB_ID" \
  "Expected: Shows detailed information for a specific hub" \
  "Review: Contains hub name, type, and region"

# SR-072: List projects in a hub
run_sample "SR-072" "project-list" \
  "raps project list \$HUB_ID" \
  "Expected: Lists all projects in the specified hub" \
  "Review: Contains project names and IDs"

# SR-073: List projects with interactive hub selection
run_sample "SR-073" "project-list-interactive" \
  "raps project list" \
  "Expected: Prompts user to select a hub interactively" \
  "Review: Interactive prompt appears for hub selection"

# SR-074: Get project details
run_sample "SR-074" "project-info" \
  "raps project info \$HUB_ID \$PROJECT_ID" \
  "Expected: Shows detailed information for a specific project" \
  "Review: Contains project name, type, status, and root folder ID"

# SR-075: List folder contents
run_sample "SR-075" "folder-list" \
  "raps folder list \$PROJECT_ID \$FOLDER_ID" \
  "Expected: Lists contents of a specific folder" \
  "Review: Contains subfolders and items with names and IDs"

# SR-076: Create a new folder
run_sample "SR-076" "folder-create" \
  "raps folder create \$PROJECT_ID \$FOLDER_ID -n \"Test Folder\"" \
  "Expected: Creates a new folder under the specified parent" \
  "Review: Exit 0; output contains new folder ID and name"

# SR-077: Rename a folder
run_sample "SR-077" "folder-rename" \
  "raps folder rename \$PROJECT_ID \$NEW_FOLDER_ID --name \"Renamed Folder\"" \
  "Expected: Renames the specified folder" \
  "Review: Exit 0; folder name updated in subsequent list"

# SR-078: Get folder permissions
run_sample "SR-078" "folder-rights" \
  "raps folder rights \$PROJECT_ID \$FOLDER_ID" \
  "Expected: Shows permission and access rights for a folder" \
  "Review: Contains permission roles and user access details"

# SR-079: Delete a folder
run_sample "SR-079" "folder-delete" \
  "raps folder delete \$PROJECT_ID \$NEW_FOLDER_ID" \
  "Expected: Deletes the specified folder" \
  "Review: Exit 0; folder no longer appears in parent listing"

# SR-080: Get item details
run_sample "SR-080" "item-info" \
  "raps item info \$PROJECT_ID \$ITEM_ID" \
  "Expected: Shows detailed information for a specific item" \
  "Review: Contains item name, type, version, and last modified date"

# SR-081: List item versions
run_sample "SR-081" "item-versions" \
  "raps item versions \$PROJECT_ID \$ITEM_ID" \
  "Expected: Lists all versions of the specified item" \
  "Review: Contains version numbers, dates, and user info"

# SR-082: Create item from OSS object
run_sample "SR-082" "item-create-from-oss" \
  "raps item create-from-oss \$PROJECT_ID \$FOLDER_ID \$OBJECT_URN -n \"Uploaded Model\"" \
  "Expected: Creates a Data Management item linked to an OSS object" \
  "Review: Exit 0; output contains new item ID"

# SR-083: Rename an item
run_sample "SR-083" "item-rename" \
  "raps item rename \$PROJECT_ID \$ITEM_ID --name \"Updated Model Name\"" \
  "Expected: Renames the specified item" \
  "Review: Exit 0; item name updated in subsequent info"

# SR-084: Delete an item
run_sample "SR-084" "item-delete" \
  "raps item delete \$PROJECT_ID \$ITEM_ID" \
  "Expected: Deletes the specified item" \
  "Review: Exit 0; item no longer appears in folder listing"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-085: Developer explores project structure
lifecycle_start "SR-085" "dm-navigation-lifecycle" "Developer explores project structure"
lifecycle_step 1 "raps hub list"
lifecycle_step 2 "raps project list \$HUB_ID"
lifecycle_step 3 "raps project info \$HUB_ID \$PROJECT_ID"
lifecycle_step 4 "raps folder list \$PROJECT_ID \$ROOT_FOLDER"
lifecycle_step 5 "raps folder list \$PROJECT_ID \$SUBFOLDER"
lifecycle_end

# SR-086: Admin creates folder structure
lifecycle_start "SR-086" "dm-folder-crud-lifecycle" "Admin creates folder structure"
lifecycle_step 1 "raps folder create \$PROJECT_ID \$ROOT -n \"Phase 1\""
lifecycle_step 2 "raps folder create \$PROJECT_ID \$PHASE1 -n \"Structural\""
lifecycle_step 3 "raps folder create \$PROJECT_ID \$PHASE1 -n \"MEP\""
lifecycle_step 4 "raps folder list \$PROJECT_ID \$PHASE1"
lifecycle_step 5 "raps folder rename \$PROJECT_ID \$MEP --name \"MEP Systems\""
lifecycle_step 6 "raps folder rights \$PROJECT_ID \$PHASE1"
lifecycle_step 7 "raps folder delete \$PROJECT_ID \$MEP"
lifecycle_step 8 "raps folder delete \$PROJECT_ID \$STRUCTURAL"
lifecycle_step 9 "raps folder delete \$PROJECT_ID \$PHASE1"
lifecycle_end

# SR-087: Developer uploads to BIM 360
lifecycle_start "SR-087" "item-upload-and-manage" "Developer uploads to BIM 360"
lifecycle_step 1 "raps bucket create"
lifecycle_step 2 "raps object upload dm-staging ./test-data/sample.rvt"
lifecycle_step 3 "raps item create-from-oss \$PROJECT_ID \$FOLDER_ID \$URN -n \"Building.rvt\""
lifecycle_step 4 "raps item info \$PROJECT_ID \$ITEM_ID"
lifecycle_step 5 "raps item versions \$PROJECT_ID \$ITEM_ID"
lifecycle_step 6 "raps item rename \$PROJECT_ID \$ITEM_ID --name \"Building-v2.rvt\""
lifecycle_step 7 "raps item delete \$PROJECT_ID \$ITEM_ID"
lifecycle_step 8 "raps bucket delete dm-staging"
lifecycle_end

section_end
