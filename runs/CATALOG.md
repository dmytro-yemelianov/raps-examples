# RAPS Sample Runs Catalog

Complete index of all sample runs defined across 25 section scripts.

**Total runs: 259** (216 atomic + 43 lifecycle)

---

## Quick Reference

| Section | Directory | Runs | Description |
|---------|-----------|------|-------------|
| 00 | `00-setup` | 3 | Setup & Prerequisites |
| 01 | `01-auth` | 15 | Authentication |
| 02 | `02-config` | 16 | Configuration |
| 03 | `03-storage` | 16 | Storage: Buckets + Objects |
| 04 | `04-data-management` | 18 | Data Management |
| 05 | `05-model-derivative` | 12 | Model Derivative / Translation |
| 06 | `06-design-automation` | 12 | Design Automation |
| 07 | `07-acc-issues` | 12 | ACC Issues |
| 08 | `08-acc-rfi` | 6 | ACC RFIs |
| 09 | `09-acc-modules` | 18 | ACC Modules: Assets, Submittals, Checklists |
| 10 | `10-webhooks` | 9 | Webhooks |
| 11 | `11-admin-users` | 17 | Admin: Bulk User Management |
| 12 | `12-admin-projects` | 6 | Admin: Project Management |
| 13 | `13-admin-folders` | 9 | Admin: Folder Permissions & Operations |
| 14 | `14-reality-capture` | 9 | Reality Capture |
| 15 | `15-reporting` | 5 | Portfolio Reports |
| 16 | `16-templates` | 6 | Templates |
| 17 | `17-plugins` | 7 | Plugins |
| 18 | `18-pipelines` | 4 | Pipelines |
| 19 | `19-api-raw` | 5 | Raw API |
| 20 | `20-generation` | 2 | Generation |
| 21 | `21-shell-serve` | 6 | Shell, Serve, Completions |
| 22 | `22-demo` | 4 | Demo |
| 30 | `30-workflows` | 10 | Cross-Domain Workflows |
| 99 | `99-cross-cutting` | 32 | Cross-Cutting |

---

## Section 00 -- Setup & Prerequisites

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-001 | atomic | setup-env-file | `env \| grep -E '^APS_(CLIENT_ID\|CLIENT_SECRET\|CALLBACK_URL)='` | Environment variables are set |
| SR-002 | atomic | setup-mock-server | `echo 'Verify raps-mock is running on port 3000'` | Server listening on port 3000 |
| SR-003 | atomic | setup-generate-test-files | `raps generate files --count 5 --out-dir ./test-data --complexity medium` | Generates 5 files of each type in ./test-data/ |

## Section 01 -- Authentication

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-010 | atomic | auth-test-2leg | `raps auth test` | 2-legged token obtained successfully |
| SR-011 | atomic | auth-login-3leg-browser | `raps auth login` | Browser opens for OAuth consent; token stored |
| SR-012 | atomic | auth-login-device-code | `raps auth login --device` | Device code displayed; user authorizes in browser |
| SR-013 | atomic | auth-login-token-direct | `raps auth login --token "eyJ..."` | Provided token stored directly |
| SR-014 | atomic | auth-login-refresh-token | `raps auth login --refresh-token "rt_..." --expires-in 3600` | Refresh token exchanged for access token |
| SR-015 | atomic | auth-status | `raps auth status` | Current auth state displayed |
| SR-016 | atomic | auth-whoami | `raps auth whoami` | User identity information returned |
| SR-017 | atomic | auth-inspect | `raps auth inspect` | Token claims and metadata shown |
| SR-018 | atomic | auth-inspect-warn | `raps auth inspect --warn-expiry-seconds 7200` | Token inspected with 2-hour warning threshold |
| SR-019 | atomic | auth-logout | `raps auth logout` | Stored token removed |
| SR-020 | atomic | auth-login-default-profile | `raps auth login --default` | Login using default profile credentials |
| SR-021 | lifecycle | auth-lifecycle-2leg | Full 2-legged auth cycle (5 steps) | -- |
| SR-022 | lifecycle | auth-lifecycle-3leg | Full 3-legged auth cycle (5 steps) | -- |
| SR-023 | lifecycle | auth-lifecycle-device | Device code auth cycle (4 steps) | -- |
| SR-024 | lifecycle | auth-lifecycle-token-injection | Token injection cycle (4 steps) | -- |

