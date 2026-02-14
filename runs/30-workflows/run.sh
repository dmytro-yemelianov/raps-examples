#!/bin/bash
# Section 30 — Cross-Domain Workflows
# Runs: SR-400 through SR-409
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "30-workflows" "Cross-Domain Workflows"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-400: Architect uploads, translates, creates issues
lifecycle_start "SR-400" "workflow-model-review-cycle" "Architect uploads, translates, creates issues"
lifecycle_step 1  "raps bucket create --name review-cycle --policy transient"
lifecycle_step 2  "raps object upload --bucket review-cycle --file ./model.rvt"
lifecycle_step 3  "raps translate start --urn \$URN --format svf2"
lifecycle_step 4  "raps translate status --urn \$URN"
lifecycle_step 5  "raps translate manifest --urn \$URN"
lifecycle_step 6  "raps issue create --project \$PID --title \"Clash at grid A-3\" --type \$TYPE"
lifecycle_step 7  "raps issue create --project \$PID --title \"Missing fire rating on wall W-12\" --type \$TYPE"
lifecycle_step 8  "raps issue comment add --project \$PID --issue \$I1 --body \"See model view at Level 2\""
lifecycle_step 9  "raps rfi create --project \$PID --title \"Confirm structural capacity at A-3\""
lifecycle_step 10 "raps bucket delete --name review-cycle --yes"
lifecycle_end

# SR-401: Admin creates project and staffs it
lifecycle_start "SR-401" "workflow-project-setup" "Admin creates project and staffs it"
lifecycle_step 1 "raps template list --account \$ACCT"
lifecycle_step 2 "raps admin project create --account \$ACCT --name \"Hospital Wing B\" --type \"Healthcare\""
lifecycle_step 3 "raps admin user add pm@co.com --account \$ACCT --role \"project_admin\" --filter \"Hospital Wing B\" --yes"
lifecycle_step 4 "raps admin user add struct@co.com --account \$ACCT --role \"viewer\" --filter \"Hospital Wing B\" --yes"
lifecycle_step 5 "raps admin user add mep@co.com --account \$ACCT --role \"viewer\" --filter \"Hospital Wing B\" --yes"
lifecycle_step 6 "raps admin folder rights struct@co.com --account \$ACCT --level view-download-upload --folder \"Structural\" --filter \"Hospital Wing B\" --yes"
lifecycle_step 7 "raps admin folder rights mep@co.com --account \$ACCT --level view-download-upload --folder \"MEP\" --filter \"Hospital Wing B\" --yes"
lifecycle_step 8 "raps admin user list --project \$NEW_PID"
lifecycle_step 9 "raps webhook create --event \"dm.version.added\" --callback-url \"https://hooks.co.com/hospital\" --scope \"folder:\$ROOT\""
lifecycle_end

# SR-402: CI/CD upload, translate, verify
lifecycle_start "SR-402" "workflow-ci-cd-pipeline" "CI/CD upload, translate, verify"
lifecycle_step 1  "raps auth test"
lifecycle_step 2  "raps bucket create --name ci-build-123 --policy transient"
lifecycle_step 3  "raps object upload-batch --bucket ci-build-123 --dir ./artifacts/"
lifecycle_step 4  "raps object list --bucket ci-build-123 --output json"
lifecycle_step 5  "raps translate start --urn \$URN1 --format svf2"
lifecycle_step 6  "raps translate start --urn \$URN2 --format svf2"
lifecycle_step 7  "raps translate status --urn \$URN1"
lifecycle_step 8  "raps translate status --urn \$URN2"
lifecycle_step 9  "raps translate download --urn \$URN1 --output ./translated/"
lifecycle_step 10 "raps bucket delete --name ci-build-123 --yes"
lifecycle_end

# SR-403: DevOps runs Revit extraction via DA
lifecycle_start "SR-403" "workflow-design-automation-job" "DevOps runs Revit extraction via DA"
lifecycle_step 1  "raps bucket create --name da-job --policy transient"
lifecycle_step 2  "raps object upload --bucket da-job --file ./input-model.rvt"
lifecycle_step 3  "raps object signed-url --bucket da-job --key input-model.rvt"
lifecycle_step 4  "raps da engines"
lifecycle_step 5  "raps da appbundle-create --name \"Extract\" --engine \"Autodesk.Revit+2025\" --bundle ./plugin.zip"
lifecycle_step 6  "raps da activity-create --name \"ExtractAct\" --engine \"Autodesk.Revit+2025\" --appbundle \"Extract\" --command-line \"...\""
lifecycle_step 7  "raps da run --activity \"ExtractAct\" --input-url \$INPUT_URL --output-url \$OUTPUT_URL"
lifecycle_step 8  "raps da status --id \$WI_ID"
lifecycle_step 9  "raps object download --bucket da-job --key output.json --output ./results/"
lifecycle_step 10 "raps da activity-delete --name \"ExtractAct\""
lifecycle_step 11 "raps da appbundle-delete --name \"Extract\""
lifecycle_step 12 "raps bucket delete --name da-job --yes"
lifecycle_end

