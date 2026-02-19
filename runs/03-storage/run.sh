#!/bin/bash
# Section 03 — Storage: Buckets + Objects
# Runs: SR-050 through SR-065
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "03-storage" "Storage: Buckets + Objects"
require_2leg_auth || { section_end; exit 0; }

# --- Pre-seed demo environment variables (override with real values) ---
: "${BUCKET_NAME:=sr-test-bucket-raps}"
: "${BUCKET:=$BUCKET_NAME}"
: "${DEST_BUCKET:=sr-backup-bucket-raps}"

# ── Bucket atomics ───────────────────────────────────────────────

# SR-050: Create a new OSS bucket
run_sample "SR-050" "bucket-create" \
  "raps bucket create $BUCKET_NAME --policy transient --region US || true" \
  "Expected: Bucket created or already exists (409)" \
  "Review: Exit 0 (created) or non-zero (conflict); bucket accessible"

# SR-051: List all buckets (fixed: concurrent regions + per-region timeout)
run_sample "SR-051" "bucket-list" \
  "raps bucket list" \
  "Expected: Lists buckets from US and EMEA regions" \
  "Review: Contains bucket names and policies"

# SR-052: Get bucket details
run_sample "SR-052" "bucket-info" \
  "raps bucket info $BUCKET_NAME || true" \
  "Expected: Bucket metadata displayed" \
  "Review: Shows bucket key, policy, creation date"

# SR-053: Delete a bucket (cleanup — may fail if objects exist)
# Deferred to end of section as cleanup
skip_sample "SR-053" "bucket-delete" "deferred to lifecycle cleanup"

# ── Object atomics ───────────────────────────────────────────────

# SR-054: Upload a single file (depends on test-data from 00-setup)
if [ -f ./test-data/sample.ifc ]; then
  run_sample "SR-054" "object-upload" \
    "raps object upload $BUCKET_NAME ./test-data/sample.ifc || true" \
    "Expected: File uploaded to bucket" \
    "Review: Exit 0; shows object key and size"
else
  skip_sample "SR-054" "object-upload" "missing ./test-data/sample.ifc (run 00-setup first)"
fi

# SR-055: Batch upload files from a directory
if [ -d ./test-data ]; then
  run_sample "SR-055" "object-upload-batch" \
    "raps object upload $BUCKET_NAME ./test-data/ || true" \
    "Expected: Multiple files uploaded" \
    "Review: Shows upload progress for each file"
else
  skip_sample "SR-055" "object-upload-batch" "missing ./test-data/ (run 00-setup first)"
fi

# SR-056: List objects in a bucket
run_sample "SR-056" "object-list" \
  "raps object list $BUCKET_NAME || true" \
  "Expected: Lists objects in bucket" \
  "Review: Contains object keys and sizes"

# SR-057: Get object details
run_sample "SR-057" "object-info" \
  "raps object info $BUCKET_NAME sample.ifc || true" \
  "Expected: Object metadata displayed" \
  "Review: Shows key, size, SHA1, content type"

# SR-058: Download an object
run_sample "SR-058" "object-download" \
  "mkdir -p ./tmp && raps object download $BUCKET_NAME sample.ifc -o ./tmp/raps-download-test.ifc || true" \
  "Expected: Object downloaded to local file" \
  "Review: File exists with correct size"

# SR-059: Generate a pre-signed URL
run_sample "SR-059" "object-signed-url" \
  "raps object signed-url $BUCKET_NAME sample.ifc || true" \
  "Expected: Pre-signed download URL generated" \
  "Review: Valid HTTPS URL with expiration"

# SR-060: Copy an object to another bucket
run_sample "SR-060" "object-copy" \
  "raps bucket create $DEST_BUCKET --policy transient --region US 2>/dev/null || true; raps object copy $BUCKET_NAME sample.ifc $DEST_BUCKET || true" \
  "Expected: Object copied to destination bucket" \
  "Review: Exit 0; object exists in both buckets"

# SR-061: Rename an object
run_sample "SR-061" "object-rename" \
  "raps object rename $DEST_BUCKET sample.ifc sample-renamed.ifc || true" \
  "Expected: Object renamed in bucket" \
  "Review: New key exists, old key removed"

# SR-062: Delete an object
run_sample "SR-062" "object-delete" \
  "raps object delete $DEST_BUCKET sample-renamed.ifc || true" \
  "Expected: Object deleted from bucket" \
  "Review: Exit 0; object no longer listed"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-063: Bucket full CRUD lifecycle
lifecycle_start "SR-063" "bucket-full-lifecycle" "Bucket create → list → info → delete"
lifecycle_step 1 "raps bucket create sr-lifecycle-bucket --policy transient --region US"
lifecycle_step 2 "raps bucket list"
lifecycle_step 3 "raps bucket info sr-lifecycle-bucket"
lifecycle_step 4 "raps bucket delete sr-lifecycle-bucket"
lifecycle_end

# SR-064: Object full lifecycle
if [ -f ./test-data/sample.ifc ]; then
  lifecycle_start "SR-064" "object-full-lifecycle" "Upload → list → info → download → delete"
  lifecycle_step 1 "raps object upload $BUCKET_NAME ./test-data/sample.ifc"
  lifecycle_step 2 "raps object list $BUCKET_NAME"
  lifecycle_step 3 "raps object info $BUCKET_NAME sample.ifc"
  lifecycle_step 4 "mkdir -p ./tmp && raps object download $BUCKET_NAME sample.ifc -o ./tmp/raps-lifecycle-test.ifc"
  lifecycle_step 5 "raps object delete $BUCKET_NAME sample.ifc"
  lifecycle_end
else
  skip_sample "SR-064" "object-full-lifecycle" "missing ./test-data/sample.ifc"
fi

# SR-065: Batch upload lifecycle
if [ -d ./test-data ]; then
  lifecycle_start "SR-065" "batch-upload-lifecycle" "Batch upload → list → cleanup"
  lifecycle_step 1 "raps bucket create sr-batch-bucket --policy transient --region US"
  lifecycle_step 2 "raps object upload sr-batch-bucket ./test-data/"
  lifecycle_step 3 "raps object list sr-batch-bucket"
  lifecycle_step 4 "raps bucket delete sr-batch-bucket"
  lifecycle_end
else
  skip_sample "SR-065" "batch-upload-lifecycle" "missing ./test-data/"
fi

# Cleanup
rm -f ./tmp/raps-download-test.ifc ./tmp/raps-lifecycle-test.ifc

section_end
