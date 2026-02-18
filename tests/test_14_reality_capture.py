"""Reality Capture"""

import pytest

pytestmark = [
    pytest.mark.require_3leg,
    pytest.mark.xdist_group("14-reality-capture"),
]

JOB_ID = "job-demo-001"
JID = "job-demo-001"


# -- Atomic commands --------------------------------------------------------


@pytest.mark.sr("SR-230")
def test_sr230_reality_list(raps):
    raps.run(
        "raps reality list",
        sr_id="SR-230",
        slug="reality-list",
        may_fail=True,
    )


@pytest.mark.sr("SR-231")
def test_sr231_reality_formats(raps):
    raps.run(
        "raps reality formats",
        sr_id="SR-231",
        slug="reality-formats",
        may_fail=True,
    )


@pytest.mark.sr("SR-232")
def test_sr232_reality_create(raps):
    raps.run(
        'raps reality create --name "Site Survey 2026-02" --scene-type object -f obj',
        sr_id="SR-232",
        slug="reality-create",
        may_fail=True,
    )


@pytest.mark.sr("SR-233")
def test_sr233_reality_upload(raps):
    raps.run(
        f"raps reality upload {JOB_ID} ./test-data/sample.rvt",
        sr_id="SR-233",
        slug="reality-upload",
        may_fail=True,
    )


@pytest.mark.sr("SR-234")
def test_sr234_reality_process(raps):
    raps.run(
        f"raps reality process {JOB_ID}",
        sr_id="SR-234",
        slug="reality-process",
        may_fail=True,
    )


@pytest.mark.sr("SR-235")
def test_sr235_reality_status(raps):
    raps.run(
        f"raps reality status {JOB_ID}",
        sr_id="SR-235",
        slug="reality-status",
        may_fail=True,
    )


@pytest.mark.sr("SR-236")
def test_sr236_reality_result(raps):
    raps.run(
        f"raps reality result {JOB_ID}",
        sr_id="SR-236",
        slug="reality-result",
        may_fail=True,
    )


@pytest.mark.sr("SR-237")
def test_sr237_reality_delete(raps):
    raps.run(
        f"raps reality delete {JOB_ID}",
        sr_id="SR-237",
        slug="reality-delete",
        may_fail=True,
    )


# -- Lifecycles -------------------------------------------------------------


@pytest.mark.sr("SR-238")
@pytest.mark.lifecycle
def test_sr238_reality_capture_lifecycle(raps):
    import json

    lc = raps.lifecycle(
        "SR-238", "reality-capture-lifecycle", "Capture and process construction site"
    )
    lc.step("raps reality formats", may_fail=True)
    result = lc.step(
        'raps reality create --name "Foundation Survey" --scene-type object -f obj --output json',
        may_fail=True,
    )
    jid = JID
    if result.ok:
        try:
            jid = json.loads(result.stdout).get("photoscene_id", jid)
        except (json.JSONDecodeError, KeyError):
            pass
    lc.step(f"raps reality upload {jid} ./test-data/sample.rvt", may_fail=True)
    lc.step(f"raps reality process {jid}", may_fail=True)
    lc.step(f"raps reality status {jid}", may_fail=True)
    lc.step(f"raps reality result {jid}", may_fail=True)
    lc.step("raps reality list", may_fail=True)
    lc.step(f"raps reality delete {jid}", may_fail=True)
    lc.assert_all_passed()