# SR-404: Executive reviews portfolio health
lifecycle_start "SR-404" "workflow-portfolio-health-check" "Executive reviews portfolio health"
lifecycle_step 1 "raps admin project list --account \$ACCT --status active"
lifecycle_step 2 "raps report issues-summary --account \$ACCT --status open --output json"
lifecycle_step 3 "raps report rfi-summary --account \$ACCT --status open --since \"2026-01-01\" --output json"
lifecycle_step 4 "raps report submittals-summary --account \$ACCT --output json"
lifecycle_step 5 "raps report checklists-summary --account \$ACCT --status \"in_progress\" --output json"
lifecycle_step 6 "raps report assets-summary --account \$ACCT --output json"
lifecycle_end

# SR-405: Survey captures, processes, uploads to BIM 360
lifecycle_start "SR-405" "workflow-site-survey-to-model" "Survey captures, processes, uploads to BIM 360"
lifecycle_step 1  "raps reality create --name \"Foundation Survey\" --format obj"
lifecycle_step 2  "raps reality upload --job \$JID --photos ./site-photos/"
lifecycle_step 3  "raps reality process --job \$JID"
lifecycle_step 4  "raps reality status --job \$JID"
lifecycle_step 5  "raps reality result --job \$JID --output ./survey-results/"
lifecycle_step 6  "raps bucket create --name survey-upload --policy transient"
lifecycle_step 7  "raps object upload --bucket survey-upload --file ./survey-results/model.obj"
lifecycle_step 8  "raps item create-from-oss \$PROJECT_ID \$FOLDER_ID --name \"Foundation Survey 2026-02\" --object-id \$URN"
lifecycle_step 9  "raps reality delete --job \$JID --yes"
lifecycle_step 10 "raps bucket delete --name survey-upload --yes"
lifecycle_end

# SR-406: Admin weekly maintenance
lifecycle_start "SR-406" "workflow-weekly-admin-operations" "Admin weekly maintenance"
lifecycle_step 1 "raps admin user list --account \$ACCT --status \"active\" --output json"
lifecycle_step 2 "raps admin user list --account \$ACCT --role \"project_admin\""
lifecycle_step 3 "raps admin project list --account \$ACCT --filter \"2024\" --status active"
lifecycle_step 4 "raps admin user update admin@old.com --account \$ACCT --role \"viewer\" --from-role \"project_admin\" --filter \"2024\" --dry-run"
lifecycle_step 5 "raps admin user update admin@old.com --account \$ACCT --role \"viewer\" --from-role \"project_admin\" --filter \"2024\" --yes"
lifecycle_step 6 "raps admin operation status \$OP_ID"
lifecycle_step 7 "raps admin company-list --account \$ACCT"
lifecycle_step 8 "raps report issues-summary --account \$ACCT --status open"
lifecycle_end

# SR-407: DevOps sets up webhooks
lifecycle_start "SR-407" "workflow-webhook-driven-automation" "DevOps sets up webhooks"
lifecycle_step 1  "raps webhook events"
lifecycle_step 2  "raps webhook create --event \"dm.version.added\" --callback-url \"https://ci.co.com/trigger\" --scope \"folder:\$PLANS\""
lifecycle_step 3  "raps webhook create --event \"dm.version.added\" --callback-url \"https://ci.co.com/trigger\" --scope \"folder:\$MODELS\""
lifecycle_step 4  "raps webhook list"
lifecycle_step 5  "raps webhook test --id \$WH1"
lifecycle_step 6  "raps object upload --bucket staging --file ./new-model.rvt"
lifecycle_step 7  "raps webhook get --id \$WH1"
lifecycle_step 8  "raps webhook update --id \$WH2 --status \"inactive\""
lifecycle_step 9  "raps webhook delete --id \$WH1 --yes"
lifecycle_step 10 "raps webhook delete --id \$WH2 --yes"
lifecycle_end

# SR-408: Consultant switches profiles
lifecycle_start "SR-408" "workflow-multi-profile-operations" "Consultant switches profiles"
lifecycle_step 1  "raps config profile create client-a"
lifecycle_step 2  "raps config set client_id \$CLIENT_A_ID"
lifecycle_step 3  "raps config set client_secret \$CLIENT_A_SECRET"
lifecycle_step 4  "raps config profile create client-b"
lifecycle_step 5  "raps config set client_id \$CLIENT_B_ID"
lifecycle_step 6  "raps config set client_secret \$CLIENT_B_SECRET"
lifecycle_step 7  "raps config profile use client-a"
lifecycle_step 8  "raps auth test"
lifecycle_step 9  "raps bucket list"
lifecycle_step 10 "raps config profile use client-b"
lifecycle_step 11 "raps auth test"
lifecycle_step 12 "raps bucket list"
lifecycle_step 13 "raps config profile delete client-a"
lifecycle_step 14 "raps config profile delete client-b"
lifecycle_end

# SR-409: Create, validate, run pipeline
lifecycle_start "SR-409" "workflow-pipeline-yaml-automation" "Create, validate, run pipeline"
lifecycle_step 1 "raps pipeline sample --output ./my-pipeline.yaml"
lifecycle_step 2 "raps pipeline validate --file ./my-pipeline.yaml"
lifecycle_step 3 "raps generate files --count 3 --output ./pipeline-input/ --complexity medium"
lifecycle_step 4 "raps pipeline run --file ./my-pipeline.yaml"
lifecycle_step 5 "raps admin operation list --limit 1"
lifecycle_end

section_end
