"""Cross-Domain Workflows"""

import pytest

pytestmark = [
    pytest.mark.require_2leg,
    pytest.mark.xdist_group("30-workflows"),
]

# --- Demo environment variable defaults ---
URN = "dXJuOmFkc2sub2JqZWN0czpvcy5vYmplY3Q6ZGVtby1idWNrZXQvc2FtcGxlLmlmYw"
URN1 = "dXJuOmFkc2sub2JqZWN0czpvcy5vYmplY3Q6ZGVtby1idWNrZXQvbW9kZWwxLnJ2dA"
URN2 = "dXJuOmFkc2sub2JqZWN0czpvcy5vYmplY3Q6ZGVtby1idWNrZXQvbW9kZWwyLnJ2dA"
I1 = "demo-issue-001"
NEW_PID = "b.demo-project-002"
INPUT_URL = "https://developer.api.autodesk.com/oss/v2/signedresources/demo-input"
OUTPUT_URL = "https://developer.api.autodesk.com/oss/v2/signedresources/demo-output"
WI_ID = "demo-workitem-001"
JID = "demo-reality-job-001"
FOLDER_ID = "urn:adsk.wipprod:fs.folder:co.demo-folder-001"
OP_ID = "12345678-1234-1234-1234-123456789012"
WH1 = "demo-webhook-001"
WH2 = "demo-webhook-002"
CLIENT_A_ID = "demo-client-a-id"
CLIENT_A_SECRET = "demo-client-a-secret"
CLIENT_B_ID = "demo-client-b-id"
CLIENT_B_SECRET = "demo-client-b-secret"


@pytest.mark.sr("SR-400")
@pytest.mark.lifecycle
def test_sr400_workflow_model_review_cycle(raps, ids):
    pid = ids.project_id or "b.demo-project-001"
    lc = raps.lifecycle("SR-400", "workflow-model-review-cycle",
                        "Architect uploads, translates, creates issues")
    lc.step("raps bucket create -k review-cycle -p transient", may_fail=True)
    lc.step("raps object upload review-cycle ./test-data/sample.rvt", may_fail=True)
    lc.step(f"raps translate start {URN} -f svf2", may_fail=True)
    lc.step(f"raps translate status {URN}", may_fail=True)
    lc.step(f"raps translate manifest {URN}", may_fail=True)
    lc.step(f'raps issue create {pid} -t "Clash at grid A-3"', may_fail=True)
    lc.step(f'raps issue create {pid} -t "Missing fire rating on wall W-12"', may_fail=True)
    lc.step(f'raps issue comment add {pid} {I1} -b "See model view at Level 2"', may_fail=True)
    lc.step(f'raps rfi create {pid} --title "Confirm structural capacity at A-3"', may_fail=True)
    lc.step("raps bucket delete review-cycle --yes", may_fail=True)
    lc.assert_all_passed()


@pytest.mark.sr("SR-401")
@pytest.mark.lifecycle
def test_sr401_workflow_project_setup(raps, ids, users):
    acct = ids.account_id or "demo-account-001"
    lc = raps.lifecycle("SR-401", "workflow-project-setup",
                        "Admin creates project and staffs it")
    lc.step(f"raps template list -a {acct}", may_fail=True)
    lc.step(f'raps admin project create -a {acct} -n "Hospital Wing B" -t "Healthcare"', may_fail=True)
    lc.step(f'raps admin user add {users.user_pm} -a {acct} -r "project_admin" -f "name:*Hospital Wing B*" -y', may_fail=True)
    lc.step(f'raps admin user add {users.user_struct} -a {acct} -r "viewer" -f "name:*Hospital Wing B*" -y', may_fail=True)
    lc.step(f'raps admin user add {users.user_mep} -a {acct} -r "viewer" -f "name:*Hospital Wing B*" -y', may_fail=True)
    lc.step(f'raps admin folder rights {users.user_struct} -a {acct} -l view-download-upload --folder "Structural" -f "name:*Hospital Wing B*" -y', may_fail=True)
    lc.step(f'raps admin folder rights {users.user_mep} -a {acct} -l view-download-upload --folder "MEP" -f "name:*Hospital Wing B*" -y', may_fail=True)
    lc.step(f"raps admin user list -a {acct} -p {NEW_PID}", may_fail=True)
    lc.step(f'raps webhook create -e "dm.version.added" -u "https://hooks.co.com/hospital"', may_fail=True)
    lc.assert_all_passed()


