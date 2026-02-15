# Section 07 — ACC Issues
# Runs: SR-130 through SR-141
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "07-acc-issues" -Title "ACC Issues"

# -- Issue atomics -----------------------------------------------------

# SR-130: List issues
Invoke-Sample -Id "SR-130" -Slug "issue-list" `
  -Command "raps issue list $env:PROJECT_ID" `
  -Expects "Expected: Lists issues" `
  -Review "Review: Contains IDs, titles, statuses"

# SR-131: List issue types
Invoke-Sample -Id "SR-131" -Slug "issue-types" `
  -Command "raps issue types $env:PROJECT_ID" `
  -Expects "Expected: Lists issue types" `
  -Review "Review: Contains type names"

# SR-132: Create an issue
Invoke-Sample -Id "SR-132" -Slug "issue-create" `
  -Command "raps issue create $env:PROJECT_ID --title `"Cracked concrete on Level 2`" --description `"Visible crack near column C4`"" `
  -Expects "Expected: Creates issue" `
  -Review "Review: Exit 0; contains issue ID"

# SR-133: Update an issue
Invoke-Sample -Id "SR-133" -Slug "issue-update" `
  -Command "raps issue update $env:PROJECT_ID $env:ISSUE_ID --title `"Cracked concrete on Level 2 - URGENT`"" `
  -Expects "Expected: Updates issue" `
  -Review "Review: Exit 0"

# SR-134: Transition issue status
Invoke-Sample -Id "SR-134" -Slug "issue-transition" `
  -Command "raps issue transition $env:PROJECT_ID $env:ISSUE_ID --to `"in_review`"" `
  -Expects "Expected: Transitions status" `
  -Review "Review: Exit 0"

# SR-135: Add a comment
Invoke-Sample -Id "SR-135" -Slug "issue-comment-add" `
  -Command "raps issue comment add $env:PROJECT_ID $env:ISSUE_ID --body `"Structural engineer notified`"" `
  -Expects "Expected: Adds comment" `
  -Review "Review: Exit 0"

# SR-136: List comments
Invoke-Sample -Id "SR-136" -Slug "issue-comment-list" `
  -Command "raps issue comment list $env:PROJECT_ID $env:ISSUE_ID" `
  -Expects "Expected: Lists comments" `
  -Review "Review: Contains bodies and authors"

# SR-137: Delete a comment
Invoke-Sample -Id "SR-137" -Slug "issue-comment-delete" `
  -Command "raps issue comment delete $env:PROJECT_ID $env:ISSUE_ID $env:COMMENT_ID --yes" `
  -Expects "Expected: Deletes comment" `
  -Review "Review: Exit 0"

# SR-138: List attachments
Invoke-Sample -Id "SR-138" -Slug "issue-attachments" `
  -Command "raps issue attachments $env:PROJECT_ID $env:ISSUE_ID" `
  -Expects "Expected: Lists attachments" `
  -Review "Review: List output"

# SR-139: Delete an issue
Invoke-Sample -Id "SR-139" -Slug "issue-delete" `
  -Command "raps issue delete $env:PROJECT_ID $env:ISSUE_ID --yes" `
  -Expects "Expected: Deletes issue" `
  -Review "Review: Exit 0"

# -- Lifecycles --------------------------------------------------------

# SR-140: Field engineer reports and tracks a defect
Start-Lifecycle -Id "SR-140" -Slug "issue-full-lifecycle" -Description "Field engineer reports and tracks a defect"
Invoke-LifecycleStep -StepNum 1 -Command "raps issue types $env:PROJECT_ID"
Invoke-LifecycleStep -StepNum 2 -Command "raps issue create $env:PROJECT_ID --title `"Water damage in corridor B`""
Invoke-LifecycleStep -StepNum 3 -Command "raps issue list $env:PROJECT_ID"
Invoke-LifecycleStep -StepNum 4 -Command "raps issue comment add $env:PROJECT_ID $env:ID --body `"Photo attached via mobile`""
Invoke-LifecycleStep -StepNum 5 -Command "raps issue comment list $env:PROJECT_ID $env:ID"
Invoke-LifecycleStep -StepNum 6 -Command "raps issue update $env:PROJECT_ID $env:ID --title `"Water damage in corridor B - assigned`""
Invoke-LifecycleStep -StepNum 7 -Command "raps issue transition $env:PROJECT_ID $env:ID --to `"in_review`""
Invoke-LifecycleStep -StepNum 8 -Command "raps issue transition $env:PROJECT_ID $env:ID --to `"closed`""
Invoke-LifecycleStep -StepNum 9 -Command "raps issue delete $env:PROJECT_ID $env:ID --yes"
End-Lifecycle

# SR-141: QA lead triages multiple issues
Start-Lifecycle -Id "SR-141" -Slug "issue-triage-workflow" -Description "QA lead triages multiple issues"
Invoke-LifecycleStep -StepNum 1 -Command "raps issue create $env:PROJECT_ID --title `"Issue A`""
Invoke-LifecycleStep -StepNum 2 -Command "raps issue create $env:PROJECT_ID --title `"Issue B`""
Invoke-LifecycleStep -StepNum 3 -Command "raps issue create $env:PROJECT_ID --title `"Issue C`""
Invoke-LifecycleStep -StepNum 4 -Command "raps issue list $env:PROJECT_ID --output json"
Invoke-LifecycleStep -StepNum 5 -Command "raps issue update $env:PROJECT_ID $env:A --title `"Issue A - assigned`""
Invoke-LifecycleStep -StepNum 6 -Command "raps issue update $env:PROJECT_ID $env:B --title `"Issue B - assigned`""
Invoke-LifecycleStep -StepNum 7 -Command "raps issue transition $env:PROJECT_ID $env:C --to `"void`""
Invoke-LifecycleStep -StepNum 8 -Command "raps issue list $env:PROJECT_ID"
End-Lifecycle

End-Section
