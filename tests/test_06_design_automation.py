"""Design Automation"""

import time

import pytest

pytestmark = [
    pytest.mark.require_2leg,
    pytest.mark.xdist_group("06-design-automation"),
]

_TS = str(int(time.time()))
INPUT_URL = "https://developer.api.autodesk.com/oss/v2/buckets/demo/objects/input.rvt?token=demo"
OUTPUT_URL = "https://developer.api.autodesk.com/oss/v2/buckets/demo/objects/output.json?token=demo"
WORKITEM_ID = "demo-workitem-001"


# ── Engine & AppBundle atomics ────────────────────────────────────


@pytest.mark.sr("SR-110")
def test_sr110_da_engines(raps):
    raps.run("raps da engines", sr_id="SR-110", slug="da-engines")


@pytest.mark.sr("SR-111")
def test_sr111_da_appbundles_list(raps):
    raps.run("raps da appbundles", sr_id="SR-111", slug="da-appbundles-list")


@pytest.mark.sr("SR-112")
def test_sr112_da_appbundle_create(raps):
    raps.run(
        f'raps da appbundle-create -i SrTestBundle{_TS} -e "Autodesk.Revit+2025" -d "RAPS test bundle"',
        sr_id="SR-112",
        slug="da-appbundle-create",
    )


@pytest.mark.sr("SR-113")
def test_sr113_da_appbundle_delete(raps):
    raps.run(
        f"raps da appbundle-delete SrTestBundle{_TS}",
        sr_id="SR-113",
        slug="da-appbundle-delete",
    )


# ── Activity atomics ─────────────────────────────────────────────


@pytest.mark.sr("SR-114")
def test_sr114_da_activities_list(raps):
    raps.run("raps da activities", sr_id="SR-114", slug="da-activities-list")


@pytest.mark.sr("SR-115")
def test_sr115_da_activity_create(raps):
    raps.run(
        f"raps da activity-create --id SrTestActivity{_TS}"
        ' --engine "Autodesk.Revit+2025"'
        " --command '$(engine.path)\\\\revitcoreconsole.exe /i $(args[input].path)'"
        f' --appbundle "SrTestBundle{_TS}"',
        sr_id="SR-115",
        slug="da-activity-create",
    )


@pytest.mark.sr("SR-116")
def test_sr116_da_activity_delete(raps):
    raps.run(
        f"raps da activity-delete SrTestActivity{_TS}",
        sr_id="SR-116",
        slug="da-activity-delete",
    )


# ── Work item atomics ────────────────────────────────────────────


@pytest.mark.sr("SR-117")
def test_sr117_da_run(raps):
    raps.run(
        f'raps da run SrTestActivity{_TS} -i "input={INPUT_URL}" --out-arg "output={OUTPUT_URL}"',
        sr_id="SR-117",
        slug="da-run",
    )


@pytest.mark.sr("SR-118")
def test_sr118_da_workitems(raps):
    raps.run(
        "raps da workitems",
        sr_id="SR-118",
        slug="da-workitems",
    )


@pytest.mark.sr("SR-119")
def test_sr119_da_status(raps):
    raps.run(
        f"raps da status {WORKITEM_ID}",
        sr_id="SR-119",
        slug="da-status",
    )


# ── Lifecycles ───────────────────────────────────────────────────


@pytest.mark.sr("SR-120")
@pytest.mark.lifecycle
def test_sr120_da_appbundle_lifecycle(raps):
    bundle_id = f"SrLcBundle{_TS}"
    lc = raps.lifecycle("SR-120", "da-appbundle-lifecycle", "AppBundle create -> list -> delete")
    lc.step(f'raps da appbundle-create -i {bundle_id} -e "Autodesk.Revit+2025"')
    lc.step("raps da appbundles")
    lc.step(f"raps da appbundle-delete {bundle_id}")
    lc.assert_all_passed()


@pytest.mark.sr("SR-121")
@pytest.mark.lifecycle
def test_sr121_da_workitem_lifecycle(raps):
    bundle_id = f"SrLcBundle{_TS}"
    activity_id = f"SrLcActivity{_TS}"
    lc = raps.lifecycle(
        "SR-121", "da-workitem-lifecycle", "Bundle + Activity create -> list -> cleanup"
    )
    lc.step(
        f'raps da appbundle-create -i {bundle_id} -e "Autodesk.Revit+2025"',
    )
    lc.step(
        f"raps da activity-create --id {activity_id}"
        ' --engine "Autodesk.Revit+2025"'
        " --command 'test'"
        f' --appbundle "{bundle_id}"',
    )
    # Note: da run requires a real uploaded plugin binary — skip in test env
    lc.step("raps da activities")
    lc.step("raps da appbundles")
    lc.step(f"raps da activity-delete {activity_id}")
    lc.step(f"raps da appbundle-delete {bundle_id}")
    lc.assert_all_passed()