## Section 02 -- Configuration

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-030 | atomic | config-show | `raps config show` | Full configuration displayed |
| SR-031 | atomic | config-get | `raps config get client_id` | Value of client_id printed |
| SR-032 | atomic | config-set | `raps config set output_format json` | output_format updated to json |
| SR-033 | atomic | config-profile-create | `raps config profile create staging` | Profile 'staging' created |
| SR-034 | atomic | config-profile-list | `raps config profile list` | All profiles listed |
| SR-035 | atomic | config-profile-use | `raps config profile use staging` | Active profile switched to staging |
| SR-036 | atomic | config-profile-current | `raps config profile current` | Current profile name printed |
| SR-037 | atomic | config-profile-export | `raps config profile export staging` | Profile exported as JSON |
| SR-038 | atomic | config-profile-import | `raps config profile import ./staging-profile.json` | Profile imported from file |
| SR-039 | atomic | config-profile-diff | `raps config profile diff default staging` | Differences between profiles displayed |
| SR-040 | atomic | config-profile-delete | `raps config profile delete staging` | Profile 'staging' removed |
| SR-041 | atomic | config-context-show | `raps config context show` | Active hub/project context displayed |
| SR-042 | atomic | config-context-set | `raps config context set --hub $HUB_ID --project $PROJECT_ID` | Context bound to specified hub and project |
| SR-043 | atomic | config-context-clear | `raps config context clear` | Context cleared |
| SR-044 | lifecycle | config-profile-lifecycle | Full profile CRUD (10 steps) | -- |
| SR-045 | lifecycle | config-context-lifecycle | Context set and clear (7 steps) | -- |

## Section 03 -- Storage: Buckets + Objects

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-050 | atomic | bucket-create | `raps bucket create --name "test-bucket-$(date +%s)" --policy transient` | Creates a new OSS bucket with transient retention |
| SR-051 | atomic | bucket-list | `raps bucket list` | Lists all buckets in the account |
| SR-052 | atomic | bucket-info | `raps bucket info --name $BUCKET_NAME` | Shows detailed information for a specific bucket |
| SR-053 | atomic | bucket-delete | `raps bucket delete --name $BUCKET_NAME --yes` | Deletes the specified bucket |
| SR-054 | atomic | object-upload | `raps object upload --bucket $BUCKET --file ./test-data/sample.ifc` | Uploads file to the specified bucket |
| SR-055 | atomic | object-upload-batch | `raps object upload-batch --bucket $BUCKET --dir ./test-data/` | Uploads all files from the directory |
| SR-056 | atomic | object-list | `raps object list --bucket $BUCKET` | Lists all objects in the bucket |
| SR-057 | atomic | object-info | `raps object info --bucket $BUCKET --key sample.ifc` | Shows detailed information for a specific object |
| SR-058 | atomic | object-download | `raps object download --bucket $BUCKET --key sample.ifc --out-file ./downloads/` | Downloads object to the specified directory |
| SR-059 | atomic | object-signed-url | `raps object signed-url --bucket $BUCKET --key sample.ifc` | Generates a pre-signed URL for the object |
| SR-060 | atomic | object-copy | `raps object copy --bucket $BUCKET --key sample.ifc --dest-bucket $DEST_BUCKET ...` | Copies object to destination bucket with new key |
| SR-061 | atomic | object-rename | `raps object rename --bucket $BUCKET --key sample-copy.ifc --new-key renamed.ifc` | Renames object by changing its key |
| SR-062 | atomic | object-delete | `raps object delete --bucket $BUCKET --key renamed.ifc --yes` | Deletes the specified object |
| SR-063 | lifecycle | bucket-full-lifecycle | Clean CRUD cycle for buckets (5 steps) | -- |
| SR-064 | lifecycle | object-full-lifecycle | Upload through delete (10 steps) | -- |
| SR-065 | lifecycle | batch-upload-lifecycle | Batch upload test (5 steps) | -- |

## Section 04 -- Data Management

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-070 | atomic | hub-list | `raps hub list` | Lists all accessible BIM 360 / ACC hubs |
| SR-071 | atomic | hub-info | `raps hub info $HUB_ID` | Shows detailed information for a specific hub |
| SR-072 | atomic | project-list | `raps project list $HUB_ID` | Lists all projects in the specified hub |
| SR-073 | atomic | project-list-interactive | `raps project list` | Prompts user to select a hub interactively |
| SR-074 | atomic | project-info | `raps project info $HUB_ID $PROJECT_ID` | Shows detailed information for a specific project |
| SR-075 | atomic | folder-list | `raps folder list --project $PROJECT_ID --folder $FOLDER_ID` | Lists contents of a specific folder |
| SR-076 | atomic | folder-create | `raps folder create --project $PROJECT_ID --parent $FOLDER_ID --name "Test Folder"` | Creates a new folder under the specified parent |
| SR-077 | atomic | folder-rename | `raps folder rename --project $PROJECT_ID --folder $NEW_FOLDER_ID ...` | Renames the specified folder |
| SR-078 | atomic | folder-rights | `raps folder rights --project $PROJECT_ID --folder $FOLDER_ID` | Shows permission and access rights for a folder |
| SR-079 | atomic | folder-delete | `raps folder delete --project $PROJECT_ID --folder $NEW_FOLDER_ID --yes` | Deletes the specified folder |
| SR-080 | atomic | item-info | `raps item info $PROJECT_ID $ITEM_ID` | Shows detailed information for a specific item |
| SR-081 | atomic | item-versions | `raps item versions $PROJECT_ID $ITEM_ID` | Lists all versions of the specified item |
| SR-082 | atomic | item-create-from-oss | `raps item create-from-oss $PROJECT_ID $FOLDER_ID --name "Uploaded Model" ...` | Creates a Data Management item linked to an OSS object |
| SR-083 | atomic | item-rename | `raps item rename $PROJECT_ID $ITEM_ID --name "Updated Model Name"` | Renames the specified item |
| SR-084 | atomic | item-delete | `raps item delete $PROJECT_ID $ITEM_ID --yes` | Deletes the specified item |
| SR-085 | lifecycle | dm-navigation-lifecycle | Developer explores project structure (5 steps) | -- |
| SR-086 | lifecycle | dm-folder-crud-lifecycle | Admin creates folder structure (9 steps) | -- |
| SR-087 | lifecycle | item-upload-and-manage | Developer uploads to BIM 360 (8 steps) | -- |