@pytest.mark.sr("SR-402")
@pytest.mark.lifecycle
def test_sr402_workflow_ci_cd_pipeline(raps):
    lc = raps.lifecycle("SR-402", "workflow-ci-cd-pipeline",
                        "CI/CD upload, translate, verify")
    lc.step("raps auth test", may_fail=True)
    lc.step("raps bucket create -k ci-build-123 -p transient", may_fail=True)
    lc.step("raps object upload ci-build-123 ./test-data/sample.rvt", may_fail=True)
    lc.step("raps object list ci-build-123 --output json", may_fail=True)
    lc.step(f"raps translate start {URN1} -f svf2", may_fail=True)
    lc.step(f"raps translate start {URN2} -f svf2", may_fail=True)
    lc.step(f"raps translate status {URN1}", may_fail=True)
    lc.step(f"raps translate status {URN2}", may_fail=True)
    lc.step(f"raps translate manifest {URN1}", may_fail=True)
    lc.step("raps bucket delete ci-build-123 --yes", may_fail=True)
    lc.assert_all_passed()


@pytest.mark.sr("SR-403")
@pytest.mark.lifecycle
def test_sr403_workflow_design_automation_job(raps):
    lc = raps.lifecycle("SR-403", "workflow-design-automation-job",
                        "DevOps runs Revit extraction via DA")
    lc.step("raps bucket create -k da-job -p transient", may_fail=True)
    lc.step("raps object upload da-job ./test-data/sample.rvt", may_fail=True)
    lc.step("raps object signed-url da-job sample.rvt", may_fail=True)
    lc.step("raps da engines", may_fail=True)
    lc.step('raps da appbundle-create -i "Extract" -e "Autodesk.Revit+2025"', may_fail=True)
    lc.step('raps da activity-create --id "ExtractAct" --engine "Autodesk.Revit+2025" --appbundle "Extract" --command "..."', may_fail=True)
    lc.step(f'raps da run "ExtractAct" -i "input={INPUT_URL}" --out-arg "output={OUTPUT_URL}"', may_fail=True)
    lc.step(f"raps da status {WI_ID}", may_fail=True)
    lc.step("raps object download da-job output.json -o ./results/", may_fail=True)
    lc.step('raps da activity-delete "ExtractAct"', may_fail=True)
    lc.step('raps da appbundle-delete "Extract"', may_fail=True)
    lc.step("raps bucket delete da-job --yes", may_fail=True)
    lc.assert_all_passed()


@pytest.mark.sr("SR-404")
@pytest.mark.lifecycle
def test_sr404_workflow_portfolio_health_check(raps, ids):
    acct = ids.account_id or "demo-account-001"
    lc = raps.lifecycle("SR-404", "workflow-portfolio-health-check",
                        "Executive reviews portfolio health")
    lc.step(f"raps admin project list -a {acct} --status active", may_fail=True)
    lc.step(f"raps report issues-summary -a {acct} --status open --output json", may_fail=True)
    lc.step(f'raps report rfi-summary -a {acct} --status open --since "2026-01-01" --output json', may_fail=True)
    lc.step(f"raps report submittals-summary -a {acct} --output json", may_fail=True)
    lc.step(f'raps report checklists-summary -a {acct} --status "in_progress" --output json', may_fail=True)
    lc.step(f"raps report assets-summary -a {acct} --output json", may_fail=True)
    lc.assert_all_passed()


@pytest.mark.sr("SR-405")
@pytest.mark.lifecycle
def test_sr405_workflow_site_survey_to_model(raps, ids):
    pid = ids.project_full_id or "b.demo-project-001"
    lc = raps.lifecycle("SR-405", "workflow-site-survey-to-model",
                        "Survey captures, processes, uploads to BIM 360")
    lc.step('raps reality create -n "Foundation Survey" -f obj', may_fail=True)
    lc.step(f"raps reality upload {JID} ./test-data/sample.rvt", may_fail=True)
    lc.step(f"raps reality process {JID}", may_fail=True)
    lc.step(f"raps reality status {JID}", may_fail=True)
    lc.step(f"raps reality result {JID}", may_fail=True)
    lc.step("raps bucket create -k survey-upload -p transient", may_fail=True)
    lc.step("raps object upload survey-upload ./test-data/sample.rvt", may_fail=True)
    lc.step(f'raps item create-from-oss {pid} {FOLDER_ID} --name "Foundation Survey 2026-02" --object-id {URN}', may_fail=True)
    lc.step(f"raps reality delete {JID} --yes", may_fail=True)
    lc.step("raps bucket delete survey-upload --yes", may_fail=True)
    lc.assert_all_passed()


