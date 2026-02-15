# Section 30 — Cross-Domain Workflows
# Runs: SR-400 through SR-409
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "30-workflows" -Title "Cross-Domain Workflows"

# -- Lifecycles ------------------------------------------------------------

# SR-400: Architect uploads, translates, creates issues
Start-Lifecycle -Id "SR-400" -Slug "workflow-model-review-cycle" -Description "Architect uploads, translates, creates issues"
Invoke-LifecycleStep -StepNum 1  -Command "raps bucket create -k review-cycle -p transient"
Invoke-LifecycleStep -StepNum 2  -Command "raps object upload review-cycle ./model.rvt"
Invoke-LifecycleStep -StepNum 3  -Command "raps translate start $env:URN -f svf2"
Invoke-LifecycleStep -StepNum 4  -Command "raps translate status $env:URN"
Invoke-LifecycleStep -StepNum 5  -Command "raps translate manifest $env:URN"
Invoke-LifecycleStep -StepNum 6  -Command "raps issue create $env:PID -t `"Clash at grid A-3`""
Invoke-LifecycleStep -StepNum 7  -Command "raps issue create $env:PID -t `"Missing fire rating on wall W-12`""
Invoke-LifecycleStep -StepNum 8  -Command "raps issue comment add $env:PID $env:I1 -b `"See model view at Level 2`""
Invoke-LifecycleStep -StepNum 9  -Command "raps rfi create $env:PID --title `"Confirm structural capacity at A-3`""
Invoke-LifecycleStep -StepNum 10 -Command "raps bucket delete review-cycle --yes"
End-Lifecycle

# SR-401: Admin creates project and staffs it
Start-Lifecycle -Id "SR-401" -Slug "workflow-project-setup" -Description "Admin creates project and staffs it"
Invoke-LifecycleStep -StepNum 1 -Command "raps template list -a $env:ACCT"
Invoke-LifecycleStep -StepNum 2 -Command "raps admin project create -a $env:ACCT -n `"Hospital Wing B`" -t `"Healthcare`""
Invoke-LifecycleStep -StepNum 3 -Command "raps admin user add pm@co.com -a $env:ACCT -r `"project_admin`" -f `"Hospital Wing B`" -y"
Invoke-LifecycleStep -StepNum 4 -Command "raps admin user add struct@co.com -a $env:ACCT -r `"viewer`" -f `"Hospital Wing B`" -y"
Invoke-LifecycleStep -StepNum 5 -Command "raps admin user add mep@co.com -a $env:ACCT -r `"viewer`" -f `"Hospital Wing B`" -y"
Invoke-LifecycleStep -StepNum 6 -Command "raps admin folder rights struct@co.com -a $env:ACCT -l view-download-upload --folder `"Structural`" -f `"Hospital Wing B`" -y"
Invoke-LifecycleStep -StepNum 7 -Command "raps admin folder rights mep@co.com -a $env:ACCT -l view-download-upload --folder `"MEP`" -f `"Hospital Wing B`" -y"
Invoke-LifecycleStep -StepNum 8 -Command "raps admin user list -p $env:NEW_PID"
Invoke-LifecycleStep -StepNum 9 -Command "raps webhook create -e `"dm.version.added`" -u `"https://hooks.co.com/hospital`""
End-Lifecycle

# SR-402: CI/CD upload, translate, verify
Start-Lifecycle -Id "SR-402" -Slug "workflow-ci-cd-pipeline" -Description "CI/CD upload, translate, verify"
Invoke-LifecycleStep -StepNum 1  -Command "raps auth test"
Invoke-LifecycleStep -StepNum 2  -Command "raps bucket create -k ci-build-123 -p transient"
Invoke-LifecycleStep -StepNum 3  -Command "raps object upload-batch ci-build-123 ./artifacts/*"
Invoke-LifecycleStep -StepNum 4  -Command "raps object list ci-build-123 --output json"
Invoke-LifecycleStep -StepNum 5  -Command "raps translate start $env:URN1 -f svf2"
Invoke-LifecycleStep -StepNum 6  -Command "raps translate start $env:URN2 -f svf2"
Invoke-LifecycleStep -StepNum 7  -Command "raps translate status $env:URN1"
Invoke-LifecycleStep -StepNum 8  -Command "raps translate status $env:URN2"
Invoke-LifecycleStep -StepNum 9  -Command "raps translate download $env:URN1 -o ./translated/"
Invoke-LifecycleStep -StepNum 10 -Command "raps bucket delete ci-build-123 --yes"
End-Lifecycle