## Section 05 -- Model Derivative / Translation

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-090 | atomic | translate-start | `raps translate start --urn $OBJECT_URN --format svf2` | Starts a model translation job to SVF2 format |
| SR-091 | atomic | translate-status | `raps translate status --urn $OBJECT_URN` | Reports current translation progress |
| SR-092 | atomic | translate-manifest | `raps translate manifest --urn $OBJECT_URN` | Shows the translation manifest with derivative tree |
| SR-093 | atomic | translate-derivatives | `raps translate derivatives --urn $OBJECT_URN` | Lists all available derivative outputs for the model |
| SR-094 | atomic | translate-download | `raps translate download --urn $OBJECT_URN --output ./derivatives/` | Downloads derivative files to the specified directory |
| SR-095 | atomic | translate-preset-list | `raps translate preset list` | Lists all saved translation presets |
| SR-096 | atomic | translate-preset-create | `raps translate preset create --name "svf2-default" --format svf2` | Creates a reusable translation preset |
| SR-097 | atomic | translate-preset-show | `raps translate preset show --name "svf2-default"` | Displays details of the specified preset |
| SR-098 | atomic | translate-preset-use | `raps translate preset use --name "svf2-default" --urn $OBJECT_URN` | Starts a translation using the saved preset configuration |
| SR-099 | atomic | translate-preset-delete | `raps translate preset delete --name "svf2-default"` | Deletes the specified preset |
| SR-100 | lifecycle | translate-full-pipeline | Upload and translate a model (8 steps) | -- |
| SR-101 | lifecycle | translate-preset-lifecycle | Preset CRUD + use (5 steps) | -- |

## Section 06 -- Design Automation

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-110 | atomic | da-engines | `raps da engines` | Lists DA engines |
| SR-111 | atomic | da-appbundles-list | `raps da appbundles` | Lists appbundles |
| SR-112 | atomic | da-appbundle-create | `raps da appbundle-create --name "CountWalls" --engine "Autodesk.Revit+2025" ...` | Creates appbundle |
| SR-113 | atomic | da-appbundle-delete | `raps da appbundle-delete --name "CountWalls"` | Deletes appbundle |
| SR-114 | atomic | da-activities-list | `raps da activities` | Lists activities |
| SR-115 | atomic | da-activity-create | `raps da activity-create --name "CountWallsActivity" --engine "Autodesk.Revit+2025" ...` | Creates activity |
| SR-116 | atomic | da-activity-delete | `raps da activity-delete --name "CountWallsActivity"` | Deletes activity |
| SR-117 | atomic | da-run | `raps da run --activity "CountWallsActivity" --input-url $SIGNED_URL ...` | Submits workitem |
| SR-118 | atomic | da-workitems | `raps da workitems` | Lists work items |
| SR-119 | atomic | da-status | `raps da status --id $WORKITEM_ID` | Shows status |
| SR-120 | lifecycle | da-appbundle-lifecycle | Register and test a Revit plugin (7 steps) | -- |
| SR-121 | lifecycle | da-workitem-lifecycle | Run and monitor a DA job (6 steps) | -- |

