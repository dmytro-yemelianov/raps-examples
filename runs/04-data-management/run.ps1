# Section 04 — Data Management
# Runs: SR-070 through SR-087
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "04-data-management" -Title "Data Management"

# -- Atomic commands ---------------------------------------------------

# SR-070: List all hubs
Invoke-Sample -Id "SR-070" -Slug "hub-list" `
  -Command "raps hub list" `
  -Expects "Expected: Lists all accessible BIM 360 / ACC hubs" `
  -Review "Review: Table or list output containing hub names and IDs"

# SR-071: Get hub details
Invoke-Sample -Id "SR-071" -Slug "hub-info" `
  -Command "raps hub info $env:HUB_ID" `
  -Expects "Expected: Shows detailed information for a specific hub" `
  -Review "Review: Contains hub name, type, and region"

# SR-072: List projects in a hub
Invoke-Sample -Id "SR-072" -Slug "project-list" `
  -Command "raps project list $env:HUB_ID" `
  -Expects "Expected: Lists all projects in the specified hub" `
  -Review "Review: Contains project names and IDs"

# SR-073: List projects with interactive hub selection
Invoke-Sample -Id "SR-073" -Slug "project-list-interactive" `
  -Command "raps project list" `
  -Expects "Expected: Prompts user to select a hub interactively" `
  -Review "Review: Interactive prompt appears for hub selection"

# SR-074: Get project details
Invoke-Sample -Id "SR-074" -Slug "project-info" `
  -Command "raps project info $env:HUB_ID $env:PROJECT_ID" `
  -Expects "Expected: Shows detailed information for a specific project" `
  -Review "Review: Contains project name, type, status, and root folder ID"

# SR-075: List folder contents
Invoke-Sample -Id "SR-075" -Slug "folder-list" `
  -Command "raps folder list $env:PROJECT_ID $env:FOLDER_ID" `
  -Expects "Expected: Lists contents of a specific folder" `
  -Review "Review: Contains subfolders and items with names and IDs"

# SR-076: Create a new folder
Invoke-Sample -Id "SR-076" -Slug "folder-create" `
  -Command "raps folder create $env:PROJECT_ID $env:FOLDER_ID -n 'Test Folder'" `
  -Expects "Expected: Creates a new folder under the specified parent" `
  -Review "Review: Exit 0; output contains new folder ID and name"

# SR-077: Rename a folder
Invoke-Sample -Id "SR-077" -Slug "folder-rename" `
  -Command "raps folder rename $env:PROJECT_ID $env:NEW_FOLDER_ID --name 'Renamed Folder'" `
  -Expects "Expected: Renames the specified folder" `
  -Review "Review: Exit 0; folder name updated in subsequent list"

# SR-078: Get folder permissions
Invoke-Sample -Id "SR-078" -Slug "folder-rights" `
  -Command "raps folder rights $env:PROJECT_ID $env:FOLDER_ID" `
  -Expects "Expected: Shows permission and access rights for a folder" `
  -Review "Review: Contains permission roles and user access details"

# SR-079: Delete a folder
Invoke-Sample -Id "SR-079" -Slug "folder-delete" `
  -Command "raps folder delete $env:PROJECT_ID $env:NEW_FOLDER_ID" `
  -Expects "Expected: Deletes the specified folder" `
  -Review "Review: Exit 0; folder no longer appears in parent listing"

# SR-080: Get item details
Invoke-Sample -Id "SR-080" -Slug "item-info" `
  -Command "raps item info $env:PROJECT_ID $env:ITEM_ID" `
  -Expects "Expected: Shows detailed information for a specific item" `
  -Review "Review: Contains item name, type, version, and last modified date"

# SR-081: List item versions
Invoke-Sample -Id "SR-081" -Slug "item-versions" `
  -Command "raps item versions $env:PROJECT_ID $env:ITEM_ID" `
  -Expects "Expected: Lists all versions of the specified item" `
  -Review "Review: Contains version numbers, dates, and user info"

