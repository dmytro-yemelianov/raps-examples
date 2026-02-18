"""Model Derivative / Translation"""

import base64
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.require_2leg,
    pytest.mark.xdist_group("05-model-derivative"),
]

BUCKET_NAME = "sr-test-bucket-raps"
OBJECT_KEY = "sample.ifc"
URN = base64.urlsafe_b64encode(
    f"urn:adsk.objects:os.object:{BUCKET_NAME}/{OBJECT_KEY}".encode()
).decode().rstrip("=")


# ── Atomic commands ──────────────────────────────────────────────


@pytest.mark.sr("SR-090")
def test_sr090_translate_start(raps):
    raps.run(
        f"raps translate start {URN} --format svf2",
        sr_id="SR-090",
        slug="translate-start",
        may_fail=True,
    )


@pytest.mark.sr("SR-091")
def test_sr091_translate_status(raps):
    raps.run(
        f"raps translate status {URN}",
        sr_id="SR-091",
        slug="translate-status",
        may_fail=True,
    )


@pytest.mark.sr("SR-092")
def test_sr092_translate_manifest(raps):
    raps.run(
        f"raps translate manifest {URN}",
        sr_id="SR-092",
        slug="translate-manifest",
        may_fail=True,
    )


@pytest.mark.sr("SR-093")
def test_sr093_translate_derivatives(raps):
    raps.run(
        f"raps translate derivatives {URN}",
        sr_id="SR-093",
        slug="translate-derivatives",
        may_fail=True,
    )


@pytest.mark.sr("SR-094")
def test_sr094_translate_download(raps):
    raps.run(
        f"raps translate download {URN} -o /tmp/raps-derivative-test/",
        sr_id="SR-094",
        slug="translate-download",
        may_fail=True,
    )


@pytest.mark.sr("SR-095")
def test_sr095_translate_preset_list(raps):
    raps.run(
        "raps translate preset list",
        sr_id="SR-095",
        slug="translate-preset-list",
        may_fail=True,
    )


@pytest.mark.sr("SR-096")
def test_sr096_translate_preset_create(raps):
    raps.run(
        'raps translate preset create "svf2-default" -f svf2',
        sr_id="SR-096",
        slug="translate-preset-create",
        may_fail=True,
    )


@pytest.mark.sr("SR-097")
def test_sr097_translate_preset_show(raps):
    raps.run(
        'raps translate preset show "svf2-default"',
        sr_id="SR-097",
        slug="translate-preset-show",
        may_fail=True,
    )


@pytest.mark.sr("SR-098")
def test_sr098_translate_preset_use(raps):
    raps.run(
        f'raps translate preset use {URN} svf2-default',
        sr_id="SR-098",
        slug="translate-preset-use",
        may_fail=True,
    )


@pytest.mark.sr("SR-099")
def test_sr099_translate_preset_delete(raps):
    raps.run(
        'raps translate preset delete "svf2-default"',
        sr_id="SR-099",
        slug="translate-preset-delete",
        may_fail=True,
    )


# ── Lifecycles ───────────────────────────────────────────────────


@pytest.mark.sr("SR-100")
@pytest.mark.lifecycle
def test_sr100_translate_full_pipeline(raps):
    if not Path("./test-data/sample.rvt").is_file():
        pytest.skip("missing ./test-data/sample.rvt")
    rvt_urn = base64.urlsafe_b64encode(
        f"urn:adsk.objects:os.object:{BUCKET_NAME}/sample.rvt".encode()
    ).decode().rstrip("=")
    lc = raps.lifecycle(
        "SR-100", "translate-full-pipeline", "Upload -> translate -> poll -> download"
    )
    lc.step(f"raps object upload {BUCKET_NAME} ./test-data/sample.rvt", may_fail=True)
    lc.step(f"raps translate start {rvt_urn} --format svf2", may_fail=True)
    lc.step(f"raps translate status {rvt_urn}", may_fail=True)
    lc.step(f"raps translate manifest {rvt_urn}", may_fail=True)
    lc.assert_all_passed()


@pytest.mark.sr("SR-101")
@pytest.mark.lifecycle
def test_sr101_translate_preset_lifecycle(raps):
    lc = raps.lifecycle("SR-101", "translate-preset-lifecycle", "Preset CRUD + use")
    lc.step('raps translate preset create "ifc-to-svf" -f svf2', may_fail=True)
    lc.step("raps translate preset list", may_fail=True)
    lc.step('raps translate preset show "ifc-to-svf"', may_fail=True)
    lc.step('raps translate preset delete "ifc-to-svf"', may_fail=True)
    lc.assert_all_passed()
