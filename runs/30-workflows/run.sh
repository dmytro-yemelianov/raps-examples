#!/bin/bash
# Section 30 — Cross-Domain Workflows
# Runs: SR-400 through SR-409
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "30-workflows" "Cross-Domain Workflows"

# --- Pre-seed demo environment variables (override with real values) ---
: "${URN:=dXJuOmFkc2sub2JqZWN0czpvcy5vYmplY3Q6ZGVtby1idWNrZXQvc2FtcGxlLmlmYw}"
: "${URN1:=dXJuOmFkc2sub2JqZWN0czpvcy5vYmplY3Q6ZGVtby1idWNrZXQvbW9kZWwxLnJ2dA}"
: "${URN2:=dXJuOmFkc2sub2JqZWN0czpvcy5vYmplY3Q6ZGVtby1idWNrZXQvbW9kZWwyLnJ2dA}"
: "${PID:=${RAPS_PROJECT_ID:-b.demo-project-001}}"
: "${I1:=demo-issue-001}"
: "${ACCT:=${RAPS_ACCOUNT_ID:-demo-account-001}}"
: "${NEW_PID:=b.demo-project-002}"
: "${INPUT_URL:=https://developer.api.autodesk.com/oss/v2/signedresources/demo-input}"
: "${OUTPUT_URL:=https://developer.api.autodesk.com/oss/v2/signedresources/demo-output}"
: "${WI_ID:=demo-workitem-001}"
: "${JID:=demo-reality-job-001}"
: "${PROJECT_ID:=${RAPS_PROJECT_ID:-b.demo-project-001}}"
: "${FOLDER_ID:=urn:adsk.wipprod:fs.folder:co.demo-folder-001}"
: "${OP_ID:=12345678-1234-1234-1234-123456789012}"
: "${WH1:=demo-webhook-001}"
: "${WH2:=demo-webhook-002}"
: "${CLIENT_A_ID:=demo-client-a-id}"
: "${CLIENT_A_SECRET:=demo-client-a-secret}"
: "${CLIENT_B_ID:=demo-client-b-id}"
: "${CLIENT_B_SECRET:=demo-client-b-secret}"

# NOTE: Lifecycle steps use || true because they exercise API *flows* with
# demo/placeholder IDs. Steps may return errors (404, 403) which is expected.

# ── Lifecycles ───────────────────────────────────────────────────

# SR-400: Architect uploads, translates, creates issues
lifecycle_start "SR-400" "workflow-model-review-cycle" "Architect uploads, translates, creates issues"
lifecycle_step 1  "raps bucket create -k review-cycle -p transient || true"
lifecycle_step 2  "raps object upload review-cycle ./test-data/sample.rvt || true"
lifecycle_step 3  "raps translate start \$URN -f svf2 || true"
lifecycle_step 4  "raps translate status \$URN || true"
lifecycle_step 5  "raps translate manifest \$URN || true"
lifecycle_step 6  "raps issue create \$PID -t \"Clash at grid A-3\" || true"
lifecycle_step 7  "raps issue create \$PID -t \"Missing fire rating on wall W-12\" || true"
lifecycle_step 8  "raps issue comment add \$PID \$I1 -b \"See model view at Level 2\" || true"
lifecycle_step 9  "raps rfi create \$PID --title \"Confirm structural capacity at A-3\" || true"
lifecycle_step 10 "raps bucket delete review-cycle --yes || true"
lifecycle_end

# SR-401: Admin creates project and staffs it
lifecycle_start "SR-401" "workflow-project-setup" "Admin creates project and staffs it"
lifecycle_step 1 "raps template list -a \$ACCT || true"
lifecycle_step 2 "raps admin project create -a \$ACCT -n \"Hospital Wing B\" -t \"Healthcare\" || true"
lifecycle_step 3 "raps admin user add pm@co.com -a \$ACCT -r \"project_admin\" -f \"name:*Hospital Wing B*\" -y || true"
lifecycle_step 4 "raps admin user add struct@co.com -a \$ACCT -r \"viewer\" -f \"name:*Hospital Wing B*\" -y || true"
lifecycle_step 5 "raps admin user add mep@co.com -a \$ACCT -r \"viewer\" -f \"name:*Hospital Wing B*\" -y || true"
lifecycle_step 6 "raps admin folder rights struct@co.com -a \$ACCT -l view-download-upload --folder \"Structural\" -f \"name:*Hospital Wing B*\" -y || true"
lifecycle_step 7 "raps admin folder rights mep@co.com -a \$ACCT -l view-download-upload --folder \"MEP\" -f \"name:*Hospital Wing B*\" -y || true"
lifecycle_step 8 "raps admin user list -p \$NEW_PID || true"
lifecycle_step 9 "raps webhook create -e \"dm.version.added\" -u \"https://hooks.co.com/hospital\" || true"
lifecycle_end

