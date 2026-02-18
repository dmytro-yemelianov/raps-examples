"""ACC Modules: Assets, Submittals, Checklists"""

import pytest

pytestmark = [
    pytest.mark.require_3leg,
    pytest.mark.xdist_group("09-acc-modules"),
]

CATEGORY_ID = "cat-demo-001"
ASSET_ID = "ast-demo-001"
STATUS_ID = "st-demo-001"
SUBMITTAL_ID = "sub-demo-001"
CHECKLIST_ID = "chk-demo-001"
TEMPLATE_ID = "tpl-demo-001"
MECH_CAT = "cat-mechanical-001"
CH01 = "ast-chiller-01"
CH02 = "ast-chiller-02"
DELIVERED_STATUS = "st-delivered-001"
INSTALLED_STATUS = "st-installed-001"
TPL = "tpl-demo-001"
FOLDER_ID = "urn:adsk.wipprod:fs.folder:co.demo-folder-001"


# -- Asset atomics ----------------------------------------------------------


@pytest.mark.sr("SR-160")
def test_sr160_acc_asset_list(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps acc asset list {project_id}",
        sr_id="SR-160",
        slug="acc-asset-list",
        may_fail=True,
    )


@pytest.mark.sr("SR-161")
def test_sr161_acc_asset_create(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f'raps acc asset create {project_id} --category-id {CATEGORY_ID} --description "HVAC Unit AHU-01"',
        sr_id="SR-161",
        slug="acc-asset-create",
        may_fail=True,
    )


@pytest.mark.sr("SR-162")
def test_sr162_acc_asset_get(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps acc asset get {project_id} {ASSET_ID}",
        sr_id="SR-162",
        slug="acc-asset-get",
        may_fail=True,
    )


@pytest.mark.sr("SR-163")
def test_sr163_acc_asset_update(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps acc asset update {project_id} {ASSET_ID} --status-id {STATUS_ID}",
        sr_id="SR-163",
        slug="acc-asset-update",
        may_fail=True,
    )


@pytest.mark.sr("SR-164")
def test_sr164_acc_asset_delete(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps acc asset delete {project_id} {ASSET_ID} --yes",
        sr_id="SR-164",
        slug="acc-asset-delete",
        may_fail=True,
    )


# -- Submittal atomics -----------------------------------------------------


@pytest.mark.sr("SR-165")
def test_sr165_acc_submittal_list(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps acc submittal list {project_id}",
        sr_id="SR-165",
        slug="acc-submittal-list",
        may_fail=True,
    )


@pytest.mark.sr("SR-166")
def test_sr166_acc_submittal_create(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f'raps acc submittal create {project_id} --title "Concrete mix design for Level 5"'
        f' --spec-section "03 30 00"',
        sr_id="SR-166",
        slug="acc-submittal-create",
        may_fail=True,
    )


@pytest.mark.sr("SR-167")
def test_sr167_acc_submittal_get(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps acc submittal get {project_id} {SUBMITTAL_ID}",
        sr_id="SR-167",
        slug="acc-submittal-get",
        may_fail=True,
    )


@pytest.mark.sr("SR-168")
def test_sr168_acc_submittal_update(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f'raps acc submittal update {project_id} {SUBMITTAL_ID} --status "approved"',
        sr_id="SR-168",
        slug="acc-submittal-update",
        may_fail=True,
    )


@pytest.mark.sr("SR-169")
def test_sr169_acc_submittal_delete(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps acc submittal delete {project_id} {SUBMITTAL_ID} --yes",
        sr_id="SR-169",
        slug="acc-submittal-delete",
        may_fail=True,
    )


# -- Checklist atomics -----------------------------------------------------


@pytest.mark.sr("SR-170")
def test_sr170_acc_checklist_list(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps acc checklist list {project_id}",
        sr_id="SR-170",
        slug="acc-checklist-list",
        may_fail=True,
    )


@pytest.mark.sr("SR-171")
def test_sr171_acc_checklist_create(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f'raps acc checklist create {project_id} --title "Pre-pour inspection - Level 3"'
        f" --template-id {TEMPLATE_ID}",
        sr_id="SR-171",
        slug="acc-checklist-create",
        may_fail=True,
    )


