# Section 18 — Pipelines
# Runs: SR-270 through SR-273
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "18-pipelines" -Title "Pipelines"

# -- Atomic commands -------------------------------------------------------

# SR-270: Generate sample pipeline YAML
Invoke-Sample -Id "SR-270" -Slug "pipeline-sample" `
  -Command "raps pipeline sample --output ./sample-pipeline.yaml" `
  -Expects "Expected: Generates sample YAML" `
  -Review "Review: File created with valid pipeline structure"

# SR-271: Validate pipeline file
Invoke-Sample -Id "SR-271" -Slug "pipeline-validate" `
  -Command "raps pipeline validate --file ./sample-pipeline.yaml" `
  -Expects "Expected: Validates structure" `
  -Review "Review: Exit 0; reports valid or lists errors"

# SR-272: Run a pipeline
Invoke-Sample -Id "SR-272" -Slug "pipeline-run" `
  -Command "raps pipeline run --file ./sample-pipeline.yaml" `
  -Expects "Expected: Executes pipeline" `
  -Review "Review: Exit 0; shows step-by-step progress"

# -- Lifecycles ------------------------------------------------------------

# SR-273: DevOps creates and runs pipeline
Start-Lifecycle -Id "SR-273" -Slug "pipeline-author-and-run" -Description "DevOps creates and runs pipeline"
Invoke-LifecycleStep -StepNum 1 -Command "raps pipeline sample --output ./my-pipeline.yaml"
Invoke-LifecycleStep -StepNum 2 -Command "raps pipeline validate --file ./my-pipeline.yaml"
Invoke-LifecycleStep -StepNum 3 -Command "raps pipeline run --file ./my-pipeline.yaml"
End-Lifecycle

End-Section