## Section 07 -- ACC Issues

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-130 | atomic | issue-list | `raps issue list --project $PROJECT_ID` | Lists issues |
| SR-131 | atomic | issue-types | `raps issue types --project $PROJECT_ID` | Lists issue types |
| SR-132 | atomic | issue-create | `raps issue create --project $PROJECT_ID --title "Cracked concrete on Level 2" ...` | Creates issue |
| SR-133 | atomic | issue-update | `raps issue update --project $PROJECT_ID --issue $ISSUE_ID --title "..." ...` | Updates issue |
| SR-134 | atomic | issue-transition | `raps issue transition --project $PROJECT_ID --issue $ISSUE_ID --status "in_review"` | Transitions status |
| SR-135 | atomic | issue-comment-add | `raps issue comment add --project $PROJECT_ID --issue $ISSUE_ID --body "..."` | Adds comment |
| SR-136 | atomic | issue-comment-list | `raps issue comment list --project $PROJECT_ID --issue $ISSUE_ID` | Lists comments |
| SR-137 | atomic | issue-comment-delete | `raps issue comment delete --project $PROJECT_ID --issue $ISSUE_ID --comment $COMMENT_ID ...` | Deletes comment |
| SR-138 | atomic | issue-attachments | `raps issue attachments --project $PROJECT_ID --issue $ISSUE_ID` | Lists attachments |
| SR-139 | atomic | issue-delete | `raps issue delete --project $PROJECT_ID --issue $ISSUE_ID --yes` | Deletes issue |
| SR-140 | lifecycle | issue-full-lifecycle | Field engineer reports and tracks a defect (9 steps) | -- |
| SR-141 | lifecycle | issue-triage-workflow | QA lead triages multiple issues (8 steps) | -- |

## Section 08 -- ACC RFIs

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-150 | atomic | rfi-list | `raps rfi list --project $PROJECT_ID` | Lists RFIs |
| SR-151 | atomic | rfi-create | `raps rfi create --project $PROJECT_ID --title "Clarification on MEP routing ..."` | Creates RFI |
| SR-152 | atomic | rfi-get | `raps rfi get --project $PROJECT_ID --rfi $RFI_ID` | Shows details |
| SR-153 | atomic | rfi-update | `raps rfi update --project $PROJECT_ID --rfi $RFI_ID --assignee $USER_ID ...` | Updates RFI |
| SR-154 | atomic | rfi-delete | `raps rfi delete --project $PROJECT_ID --rfi $RFI_ID --yes` | Deletes RFI |
| SR-155 | lifecycle | rfi-full-lifecycle | Architect raises and resolves an RFI (7 steps) | -- |

## Section 09 -- ACC Modules: Assets, Submittals, Checklists

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-160 | atomic | acc-asset-list | `raps acc asset list --project $PROJECT_ID` | Lists assets |
| SR-161 | atomic | acc-asset-create | `raps acc asset create --project $PROJECT_ID --name "HVAC Unit AHU-01" ...` | Creates asset |
| SR-162 | atomic | acc-asset-get | `raps acc asset get --project $PROJECT_ID --asset $ASSET_ID` | Shows details |
| SR-163 | atomic | acc-asset-update | `raps acc asset update --project $PROJECT_ID --asset $ASSET_ID --status "installed"` | Updates asset |
| SR-164 | atomic | acc-asset-delete | `raps acc asset delete --project $PROJECT_ID --asset $ASSET_ID --yes` | Deletes asset |
| SR-165 | atomic | acc-submittal-list | `raps acc submittal list --project $PROJECT_ID` | Lists submittals |
| SR-166 | atomic | acc-submittal-create | `raps acc submittal create --project $PROJECT_ID --title "Concrete mix design ..."` | Creates submittal |
| SR-167 | atomic | acc-submittal-get | `raps acc submittal get --project $PROJECT_ID --submittal $SUBMITTAL_ID` | Shows details |
| SR-168 | atomic | acc-submittal-update | `raps acc submittal update --project $PROJECT_ID --submittal $SUBMITTAL_ID ...` | Updates submittal |
| SR-169 | atomic | acc-submittal-delete | `raps acc submittal delete --project $PROJECT_ID --submittal $SUBMITTAL_ID --yes` | Deletes submittal |
| SR-170 | atomic | acc-checklist-list | `raps acc checklist list --project $PROJECT_ID` | Lists checklists |
| SR-171 | atomic | acc-checklist-create | `raps acc checklist create --project $PROJECT_ID --name "Pre-pour inspection ..."` | Creates checklist |
| SR-172 | atomic | acc-checklist-get | `raps acc checklist get --project $PROJECT_ID --checklist $CHECKLIST_ID` | Shows details |
| SR-173 | atomic | acc-checklist-update | `raps acc checklist update --project $PROJECT_ID --checklist $CHECKLIST_ID ...` | Updates checklist |
| SR-174 | atomic | acc-checklist-templates | `raps acc checklist templates --project $PROJECT_ID` | Lists checklist templates |
| SR-175 | lifecycle | asset-tracking-lifecycle | Facilities manager tracks equipment (7 steps) | -- |
| SR-176 | lifecycle | submittal-review-lifecycle | GC submits shop drawings (6 steps) | -- |
| SR-177 | lifecycle | checklist-inspection-lifecycle | Inspector completes inspection (6 steps) | -- |

