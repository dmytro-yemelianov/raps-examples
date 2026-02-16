#!/bin/bash
# Section 19 — Raw API
# Runs: SR-280 through SR-284
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "19-api-raw" "Raw API"
require_2leg_auth || { section_end; exit 0; }

# MSYS_NO_PATHCONV=1 prevents Git Bash from mangling /path/like/this into C:/Program Files/...

# SR-280: GET request — list DA engines (idempotent, always works)
run_sample "SR-280" "api-get" \
  "MSYS_NO_PATHCONV=1 raps api get /oss/v2/buckets || true" \
  "Expected: JSON response with buckets" \
  "Review: Contains bucket details"

# SR-281: POST request — create transient bucket for testing
run_sample "SR-281" "api-post" \
  "MSYS_NO_PATHCONV=1 raps api post \"/oss/v2/buckets\" -d '{\"bucketKey\":\"api-raw-test-raps\",\"policyKey\":\"transient\"}' || true" \
  "Expected: Creates a transient bucket or returns conflict" \
  "Review: 200/409 response with bucket details"

# SR-282: PUT request — attempt webhook update (idempotent, 404 expected)
run_sample "SR-282" "api-put" \
  "MSYS_NO_PATHCONV=1 raps api put \"/webhooks/v1/systems/data/events/dm.version.added/hooks/dummy-hook-id\" -d '{\"status\":\"inactive\"}' || true" \
  "Expected: PUT request sent (may return 404 for dummy ID)" \
  "Review: Request executed, API responded"

# SR-283: PATCH request — attempt issue update (idempotent, 4xx expected)
run_sample "SR-283" "api-patch" \
  "MSYS_NO_PATHCONV=1 raps api patch \"/construction/issues/v1/projects/dummy-project/issues/dummy-issue\" -d '{\"title\":\"updated\"}' || true" \
  "Expected: PATCH request sent (may return 4xx for dummy IDs)" \
  "Review: Request executed, API responded"

# SR-284: DELETE request — attempt to delete non-existent bucket (safe)
run_sample "SR-284" "api-delete" \
  "MSYS_NO_PATHCONV=1 raps api delete \"/oss/v2/buckets/api-raw-nonexistent-bucket\" || true" \
  "Expected: DELETE request sent (returns 404 for non-existent)" \
  "Review: Request executed, 404 response expected"

section_end
