# Section 19 — Raw API
# Runs: SR-280 through SR-284
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "19-api-raw" -Title "Raw API"

# -- Atomic commands -------------------------------------------------------

# SR-280: GET request
Invoke-Sample -Id "SR-280" -Slug "api-get" `
  -Command "raps api get `"/oss/v2/buckets`"" `
  -Expects "Expected: Makes GET request" `
  -Review "Review: Raw JSON; HTTP 200"

# SR-281: POST request
Invoke-Sample -Id "SR-281" -Slug "api-post" `
  -Command "raps api post `"/oss/v2/buckets`" --body '{`"bucketKey`":`"api-test`",`"policyKey`":`"transient`"}'" `
  -Expects "Expected: Creates via POST" `
  -Review "Review: HTTP 200; bucket created"

# SR-282: PUT request
Invoke-Sample -Id "SR-282" -Slug "api-put" `
  -Command "raps api put `"/project/v1/hubs/$env:HUB_ID/projects/$env:PID`" --body '{`"name`":`"Updated`"}'" `
  -Expects "Expected: PUT request" `
  -Review "Review: HTTP 200; resource updated"

# SR-283: PATCH request
Invoke-Sample -Id "SR-283" -Slug "api-patch" `
  -Command "raps api patch `"/issues/v1/containers/$env:CID/quality-issues/$env:IID`" --body '{`"title`":`"Patched`"}'" `
  -Expects "Expected: PATCH request" `
  -Review "Review: HTTP 200; field patched"

# SR-284: DELETE request
Invoke-Sample -Id "SR-284" -Slug "api-delete" `
  -Command "raps api delete `"/oss/v2/buckets/api-test`"" `
  -Expects "Expected: DELETE request" `
  -Review "Review: HTTP 200; resource deleted"

End-Section