## Section 10 -- Webhooks

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-180 | atomic | webhook-events | `raps webhook events` | Lists event types |
| SR-181 | atomic | webhook-create | `raps webhook create --event "dm.version.added" --callback-url "..." --scope "..."` | Creates webhook |
| SR-182 | atomic | webhook-list | `raps webhook list` | Lists webhooks |
| SR-183 | atomic | webhook-get | `raps webhook get --id $WEBHOOK_ID` | Shows details |
| SR-184 | atomic | webhook-update | `raps webhook update --id $WEBHOOK_ID --status "inactive"` | Updates webhook |
| SR-185 | atomic | webhook-test | `raps webhook test --id $WEBHOOK_ID` | Sends test event |
| SR-186 | atomic | webhook-verify-signature | `raps webhook verify-signature --payload '...' --signature "..." --secret "..."` | Verifies signature |
| SR-187 | atomic | webhook-delete | `raps webhook delete --id $WEBHOOK_ID --yes` | Deletes webhook |
| SR-188 | lifecycle | webhook-subscription-lifecycle | DevOps sets up file change notifications (8 steps) | -- |

## Section 11 -- Admin: Bulk User Management

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-190 | atomic | admin-user-list-account | `raps admin user list --account $ACCOUNT_ID` | Lists all users in account |
| SR-191 | atomic | admin-user-list-project | `raps admin user list --project $PROJECT_ID` | Lists users in project |
| SR-192 | atomic | admin-user-list-filtered | `raps admin user list --account $ACCOUNT_ID --role "project_admin" --status "active" ...` | Filtered user list |
| SR-193 | atomic | admin-user-add-bulk-dryrun | `raps admin user add user@company.com --account $ACCOUNT_ID ... --dry-run` | Shows which projects affected |
| SR-194 | atomic | admin-user-add-bulk-execute | `raps admin user add user@company.com --account $ACCOUNT_ID ... --yes` | Adds user to matching projects |
| SR-195 | atomic | admin-user-add-from-file | `raps admin user add user@company.com --account $ACCOUNT_ID --project-ids ./project-ids.txt ...` | Adds user to projects in file |
| SR-196 | atomic | admin-user-remove-bulk-dryrun | `raps admin user remove user@company.com --account $ACCOUNT_ID ... --dry-run` | Shows projects user would be removed from |
| SR-197 | atomic | admin-user-update-bulk-dryrun | `raps admin user update user@company.com --account $ACCOUNT_ID ... --dry-run` | Shows role change preview |
| SR-198 | atomic | admin-user-update-from-csv | `raps admin user update user@company.com --account $ACCOUNT_ID --from-csv ... --yes` | Updates roles per CSV |
| SR-199 | atomic | admin-user-add-single | `raps admin user add-to-project --project $PROJECT_ID --email "..." --role-id $ROLE_ID` | Adds single user |
| SR-200 | atomic | admin-user-update-single | `raps admin user update-in-project --project $PROJECT_ID --user-id $USER_ID ...` | Updates user role |
| SR-201 | atomic | admin-user-remove-single | `raps admin user remove-from-project --project $PROJECT_ID --user-id $USER_ID --yes` | Removes user |
| SR-202 | atomic | admin-user-import-csv | `raps admin user import --project $PROJECT_ID --from-csv ./new-users.csv` | Imports users from CSV |
| SR-203 | lifecycle | new-employee-onboarding | Account admin onboards new team member (7 steps) | -- |
| SR-204 | lifecycle | employee-offboarding | Remove departing employee (4 steps) | -- |
| SR-205 | lifecycle | role-migration | Downgrade stale admins to viewers (5 steps) | -- |
| SR-206 | lifecycle | csv-batch-onboarding | Onboard 50 users from CSV (4 steps) | -- |

## Section 12 -- Admin: Project Management

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-210 | atomic | admin-project-list | `raps admin project list --account $ACCOUNT_ID` | Lists all projects in the account |
| SR-211 | atomic | admin-project-list-filtered | `raps admin project list --account $ACCOUNT_ID --filter "Tower" --status active ...` | Filtered project list |
| SR-212 | atomic | admin-project-create | `raps admin project create --account $ACCOUNT_ID --name "Tower Phase 3" ...` | Creates a new project |
| SR-213 | atomic | admin-project-update | `raps admin project update --account $ACCOUNT_ID --project $PROJECT_ID ...` | Updates project name and status |
| SR-214 | atomic | admin-project-archive | `raps admin project archive --account $ACCOUNT_ID --project $PROJECT_ID` | Archives the project |
| SR-215 | lifecycle | project-lifecycle-admin | Create and manage project (6 steps) | -- |

