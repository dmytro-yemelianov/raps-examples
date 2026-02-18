"""Storage: Buckets + Objects"""

from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.require_2leg,
    pytest.mark.xdist_group("03-storage"),
]

BUCKET_NAME = "sr-test-bucket-raps"
DEST_BUCKET = "sr-backup-bucket-raps"


# ── Bucket atomics ───────────────────────────────────────────────


@pytest.mark.sr("SR-050")
def test_sr050_bucket_create(raps):
    raps.run(
        f"raps bucket create -k {BUCKET_NAME} -p transient -r US",
        sr_id="SR-050",
        slug="bucket-create",
        may_fail=True,
    )


@pytest.mark.sr("SR-051")
def test_sr051_bucket_list(raps):
    raps.run("raps bucket list", sr_id="SR-051", slug="bucket-list", may_fail=True)


@pytest.mark.sr("SR-052")
def test_sr052_bucket_info(raps):
    raps.run(
        f"raps bucket info {BUCKET_NAME}",
        sr_id="SR-052",
        slug="bucket-info",
        may_fail=True,
    )


@pytest.mark.sr("SR-053")
def test_sr053_bucket_delete():
    pytest.skip("deferred to lifecycle cleanup")


# ── Object atomics ───────────────────────────────────────────────


@pytest.mark.sr("SR-054")
def test_sr054_object_upload(raps):
    if not Path("./test-data/sample.ifc").is_file():
        pytest.skip("missing ./test-data/sample.ifc")
    raps.run(
        f"raps object upload {BUCKET_NAME} ./test-data/sample.ifc",
        sr_id="SR-054",
        slug="object-upload",
        may_fail=True,
    )


@pytest.mark.sr("SR-055")
def test_sr055_object_upload_batch(raps):
    if not Path("./test-data").is_dir():
        pytest.skip("missing ./test-data/")
    raps.run(
        f"raps object upload {BUCKET_NAME} ./test-data/",
        sr_id="SR-055",
        slug="object-upload-batch",
        may_fail=True,
    )


@pytest.mark.sr("SR-056")
def test_sr056_object_list(raps):
    raps.run(
        f"raps object list {BUCKET_NAME}",
        sr_id="SR-056",
        slug="object-list",
        may_fail=True,
    )


@pytest.mark.sr("SR-057")
def test_sr057_object_info(raps):
    raps.run(
        f"raps object info {BUCKET_NAME} sample.ifc",
        sr_id="SR-057",
        slug="object-info",
        may_fail=True,
    )


@pytest.mark.sr("SR-058")
def test_sr058_object_download(raps):
    raps.run(
        f"mkdir -p ./tmp && raps object download {BUCKET_NAME} sample.ifc -o ./tmp/raps-download-test.ifc",
        sr_id="SR-058",
        slug="object-download",
        may_fail=True,
    )


@pytest.mark.sr("SR-059")
def test_sr059_object_signed_url(raps):
    raps.run(
        f"raps object signed-url {BUCKET_NAME} sample.ifc",
        sr_id="SR-059",
        slug="object-signed-url",
        may_fail=True,
    )


@pytest.mark.sr("SR-060")
def test_sr060_object_copy(raps):
    # Ensure destination bucket exists (may already exist)
    raps.run(
        f"raps bucket create -k {DEST_BUCKET} -p transient -r US",
        sr_id="SR-060",
        slug="object-copy-setup",
        may_fail=True,
    )
    raps.run(
        f"raps object copy --source-bucket {BUCKET_NAME} --source-object sample.ifc --dest-bucket {DEST_BUCKET}",
        sr_id="SR-060",
        slug="object-copy",
        may_fail=True,
    )


@pytest.mark.sr("SR-061")
def test_sr061_object_rename(raps):
    raps.run(
        f"raps object rename {DEST_BUCKET} sample.ifc --new-key sample-renamed.ifc",
        sr_id="SR-061",
        slug="object-rename",
        may_fail=True,
    )


@pytest.mark.sr("SR-062")
def test_sr062_object_delete(raps):
    raps.run(
        f"raps object delete {DEST_BUCKET} sample-renamed.ifc -y",
        sr_id="SR-062",
        slug="object-delete",
        may_fail=True,
    )


# ── Lifecycles ───────────────────────────────────────────────────


@pytest.mark.sr("SR-063")
@pytest.mark.lifecycle
def test_sr063_bucket_full_lifecycle(raps):
    lc = raps.lifecycle("SR-063", "bucket-full-lifecycle", "Create -> list -> info -> delete")
    lc.step("raps bucket create -k sr-lifecycle-bucket -p transient -r US", may_fail=True)
    lc.step("raps bucket list", may_fail=True)
    lc.step("raps bucket info sr-lifecycle-bucket", may_fail=True)
    lc.step("raps bucket delete sr-lifecycle-bucket -y", may_fail=True)
    lc.assert_all_passed()


@pytest.mark.sr("SR-064")
@pytest.mark.lifecycle
def test_sr064_object_full_lifecycle(raps):
    if not Path("./test-data/sample.ifc").is_file():
        pytest.skip("missing ./test-data/sample.ifc")
    lc = raps.lifecycle(
        "SR-064", "object-full-lifecycle", "Upload -> list -> info -> download -> delete"
    )
    lc.step(f"raps object upload {BUCKET_NAME} ./test-data/sample.ifc", may_fail=True)
    lc.step(f"raps object list {BUCKET_NAME}", may_fail=True)
    lc.step(f"raps object info {BUCKET_NAME} sample.ifc", may_fail=True)
    lc.step(
        f"mkdir -p ./tmp && raps object download {BUCKET_NAME} sample.ifc -o ./tmp/raps-lifecycle-test.ifc",
        may_fail=True,
    )
    lc.step(f"raps object delete {BUCKET_NAME} sample.ifc -y", may_fail=True)
    lc.assert_all_passed()


@pytest.mark.sr("SR-065")
@pytest.mark.lifecycle
def test_sr065_batch_upload_lifecycle(raps):
    if not Path("./test-data").is_dir():
        pytest.skip("missing ./test-data/")
    lc = raps.lifecycle("SR-065", "batch-upload-lifecycle", "Batch upload -> list -> cleanup")
    lc.step("raps bucket create -k sr-batch-bucket -p transient -r US", may_fail=True)
    lc.step("raps object upload sr-batch-bucket ./test-data/", may_fail=True)
    lc.step("raps object list sr-batch-bucket", may_fail=True)
    lc.step("raps bucket delete sr-batch-bucket -y", may_fail=True)
    lc.assert_all_passed()
