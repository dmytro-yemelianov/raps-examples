# Section 30 — Cross-Domain Workflows
# Runs: SR-400 through SR-409
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "30-workflows" -Title "Cross-Domain Workflows"

# -- Lifecycles ------------------------------------------------------------

# SR-400: Architect uploads, translates, creates issues
Start-Lifecycle -Id "SR-400" -Slug "workflow-model-review-cycle" -Description "Architect uploads, translates, creates issues"
Invoke-LifecycleStep -StepNum 1  -Command "raps bucket create --name review-cycle --policy transient"
Invoke-LifecycleStep -StepNum 2  -Command "raps object upload --bucket review-cycle --file ./model.rvt"
Invoke-LifecycleStep -StepNum 3  -Command "raps translate start --urn $env:URN --format svf2"
Invoke-LifecycleStep -StepNum 4  -Command "raps translate status --urn $env:URN"
Invoke-LifecycleStep -StepNum 5  -Command "raps translate manifest --urn $env:URN"
Invoke-LifecycleStep -StepNum 6  -Command "raps issue create --project $env:PID --title `"Clash at grid A-3`" --type $env:TYPE"
Invoke-LifecycleStep -StepNum 7  -Command "raps issue create --project $env:PID --title `"Missing fire rating on wall W-12`" --type $env:TYPE"
Invoke-LifecycleStep -StepNum 8  -Command "raps issue comment add --project $env:PID --issue $env:I1 --body `"See model view at Level 2`""
Invoke-LifecycleStep -StepNum 9  -Command "raps rfi create --project $env:PID --title `"Confirm structural capacity at A-3`""
Invoke-LifecycleStep -StepNum 10 -Command "raps bucket delete --name review-cycle --yes"
End-Lifecycle

# SR-401: Admin creates project and staffs it
Start-Lifecycle -Id "SR-401" -Slug "workflow-project-setup" -Description "Admin creates project and staffs it"
Invoke-LifecycleStep -StepNum 1 -Command "raps template list --account $env:ACCT"
Invoke-LifecycleStep -StepNum 2 -Command "raps admin project create --account $env:ACCT --name `"Hospital Wing B`" --type `"Healthcare`""
Invoke-LifecycleStep -StepNum 3 -Command "raps admin user add pm@co.com --account $env:ACCT --role `"project_admin`" --filter `"Hospital Wing B`" --yes"
Invoke-LifecycleStep -StepNum 4 -Command "raps admin user add struct@co.com --account $env:ACCT --role `"viewer`" --filter `"Hospital Wing B`" --yes"
Invoke-LifecycleStep -StepNum 5 -Command "raps admin user add mep@co.com --account $env:ACCT --role `"viewer`" --filter `"Hospital Wing B`" --yes"
Invoke-LifecycleStep -StepNum 6 -Command "raps admin folder rights struct@co.com --account $env:ACCT --level view-download-upload --folder `"Structural`" --filter `"Hospital Wing B`" --yes"
Invoke-LifecycleStep -StepNum 7 -Command "raps admin folder rights mep@co.com --account $env:ACCT --level view-download-upload --folder `"MEP`" --filter `"Hospital Wing B`" --yes"
Invoke-LifecycleStep -StepNum 8 -Command "raps admin user list --project $env:NEW_PID"
Invoke-LifecycleStep -StepNum 9 -Command "raps webhook create --event `"dm.version.added`" --callback-url `"https://hooks.co.com/hospital`" --scope `"folder:$env:ROOT`""
End-Lifecycle

# SR-402: CI/CD upload, translate, verify
Start-Lifecycle -Id "SR-402" -Slug "workflow-ci-cd-pipeline" -Description "CI/CD upload, translate, verify"
Invoke-LifecycleStep -StepNum 1  -Command "raps auth test"
Invoke-LifecycleStep -StepNum 2  -Command "raps bucket create --name ci-build-123 --policy transient"
Invoke-LifecycleStep -StepNum 3  -Command "raps object upload-batch --bucket ci-build-123 --dir ./artifacts/"
Invoke-LifecycleStep -StepNum 4  -Command "raps object list --bucket ci-build-123 --output json"
Invoke-LifecycleStep -StepNum 5  -Command "raps translate start --urn $env:URN1 --format svf2"
Invoke-LifecycleStep -StepNum 6  -Command "raps translate start --urn $env:URN2 --format svf2"
Invoke-LifecycleStep -StepNum 7  -Command "raps translate status --urn $env:URN1"
Invoke-LifecycleStep -StepNum 8  -Command "raps translate status --urn $env:URN2"
Invoke-LifecycleStep -StepNum 9  -Command "raps translate download --urn $env:URN1 --output ./translated/"
Invoke-LifecycleStep -StepNum 10 -Command "raps bucket delete --name ci-build-123 --yes"
End-Lifecycle

