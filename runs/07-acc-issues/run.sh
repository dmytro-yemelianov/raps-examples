#!/bin/bash
# Section 07 — ACC Issues
# Runs: SR-130 through SR-141
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "07-acc-issues" "ACC Issues"

# ── Issue atomics ────────────────────────────────────────────────

# SR-130: List issues
run_sample "SR-130" "issue-list" \
  "raps issue list --project \$PROJECT_ID" \
  "Expected: Lists issues" \
  "Review: Contains IDs, titles, statuses"

# SR-131: List issue types
run_sample "SR-131" "issue-types" \
  "raps issue types --project \$PROJECT_ID" \
  "Expected: Lists issue types" \
  "Review: Contains type names"

# SR-132: Create an issue
run_sample "SR-132" "issue-create" \
  "raps issue create --project \$PROJECT_ID --title \"Cracked concrete on Level 2\" --type \$TYPE_ID --description \"Visible crack near column C4\"" \
  "Expected: Creates issue" \
  "Review: Exit 0; contains issue ID"

# SR-133: Update an issue
run_sample "SR-133" "issue-update" \
  "raps issue update --project \$PROJECT_ID --issue \$ISSUE_ID --title \"Cracked concrete on Level 2 - URGENT\" --assignee \$USER_ID" \
  "Expected: Updates issue" \
  "Review: Exit 0"

# SR-134: Transition issue status
run_sample "SR-134" "issue-transition" \
  "raps issue transition --project \$PROJECT_ID --issue \$ISSUE_ID --status \"in_review\"" \
  "Expected: Transitions status" \
  "Review: Exit 0"

# SR-135: Add a comment
run_sample "SR-135" "issue-comment-add" \
  "raps issue comment add --project \$PROJECT_ID --issue \$ISSUE_ID --body \"Structural engineer notified\"" \
  "Expected: Adds comment" \
  "Review: Exit 0"

# SR-136: List comments
run_sample "SR-136" "issue-comment-list" \
  "raps issue comment list --project \$PROJECT_ID --issue \$ISSUE_ID" \
  "Expected: Lists comments" \
  "Review: Contains bodies and authors"

# SR-137: Delete a comment
run_sample "SR-137" "issue-comment-delete" \
  "raps issue comment delete --project \$PROJECT_ID --issue \$ISSUE_ID --comment \$COMMENT_ID --yes" \
  "Expected: Deletes comment" \
  "Review: Exit 0"

# SR-138: List attachments
run_sample "SR-138" "issue-attachments" \
  "raps issue attachments --project \$PROJECT_ID --issue \$ISSUE_ID" \
  "Expected: Lists attachments" \
  "Review: List output"

# SR-139: Delete an issue
run_sample "SR-139" "issue-delete" \
  "raps issue delete --project \$PROJECT_ID --issue \$ISSUE_ID --yes" \
  "Expected: Deletes issue" \
  "Review: Exit 0"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-140: Field engineer reports and tracks a defect
lifecycle_start "SR-140" "issue-full-lifecycle" "Field engineer reports and tracks a defect"
lifecycle_step 1 "raps issue types --project \$PROJECT_ID"
lifecycle_step 2 "raps issue create --project \$PROJECT_ID --title \"Water damage in corridor B\" --type \$TYPE_ID"
lifecycle_step 3 "raps issue list --project \$PROJECT_ID"
lifecycle_step 4 "raps issue comment add --project \$PROJECT_ID --issue \$ID --body \"Photo attached via mobile\""
lifecycle_step 5 "raps issue comment list --project \$PROJECT_ID --issue \$ID"
lifecycle_step 6 "raps issue update --project \$PROJECT_ID --issue \$ID --assignee \$USER_ID"
lifecycle_step 7 "raps issue transition --project \$PROJECT_ID --issue \$ID --status \"in_review\""
lifecycle_step 8 "raps issue transition --project \$PROJECT_ID --issue \$ID --status \"closed\""
lifecycle_step 9 "raps issue delete --project \$PROJECT_ID --issue \$ID --yes"
lifecycle_end

# SR-141: QA lead triages multiple issues
lifecycle_start "SR-141" "issue-triage-workflow" "QA lead triages multiple issues"
lifecycle_step 1 "raps issue create --project \$PROJECT_ID --title \"Issue A\" --type \$TYPE"
lifecycle_step 2 "raps issue create --project \$PROJECT_ID --title \"Issue B\" --type \$TYPE"
lifecycle_step 3 "raps issue create --project \$PROJECT_ID --title \"Issue C\" --type \$TYPE"
lifecycle_step 4 "raps issue list --project \$PROJECT_ID --output json"
lifecycle_step 5 "raps issue update --project \$PROJECT_ID --issue \$A --assignee \$USER1"
lifecycle_step 6 "raps issue update --project \$PROJECT_ID --issue \$B --assignee \$USER2"
lifecycle_step 7 "raps issue transition --project \$PROJECT_ID --issue \$C --status \"void\""
lifecycle_step 8 "raps issue list --project \$PROJECT_ID"
lifecycle_end

section_end