@pytest.mark.sr("SR-172")
def test_sr172_acc_checklist_get(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps acc checklist get {project_id} {CHECKLIST_ID}",
        sr_id="SR-172",
        slug="acc-checklist-get",
        may_fail=True,
    )


@pytest.mark.sr("SR-173")
def test_sr173_acc_checklist_update(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f'raps acc checklist update {project_id} {CHECKLIST_ID} --status "completed"',
        sr_id="SR-173",
        slug="acc-checklist-update",
        may_fail=True,
    )


@pytest.mark.sr("SR-174")
def test_sr174_acc_checklist_templates(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps acc checklist templates {project_id}",
        sr_id="SR-174",
        slug="acc-checklist-templates",
        may_fail=True,
    )


# -- Lifecycles -------------------------------------------------------------


@pytest.mark.sr("SR-175")
@pytest.mark.lifecycle
def test_sr175_asset_tracking_lifecycle(raps, ids):
    pid = ids.project_id or "demo-project-001"
    lc = raps.lifecycle("SR-175", "asset-tracking-lifecycle", "Facilities manager tracks equipment")
    lc.step(f'raps acc asset create {pid} --category-id {MECH_CAT} --description "Chiller CH-01"', may_fail=True)
    lc.step(f'raps acc asset create {pid} --category-id {MECH_CAT} --description "Chiller CH-02"', may_fail=True)
    lc.step(f"raps acc asset list {pid}", may_fail=True)
    lc.step(f"raps acc asset update {pid} {CH01} --status-id {DELIVERED_STATUS}", may_fail=True)
    lc.step(f"raps acc asset update {pid} {CH01} --status-id {INSTALLED_STATUS}", may_fail=True)
    lc.step(f"raps acc asset get {pid} {CH01}", may_fail=True)
    lc.step(f"raps acc asset delete {pid} {CH02} --yes", may_fail=True)
    lc.assert_all_passed()


@pytest.mark.sr("SR-176")
@pytest.mark.lifecycle
def test_sr176_submittal_review_lifecycle(raps, ids):
    pid = ids.project_id or "demo-project-001"
    lc = raps.lifecycle("SR-176", "submittal-review-lifecycle", "GC submits shop drawings")
    lc.step(
        f'raps acc submittal create {pid} --title "Structural steel shop drawings"'
        f' --spec-section "05 12 00"',
        may_fail=True,
    )
    lc.step(f"raps acc submittal get {pid} {SUBMITTAL_ID}", may_fail=True)
    lc.step(f'raps acc submittal update {pid} {SUBMITTAL_ID} --status "in_review"', may_fail=True)
    lc.step(f'raps acc submittal update {pid} {SUBMITTAL_ID} --status "revise_resubmit"', may_fail=True)
    lc.step(f'raps acc submittal update {pid} {SUBMITTAL_ID} --status "approved"', may_fail=True)
    lc.step(f"raps acc submittal delete {pid} {SUBMITTAL_ID} --yes", may_fail=True)
    lc.assert_all_passed()


@pytest.mark.sr("SR-177")
@pytest.mark.lifecycle
def test_sr177_checklist_inspection_lifecycle(raps, ids):
    pid = ids.project_id or "demo-project-001"
    lc = raps.lifecycle(
        "SR-177", "checklist-inspection-lifecycle", "Inspector completes inspection"
    )
    lc.step(f"raps acc checklist templates {pid}", may_fail=True)
    lc.step(
        f'raps acc checklist create {pid} --title "Fire stopping inspection B3" --template-id {TPL}',
        may_fail=True,
    )
    lc.step(f"raps acc checklist get {pid} {CHECKLIST_ID}", may_fail=True)
    lc.step(f'raps acc checklist update {pid} {CHECKLIST_ID} --status "in_progress"', may_fail=True)
    lc.step(f'raps acc checklist update {pid} {CHECKLIST_ID} --status "completed"', may_fail=True)
    lc.step(f"raps acc checklist get {pid} {CHECKLIST_ID}", may_fail=True)
    lc.assert_all_passed()
