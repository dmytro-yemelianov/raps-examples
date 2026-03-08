"""Storage: Buckets + Objects"""

import time
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.require_2leg,
    pytest.mark.xdist_group("03-storage"),
]

_TS = str(int(time.time()))
BUCKET_NAME = f"sr-test-{_TS}"
DEST_BUCKET = f"sr-backup-{_TS}"


# ── Bucket atomics ───────────────────────────────────────────────


@pytest.mark.sr("SR-050")
def test_sr050_bucket_create(raps):
    raps.run(
        f"raps bucket create -k {BUCKET_NAME} -p transient -r US",
        sr_id="SR-050",
        slug="bucket-create",
    )


@pytest.mark.sr("SR-051")
def test_sr051_bucket_list(raps):
    raps.run("raps bucket list", sr_id="SR-051", slug="bucket-list")


@pytest.mark.sr("SR-052")
def test_sr052_bucket_info(raps):
    raps.run(
        f"raps bucket info {BUCKET_NAME}",
        sr_id="SR-052",
        slug="bucket-info",
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
    )


@pytest.mark.sr("SR-055")
def test_sr055_object_upload_batch(raps):
    if not Path("./test-data").is_dir():
        pytest.skip("missing ./test-data/")
    raps.run(
        f"raps object upload {BUCKET_NAME} ./test-data/",
        sr_id="SR-055",
        slug="object-upload-batch",
    )


@pytest.mark.sr("SR-066")
def test_sr066_object_upload_batch(raps):
    if not Path("./test-data").is_dir():
        pytest.skip("missing ./test-data/")
    raps.run(
        f"raps object upload-batch {BUCKET_NAME} ./test-data/",
        sr_id="SR-066",
        slug="object-upload-batch",
    )


@pytest.mark.sr("SR-056")
def test_sr056_object_list(raps):
    raps.run(
        f"raps object list {BUCKET_NAME}",
        sr_id="SR-056",
        slug="object-list",
    )


@pytest.mark.sr("SR-057")
def test_sr057_object_info(raps):
    raps.run(
        f"raps object info {BUCKET_NAME} sample.ifc",
        sr_id="SR-057",
        slug="object-info",
    )


@pytest.mark.sr("SR-058")
def test_sr058_object_download(raps):
    raps.run(
        f"mkdir -p ./tmp && raps object download {BUCKET_NAME} sample.ifc --out-file ./tmp/raps-download-test.ifc",
        sr_id="SR-058",
        slug="object-download",
    )


@pytest.mark.sr("SR-059")
def test_sr059_object_signed_url(raps):
    raps.run(
        f"raps object signed-url {BUCKET_NAME} sample.ifc",
        sr_id="SR-059",
        slug="object-signed-url",
    )


@pytest.mark.sr("SR-060")
def test_sr060_object_copy(raps):
    # Ensure destination bucket exists (may already exist)
    raps.run(
        f"raps bucket create -k {DEST_BUCKET} -p transient -r US",
        sr_id="SR-060",
        slug="object-copy-setup",
    )
    raps.run(
        f"raps object copy --source-bucket {BUCKET_NAME} --source-object sample.ifc --dest-bucket {DEST_BUCKET}",
        sr_id="SR-060",
        slug="object-copy",
    )


@pytest.mark.sr("SR-061")
def test_sr061_object_rename(raps):
    raps.run(
        f"raps object rename {DEST_BUCKET} sample.ifc --new-key sample-renamed.ifc",
        sr_id="SR-061",
        slug="object-rename",
    )


@pytest.mark.sr("SR-062")
def test_sr062_object_delete(raps):
    raps.run(
        f"raps object delete {DEST_BUCKET} sample-renamed.ifc -y",
        sr_id="SR-062",
        slug="object-delete",
    )


# ── Batch operations ────────────────────────────────────────────


@pytest.mark.sr("SR-551")
def test_sr551_object_batch_copy(raps):
    raps.run(
        f"raps object batch-copy {BUCKET_NAME} {DEST_BUCKET} --keys sample.ifc",
        sr_id="SR-551",
        slug="object-batch-copy",
    )


@pytest.mark.sr("SR-552")
def test_sr552_object_batch_rename(raps):
    raps.run(
        f"raps object batch-rename {DEST_BUCKET} --from sample --to batch-renamed",
        sr_id="SR-552",
        slug="object-batch-rename",
    )


# ── Lifecycles ───────────────────────────────────────────────────


