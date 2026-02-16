#!/bin/bash
# Section 05 — Model Derivative / Translation
# Runs: SR-090 through SR-101
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "05-model-derivative" "Model Derivative / Translation"
require_2leg_auth || { section_end; exit 0; }

# --- Pre-seed demo environment variables (override with real values) ---
# Construct a URN from bucket+object if we have uploaded data
: "${BUCKET_NAME:=sr-test-bucket-raps}"
: "${OBJECT_KEY:=sample.ifc}"

# Generate URN from bucket/object key (base64url of urn:adsk.objects:os.object:bucket/key)
COMPUTED_URN=$(python3 -c "import base64; print(base64.urlsafe_b64encode(b'urn:adsk.objects:os.object:$BUCKET_NAME/$OBJECT_KEY').decode().rstrip('='))" 2>/dev/null || echo "dXJuOmFkc2sub2JqZWN0czpvcy5vYmplY3Q6ZGVtby1idWNrZXQvc2FtcGxlLmlmYw")
: "${URN:=$COMPUTED_URN}"
: "${OBJECT_URN:=$URN}"
: "${ITEM_ID:=urn:adsk.wipprod:dm.lineage:demo-item-001}"
: "${FOLDER_ID:=urn:adsk.wipprod:fs.folder:co.demo-folder-001}"

# ── Atomic commands ──────────────────────────────────────────────

# SR-090: Start a translation job (may fail with invalid URN but executes)
run_sample "SR-090" "translate-start" \
  "raps translate start $URN --format svf2 || true" \
  "Expected: Translation job submitted (or error for invalid URN)" \
  "Review: API call executed; 200 or 4xx response"

# SR-091: Check translation status
run_sample "SR-091" "translate-status" \
  "raps translate status $URN || true" \
  "Expected: Translation status returned (or error for no job)" \
  "Review: Shows status or 404 if no translation exists"

# SR-092: Get translation manifest
run_sample "SR-092" "translate-manifest" \
  "raps translate manifest $URN || true" \
  "Expected: Manifest data or error" \
  "Review: JSON manifest or 404 response"

# SR-093: List available derivatives
run_sample "SR-093" "translate-derivatives" \
  "raps translate derivatives $URN || true" \
  "Expected: List of derivative outputs or error" \
  "Review: Shows available formats or 404"

# SR-094: Download derivatives
run_sample "SR-094" "translate-download" \
  "raps translate download $URN -o /tmp/raps-derivative-test/ || true" \
  "Expected: Downloads derivative files or error" \
  "Review: Files downloaded or 404 for no derivatives"

# SR-095: List translation presets
run_sample "SR-095" "translate-preset-list" \
  "raps translate preset list" \
  "Expected: Lists all saved translation presets" \
  "Review: Table or list with preset names and target formats"

# SR-096: Create a translation preset
run_sample "SR-096" "translate-preset-create" \
  "raps translate preset create \"svf2-default\" -f svf2" \
  "Expected: Creates a reusable translation preset" \
  "Review: Exit 0; output confirms preset saved with name and format"

# SR-097: Show a translation preset
run_sample "SR-097" "translate-preset-show" \
  "raps translate preset show \"svf2-default\"" \
  "Expected: Displays details of the specified preset" \
  "Review: Contains preset name, target format, and configuration"

# SR-098: Use a preset for translation (may fail with invalid URN but executes)
run_sample "SR-098" "translate-preset-use" \
  "raps translate start $URN --preset \"svf2-default\" || true" \
  "Expected: Translation started with preset or error for invalid URN" \
  "Review: API call executed"

# SR-099: Delete a translation preset
run_sample "SR-099" "translate-preset-delete" \
  "raps translate preset delete \"svf2-default\"" \
  "Expected: Deletes the specified preset" \
  "Review: Exit 0; preset no longer appears in list"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-100: Full translation pipeline
if [ -f ./test-data/sample.rvt ]; then
  lifecycle_start "SR-100" "translate-full-pipeline" "Upload → translate → poll → download"
  lifecycle_step 1 "raps object upload $BUCKET_NAME ./test-data/sample.rvt || true"
  RVT_URN=$(python3 -c "import base64; print(base64.urlsafe_b64encode(b'urn:adsk.objects:os.object:$BUCKET_NAME/sample.rvt').decode().rstrip('='))" 2>/dev/null || echo "$URN")
  lifecycle_step 2 "raps translate start $RVT_URN --format svf2 || true"
  lifecycle_step 3 "raps translate status $RVT_URN || true"
  lifecycle_step 4 "raps translate manifest $RVT_URN || true"
  lifecycle_end
else
  skip_sample "SR-100" "translate-full-pipeline" "missing ./test-data/sample.rvt"
fi

# SR-101: Preset CRUD + use lifecycle
lifecycle_start "SR-101" "translate-preset-lifecycle" "Preset CRUD + use"
lifecycle_step 1 "raps translate preset create \"ifc-to-svf\" -f svf2"
lifecycle_step 2 "raps translate preset list"
lifecycle_step 3 "raps translate preset show \"ifc-to-svf\""
lifecycle_step 4 "raps translate preset delete \"ifc-to-svf\""
lifecycle_end

# Cleanup
rm -rf /tmp/raps-derivative-test/

section_end
