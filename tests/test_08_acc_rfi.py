"""ACC RFIs"""

import pytest

pytestmark = [
    pytest.mark.require_3leg,
    pytest.mark.xdist_group("08-acc-rfi"),
]

RFI_ID = "rfi-demo-001"
ID = "rfi-demo-001"
LC_ID = "lc-rfi-001"
STRUCT_ENG = "demo-struct-eng-001"


# -- RFI atomics ------------------------------------------------------------


@pytest.mark.sr("SR-150")
def test_sr150_rfi_list(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps rfi list {project_id}",
        sr_id="SR-150",
        slug="rfi-list",
    )


@pytest.mark.sr("SR-151")
def test_sr151_rfi_create(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f'raps rfi create {project_id} --title "Clarification on MEP routing at Level 3"'
        f' --question "Conflict between HVAC duct and structural beam at grid C-4"',
        sr_id="SR-151",
        slug="rfi-create",
    )


@pytest.mark.sr("SR-152")
def test_sr152_rfi_get(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps rfi get {project_id} {RFI_ID}",
        sr_id="SR-152",
        slug="rfi-get",
    )


@pytest.mark.sr("SR-153")
def test_sr153_rfi_update(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    user_id = ids.user_id or "demo-user-001"
    raps.run(
        f'raps rfi update {project_id} {RFI_ID} --assigned-to {user_id} --priority "high"',
        sr_id="SR-153",
        slug="rfi-update",
    )


@pytest.mark.sr("SR-154")
def test_sr154_rfi_delete(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps rfi delete {project_id} {RFI_ID} --yes",
        sr_id="SR-154",
        slug="rfi-delete",
    )


# -- Lifecycles -------------------------------------------------------------


@pytest.mark.sr("SR-155")
@pytest.mark.lifecycle
def test_sr155_rfi_full_lifecycle(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    lc = raps.lifecycle("SR-155", "rfi-full-lifecycle", "Architect raises and resolves an RFI")
    lc.step(f'raps rfi create {project_id} --title "Beam depth at grid D-7"')
    lc.step(f"raps rfi list {project_id}")
    lc.step(f"raps rfi get {project_id} {LC_ID}")
    lc.step(f'raps rfi update {project_id} {LC_ID} --assigned-to {STRUCT_ENG} --priority "high"')
    lc.step(
        f'raps rfi update {project_id} {LC_ID} --status "answered" --answer "Use W14x30, see SK-204"',
    )
    lc.step(f"raps rfi get {project_id} {LC_ID}")
    lc.step(f"raps rfi delete {project_id} {LC_ID} --yes")
    lc.assert_all_passed()