# SR-403: DevOps runs Revit extraction via DA
Start-Lifecycle -Id "SR-403" -Slug "workflow-design-automation-job" -Description "DevOps runs Revit extraction via DA"
Invoke-LifecycleStep -StepNum 1  -Command "raps bucket create --name da-job --policy transient"
Invoke-LifecycleStep -StepNum 2  -Command "raps object upload --bucket da-job --file ./input-model.rvt"
Invoke-LifecycleStep -StepNum 3  -Command "raps object signed-url --bucket da-job --key input-model.rvt"
Invoke-LifecycleStep -StepNum 4  -Command "raps da engines"
Invoke-LifecycleStep -StepNum 5  -Command "raps da appbundle-create --name `"Extract`" --engine `"Autodesk.Revit+2025`" --bundle ./plugin.zip"
Invoke-LifecycleStep -StepNum 6  -Command "raps da activity-create --name `"ExtractAct`" --engine `"Autodesk.Revit+2025`" --appbundle `"Extract`" --command-line `"...`""
Invoke-LifecycleStep -StepNum 7  -Command "raps da run --activity `"ExtractAct`" --input-url $env:INPUT_URL --output-url $env:OUTPUT_URL"
Invoke-LifecycleStep -StepNum 8  -Command "raps da status --id $env:WI_ID"
Invoke-LifecycleStep -StepNum 9  -Command "raps object download --bucket da-job --key output.json --output ./results/"
Invoke-LifecycleStep -StepNum 10 -Command "raps da activity-delete --name `"ExtractAct`""
Invoke-LifecycleStep -StepNum 11 -Command "raps da appbundle-delete --name `"Extract`""
Invoke-LifecycleStep -StepNum 12 -Command "raps bucket delete --name da-job --yes"
End-Lifecycle

# SR-404: Executive reviews portfolio health
Start-Lifecycle -Id "SR-404" -Slug "workflow-portfolio-health-check" -Description "Executive reviews portfolio health"
Invoke-LifecycleStep -StepNum 1 -Command "raps admin project list --account $env:ACCT --status active"
Invoke-LifecycleStep -StepNum 2 -Command "raps report issues-summary --account $env:ACCT --status open --output json"
Invoke-LifecycleStep -StepNum 3 -Command "raps report rfi-summary --account $env:ACCT --status open --since `"2026-01-01`" --output json"
Invoke-LifecycleStep -StepNum 4 -Command "raps report submittals-summary --account $env:ACCT --output json"
Invoke-LifecycleStep -StepNum 5 -Command "raps report checklists-summary --account $env:ACCT --status `"in_progress`" --output json"
Invoke-LifecycleStep -StepNum 6 -Command "raps report assets-summary --account $env:ACCT --output json"
End-Lifecycle

# SR-405: Survey captures, processes, uploads to BIM 360
Start-Lifecycle -Id "SR-405" -Slug "workflow-site-survey-to-model" -Description "Survey captures, processes, uploads to BIM 360"
Invoke-LifecycleStep -StepNum 1  -Command "raps reality create --name `"Foundation Survey`" --format obj"
Invoke-LifecycleStep -StepNum 2  -Command "raps reality upload --job $env:JID --photos ./site-photos/"
Invoke-LifecycleStep -StepNum 3  -Command "raps reality process --job $env:JID"
Invoke-LifecycleStep -StepNum 4  -Command "raps reality status --job $env:JID"
Invoke-LifecycleStep -StepNum 5  -Command "raps reality result --job $env:JID --output ./survey-results/"
Invoke-LifecycleStep -StepNum 6  -Command "raps bucket create --name survey-upload --policy transient"
Invoke-LifecycleStep -StepNum 7  -Command "raps object upload --bucket survey-upload --file ./survey-results/model.obj"
Invoke-LifecycleStep -StepNum 8  -Command "raps item create-from-oss $env:PROJECT_ID $env:FOLDER_ID --name `"Foundation Survey 2026-02`" --object-id $env:URN"
Invoke-LifecycleStep -StepNum 9  -Command "raps reality delete --job $env:JID --yes"
Invoke-LifecycleStep -StepNum 10 -Command "raps bucket delete --name survey-upload --yes"
End-Lifecycle

