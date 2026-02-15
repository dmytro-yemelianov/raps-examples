# Section 03 — Storage: Buckets + Objects
# Runs: SR-050 through SR-065
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "03-storage" -Title "Storage: Buckets + Objects"

# --- Pre-seed demo environment variables (override with real values) ---
if (-not $env:BUCKET_NAME) { $env:BUCKET_NAME = "demo-test-bucket-raps" }
if (-not $env:BUCKET) { $env:BUCKET = "demo-test-bucket-raps" }
if (-not $env:DEST_BUCKET) { $env:DEST_BUCKET = "demo-backup-bucket-raps" }

# -- Bucket atomics ----------------------------------------------------

# SR-050: Create a new OSS bucket
Invoke-Sample -Id "SR-050" -Slug "bucket-create" `
  -Command "raps bucket create" `
  -Expects "Expected: Creates a new OSS bucket with transient retention" `
  -Review "Review: Exit 0; output contains bucket key matching the name"

# SR-051: List all buckets
Invoke-Sample -Id "SR-051" -Slug "bucket-list" `
  -Command "raps bucket list" `
  -Expects "Expected: Lists all buckets in the account" `
  -Review "Review: Table or list output with bucket keys and policies"

# SR-052: Get bucket details
Invoke-Sample -Id "SR-052" -Slug "bucket-info" `
  -Command "raps bucket info $env:BUCKET_NAME" `
  -Expects "Expected: Shows detailed information for a specific bucket" `
  -Review "Review: Contains bucket key, retention policy, and creation date"

# SR-053: Delete a bucket
Invoke-Sample -Id "SR-053" -Slug "bucket-delete" `
  -Command "raps bucket delete $env:BUCKET_NAME" `
  -Expects "Expected: Deletes the specified bucket" `
  -Review "Review: Exit 0; bucket no longer appears in list"

# -- Object atomics ----------------------------------------------------

# SR-054: Upload a single file
Invoke-Sample -Id "SR-054" -Slug "object-upload" `
  -Command "raps object upload $env:BUCKET ./test-data/sample.ifc" `
  -Expects "Expected: Uploads file to the specified bucket" `
  -Review "Review: Exit 0; output contains object ID or URN"

# SR-055: Batch upload files from a directory
Invoke-Sample -Id "SR-055" -Slug "object-upload-batch" `
  -Command "raps object upload-batch $env:BUCKET ./test-data/" `
  -Expects "Expected: Uploads all files from the directory" `
  -Review "Review: Exit 0; shows uploaded file count"

# SR-056: List objects in a bucket
Invoke-Sample -Id "SR-056" -Slug "object-list" `
  -Command "raps object list $env:BUCKET" `
  -Expects "Expected: Lists all objects in the bucket" `
  -Review "Review: Contains uploaded file names and object keys"

# SR-057: Get object details
Invoke-Sample -Id "SR-057" -Slug "object-info" `
  -Command "raps object info $env:BUCKET sample.ifc" `
  -Expects "Expected: Shows detailed information for a specific object" `
  -Review "Review: Contains size, SHA hash, and content-type"

# SR-058: Download an object
Invoke-Sample -Id "SR-058" -Slug "object-download" `
  -Command "raps object download $env:BUCKET sample.ifc -o ./downloads/" `
  -Expects "Expected: Downloads object to the specified directory" `
  -Review "Review: File exists at output path; file size matches upload"

# SR-059: Generate a pre-signed URL
Invoke-Sample -Id "SR-059" -Slug "object-signed-url" `
  -Command "raps object signed-url $env:BUCKET sample.ifc" `
  -Expects "Expected: Generates a pre-signed URL for the object" `
  -Review "Review: Output contains an HTTPS URL with signature parameters"

# SR-060: Copy an object to another bucket
Invoke-Sample -Id "SR-060" -Slug "object-copy" `
  -Command "raps object copy --source-bucket $env:BUCKET --source-object sample.ifc --dest-bucket $env:DEST_BUCKET --dest-object sample-copy.ifc" `
  -Expects "Expected: Copies object to destination bucket with new key" `
  -Review "Review: Exit 0; object exists in destination bucket"

# SR-061: Rename an object
Invoke-Sample -Id "SR-061" -Slug "object-rename" `
  -Command "raps object rename $env:BUCKET sample-copy.ifc --new-key renamed.ifc" `
  -Expects "Expected: Renames object by changing its key" `
  -Review "Review: Exit 0; old key gone, new key present in list"

# SR-062: Delete an object
Invoke-Sample -Id "SR-062" -Slug "object-delete" `
  -Command "raps object delete $env:BUCKET renamed.ifc" `
  -Expects "Expected: Deletes the specified object" `
  -Review "Review: Exit 0; object no longer appears in list"

# -- Lifecycles --------------------------------------------------------

# SR-063: Bucket full CRUD lifecycle
Start-Lifecycle -Id "SR-063" -Slug "bucket-full-lifecycle" -Description "Clean CRUD cycle for buckets"
Invoke-LifecycleStep -StepNum 1 -Command "raps bucket create"
Invoke-LifecycleStep -StepNum 2 -Command "raps bucket list"
Invoke-LifecycleStep -StepNum 3 -Command "raps bucket info lifecycle-test"
Invoke-LifecycleStep -StepNum 4 -Command "raps bucket delete lifecycle-test"
Invoke-LifecycleStep -StepNum 5 -Command "raps bucket list"
End-Lifecycle

# SR-064: Object full lifecycle (upload through delete)
Start-Lifecycle -Id "SR-064" -Slug "object-full-lifecycle" -Description "Upload through delete"
Invoke-LifecycleStep -StepNum 1  -Command "raps bucket create"
Invoke-LifecycleStep -StepNum 2  -Command "raps object upload obj-lifecycle ./test-data/sample.ifc"
Invoke-LifecycleStep -StepNum 3  -Command "raps object list obj-lifecycle"
Invoke-LifecycleStep -StepNum 4  -Command "raps object info obj-lifecycle sample.ifc"
Invoke-LifecycleStep -StepNum 5  -Command "raps object signed-url obj-lifecycle sample.ifc"
Invoke-LifecycleStep -StepNum 6  -Command "raps object download obj-lifecycle sample.ifc -o ./tmp/"
Invoke-LifecycleStep -StepNum 7  -Command "raps object rename obj-lifecycle sample.ifc --new-key moved.ifc"
Invoke-LifecycleStep -StepNum 8  -Command "raps object list obj-lifecycle"
Invoke-LifecycleStep -StepNum 9  -Command "raps object delete obj-lifecycle moved.ifc"
Invoke-LifecycleStep -StepNum 10 -Command "raps bucket delete obj-lifecycle"
End-Lifecycle

# SR-065: Batch upload lifecycle
Start-Lifecycle -Id "SR-065" -Slug "batch-upload-lifecycle" -Description "Batch upload test"
Invoke-LifecycleStep -StepNum 1 -Command "raps generate files -c 3 -o ./batch-test/ --complexity simple"
Invoke-LifecycleStep -StepNum 2 -Command "raps bucket create"
Invoke-LifecycleStep -StepNum 3 -Command "raps object upload-batch batch-test ./batch-test/"
Invoke-LifecycleStep -StepNum 4 -Command "raps object list batch-test"
Invoke-LifecycleStep -StepNum 5 -Command "raps bucket delete batch-test"
End-Lifecycle

End-Section
