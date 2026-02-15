#!/bin/bash
# Section 03 — Storage: Buckets + Objects
# Runs: SR-050 through SR-065
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "03-storage" "Storage: Buckets + Objects"

# ── Bucket atomics ───────────────────────────────────────────────

# SR-050: Create a new OSS bucket
run_sample "SR-050" "bucket-create" \
  "raps bucket create" \
  "Expected: Creates a new OSS bucket with transient retention" \
  "Review: Exit 0; output contains bucket key matching the name"

# SR-051: List all buckets
run_sample "SR-051" "bucket-list" \
  "raps bucket list" \
  "Expected: Lists all buckets in the account" \
  "Review: Table or list output with bucket keys and policies"

# SR-052: Get bucket details
run_sample "SR-052" "bucket-info" \
  "raps bucket info \$BUCKET_NAME" \
  "Expected: Shows detailed information for a specific bucket" \
  "Review: Contains bucket key, retention policy, and creation date"

# SR-053: Delete a bucket
run_sample "SR-053" "bucket-delete" \
  "raps bucket delete \$BUCKET_NAME" \
  "Expected: Deletes the specified bucket" \
  "Review: Exit 0; bucket no longer appears in list"

# ── Object atomics ───────────────────────────────────────────────

# SR-054: Upload a single file
run_sample "SR-054" "object-upload" \
  "raps object upload \$BUCKET ./test-data/sample.ifc" \
  "Expected: Uploads file to the specified bucket" \
  "Review: Exit 0; output contains object ID or URN"

# SR-055: Batch upload files from a directory
run_sample "SR-055" "object-upload-batch" \
  "raps object upload-batch \$BUCKET ./test-data/" \
  "Expected: Uploads all files from the directory" \
  "Review: Exit 0; shows uploaded file count"

# SR-056: List objects in a bucket
run_sample "SR-056" "object-list" \
  "raps object list \$BUCKET" \
  "Expected: Lists all objects in the bucket" \
  "Review: Contains uploaded file names and object keys"

# SR-057: Get object details
run_sample "SR-057" "object-info" \
  "raps object info \$BUCKET sample.ifc" \
  "Expected: Shows detailed information for a specific object" \
  "Review: Contains size, SHA hash, and content-type"

# SR-058: Download an object
run_sample "SR-058" "object-download" \
  "raps object download \$BUCKET sample.ifc -o ./downloads/" \
  "Expected: Downloads object to the specified directory" \
  "Review: File exists at output path; file size matches upload"

# SR-059: Generate a pre-signed URL
run_sample "SR-059" "object-signed-url" \
  "raps object signed-url \$BUCKET sample.ifc" \
  "Expected: Generates a pre-signed URL for the object" \
  "Review: Output contains an HTTPS URL with signature parameters"

# SR-060: Copy an object to another bucket
run_sample "SR-060" "object-copy" \
  "raps object copy \$BUCKET sample.ifc \$DEST_BUCKET sample-copy.ifc" \
  "Expected: Copies object to destination bucket with new key" \
  "Review: Exit 0; object exists in destination bucket"

# SR-061: Rename an object
run_sample "SR-061" "object-rename" \
  "raps object rename \$BUCKET sample-copy.ifc renamed.ifc" \
  "Expected: Renames object by changing its key" \
  "Review: Exit 0; old key gone, new key present in list"

# SR-062: Delete an object
run_sample "SR-062" "object-delete" \
  "raps object delete \$BUCKET renamed.ifc" \
  "Expected: Deletes the specified object" \
  "Review: Exit 0; object no longer appears in list"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-063: Bucket full CRUD lifecycle
lifecycle_start "SR-063" "bucket-full-lifecycle" "Clean CRUD cycle for buckets"
lifecycle_step 1 "raps bucket create"
lifecycle_step 2 "raps bucket list"
lifecycle_step 3 "raps bucket info lifecycle-test"
lifecycle_step 4 "raps bucket delete lifecycle-test"
lifecycle_step 5 "raps bucket list"
lifecycle_end

# SR-064: Object full lifecycle (upload through delete)
lifecycle_start "SR-064" "object-full-lifecycle" "Upload through delete"
lifecycle_step 1  "raps bucket create"
lifecycle_step 2  "raps object upload obj-lifecycle ./test-data/sample.ifc"
lifecycle_step 3  "raps object list obj-lifecycle"
lifecycle_step 4  "raps object info obj-lifecycle sample.ifc"
lifecycle_step 5  "raps object signed-url obj-lifecycle sample.ifc"
lifecycle_step 6  "raps object download obj-lifecycle sample.ifc -o ./tmp/"
lifecycle_step 7  "raps object rename obj-lifecycle sample.ifc moved.ifc"
lifecycle_step 8  "raps object list obj-lifecycle"
lifecycle_step 9  "raps object delete obj-lifecycle moved.ifc"
lifecycle_step 10 "raps bucket delete obj-lifecycle"
lifecycle_end

# SR-065: Batch upload lifecycle
lifecycle_start "SR-065" "batch-upload-lifecycle" "Batch upload test"
lifecycle_step 1 "raps generate files -c 3 -o ./batch-test/ --complexity simple"  # NOTE: raps bug - clap output flag conflict, exit 101 expected
lifecycle_step 2 "raps bucket create"
lifecycle_step 3 "raps object upload-batch batch-test ./batch-test/"
lifecycle_step 4 "raps object list batch-test"
lifecycle_step 5 "raps bucket delete batch-test"
lifecycle_end

section_end