# SR-082: Create item from OSS object
Invoke-Sample -Id "SR-082" -Slug "item-create-from-oss" `
  -Command "raps item create-from-oss $env:PROJECT_ID $env:FOLDER_ID $env:OBJECT_URN -n 'Uploaded Model'" `
  -Expects "Expected: Creates a Data Management item linked to an OSS object" `
  -Review "Review: Exit 0; output contains new item ID"

# SR-083: Rename an item
Invoke-Sample -Id "SR-083" -Slug "item-rename" `
  -Command "raps item rename $env:PROJECT_ID $env:ITEM_ID --name 'Updated Model Name'" `
  -Expects "Expected: Renames the specified item" `
  -Review "Review: Exit 0; item name updated in subsequent info"

# SR-084: Delete an item
Invoke-Sample -Id "SR-084" -Slug "item-delete" `
  -Command "raps item delete $env:PROJECT_ID $env:ITEM_ID" `
  -Expects "Expected: Deletes the specified item" `
  -Review "Review: Exit 0; item no longer appears in folder listing"

# -- Lifecycles --------------------------------------------------------

# SR-085: Developer explores project structure
Start-Lifecycle -Id "SR-085" -Slug "dm-navigation-lifecycle" -Description "Developer explores project structure"
Invoke-LifecycleStep -StepNum 1 -Command "raps hub list"
Invoke-LifecycleStep -StepNum 2 -Command "raps project list $env:HUB_ID"
Invoke-LifecycleStep -StepNum 3 -Command "raps project info $env:HUB_ID $env:PROJECT_ID"
Invoke-LifecycleStep -StepNum 4 -Command "raps folder list $env:PROJECT_ID $env:ROOT_FOLDER"
Invoke-LifecycleStep -StepNum 5 -Command "raps folder list $env:PROJECT_ID $env:SUBFOLDER"
End-Lifecycle

# SR-086: Admin creates folder structure
Start-Lifecycle -Id "SR-086" -Slug "dm-folder-crud-lifecycle" -Description "Admin creates folder structure"
Invoke-LifecycleStep -StepNum 1 -Command "raps folder create $env:PROJECT_ID $env:ROOT -n 'Phase 1'"
Invoke-LifecycleStep -StepNum 2 -Command "raps folder create $env:PROJECT_ID $env:PHASE1 -n 'Structural'"
Invoke-LifecycleStep -StepNum 3 -Command "raps folder create $env:PROJECT_ID $env:PHASE1 -n 'MEP'"
Invoke-LifecycleStep -StepNum 4 -Command "raps folder list $env:PROJECT_ID $env:PHASE1"
Invoke-LifecycleStep -StepNum 5 -Command "raps folder rename $env:PROJECT_ID $env:MEP --name 'MEP Systems'"
Invoke-LifecycleStep -StepNum 6 -Command "raps folder rights $env:PROJECT_ID $env:PHASE1"
Invoke-LifecycleStep -StepNum 7 -Command "raps folder delete $env:PROJECT_ID $env:MEP"
Invoke-LifecycleStep -StepNum 8 -Command "raps folder delete $env:PROJECT_ID $env:STRUCTURAL"
Invoke-LifecycleStep -StepNum 9 -Command "raps folder delete $env:PROJECT_ID $env:PHASE1"
End-Lifecycle

# SR-087: Developer uploads to BIM 360
Start-Lifecycle -Id "SR-087" -Slug "item-upload-and-manage" -Description "Developer uploads to BIM 360"
Invoke-LifecycleStep -StepNum 1 -Command "raps bucket create"
Invoke-LifecycleStep -StepNum 2 -Command "raps object upload dm-staging ./test-data/sample.rvt"
Invoke-LifecycleStep -StepNum 3 -Command "raps item create-from-oss $env:PROJECT_ID $env:FOLDER_ID $env:URN -n 'Building.rvt'"
Invoke-LifecycleStep -StepNum 4 -Command "raps item info $env:PROJECT_ID $env:ITEM_ID"
Invoke-LifecycleStep -StepNum 5 -Command "raps item versions $env:PROJECT_ID $env:ITEM_ID"
Invoke-LifecycleStep -StepNum 6 -Command "raps item rename $env:PROJECT_ID $env:ITEM_ID --name 'Building-v2.rvt'"
Invoke-LifecycleStep -StepNum 7 -Command "raps item delete $env:PROJECT_ID $env:ITEM_ID"
Invoke-LifecycleStep -StepNum 8 -Command "raps bucket delete dm-staging"
End-Lifecycle

End-Section