# SR-403: DevOps runs Revit extraction via DA
Start-Lifecycle -Id "SR-403" -Slug "workflow-design-automation-job" -Description "DevOps runs Revit extraction via DA"
Invoke-LifecycleStep -StepNum 1  -Command "raps bucket create -k da-job -p transient"
Invoke-LifecycleStep -StepNum 2  -Command "raps object upload da-job ./input-model.rvt"
Invoke-LifecycleStep -StepNum 3  -Command "raps object signed-url da-job input-model.rvt"
Invoke-LifecycleStep -StepNum 4  -Command "raps da engines"
Invoke-LifecycleStep -StepNum 5  -Command "raps da appbundle-create -i `"Extract`" -e `"Autodesk.Revit+2025`""
Invoke-LifecycleStep -StepNum 6  -Command "raps da activity-create --id `"ExtractAct`" --engine `"Autodesk.Revit+2025`" --appbundle `"Extract`" --command `"...`""
Invoke-LifecycleStep -StepNum 7  -Command "raps da run `"ExtractAct`" -i $env:INPUT_URL -o $env:OUTPUT_URL"
Invoke-LifecycleStep -StepNum 8  -Command "raps da status $env:WI_ID"
Invoke-LifecycleStep -StepNum 9  -Command "raps object download da-job output.json -o ./results/"
Invoke-LifecycleStep -StepNum 10 -Command "raps da activity-delete `"ExtractAct`""
Invoke-LifecycleStep -StepNum 11 -Command "raps da appbundle-delete `"Extract`""
Invoke-LifecycleStep -StepNum 12 -Command "raps bucket delete da-job --yes"
End-Lifecycle

# SR-404: Executive reviews portfolio health
Start-Lifecycle -Id "SR-404" -Slug "workflow-portfolio-health-check" -Description "Executive reviews portfolio health"
Invoke-LifecycleStep -StepNum 1 -Command "raps admin project list -a $env:ACCT --status active"
Invoke-LifecycleStep -StepNum 2 -Command "raps report issues-summary -a $env:ACCT --status open --output json"
Invoke-LifecycleStep -StepNum 3 -Command "raps report rfi-summary -a $env:ACCT --status open --since `"2026-01-01`" --output json"
Invoke-LifecycleStep -StepNum 4 -Command "raps report submittals-summary -a $env:ACCT --output json"
Invoke-LifecycleStep -StepNum 5 -Command "raps report checklists-summary -a $env:ACCT --status `"in_progress`" --output json"
Invoke-LifecycleStep -StepNum 6 -Command "raps report assets-summary -a $env:ACCT --output json"
End-Lifecycle

# SR-405: Survey captures, processes, uploads to BIM 360
Start-Lifecycle -Id "SR-405" -Slug "workflow-site-survey-to-model" -Description "Survey captures, processes, uploads to BIM 360"
Invoke-LifecycleStep -StepNum 1  -Command "raps reality create -n `"Foundation Survey`" -f obj"
Invoke-LifecycleStep -StepNum 2  -Command "raps reality upload $env:JID ./site-photos/*"
Invoke-LifecycleStep -StepNum 3  -Command "raps reality process $env:JID"
Invoke-LifecycleStep -StepNum 4  -Command "raps reality status $env:JID"
Invoke-LifecycleStep -StepNum 5  -Command "raps reality result $env:JID"
Invoke-LifecycleStep -StepNum 6  -Command "raps bucket create -k survey-upload -p transient"
Invoke-LifecycleStep -StepNum 7  -Command "raps object upload survey-upload ./survey-results/model.obj"
Invoke-LifecycleStep -StepNum 8  -Command "raps item create-from-oss $env:PROJECT_ID $env:FOLDER_ID -n `"Foundation Survey 2026-02`" --object-id $env:URN"
Invoke-LifecycleStep -StepNum 9  -Command "raps reality delete $env:JID --yes"
Invoke-LifecycleStep -StepNum 10 -Command "raps bucket delete survey-upload --yes"
End-Lifecycle

