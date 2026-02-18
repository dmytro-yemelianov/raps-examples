"""Design Automation"""

import pytest

pytestmark = [
    pytest.mark.require_2leg,
    pytest.mark.xdist_group("06-design-automation"),
]

INPUT_URL = "https://developer.api.autodesk.com/oss/v2/buckets/demo/objects/input.rvt?token=demo"
OUTPUT_URL = "https://developer.api.autodesk.com/oss/v2/buckets/demo/objects/output.json?token=demo"
WORKITEM_ID = "demo-workitem-001"


# ── Engine & AppBundle atomics ────────────────────────────────────


@pytest.mark.sr("SR-110")
def test_sr110_da_engines(raps):
    raps.run("raps da engines", sr_id="SR-110", slug="da-engines", may_fail=True)


@pytest.mark.sr("SR-111")
def test_sr111_da_appbundles_list(raps):
    raps.run("raps da appbundles", sr_id="SR-111", slug="da-appbundles-list", may_fail=True)


@pytest.mark.sr("SR-112")
def test_sr112_da_appbundle_create(raps):
    raps.run(
        'raps da appbundle-create -i sr-test-bundle -e "Autodesk.Revit+2025" -d "RAPS test bundle"',
        sr_id="SR-112",
        slug="da-appbundle-create",
        may_fail=True,
    )


@pytest.mark.sr("SR-113")
def test_sr113_da_appbundle_delete(raps):
    raps.run(
        "raps da appbundle-delete sr-test-bundle",
        sr_id="SR-113",
        slug="da-appbundle-delete",
        may_fail=True,
    )


# ── Activity atomics ─────────────────────────────────────────────


@pytest.mark.sr("SR-114")
def test_sr114_da_activities_list(raps):
    raps.run("raps da activities", sr_id="SR-114", slug="da-activities-list", may_fail=True)


@pytest.mark.sr("SR-115")
def test_sr115_da_activity_create(raps):
    raps.run(
        "raps da activity-create --id sr-test-activity"
        ' --engine "Autodesk.Revit+2025"'
        " --command '$(engine.path)\\\\revitcoreconsole.exe /i $(args[input].path)'"
        ' --appbundle "sr-test-bundle"',
        sr_id="SR-115",
        slug="da-activity-create",
        may_fail=True,
    )


@pytest.mark.sr("SR-116")
def test_sr116_da_activity_delete(raps):
    raps.run(
        "raps da activity-delete sr-test-activity",
        sr_id="SR-116",
        slug="da-activity-delete",
        may_fail=True,
    )


# ── Work item atomics ────────────────────────────────────────────


@pytest.mark.sr("SR-117")
def test_sr117_da_run(raps):
    raps.run(
        f'raps da run sr-test-activity -i "input={INPUT_URL}" --out-arg "output={OUTPUT_URL}"',
        sr_id="SR-117",
        slug="da-run",
        may_fail=True,
    )


@pytest.mark.sr("SR-118")
def test_sr118_da_workitems(raps):
    raps.run(
        "raps da workitems",
        sr_id="SR-118",
        slug="da-workitems",
        may_fail=True,
    )


@pytest.mark.sr("SR-119")
def test_sr119_da_status(raps):
    raps.run(
        f"raps da status {WORKITEM_ID}",
        sr_id="SR-119",
        slug="da-status",
        may_fail=True,
    )


# ── Lifecycles ───────────────────────────────────────────────────


@pytest.mark.sr("SR-120")
@pytest.mark.lifecycle
def test_sr120_da_appbundle_lifecycle(raps):
    lc = raps.lifecycle("SR-120", "da-appbundle-lifecycle", "AppBundle create -> list -> delete")
    lc.step('raps da appbundle-create -i sr-lifecycle-bundle -e "Autodesk.Revit+2025"', may_fail=True)
    lc.step("raps da appbundles", may_fail=True)
    lc.step("raps da appbundle-delete sr-lifecycle-bundle", may_fail=True)
    lc.assert_all_passed()


@pytest.mark.sr("SR-121")
@pytest.mark.lifecycle
def test_sr121_da_workitem_lifecycle(raps):
    lc = raps.lifecycle(
        "SR-121", "da-workitem-lifecycle", "Activity create -> run -> status -> cleanup"
    )
    lc.step(
        "raps da activity-create --id sr-lifecycle-activity"
        ' --engine "Autodesk.Revit+2025"'
        " --command 'test'"
        ' --appbundle "sr-lifecycle-bundle"',
        may_fail=True,
    )
    lc.step(
        f'raps da run sr-lifecycle-activity -i "input={INPUT_URL}" --out-arg "output={OUTPUT_URL}"',
        may_fail=True,
    )
    lc.step("raps da workitems", may_fail=True)
    lc.step("raps da activity-delete sr-lifecycle-activity", may_fail=True)
    lc.assert_all_passed()