## Section 13 -- Admin: Folder Permissions & Operations

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-220 | atomic | admin-folder-rights-dryrun | `raps admin folder rights user@company.com --account $ACCT ... --dry-run` | Shows which projects and folders would be affected |
| SR-221 | atomic | admin-folder-rights-execute | `raps admin folder rights user@company.com --account $ACCT ... --yes` | Grants folder permissions across matching projects |
| SR-222 | atomic | admin-folder-rights-from-file | `raps admin folder rights user@company.com --account $ACCT --project-ids ... --yes` | Grants folder permissions to projects in file |
| SR-223 | atomic | admin-company-list | `raps admin company-list --account $ACCOUNT_ID` | Lists all companies in the account |
| SR-224 | atomic | admin-operation-list | `raps admin operation list --status completed --limit 5` | Lists recent completed operations |
| SR-225 | atomic | admin-operation-status | `raps admin operation status $OPERATION_ID` | Shows detailed operation status |
| SR-226 | atomic | admin-operation-resume | `raps admin operation resume $OPERATION_ID --concurrency 3` | Resumes the operation with specified concurrency |
| SR-227 | atomic | admin-operation-cancel | `raps admin operation cancel $OPERATION_ID --yes` | Cancels the operation |
| SR-228 | lifecycle | folder-permissions-lifecycle | Grant, verify, restrict folder access (6 steps) | -- |

## Section 14 -- Reality Capture

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-230 | atomic | reality-list | `raps reality list` | Lists all reality capture jobs |
| SR-231 | atomic | reality-formats | `raps reality formats` | Lists supported output formats |
| SR-232 | atomic | reality-create | `raps reality create --name "Site Survey 2026-02" --format obj` | Creates a new reality capture job |
| SR-233 | atomic | reality-upload | `raps reality upload --job $JOB_ID --photos ./site-photos/` | Uploads photos to the reality capture job |
| SR-234 | atomic | reality-process | `raps reality process --job $JOB_ID` | Starts photogrammetry processing |
| SR-235 | atomic | reality-status | `raps reality status --job $JOB_ID` | Shows current job status and progress |
| SR-236 | atomic | reality-result | `raps reality result --job $JOB_ID --output ./results/` | Downloads processed output files |
| SR-237 | atomic | reality-delete | `raps reality delete --job $JOB_ID --yes` | Deletes the reality capture job |
| SR-238 | lifecycle | reality-capture-lifecycle | Capture and process construction site (8 steps) | -- |

## Section 15 -- Portfolio Reports

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-240 | atomic | report-rfi-summary | `raps report rfi-summary --account $ACCOUNT_ID --filter "Tower" ...` | Aggregated RFI summary |
| SR-241 | atomic | report-issues-summary | `raps report issues-summary --account $ACCOUNT_ID --filter "Phase 2" ...` | Aggregated issue summary |
| SR-242 | atomic | report-submittals-summary | `raps report submittals-summary --account $ACCOUNT_ID` | Submittal summary |
| SR-243 | atomic | report-checklists-summary | `raps report checklists-summary --account $ACCOUNT_ID --status "in_progress"` | Checklist summary |
| SR-244 | atomic | report-assets-summary | `raps report assets-summary --account $ACCOUNT_ID --filter "Hospital"` | Asset summary |

## Section 16 -- Templates

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-250 | atomic | template-list | `raps template list --account $ACCOUNT_ID` | Lists templates |
| SR-251 | atomic | template-create | `raps template create --account $ACCOUNT_ID --name "Standard Building Template"` | Creates template |
| SR-252 | atomic | template-info | `raps template info $TEMPLATE_ID --account $ACCOUNT_ID` | Shows template details |
| SR-253 | atomic | template-update | `raps template update $TEMPLATE_ID --account $ACCOUNT_ID --name "... v2"` | Updates template |
| SR-254 | atomic | template-archive | `raps template archive $TEMPLATE_ID --account $ACCOUNT_ID` | Archives template |
| SR-255 | lifecycle | template-management-lifecycle | Admin manages templates (6 steps) | -- |

## Section 17 -- Plugins

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-260 | atomic | plugin-list | `raps plugin list` | Lists plugins |
| SR-261 | atomic | plugin-enable | `raps plugin enable my-plugin` | Enables plugin |
| SR-262 | atomic | plugin-disable | `raps plugin disable my-plugin` | Disables plugin |
| SR-263 | atomic | plugin-alias-list | `raps plugin alias list` | Lists aliases |
| SR-264 | atomic | plugin-alias-add | `raps plugin alias add "bl" "bucket list"` | Creates alias |
| SR-265 | atomic | plugin-alias-remove | `raps plugin alias remove "bl"` | Removes alias |
| SR-266 | lifecycle | alias-power-user-lifecycle | Developer sets up aliases (7 steps) | -- |