# SR-406: Admin weekly maintenance
Start-Lifecycle -Id "SR-406" -Slug "workflow-weekly-admin-operations" -Description "Admin weekly maintenance"
Invoke-LifecycleStep -StepNum 1 -Command "raps admin user list -a $env:ACCT --status `"active`" --output json"
Invoke-LifecycleStep -StepNum 2 -Command "raps admin user list -a $env:ACCT --role `"project_admin`""
Invoke-LifecycleStep -StepNum 3 -Command "raps admin project list -a $env:ACCT -f `"2024`" --status active"
Invoke-LifecycleStep -StepNum 4 -Command "raps admin user update admin@old.com -a $env:ACCT -r `"viewer`" --from-role `"project_admin`" -f `"2024`" --dry-run"
Invoke-LifecycleStep -StepNum 5 -Command "raps admin user update admin@old.com -a $env:ACCT -r `"viewer`" --from-role `"project_admin`" -f `"2024`" -y"
Invoke-LifecycleStep -StepNum 6 -Command "raps admin operation status $env:OP_ID"
Invoke-LifecycleStep -StepNum 7 -Command "raps admin company-list -a $env:ACCT"
Invoke-LifecycleStep -StepNum 8 -Command "raps report issues-summary -a $env:ACCT --status open"
End-Lifecycle

# SR-407: DevOps sets up webhooks
Start-Lifecycle -Id "SR-407" -Slug "workflow-webhook-driven-automation" -Description "DevOps sets up webhooks"
Invoke-LifecycleStep -StepNum 1  -Command "raps webhook events"
Invoke-LifecycleStep -StepNum 2  -Command "raps webhook create -e `"dm.version.added`" -u `"https://ci.co.com/trigger`""
Invoke-LifecycleStep -StepNum 3  -Command "raps webhook create -e `"dm.version.added`" -u `"https://ci.co.com/trigger`""
Invoke-LifecycleStep -StepNum 4  -Command "raps webhook list"
Invoke-LifecycleStep -StepNum 5  -Command "raps webhook test `"https://ci.co.com/trigger`""
Invoke-LifecycleStep -StepNum 6  -Command "raps object upload staging ./new-model.rvt"
Invoke-LifecycleStep -StepNum 7  -Command "raps webhook get -e `"dm.version.added`" --hook-id $env:WH1"
Invoke-LifecycleStep -StepNum 8  -Command "raps webhook update -e `"dm.version.added`" --hook-id $env:WH2 --status `"inactive`""
Invoke-LifecycleStep -StepNum 9  -Command "raps webhook delete $env:WH1 -e `"dm.version.added`" --yes"
Invoke-LifecycleStep -StepNum 10 -Command "raps webhook delete $env:WH2 -e `"dm.version.added`" --yes"
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
Invoke-LifecycleStep -StepNum 1 -Command "raps pipeline sample -o ./my-pipeline.yaml"
Invoke-LifecycleStep -StepNum 2 -Command "raps pipeline validate ./my-pipeline.yaml"
Invoke-LifecycleStep -StepNum 3 -Command "raps generate files -c 3 -o ./pipeline-input/ --complexity medium"
Invoke-LifecycleStep -StepNum 4 -Command "raps pipeline run ./my-pipeline.yaml"
Invoke-LifecycleStep -StepNum 5 -Command "raps admin operation list --limit 1"
End-Lifecycle

End-Section
