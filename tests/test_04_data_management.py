"""Data Management"""

import pytest

pytestmark = [
    pytest.mark.require_3leg,
    pytest.mark.xdist_group("04-data-management"),
]

FOLDER_ID = "urn:adsk.wipprod:fs.folder:co.demo-folder-001"
NEW_FOLDER_ID = "urn:adsk.wipprod:fs.folder:co.demo-folder-002"
ITEM_ID = "urn:adsk.wipprod:dm.lineage:demo-item-001"
OBJECT_URN = "dXJuOmFkc2sub2JqZWN0czpvcy5vYmplY3Q6ZGVtby1idWNrZXQvc2FtcGxlLmlmYw"
ROOT_FOLDER = "urn:adsk.wipprod:fs.folder:co.demo-root-001"
PHASE1 = "urn:adsk.wipprod:fs.folder:co.demo-phase1-001"
STRUCTURAL = "urn:adsk.wipprod:fs.folder:co.demo-structural-001"
MEP = "urn:adsk.wipprod:fs.folder:co.demo-mep-001"
SUBFOLDER = "urn:adsk.wipprod:fs.folder:co.demo-subfolder-001"


# -- Atomic commands -------------------------------------------------------


@pytest.mark.sr("SR-070")
def test_sr070_hub_list(raps):
    raps.run(
        "raps hub list",
        sr_id="SR-070",
        slug="hub-list",
        may_fail=True,
    )


@pytest.mark.sr("SR-071")
def test_sr071_hub_info(raps, ids):
    hub_id = ids.hub_id or "b.demo-hub-001"
    raps.run(
        f"raps hub info {hub_id}",
        sr_id="SR-071",
        slug="hub-info",
        may_fail=True,
    )


@pytest.mark.sr("SR-072")
def test_sr072_project_list(raps, ids):
    hub_id = ids.hub_id or "b.demo-hub-001"
    raps.run(
        f"raps project list {hub_id}",
        sr_id="SR-072",
        slug="project-list",
        may_fail=True,
    )


@pytest.mark.sr("SR-073")
def test_sr073_project_list_interactive(raps):
    raps.run(
        "raps project list",
        sr_id="SR-073",
        slug="project-list-interactive",
        may_fail=True,
    )


@pytest.mark.sr("SR-074")
def test_sr074_project_info(raps, ids):
    hub_id = ids.hub_id or "b.demo-hub-001"
    project_id = ids.project_full_id or "b.demo-project-001"
    raps.run(
        f"raps project info {hub_id} {project_id}",
        sr_id="SR-074",
        slug="project-info",
        may_fail=True,
    )


@pytest.mark.sr("SR-075")
def test_sr075_folder_list(raps, ids):
    project_id = ids.project_full_id or "b.demo-project-001"
    raps.run(
        f"raps folder list {project_id} {FOLDER_ID}",
        sr_id="SR-075",
        slug="folder-list",
        may_fail=True,
    )


@pytest.mark.sr("SR-076")
def test_sr076_folder_create(raps, ids):
    project_id = ids.project_full_id or "b.demo-project-001"
    raps.run(
        f'raps folder create {project_id} {FOLDER_ID} -n "Test Folder"',
        sr_id="SR-076",
        slug="folder-create",
        may_fail=True,
    )


@pytest.mark.sr("SR-077")
def test_sr077_folder_rename(raps, ids):
    project_id = ids.project_full_id or "b.demo-project-001"
    raps.run(
        f'raps folder rename {project_id} {NEW_FOLDER_ID} --name "Renamed Folder"',
        sr_id="SR-077",
        slug="folder-rename",
        may_fail=True,
    )


@pytest.mark.sr("SR-078")
def test_sr078_folder_rights(raps, ids):
    project_id = ids.project_full_id or "b.demo-project-001"
    raps.run(
        f"raps folder rights {project_id} {FOLDER_ID}",
        sr_id="SR-078",
        slug="folder-rights",
        may_fail=True,
    )


@pytest.mark.sr("SR-079")
def test_sr079_folder_delete(raps, ids):
    project_id = ids.project_full_id or "b.demo-project-001"
    raps.run(
        f"raps folder delete {project_id} {NEW_FOLDER_ID}",
        sr_id="SR-079",
        slug="folder-delete",
        may_fail=True,
    )


@pytest.mark.sr("SR-080")
def test_sr080_item_info(raps, ids):
    project_id = ids.project_full_id or "b.demo-project-001"
    raps.run(
        f"raps item info {project_id} {ITEM_ID}",
        sr_id="SR-080",
        slug="item-info",
        may_fail=True,
    )


