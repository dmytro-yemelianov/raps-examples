# Section 20 — Generation
# Runs: SR-290 through SR-291
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "20-generation" -Title "Generation"

# -- Atomic commands -------------------------------------------------------

# SR-290: Generate simple files
# NOTE: raps bug - clap output flag conflict, exit 101 expected
Invoke-Sample -Id "SR-290" -Slug "generate-files-simple" `
  -Command "raps generate files -c 1 -o ./gen-simple/ --complexity simple" `
  -Expects "Expected: Generates simple files" `
  -Review "Review: Exit 0; files created in output directory"

# SR-291: Generate complex files
# NOTE: raps bug - clap output flag conflict, exit 101 expected
Invoke-Sample -Id "SR-291" -Slug "generate-files-complex" `
  -Command "raps generate files -c 10 -o ./gen-complex/ --complexity complex" `
  -Expects "Expected: Generates complex files" `
  -Review "Review: Exit 0; 10 files created in output directory"

End-Section
