"""Cross-Domain Workflows"""

import base64
import time

import pytest

pytestmark = [
    pytest.mark.require_2leg,
    pytest.mark.xdist_group("30-workflows"),
]

_TS = str(int(time.time()))

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
@pytest.mark.require_3leg
@pytest.mark.require_acc
def test_sr400_workflow_model_review_cycle(raps, ids):
    pid = ids.project_id or "b.demo-project-001"
    lc = raps.lifecycle("SR-400", "workflow-model-review-cycle",
                        "Architect uploads, translates, creates issues")
    bkt = f"review-cycle-{_TS}"
    lc.step(f"raps bucket create -k {bkt} -p transient -r US")
    lc.step(f"raps object upload {bkt} ./test-data/sample.rvt")
    lc.step(f"raps translate start {URN} -f svf2")
    lc.step(f"raps translate status {URN}")
    lc.step(f"raps translate manifest {URN}")
    lc.step(f'raps issue create {pid} -t "Clash at grid A-3"')
    lc.step(f'raps issue create {pid} -t "Missing fire rating on wall W-12"')
    lc.step(f'raps issue comment add {pid} {I1} -b "See model view at Level 2"')
    lc.step(f'raps rfi create {pid} --title "Confirm structural capacity at A-3"')
    lc.step(f"raps bucket delete {bkt} --yes")
    lc.assert_all_passed()


@pytest.mark.sr("SR-401")
@pytest.mark.lifecycle
@pytest.mark.require_3leg
@pytest.mark.require_acc
def test_sr401_workflow_project_setup(raps, ids, users):
    acct = ids.account_id or "demo-account-001"
    lc = raps.lifecycle("SR-401", "workflow-project-setup",
                        "Admin creates project and staffs it")
    lc.step(f"raps template list -a {acct}")
    lc.step(f'raps admin project create -a {acct} -n "Hospital Wing B" -t "Healthcare"')
    lc.step(f'raps admin user add {users.user_pm} -a {acct} -r "project_admin" -f "name:*Hospital Wing B*" -y')
    lc.step(f'raps admin user add {users.user_struct} -a {acct} -r "viewer" -f "name:*Hospital Wing B*" -y')
    lc.step(f'raps admin user add {users.user_mep} -a {acct} -r "viewer" -f "name:*Hospital Wing B*" -y')
    lc.step(f'raps admin folder rights {users.user_struct} -a {acct} -l view-download-upload --folder "Structural" -f "name:*Hospital Wing B*" -y')
    lc.step(f'raps admin folder rights {users.user_mep} -a {acct} -l view-download-upload --folder "MEP" -f "name:*Hospital Wing B*" -y')
    lc.step(f"raps admin user list -a {acct} -p {NEW_PID}")
    lc.step(f'raps webhook create -e "dm.version.added" -u "https://hooks.co.com/hospital"')
    lc.assert_all_passed()


@pytest.mark.sr("SR-402")
@pytest.mark.lifecycle
def test_sr402_workflow_ci_cd_pipeline(raps):
    lc = raps.lifecycle("SR-402", "workflow-ci-cd-pipeline",
                        "CI/CD upload, translate, verify")
    lc.step("raps auth test")
    bkt = f"ci-build-{_TS}"
    rvt_urn = base64.urlsafe_b64encode(
        f"urn:adsk.objects:os.object:{bkt}/sample.rvt".encode()
    ).decode().rstrip("=")
    lc.step(f"raps bucket create -k {bkt} -p transient -r US")
    upload_result = lc.step(f"raps object upload {bkt} ./test-data/sample.rvt")
    lc.step(f"raps object list {bkt} --output json")
    if upload_result.ok:
        tr_result = lc.step(f"raps translate start {rvt_urn} -f svf2")
        if not tr_result.ok and "capacity exceeded" in tr_result.stderr:
            lc.step(f"raps bucket delete {bkt} --yes")
            pytest.skip("Translation API rate-limited (free tier capacity exceeded)")
        if tr_result.ok:
            lc.step(f"raps translate status {rvt_urn}")
            lc.step(f"raps translate manifest {rvt_urn}")
    lc.step(f"raps bucket delete {bkt} --yes")
    lc.assert_all_passed()


@pytest.mark.sr("SR-403")
@pytest.mark.lifecycle
def test_sr403_workflow_design_automation_job(raps):
    lc = raps.lifecycle("SR-403", "workflow-design-automation-job",
                        "DevOps sets up DA resources and cleans up")
    bkt = f"da-job-{_TS}"
    bundle_id = f"Extract{_TS}"
    activity_id = f"ExtractAct{_TS}"
    lc.step(f"raps bucket create -k {bkt} -p transient -r US")
    lc.step(f"raps object upload {bkt} ./test-data/sample.rvt")
    lc.step(f"raps object signed-url {bkt} sample.rvt")
    lc.step("raps da engines")
    lc.step(f'raps da appbundle-create -i {bundle_id} -e "Autodesk.Revit+2025"')
    lc.step(f'raps da activity-create --id {activity_id} --engine "Autodesk.Revit+2025" --appbundle "{bundle_id}" --command "..."')
    # Note: da run requires a real uploaded plugin binary — skip in test env
    # Note: da status requires a real workitem ID from a previous run
    lc.step(f"raps da activity-delete {activity_id}")
    lc.step(f"raps da appbundle-delete {bundle_id}")
    lc.step(f"raps bucket delete {bkt} --yes")
    lc.assert_all_passed()


