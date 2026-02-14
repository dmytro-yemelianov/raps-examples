#!/bin/bash
# Section 10 — Webhooks
# Runs: SR-180 through SR-188
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "10-webhooks" "Webhooks"

# ── Webhook atomics ──────────────────────────────────────────────

# SR-180: List event types
run_sample "SR-180" "webhook-events" \
  "raps webhook events" \
  "Expected: Lists event types" \
  "Review: Contains event names"

# SR-181: Create a webhook
run_sample "SR-181" "webhook-create" \
  "raps webhook create --event \"dm.version.added\" --callback-url \"https://example.com/webhook\" --scope \"folder:\$FOLDER_URN\"" \
  "Expected: Creates webhook" \
  "Review: Exit 0; contains webhook ID"

# SR-182: List webhooks
run_sample "SR-182" "webhook-list" \
  "raps webhook list" \
  "Expected: Lists webhooks" \
  "Review: Contains IDs and event types"

# SR-183: Get webhook details
run_sample "SR-183" "webhook-get" \
  "raps webhook get --id \$WEBHOOK_ID" \
  "Expected: Shows details" \
  "Review: Contains event, URL, scope"

# SR-184: Update a webhook
run_sample "SR-184" "webhook-update" \
  "raps webhook update --id \$WEBHOOK_ID --status \"inactive\"" \
  "Expected: Updates webhook" \
  "Review: Exit 0"

# SR-185: Test a webhook
run_sample "SR-185" "webhook-test" \
  "raps webhook test --id \$WEBHOOK_ID" \
  "Expected: Sends test event" \
  "Review: Exit 0"

# SR-186: Verify a webhook signature
run_sample "SR-186" "webhook-verify-signature" \
  "raps webhook verify-signature --payload '{\"event\":\"test\"}' --signature \"abc123\" --secret \"my-secret\"" \
  "Expected: Verifies signature" \
  "Review: Valid/invalid result"

# SR-187: Delete a webhook
run_sample "SR-187" "webhook-delete" \
  "raps webhook delete --id \$WEBHOOK_ID --yes" \
  "Expected: Deletes webhook" \
  "Review: Exit 0"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-188: DevOps sets up file change notifications
lifecycle_start "SR-188" "webhook-subscription-lifecycle" "DevOps sets up file change notifications"
lifecycle_step 1 "raps webhook events"
lifecycle_step 2 "raps webhook create --event \"dm.version.added\" --callback-url \"https://hooks.example.com/aps\" --scope \"folder:\$URN\""
lifecycle_step 3 "raps webhook list"
lifecycle_step 4 "raps webhook get --id \$ID"
lifecycle_step 5 "raps webhook test --id \$ID"
lifecycle_step 6 "raps webhook update --id \$ID --status \"inactive\""
lifecycle_step 7 "raps webhook get --id \$ID"
lifecycle_step 8 "raps webhook delete --id \$ID --yes"
lifecycle_end

section_end
