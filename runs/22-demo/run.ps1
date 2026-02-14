# Section 22 — Demo
# Runs: SR-310 through SR-313
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "22-demo" -Title "Demo"

# -- Atomic commands -------------------------------------------------------

# SR-310: Bucket lifecycle demo
Invoke-Sample -Id "SR-310" -Slug "demo-bucket-lifecycle" `
  -Command "raps demo bucket-lifecycle --prefix `"demo`" --skip-cleanup" `
  -Expects "Expected: Runs bucket lifecycle demo" `
  -Review "Review: Exit 0; creates, lists, and manages demo buckets"

# SR-311: Model pipeline demo
Invoke-Sample -Id "SR-311" -Slug "demo-model-pipeline" `
  -Command "raps demo model-pipeline --file ./test-data/sample.rvt --format svf2 --keep-bucket" `
  -Expects "Expected: Runs model pipeline demo" `
  -Review "Review: Exit 0; uploads, translates, and verifies model"

# SR-312: Data management demo
Invoke-Sample -Id "SR-312" -Slug "demo-data-management" `
  -Command "raps demo data-management --non-interactive --export ./dm-report.json" `
  -Expects "Expected: Runs data management demo" `
  -Review "Review: Exit 0; exports report to JSON"

# SR-313: Batch processing demo
Invoke-Sample -Id "SR-313" -Slug "demo-batch-processing" `
  -Command "raps demo batch-processing --input ./test-data/ --max-parallel 3 --format svf2 --skip-cleanup" `
  -Expects "Expected: Runs batch processing demo" `
  -Review "Review: Exit 0; processes multiple files in parallel"

End-Section