@pytest.mark.sr("SR-063")
@pytest.mark.lifecycle
def test_sr063_bucket_full_lifecycle(raps):
    bkt = f"sr-lifecycle-{_TS}"
    lc = raps.lifecycle("SR-063", "bucket-full-lifecycle", "Create -> list -> info -> delete")
    lc.step(f"raps bucket create -k {bkt} -p transient -r US")
    lc.step("raps bucket list")
    lc.step(f"raps bucket info {bkt}")
    lc.step(f"raps bucket delete {bkt} -y")
    lc.assert_all_passed()


@pytest.mark.sr("SR-064")
@pytest.mark.lifecycle
def test_sr064_object_full_lifecycle(raps):
    if not Path("./test-data/sample.ifc").is_file():
        pytest.skip("missing ./test-data/sample.ifc")
    lc = raps.lifecycle(
        "SR-064", "object-full-lifecycle", "Upload -> list -> info -> download -> delete"
    )
    lc.step(f"raps object upload {BUCKET_NAME} ./test-data/sample.ifc")
    lc.step(f"raps object list {BUCKET_NAME}")
    lc.step(f"raps object info {BUCKET_NAME} sample.ifc")
    lc.step(
        f"mkdir -p ./tmp && raps object download {BUCKET_NAME} sample.ifc --out-file ./tmp/raps-lifecycle-test.ifc",
    )
    lc.step(f"raps object delete {BUCKET_NAME} sample.ifc -y")
    lc.assert_all_passed()


@pytest.mark.sr("SR-065")
@pytest.mark.lifecycle
def test_sr065_batch_upload_lifecycle(raps):
    if not Path("./test-data").is_dir():
        pytest.skip("missing ./test-data/")
    bkt = f"sr-batch-{_TS}"
    # List a few files explicitly because `object upload <dir>` has Windows path issues
    files = [
        str(f).replace("\\", "/")
        for f in sorted(Path("./test-data").glob("*"))
        if f.is_file()
    ][:5]  # Limit to 5 files to avoid pagination issues
    if not files:
        pytest.skip("no files in ./test-data/")
    test_files = " ".join(files)
    lc = raps.lifecycle("SR-065", "batch-upload-lifecycle", "Batch upload -> list -> cleanup")
    lc.step(f"raps bucket create -k {bkt} -p transient -r US")
    lc.step(f"raps object upload-batch {bkt} {test_files}")
    lc.step(f"raps object list {bkt}")
    lc.step(f"raps bucket delete {bkt} -y")
    lc.assert_all_passed()


# ── Object audit ─────────────────────────────────────────────────


@pytest.mark.sr("SR-067")
def test_sr067_object_audit(raps):
    raps.run(
        f"raps object audit {BUCKET_NAME}",
        sr_id="SR-067",
        slug="object-audit",
    )


# ── Object tag ───────────────────────────────────────────────────


@pytest.mark.sr("SR-068")
def test_sr068_object_tag_set(raps):
    raps.run(
        f"raps object tag set {BUCKET_NAME} sample.ifc env=test owner=qa",
        sr_id="SR-068",
        slug="object-tag-set",
    )


@pytest.mark.sr("SR-069")
def test_sr069_object_tag_get(raps):
    raps.run(
        f"raps object tag get {BUCKET_NAME} sample.ifc",
        sr_id="SR-069",
        slug="object-tag-get",
    )


@pytest.mark.sr("SR-070")
def test_sr070_object_tag_delete(raps):
    raps.run(
        f"raps object tag delete {BUCKET_NAME} sample.ifc owner",
        sr_id="SR-070",
        slug="object-tag-delete",
    )


@pytest.mark.sr("SR-071")
def test_sr071_object_tag_search(raps):
    raps.run(
        f"raps object tag search {BUCKET_NAME} env=test",
        sr_id="SR-071",
        slug="object-tag-search",
    )


@pytest.mark.sr("SR-072")
@pytest.mark.lifecycle
def test_sr072_object_tag_lifecycle(raps):
    lc = raps.lifecycle("SR-072", "object-tag-lifecycle", "Set → get → search → delete")
    lc.step(f"raps object tag set {BUCKET_NAME} sample.ifc project=raps-test")
    lc.step(f"raps object tag get {BUCKET_NAME} sample.ifc")
    lc.step(f"raps object tag search {BUCKET_NAME} project=raps-test")
    lc.step(f"raps object tag delete {BUCKET_NAME} sample.ifc project")
    lc.assert_all_passed()