# SR-402: CI/CD upload, translate, verify
lifecycle_start "SR-402" "workflow-ci-cd-pipeline" "CI/CD upload, translate, verify"
lifecycle_step 1  "raps auth test"
lifecycle_step 2  "raps bucket create -k ci-build-123 -p transient || true"
lifecycle_step 3  "raps object upload ci-build-123 ./test-data/sample.rvt || true"
lifecycle_step 4  "raps object list ci-build-123 --output json || true"
lifecycle_step 5  "raps translate start \$URN1 -f svf2 || true"
lifecycle_step 6  "raps translate start \$URN2 -f svf2 || true"
lifecycle_step 7  "raps translate status \$URN1 || true"
lifecycle_step 8  "raps translate status \$URN2 || true"
lifecycle_step 9  "raps translate manifest \$URN1 || true"
lifecycle_step 10 "raps bucket delete ci-build-123 --yes || true"
lifecycle_end

# SR-403: DevOps runs Revit extraction via DA
lifecycle_start "SR-403" "workflow-design-automation-job" "DevOps runs Revit extraction via DA"
lifecycle_step 1  "raps bucket create -k da-job -p transient || true"
lifecycle_step 2  "raps object upload da-job ./test-data/sample.rvt || true"
lifecycle_step 3  "raps object signed-url da-job sample.rvt || true"
lifecycle_step 4  "raps da engines"
lifecycle_step 5  "raps da appbundle-create -i \"Extract\" -e \"Autodesk.Revit+2025\" || true"
lifecycle_step 6  "raps da activity-create --id \"ExtractAct\" --engine \"Autodesk.Revit+2025\" --appbundle \"Extract\" --command \"...\" || true"
lifecycle_step 7  "raps da run \"ExtractAct\" -i \$INPUT_URL -o \$OUTPUT_URL || true"
lifecycle_step 8  "raps da status \$WI_ID || true"
lifecycle_step 9  "raps object download da-job output.json -o ./results/ || true"
lifecycle_step 10 "raps da activity-delete \"ExtractAct\" || true"
lifecycle_step 11 "raps da appbundle-delete \"Extract\" || true"
lifecycle_step 12 "raps bucket delete da-job --yes || true"
lifecycle_end

# SR-404: Executive reviews portfolio health
lifecycle_start "SR-404" "workflow-portfolio-health-check" "Executive reviews portfolio health"
lifecycle_step 1 "raps admin project list -a \$ACCT --status active || true"
lifecycle_step 2 "raps report issues-summary -a \$ACCT --status open --output json || true"
lifecycle_step 3 "raps report rfi-summary -a \$ACCT --status open --since \"2026-01-01\" --output json || true"
lifecycle_step 4 "raps report submittals-summary -a \$ACCT --output json || true"
lifecycle_step 5 "raps report checklists-summary -a \$ACCT --status \"in_progress\" --output json || true"
lifecycle_step 6 "raps report assets-summary -a \$ACCT --output json || true"
lifecycle_end

# SR-405: Survey captures, processes, uploads to BIM 360
lifecycle_start "SR-405" "workflow-site-survey-to-model" "Survey captures, processes, uploads to BIM 360"
lifecycle_step 1  "raps reality create -n \"Foundation Survey\" -f obj || true"
lifecycle_step 2  "raps reality upload \$JID ./test-data/sample.rvt || true"
lifecycle_step 3  "raps reality process \$JID || true"
lifecycle_step 4  "raps reality status \$JID || true"
lifecycle_step 5  "raps reality result \$JID || true"
lifecycle_step 6  "raps bucket create -k survey-upload -p transient || true"
lifecycle_step 7  "raps object upload survey-upload ./test-data/sample.rvt || true"
lifecycle_step 8  "raps item create-from-oss \$PROJECT_ID \$FOLDER_ID --name \"Foundation Survey 2026-02\" --object-id \$URN || true"
lifecycle_step 9  "raps reality delete \$JID --yes || true"
lifecycle_step 10 "raps bucket delete survey-upload --yes || true"
lifecycle_end

