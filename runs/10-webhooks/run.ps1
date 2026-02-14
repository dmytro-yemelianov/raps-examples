# Section 10 — Webhooks
# Runs: SR-180 through SR-188
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "10-webhooks" -Title "Webhooks"

# -- Webhook atomics ---------------------------------------------------

# SR-180: List event types
Invoke-Sample -Id "SR-180" -Slug "webhook-events" `
  -Command "raps webhook events" `
  -Expects "Expected: Lists event types" `
  -Review "Review: Contains event names"

# SR-181: Create a webhook
Invoke-Sample -Id "SR-181" -Slug "webhook-create" `
  -Command "raps webhook create --event `"dm.version.added`" --callback-url `"https://example.com/webhook`" --scope `"folder:$env:FOLDER_URN`"" `
  -Expects "Expected: Creates webhook" `
  -Review "Review: Exit 0; contains webhook ID"

# SR-182: List webhooks
Invoke-Sample -Id "SR-182" -Slug "webhook-list" `
  -Command "raps webhook list" `
  -Expects "Expected: Lists webhooks" `
  -Review "Review: Contains IDs and event types"

# SR-183: Get webhook details
Invoke-Sample -Id "SR-183" -Slug "webhook-get" `
  -Command "raps webhook get --id $env:WEBHOOK_ID" `
  -Expects "Expected: Shows details" `
  -Review "Review: Contains event, URL, scope"

# SR-184: Update a webhook
Invoke-Sample -Id "SR-184" -Slug "webhook-update" `
  -Command "raps webhook update --id $env:WEBHOOK_ID --status `"inactive`"" `
  -Expects "Expected: Updates webhook" `
  -Review "Review: Exit 0"

# SR-185: Test a webhook
Invoke-Sample -Id "SR-185" -Slug "webhook-test" `
  -Command "raps webhook test --id $env:WEBHOOK_ID" `
  -Expects "Expected: Sends test event" `
  -Review "Review: Exit 0"

# SR-186: Verify a webhook signature
Invoke-Sample -Id "SR-186" -Slug "webhook-verify-signature" `
  -Command "raps webhook verify-signature --payload '{`"event`":`"test`"}' --signature `"abc123`" --secret `"my-secret`"" `
  -Expects "Expected: Verifies signature" `
  -Review "Review: Valid/invalid result"

# SR-187: Delete a webhook
Invoke-Sample -Id "SR-187" -Slug "webhook-delete" `
  -Command "raps webhook delete --id $env:WEBHOOK_ID --yes" `
  -Expects "Expected: Deletes webhook" `
  -Review "Review: Exit 0"

# -- Lifecycles --------------------------------------------------------

# SR-188: DevOps sets up file change notifications
Start-Lifecycle -Id "SR-188" -Slug "webhook-subscription-lifecycle" -Description "DevOps sets up file change notifications"
Invoke-LifecycleStep -StepNum 1 -Command "raps webhook events"
Invoke-LifecycleStep -StepNum 2 -Command "raps webhook create --event `"dm.version.added`" --callback-url `"https://hooks.example.com/aps`" --scope `"folder:$env:URN`""
Invoke-LifecycleStep -StepNum 3 -Command "raps webhook list"
Invoke-LifecycleStep -StepNum 4 -Command "raps webhook get --id $env:ID"
Invoke-LifecycleStep -StepNum 5 -Command "raps webhook test --id $env:ID"
Invoke-LifecycleStep -StepNum 6 -Command "raps webhook update --id $env:ID --status `"inactive`""
Invoke-LifecycleStep -StepNum 7 -Command "raps webhook get --id $env:ID"
Invoke-LifecycleStep -StepNum 8 -Command "raps webhook delete --id $env:ID --yes"
End-Lifecycle

End-Section