@pytest.mark.sr("SR-081")
def test_sr081_item_versions(raps, ids):
    project_id = ids.project_full_id or "b.demo-project-001"
    raps.run(
        f"raps item versions {project_id} {ITEM_ID}",
        sr_id="SR-081",
        slug="item-versions",
        may_fail=True,
    )


@pytest.mark.sr("SR-082")
def test_sr082_item_create_from_oss(raps, ids):
    project_id = ids.project_full_id or "b.demo-project-001"
    raps.run(
        f'raps item create-from-oss {project_id} {FOLDER_ID} --name "Uploaded Model" --object-id {OBJECT_URN}',
        sr_id="SR-082",
        slug="item-create-from-oss",
        may_fail=True,
    )


@pytest.mark.sr("SR-083")
def test_sr083_item_rename(raps, ids):
    project_id = ids.project_full_id or "b.demo-project-001"
    raps.run(
        f'raps item rename {project_id} {ITEM_ID} --name "Updated Model Name"',
        sr_id="SR-083",
        slug="item-rename",
        may_fail=True,
    )


@pytest.mark.sr("SR-084")
def test_sr084_item_delete(raps, ids):
    project_id = ids.project_full_id or "b.demo-project-001"
    raps.run(
        f"raps item delete {project_id} {ITEM_ID}",
        sr_id="SR-084",
        slug="item-delete",
        may_fail=True,
    )


# -- Lifecycles -------------------------------------------------------------


@pytest.mark.sr("SR-085")
@pytest.mark.lifecycle
def test_sr085_dm_navigation_lifecycle(raps, ids):
    hub_id = ids.hub_id or "b.demo-hub-001"
    project_id = ids.project_full_id or "b.demo-project-001"
    lc = raps.lifecycle("SR-085", "dm-navigation-lifecycle", "Developer explores project structure")
    lc.step("raps hub list", may_fail=True)
    lc.step(f"raps project list {hub_id}", may_fail=True)
    lc.step(f"raps project info {hub_id} {project_id}", may_fail=True)
    lc.step(f"raps folder list {project_id} {ROOT_FOLDER}", may_fail=True)
    lc.step(f"raps folder list {project_id} {SUBFOLDER}", may_fail=True)
    lc.assert_all_passed()


@pytest.mark.sr("SR-086")
@pytest.mark.lifecycle
def test_sr086_dm_folder_crud_lifecycle(raps, ids):
    project_id = ids.project_full_id or "b.demo-project-001"
    lc = raps.lifecycle("SR-086", "dm-folder-crud-lifecycle", "Admin creates folder structure")
    lc.step(f'raps folder create {project_id} {ROOT_FOLDER} -n "Phase 1"', may_fail=True)
    lc.step(f'raps folder create {project_id} {PHASE1} -n "Structural"', may_fail=True)
    lc.step(f'raps folder create {project_id} {PHASE1} -n "MEP"', may_fail=True)
    lc.step(f"raps folder list {project_id} {PHASE1}", may_fail=True)
    lc.step(f'raps folder rename {project_id} {MEP} --name "MEP Systems"', may_fail=True)
    lc.step(f"raps folder rights {project_id} {PHASE1}", may_fail=True)
    lc.step(f"raps folder delete {project_id} {MEP}", may_fail=True)
    lc.step(f"raps folder delete {project_id} {STRUCTURAL}", may_fail=True)
    lc.step(f"raps folder delete {project_id} {PHASE1}", may_fail=True)
    lc.assert_all_passed()


@pytest.mark.sr("SR-087")
@pytest.mark.lifecycle
def test_sr087_item_upload_and_manage(raps, ids):
    project_id = ids.project_full_id or "b.demo-project-001"
    lc = raps.lifecycle("SR-087", "item-upload-and-manage", "Developer uploads to BIM 360")
    lc.step("raps bucket create", may_fail=True)
    lc.step("raps object upload dm-staging ./test-data/sample.rvt", may_fail=True)
    lc.step(
        f'raps item create-from-oss {project_id} {FOLDER_ID} --name "Building.rvt" --object-id {OBJECT_URN}',
        may_fail=True,
    )
    lc.step(f"raps item info {project_id} {ITEM_ID}", may_fail=True)
    lc.step(f"raps item versions {project_id} {ITEM_ID}", may_fail=True)
    lc.step(f'raps item rename {project_id} {ITEM_ID} --name "Building-v2.rvt"', may_fail=True)
    lc.step(f"raps item delete {project_id} {ITEM_ID}", may_fail=True)
    lc.step("raps bucket delete dm-staging -y", may_fail=True)
    lc.assert_all_passed()
