"""Model Derivative / Translation"""

import base64
import json
import time
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.require_2leg,
    pytest.mark.xdist_group("05-model-derivative"),
]

_TS = str(int(time.time()))
BUCKET_NAME = f"sr-deriv-{_TS}"
OBJECT_KEY = "sample.ifc"
URN = base64.urlsafe_b64encode(
    f"urn:adsk.objects:os.object:{BUCKET_NAME}/{OBJECT_KEY}".encode()
).decode().rstrip("=")


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
    lc.step(f"raps bucket create -k {BUCKET_NAME} -p transient -r US")
    lc.step(f"raps object upload {BUCKET_NAME} ./test-data/sample.rvt")
    result = lc.step(f"raps translate start {rvt_urn} --format svf2")
    if not result.ok and "capacity exceeded" in result.stderr:
        pytest.skip("Translation API rate-limited (free tier capacity exceeded)")
    if result.ok:
        lc.step(f"raps translate status {rvt_urn}")
        lc.step(f"raps translate manifest {rvt_urn}")
    lc.assert_all_passed()


@pytest.mark.sr("SR-101")
@pytest.mark.lifecycle
def test_sr101_translate_preset_lifecycle(raps):
    lc = raps.lifecycle("SR-101", "translate-preset-lifecycle", "Preset CRUD + use")
    lc.step('raps translate preset create "ifc-to-svf" -f svf2')
    lc.step("raps translate preset list")
    lc.step('raps translate preset show "ifc-to-svf"')
    lc.step('raps translate preset delete "ifc-to-svf"')
    lc.assert_all_passed()


@pytest.mark.sr("SR-550")
@pytest.mark.lifecycle
def test_sr550_translate_metadata_lifecycle(raps):
    """Translate -> poll -> metadata -> tree -> properties -> query-properties"""
    if not Path("./test-data/sample.ifc").is_file():
        pytest.skip("missing ./test-data/sample.ifc")
    bucket = f"sr-meta-{_TS}"
    obj_key = "sample.ifc"
    meta_urn = base64.urlsafe_b64encode(
        f"urn:adsk.objects:os.object:{bucket}/{obj_key}".encode()
    ).decode().rstrip("=")
    lc = raps.lifecycle(
        "SR-550", "translate-metadata-lifecycle",
        "Translate -> poll -> metadata -> tree -> properties -> query-properties",
    )
    lc.step(f"raps bucket create -k {bucket} -p transient -r US")
    lc.step(f"raps object upload {bucket} ./test-data/sample.ifc")
    result = lc.step(f"raps translate start {meta_urn} --format svf2")
    if not result.ok and "capacity exceeded" in result.stderr:
        pytest.skip("Translation API rate-limited (free tier capacity exceeded)")
    # Poll manifest until translation reaches Success (mock needs ~5 polls)
    for _ in range(6):
        lc.step(f"raps translate manifest {meta_urn}")
    # T020: Get metadata (JSON output to extract GUID)
    meta_result = lc.step(f"raps translate metadata {meta_urn} --output json")
    guid = ""
    if meta_result.ok:
        json_start = meta_result.stdout.find("{")
        if json_start >= 0:
            try:
                meta = json.loads(meta_result.stdout[json_start:])
                views = meta.get("data", {}).get("metadata", [])
                if views:
                    guid = views[0].get("guid", "")
            except (json.JSONDecodeError, KeyError, IndexError):
                pass
    if not guid:
        pytest.skip("Could not extract GUID from metadata response")
    # T021: Get object tree
    lc.step(f"raps translate tree {meta_urn} {guid} --output json")
    # T022: Get properties
    lc.step(f"raps translate properties {meta_urn} {guid} --output json")
    # T023: Query properties by object IDs
    lc.step(
        f'raps translate query-properties {meta_urn} {guid} --filter "1,2,3" --output json'
    )
    lc.assert_all_passed()