@pytest.mark.sr("SR-404")
@pytest.mark.lifecycle
@pytest.mark.require_3leg
@pytest.mark.require_acc
def test_sr404_workflow_portfolio_health_check(raps, ids):
    acct = ids.account_id or "demo-account-001"
    lc = raps.lifecycle("SR-404", "workflow-portfolio-health-check",
                        "Executive reviews portfolio health")
    lc.step(f"raps admin project list -a {acct} --status active")
    lc.step(f"raps report issues-summary -a {acct} --status open --output json")
    lc.step(f'raps report rfi-summary -a {acct} --status open --since "2026-01-01" --output json')
    lc.step(f"raps report submittals-summary -a {acct} --output json")
    lc.step(f'raps report checklists-summary -a {acct} --status "in_progress" --output json')
    lc.step(f"raps report assets-summary -a {acct} --output json")
    lc.assert_all_passed()


@pytest.mark.sr("SR-405")
@pytest.mark.lifecycle
@pytest.mark.require_3leg
def test_sr405_workflow_site_survey_to_model(raps, ids):
    pid = ids.project_full_id or "b.demo-project-001"
    lc = raps.lifecycle("SR-405", "workflow-site-survey-to-model",
                        "Survey captures, processes, uploads to BIM 360")
    lc.step('raps reality create -n "Foundation Survey" -f obj')
    lc.step(f"raps reality upload {JID} ./test-data/sample.rvt")
    lc.step(f"raps reality process {JID}")
    lc.step(f"raps reality status {JID}")
    lc.step(f"raps reality result {JID}")
    bkt = f"survey-upload-{_TS}"
    lc.step(f"raps bucket create -k {bkt} -p transient -r US")
    lc.step(f"raps object upload {bkt} ./test-data/sample.rvt")
    lc.step(f'raps item create-from-oss {pid} {FOLDER_ID} --name "Foundation Survey 2026-02" --object-id {URN}')
    lc.step(f"raps reality delete {JID} --yes")
    lc.step(f"raps bucket delete {bkt} --yes")
    lc.assert_all_passed()


@pytest.mark.sr("SR-406")
@pytest.mark.lifecycle
@pytest.mark.require_3leg
@pytest.mark.require_acc
def test_sr406_workflow_weekly_admin_operations(raps, ids, users):
    acct = ids.account_id or "demo-account-001"
    lc = raps.lifecycle("SR-406", "workflow-weekly-admin-operations",
                        "Admin weekly maintenance")
    lc.step(f'raps admin user list -a {acct} --status "active" --output json')
    lc.step(f'raps admin user list -a {acct} --role "project_admin"')
    lc.step(f'raps admin project list -a {acct} -f "name:*2024*" --status active')
    lc.step(f'raps admin user update {users.user_old_admin} -a {acct} -r "viewer" --from-role "project_admin" -f "name:*2024*" --dry-run')
    lc.step(f'raps admin user update {users.user_old_admin} -a {acct} -r "viewer" --from-role "project_admin" -f "name:*2024*" -y')
    lc.step(f"raps admin operation status {OP_ID}")
    lc.step(f"raps admin company-list -a {acct}")
    lc.step(f"raps report issues-summary -a {acct} --status open")
    lc.assert_all_passed()


@pytest.mark.sr("SR-407")
@pytest.mark.lifecycle
def test_sr407_workflow_webhook_driven_automation(raps):
    lc = raps.lifecycle("SR-407", "workflow-webhook-driven-automation",
                        "DevOps lists webhook events and existing hooks")
    lc.step("raps webhook events")
    lc.step("raps webhook list")
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
    lc.step("raps auth test")
    lc.step("raps bucket list")
    lc.step("raps config profile use wf-client-b")
    lc.step("raps auth test")
    lc.step("raps bucket list")
    lc.step("raps config profile delete wf-client-a")
    lc.step("raps config profile delete wf-client-b")
    lc.assert_all_passed()


@pytest.mark.sr("SR-409")
@pytest.mark.lifecycle
def test_sr409_workflow_pipeline_yaml_automation(raps):
    lc = raps.lifecycle("SR-409", "workflow-pipeline-yaml-automation",
                        "Create, validate, run pipeline")
    lc.step("raps pipeline sample --out-file ./wf-pipeline.yaml")
    lc.step("raps pipeline validate ./wf-pipeline.yaml")
    lc.step("raps generate files -c 3 --out-dir ./pipeline-input/ --complexity medium")
    lc.step("raps pipeline run ./wf-pipeline.yaml")
    lc.step("raps admin operation list --limit 1")
    lc.assert_all_passed()
