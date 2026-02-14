#!/bin/bash
# Section 19 — Raw API
# Runs: SR-280 through SR-284
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "19-api-raw" "Raw API"

# ── Atomic commands ──────────────────────────────────────────────

# SR-280: GET request
run_sample "SR-280" "api-get" \
  "raps api get \"/oss/v2/buckets\"" \
  "Expected: Makes GET request" \
  "Review: Raw JSON; HTTP 200"

# SR-281: POST request
run_sample "SR-281" "api-post" \
  "raps api post \"/oss/v2/buckets\" --body '{\"bucketKey\":\"api-test\",\"policyKey\":\"transient\"}'" \
  "Expected: Creates via POST" \
  "Review: HTTP 200; bucket created"

# SR-282: PUT request
run_sample "SR-282" "api-put" \
  "raps api put \"/project/v1/hubs/\$HUB_ID/projects/\$PID\" --body '{\"name\":\"Updated\"}'" \
  "Expected: PUT request" \
  "Review: HTTP 200; resource updated"

# SR-283: PATCH request
run_sample "SR-283" "api-patch" \
  "raps api patch \"/issues/v1/containers/\$CID/quality-issues/\$IID\" --body '{\"title\":\"Patched\"}'" \
  "Expected: PATCH request" \
  "Review: HTTP 200; field patched"

# SR-284: DELETE request
run_sample "SR-284" "api-delete" \
  "raps api delete \"/oss/v2/buckets/api-test\"" \
  "Expected: DELETE request" \
  "Review: HTTP 200; resource deleted"

section_end
