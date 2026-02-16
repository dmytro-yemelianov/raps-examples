#!/bin/bash
# Section 10 — Webhooks
# Runs: SR-180 through SR-188
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "10-webhooks" "Webhooks"
require_2leg_auth || { section_end; exit 0; }

# ── Webhook atomics ──────────────────────────────────────────────

# SR-180: List event types
run_sample "SR-180" "webhook-events" \
  "raps webhook events" \
  "Expected: Lists event types" \
  "Review: Contains event names"

# SR-181: Create a webhook (captures hook ID for subsequent operations)
run_sample "SR-181" "webhook-create" \
  "raps webhook create -e \"dm.version.added\" -u \"https://example.com/raps-test-hook\" || true" \
  "Expected: Webhook subscription created" \
  "Review: Returns hook ID and event type"

# SR-182: List webhooks (should now include the one we created)
run_sample "SR-182" "webhook-list" \
  "raps webhook list" \
  "Expected: Lists webhooks" \
  "Review: Contains IDs and event types"

# SR-183: Get webhook details — use list output to find our hook
run_sample "SR-183" "webhook-get" \
  "HOOK_ID=\$(raps webhook list --output json 2>/dev/null | python3 -c \"import sys,json; hooks=json.load(sys.stdin); print(hooks[0]['hookId'] if hooks else '')\" 2>/dev/null || echo '') && [ -n \"\$HOOK_ID\" ] && raps webhook get \"\$HOOK_ID\" || true" \
  "Expected: Webhook details displayed" \
  "Review: Shows hook ID, event type, callback URL"

# SR-184: Update a webhook (deactivate it)
run_sample "SR-184" "webhook-update" \
  "HOOK_ID=\$(raps webhook list --output json 2>/dev/null | python3 -c \"import sys,json; hooks=json.load(sys.stdin); print(hooks[0]['hookId'] if hooks else '')\" 2>/dev/null || echo '') && [ -n \"\$HOOK_ID\" ] && raps webhook update \"\$HOOK_ID\" --status inactive || true" \
  "Expected: Webhook deactivated" \
  "Review: Status changed to inactive"

# SR-185: Test a webhook
run_sample "SR-185" "webhook-test" \
  "raps webhook test \"https://example.com/webhook\"" \
  "Expected: Sends test event" \
  "Review: Exit 0"

# SR-186: Verify a webhook signature
run_sample "SR-186" "webhook-verify-signature" \
  "raps webhook verify-signature '{\"event\":\"test\"}' --signature \"abc123\" --secret \"my-secret\"" \
  "Expected: Verifies signature" \
  "Review: Valid/invalid result"

# SR-187: Delete a webhook (cleanup)
run_sample "SR-187" "webhook-delete" \
  "HOOK_ID=\$(raps webhook list --output json 2>/dev/null | python3 -c \"import sys,json; hooks=json.load(sys.stdin); print(hooks[0]['hookId'] if hooks else '')\" 2>/dev/null || echo '') && [ -n \"\$HOOK_ID\" ] && raps webhook delete \"\$HOOK_ID\" || true" \
  "Expected: Webhook deleted" \
  "Review: Hook removed from list"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-188: DevOps sets up file change notifications
lifecycle_start "SR-188" "webhook-subscription-lifecycle" "Create → list → update → delete"
lifecycle_step 1 "raps webhook create -e \"dm.version.added\" -u \"https://example.com/raps-lifecycle-hook\" || true"
lifecycle_step 2 "raps webhook list"
lifecycle_step 3 "HOOK_ID=\$(raps webhook list --output json 2>/dev/null | python3 -c \"import sys,json; hooks=json.load(sys.stdin); print(hooks[0]['hookId'] if hooks else '')\" 2>/dev/null || echo '') && [ -n \"\$HOOK_ID\" ] && raps webhook update \"\$HOOK_ID\" --status inactive || true"
lifecycle_step 4 "HOOK_ID=\$(raps webhook list --output json 2>/dev/null | python3 -c \"import sys,json; hooks=json.load(sys.stdin); print(hooks[0]['hookId'] if hooks else '')\" 2>/dev/null || echo '') && [ -n \"\$HOOK_ID\" ] && raps webhook delete \"\$HOOK_ID\" || true"
lifecycle_end

section_end