## Section 18 -- Pipelines

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-270 | atomic | pipeline-sample | `raps pipeline sample --out-file ./sample-pipeline.yaml` | Generates sample YAML |
| SR-271 | atomic | pipeline-validate | `raps pipeline validate --file ./sample-pipeline.yaml` | Validates structure |
| SR-272 | atomic | pipeline-run | `raps pipeline run --file ./sample-pipeline.yaml` | Executes pipeline |
| SR-273 | lifecycle | pipeline-author-and-run | DevOps creates and runs pipeline (3 steps) | -- |

## Section 19 -- Raw API

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-280 | atomic | api-get | `raps api get "/oss/v2/buckets"` | Makes GET request |
| SR-281 | atomic | api-post | `raps api post "/oss/v2/buckets" --body '{...}'` | Creates via POST |
| SR-282 | atomic | api-put | `raps api put "/project/v1/hubs/$HUB_ID/projects/$PID" --body '{...}'` | PUT request |
| SR-283 | atomic | api-patch | `raps api patch "/issues/v1/containers/$CID/quality-issues/$IID" --body '{...}'` | PATCH request |
| SR-284 | atomic | api-delete | `raps api delete "/oss/v2/buckets/api-test"` | DELETE request |

## Section 20 -- Generation

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-290 | atomic | generate-files-simple | `raps generate files --count 1 --out-dir ./gen-simple/ --complexity simple` | Generates simple files |
| SR-291 | atomic | generate-files-complex | `raps generate files --count 10 --out-dir ./gen-complex/ --complexity complex` | Generates complex files |

## Section 21 -- Shell, Serve, Completions

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-300 | atomic | shell-interactive | `timeout 3 raps shell <<< "exit" \|\| true` | Starts REPL |
| SR-301 | atomic | serve-mcp | `timeout 3 raps serve \|\| true` | Starts MCP server |
| SR-302 | atomic | completions-bash | `raps completions bash` | Outputs bash completions |
| SR-303 | atomic | completions-powershell | `raps completions powershell` | Outputs PowerShell completions |
| SR-304 | atomic | completions-zsh | `raps completions zsh` | Outputs zsh completions |
| SR-305 | atomic | completions-fish | `raps completions fish` | Outputs fish completions |

## Section 22 -- Demo

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-310 | atomic | demo-bucket-lifecycle | `raps demo bucket-lifecycle --prefix "demo" --skip-cleanup` | Runs bucket lifecycle demo |
| SR-311 | atomic | demo-model-pipeline | `raps demo model-pipeline --file ./test-data/sample.rvt --format svf2 --keep-bucket` | Runs model pipeline demo |
| SR-312 | atomic | demo-data-management | `raps demo data-management --non-interactive --export ./dm-report.json` | Runs data management demo |
| SR-313 | atomic | demo-batch-processing | `raps demo batch-processing --input ./test-data/ --max-parallel 3 ...` | Runs batch processing demo |

## Section 30 -- Cross-Domain Workflows

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-400 | lifecycle | workflow-model-review-cycle | Architect uploads, translates, creates issues (10 steps) | -- |
| SR-401 | lifecycle | workflow-project-setup | Admin creates project and staffs it (9 steps) | -- |
| SR-402 | lifecycle | workflow-ci-cd-pipeline | CI/CD upload, translate, verify (10 steps) | -- |
| SR-403 | lifecycle | workflow-design-automation-job | DevOps runs Revit extraction via DA (12 steps) | -- |
| SR-404 | lifecycle | workflow-portfolio-health-check | Executive reviews portfolio health (6 steps) | -- |
| SR-405 | lifecycle | workflow-site-survey-to-model | Survey captures, processes, uploads to BIM 360 (10 steps) | -- |
| SR-406 | lifecycle | workflow-weekly-admin-operations | Admin weekly maintenance (8 steps) | -- |
| SR-407 | lifecycle | workflow-webhook-driven-automation | DevOps sets up webhooks (10 steps) | -- |
| SR-408 | lifecycle | workflow-multi-profile-operations | Consultant switches profiles (14 steps) | -- |
| SR-409 | lifecycle | workflow-pipeline-yaml-automation | Create, validate, run pipeline (5 steps) | -- |

## Section 99 -- Cross-Cutting