@pytest.mark.sr("SR-406")
@pytest.mark.lifecycle
def test_sr406_workflow_weekly_admin_operations(raps, ids, users):
    acct = ids.account_id or "demo-account-001"
    lc = raps.lifecycle("SR-406", "workflow-weekly-admin-operations",
                        "Admin weekly maintenance")
    lc.step(f'raps admin user list -a {acct} --status "active" --output json', may_fail=True)
    lc.step(f'raps admin user list -a {acct} --role "project_admin"', may_fail=True)
    lc.step(f'raps admin project list -a {acct} -f "name:*2024*" --status active', may_fail=True)
    lc.step(f'raps admin user update {users.user_old_admin} -a {acct} -r "viewer" --from-role "project_admin" -f "name:*2024*" --dry-run', may_fail=True)
    lc.step(f'raps admin user update {users.user_old_admin} -a {acct} -r "viewer" --from-role "project_admin" -f "name:*2024*" -y', may_fail=True)
    lc.step(f"raps admin operation status {OP_ID}", may_fail=True)
    lc.step(f"raps admin company-list -a {acct}", may_fail=True)
    lc.step(f"raps report issues-summary -a {acct} --status open", may_fail=True)
    lc.assert_all_passed()


@pytest.mark.sr("SR-407")
@pytest.mark.lifecycle
def test_sr407_workflow_webhook_driven_automation(raps):
    lc = raps.lifecycle("SR-407", "workflow-webhook-driven-automation",
                        "DevOps sets up webhooks")
    lc.step("raps webhook events", may_fail=True)
    lc.step('raps webhook create -e "dm.version.added" -u "https://ci.co.com/trigger"', may_fail=True)
    lc.step('raps webhook create -e "dm.version.added" -u "https://ci.co.com/trigger"', may_fail=True)
    lc.step("raps webhook list", may_fail=True)
    lc.step('raps webhook test "https://ci.co.com/trigger"', may_fail=True)
    lc.step("raps object upload staging ./test-data/sample.rvt", may_fail=True)
    lc.step(f'raps webhook get -e "dm.version.added" --hook-id {WH1}', may_fail=True)
    lc.step(f'raps webhook update -e "dm.version.added" --hook-id {WH2} --status "inactive"', may_fail=True)
    lc.step(f'raps webhook delete {WH1} -e "dm.version.added" --yes', may_fail=True)
    lc.step(f'raps webhook delete {WH2} -e "dm.version.added" --yes', may_fail=True)
    lc.assert_all_passed()


@pytest.mark.sr("SR-408")
@pytest.mark.lifecycle
def test_sr408_workflow_multi_profile_operations(raps):
    lc = raps.lifecycle("SR-408", "workflow-multi-profile-operations",
                        "Consultant switches profiles")
    lc.step("raps config profile create wf-client-a")
    lc.step("raps config profile use wf-client-a")
    lc.step(f"raps config set client_id {CLIENT_A_ID}")
    lc.step(f"raps config set client_secret {CLIENT_A_SECRET}")
    lc.step("raps config profile create wf-client-b")
    lc.step("raps config profile use wf-client-b")
    lc.step(f"raps config set client_id {CLIENT_B_ID}")
    lc.step(f"raps config set client_secret {CLIENT_B_SECRET}")
    lc.step("raps config profile use wf-client-a")
    lc.step("raps auth test", may_fail=True)
    lc.step("raps bucket list", may_fail=True)
    lc.step("raps config profile use wf-client-b")
    lc.step("raps auth test", may_fail=True)
    lc.step("raps bucket list", may_fail=True)
    lc.step("raps config profile delete wf-client-a")
    lc.step("raps config profile delete wf-client-b")
    lc.assert_all_passed()


@pytest.mark.sr("SR-409")
@pytest.mark.lifecycle
def test_sr409_workflow_pipeline_yaml_automation(raps):
    lc = raps.lifecycle("SR-409", "workflow-pipeline-yaml-automation",
                        "Create, validate, run pipeline")
    lc.step("raps pipeline sample -o ./wf-pipeline.yaml", may_fail=True)
    lc.step("raps pipeline validate ./wf-pipeline.yaml", may_fail=True)
    lc.step("raps generate files -c 3 -o ./pipeline-input/ --complexity medium", may_fail=True)
    lc.step("raps pipeline run ./wf-pipeline.yaml", may_fail=True)
    lc.step("raps admin operation list --limit 1", may_fail=True)
    lc.assert_all_passed()