# SR-406: Admin weekly maintenance
lifecycle_start "SR-406" "workflow-weekly-admin-operations" "Admin weekly maintenance"
lifecycle_step 1 "raps admin user list -a \$ACCT --status \"active\" --output json || true"
lifecycle_step 2 "raps admin user list -a \$ACCT --role \"project_admin\" || true"
lifecycle_step 3 "raps admin project list -a \$ACCT -f \"name:*2024*\" --status active || true"
lifecycle_step 4 "raps admin user update admin@old.com -a \$ACCT -r \"viewer\" --from-role \"project_admin\" -f \"name:*2024*\" --dry-run || true"
lifecycle_step 5 "raps admin user update admin@old.com -a \$ACCT -r \"viewer\" --from-role \"project_admin\" -f \"name:*2024*\" -y || true"
lifecycle_step 6 "raps admin operation status \$OP_ID || true"
lifecycle_step 7 "raps admin company-list -a \$ACCT || true"
lifecycle_step 8 "raps report issues-summary -a \$ACCT --status open || true"
lifecycle_end

# SR-407: DevOps sets up webhooks
lifecycle_start "SR-407" "workflow-webhook-driven-automation" "DevOps sets up webhooks"
lifecycle_step 1  "raps webhook events || true"
lifecycle_step 2  "raps webhook create -e \"dm.version.added\" -u \"https://ci.co.com/trigger\" || true"
lifecycle_step 3  "raps webhook create -e \"dm.version.added\" -u \"https://ci.co.com/trigger\" || true"
lifecycle_step 4  "raps webhook list || true"
lifecycle_step 5  "raps webhook test \"https://ci.co.com/trigger\" || true"
lifecycle_step 6  "raps object upload staging ./test-data/sample.rvt || true"
lifecycle_step 7  "raps webhook get -e \"dm.version.added\" --hook-id \$WH1 || true"
lifecycle_step 8  "raps webhook update -e \"dm.version.added\" --hook-id \$WH2 --status \"inactive\" || true"
lifecycle_step 9  "raps webhook delete \$WH1 -e \"dm.version.added\" --yes || true"
lifecycle_step 10 "raps webhook delete \$WH2 -e \"dm.version.added\" --yes || true"
lifecycle_end

# SR-408: Consultant switches profiles
lifecycle_start "SR-408" "workflow-multi-profile-operations" "Consultant switches profiles"
lifecycle_step 1  "raps config profile create client-a || true"
lifecycle_step 2  "raps config set client_id \$CLIENT_A_ID || true"
lifecycle_step 3  "raps config set client_secret \$CLIENT_A_SECRET || true"
lifecycle_step 4  "raps config profile create client-b || true"
lifecycle_step 5  "raps config set client_id \$CLIENT_B_ID || true"
lifecycle_step 6  "raps config set client_secret \$CLIENT_B_SECRET || true"
lifecycle_step 7  "raps config profile use client-a || true"
lifecycle_step 8  "raps auth test || true"
lifecycle_step 9  "raps bucket list || true"
lifecycle_step 10 "raps config profile use client-b || true"
lifecycle_step 11 "raps auth test || true"
lifecycle_step 12 "raps bucket list || true"
lifecycle_step 13 "raps config profile delete client-a || true"
lifecycle_step 14 "raps config profile delete client-b || true"
lifecycle_end

# SR-409: Create, validate, run pipeline
lifecycle_start "SR-409" "workflow-pipeline-yaml-automation" "Create, validate, run pipeline"
lifecycle_step 1 "raps pipeline sample -o ./my-pipeline.yaml"
lifecycle_step 2 "raps pipeline validate ./my-pipeline.yaml"
lifecycle_step 3 "raps generate files -c 3 -o ./pipeline-input/ --complexity medium"
lifecycle_step 4 "raps pipeline run ./my-pipeline.yaml || true"
lifecycle_step 5 "raps admin operation list --limit 1 || true"
lifecycle_end

section_end