| ID | Type | Slug | Command | Expected |
|----|------|------|---------|----------|
| SR-500 | atomic | bucket-list-table | `raps bucket list --output table` | Table-formatted bucket list |
| SR-501 | atomic | bucket-list-json | `raps bucket list --output json` | JSON-formatted bucket list |
| SR-502 | atomic | bucket-list-yaml | `raps bucket list --output yaml` | YAML-formatted bucket list |
| SR-503 | atomic | bucket-list-csv | `raps bucket list --output csv` | CSV-formatted bucket list |
| SR-504 | atomic | bucket-list-plain | `raps bucket list --output plain` | Plain-text bucket list |
| SR-505 | atomic | issue-list-table | `raps issue list --project $PROJECT_ID --output table` | Table-formatted issue list |
| SR-506 | atomic | issue-list-json | `raps issue list --project $PROJECT_ID --output json` | JSON-formatted issue list |
| SR-507 | atomic | issue-list-yaml | `raps issue list --project $PROJECT_ID --output yaml` | YAML-formatted issue list |
| SR-508 | atomic | issue-list-csv | `raps issue list --project $PROJECT_ID --output csv` | CSV-formatted issue list |
| SR-509 | atomic | issue-list-plain | `raps issue list --project $PROJECT_ID --output plain` | Plain-text issue list |
| SR-510 | atomic | admin-user-list-table | `raps admin user list --account $ACCOUNT_ID --output table` | Table-formatted user list |
| SR-511 | atomic | admin-user-list-json | `raps admin user list --account $ACCOUNT_ID --output json` | JSON-formatted user list |
| SR-512 | atomic | admin-user-list-yaml | `raps admin user list --account $ACCOUNT_ID --output yaml` | YAML-formatted user list |
| SR-513 | atomic | admin-user-list-csv | `raps admin user list --account $ACCOUNT_ID --output csv` | CSV-formatted user list |
| SR-514 | atomic | admin-user-list-plain | `raps admin user list --account $ACCOUNT_ID --output plain` | Plain-text user list |
| SR-515 | atomic | hub-list-table | `raps hub list --output table` | Table-formatted hub list |
| SR-516 | atomic | hub-list-json | `raps hub list --output json` | JSON-formatted hub list |
| SR-517 | atomic | hub-list-yaml | `raps hub list --output yaml` | YAML-formatted hub list |
| SR-518 | atomic | hub-list-csv | `raps hub list --output csv` | CSV-formatted hub list |
| SR-519 | atomic | hub-list-plain | `raps hub list --output plain` | Plain-text hub list |
| SR-520 | atomic | da-engines-table | `raps da engines --output table` | Table-formatted engine list |
| SR-521 | atomic | da-engines-json | `raps da engines --output json` | JSON-formatted engine list |
| SR-522 | atomic | da-engines-yaml | `raps da engines --output yaml` | YAML-formatted engine list |
| SR-523 | atomic | da-engines-csv | `raps da engines --output csv` | CSV-formatted engine list |
| SR-524 | atomic | da-engines-plain | `raps da engines --output plain` | Plain-text engine list |
| SR-530 | atomic | no-color-bucket-list | `raps bucket list --no-color` | Bucket list without ANSI colors |
| SR-531 | atomic | no-color-issue-list | `raps issue list --project $PROJECT_ID --no-color` | Issue list without ANSI colors |
| SR-540 | atomic | help-top-level | `raps --help` | Top-level help text |
| SR-541 | atomic | help-auth | `raps auth --help` | Auth subcommand help |
| SR-542 | atomic | help-admin | `raps admin --help` | Admin subcommand help |
| SR-543 | atomic | help-admin-user | `raps admin user --help` | Admin user subcommand help |
| SR-544 | atomic | help-version | `raps --version` | Version string |

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| **Total sample runs** | **259** |
| Atomic runs | 216 |
| Lifecycle runs | 43 |
| Sections | 25 |
| ID range | SR-001 through SR-544 |

### Runs per APS domain

| Domain | Atomic | Lifecycle | Total |
|--------|--------|-----------|-------|
| Setup & Prerequisites | 3 | 0 | 3 |
| Authentication | 11 | 4 | 15 |
| Configuration | 14 | 2 | 16 |
| Storage (OSS) | 13 | 3 | 16 |
| Data Management | 15 | 3 | 18 |
| Model Derivative | 10 | 2 | 12 |
| Design Automation | 10 | 2 | 12 |
| ACC Issues | 10 | 2 | 12 |
| ACC RFIs | 5 | 1 | 6 |
| ACC Modules | 15 | 3 | 18 |
| Webhooks | 8 | 1 | 9 |
| Admin: Users | 13 | 4 | 17 |
| Admin: Projects | 5 | 1 | 6 |
| Admin: Folders | 8 | 1 | 9 |
| Reality Capture | 8 | 1 | 9 |
| Portfolio Reports | 5 | 0 | 5 |
| Templates | 5 | 1 | 6 |
| Plugins | 6 | 1 | 7 |
| Pipelines | 3 | 1 | 4 |
| Raw API | 5 | 0 | 5 |
| Generation | 2 | 0 | 2 |
| Shell/Serve/Completions | 6 | 0 | 6 |
| Demo | 4 | 0 | 4 |
| Cross-Domain Workflows | 0 | 10 | 10 |
| Cross-Cutting | 32 | 0 | 32 |