# SR-406: Admin weekly maintenance
Start-Lifecycle -Id "SR-406" -Slug "workflow-weekly-admin-operations" -Description "Admin weekly maintenance"
Invoke-LifecycleStep -StepNum 1 -Command "raps admin user list --account $env:ACCT --status `"active`" --output json"
Invoke-LifecycleStep -StepNum 2 -Command "raps admin user list --account $env:ACCT --role `"project_admin`""
Invoke-LifecycleStep -StepNum 3 -Command "raps admin project list --account $env:ACCT --filter `"2024`" --status active"
Invoke-LifecycleStep -StepNum 4 -Command "raps admin user update admin@old.com --account $env:ACCT --role `"viewer`" --from-role `"project_admin`" --filter `"2024`" --dry-run"
Invoke-LifecycleStep -StepNum 5 -Command "raps admin user update admin@old.com --account $env:ACCT --role `"viewer`" --from-role `"project_admin`" --filter `"2024`" --yes"
Invoke-LifecycleStep -StepNum 6 -Command "raps admin operation status $env:OP_ID"
Invoke-LifecycleStep -StepNum 7 -Command "raps admin company-list --account $env:ACCT"
Invoke-LifecycleStep -StepNum 8 -Command "raps report issues-summary --account $env:ACCT --status open"
End-Lifecycle

# SR-407: DevOps sets up webhooks
Start-Lifecycle -Id "SR-407" -Slug "workflow-webhook-driven-automation" -Description "DevOps sets up webhooks"
Invoke-LifecycleStep -StepNum 1  -Command "raps webhook events"
Invoke-LifecycleStep -StepNum 2  -Command "raps webhook create --event `"dm.version.added`" --callback-url `"https://ci.co.com/trigger`" --scope `"folder:$env:PLANS`""
Invoke-LifecycleStep -StepNum 3  -Command "raps webhook create --event `"dm.version.added`" --callback-url `"https://ci.co.com/trigger`" --scope `"folder:$env:MODELS`""
Invoke-LifecycleStep -StepNum 4  -Command "raps webhook list"
Invoke-LifecycleStep -StepNum 5  -Command "raps webhook test --id $env:WH1"
Invoke-LifecycleStep -StepNum 6  -Command "raps object upload --bucket staging --file ./new-model.rvt"
Invoke-LifecycleStep -StepNum 7  -Command "raps webhook get --id $env:WH1"
Invoke-LifecycleStep -StepNum 8  -Command "raps webhook update --id $env:WH2 --status `"inactive`""
Invoke-LifecycleStep -StepNum 9  -Command "raps webhook delete --id $env:WH1 --yes"
Invoke-LifecycleStep -StepNum 10 -Command "raps webhook delete --id $env:WH2 --yes"
End-Lifecycle

# SR-408: Consultant switches profiles
Start-Lifecycle -Id "SR-408" -Slug "workflow-multi-profile-operations" -Description "Consultant switches profiles"
Invoke-LifecycleStep -StepNum 1  -Command "raps config profile create client-a"
Invoke-LifecycleStep -StepNum 2  -Command "raps config set client_id $env:CLIENT_A_ID"
Invoke-LifecycleStep -StepNum 3  -Command "raps config set client_secret $env:CLIENT_A_SECRET"
Invoke-LifecycleStep -StepNum 4  -Command "raps config profile create client-b"
Invoke-LifecycleStep -StepNum 5  -Command "raps config set client_id $env:CLIENT_B_ID"
Invoke-LifecycleStep -StepNum 6  -Command "raps config set client_secret $env:CLIENT_B_SECRET"
Invoke-LifecycleStep -StepNum 7  -Command "raps config profile use client-a"
Invoke-LifecycleStep -StepNum 8  -Command "raps auth test"
Invoke-LifecycleStep -StepNum 9  -Command "raps bucket list"
Invoke-LifecycleStep -StepNum 10 -Command "raps config profile use client-b"
Invoke-LifecycleStep -StepNum 11 -Command "raps auth test"
Invoke-LifecycleStep -StepNum 12 -Command "raps bucket list"
Invoke-LifecycleStep -StepNum 13 -Command "raps config profile delete client-a"
Invoke-LifecycleStep -StepNum 14 -Command "raps config profile delete client-b"
End-Lifecycle

# SR-409: Create, validate, run pipeline
Start-Lifecycle -Id "SR-409" -Slug "workflow-pipeline-yaml-automation" -Description "Create, validate, run pipeline"
Invoke-LifecycleStep -StepNum 1 -Command "raps pipeline sample --output ./my-pipeline.yaml"
Invoke-LifecycleStep -StepNum 2 -Command "raps pipeline validate --file ./my-pipeline.yaml"
Invoke-LifecycleStep -StepNum 3 -Command "raps generate files --count 3 --output ./pipeline-input/ --complexity medium"
Invoke-LifecycleStep -StepNum 4 -Command "raps pipeline run --file ./my-pipeline.yaml"
Invoke-LifecycleStep -StepNum 5 -Command "raps admin operation list --limit 1"
End-Lifecycle

End-Section
