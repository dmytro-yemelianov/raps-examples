#!/bin/bash
# Section 07 — ACC Issues
# Runs: SR-130 through SR-141
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "07-acc-issues" "ACC Issues"
require_3leg_auth || { section_end; exit 0; }

# --- Pre-seed demo environment variables (override with real values) ---
: "${PROJECT_ID:=${RAPS_PROJECT_ID:-demo-project-001}}"
: "${ISSUE_ID:=8d5b8b2c-3a1e-467c-9f1b-6c2d9a8e1f5b}"
: "${COMMENT_ID:=cmt-demo-001}"
: "${ID:=8d5b8b2c-3a1e-467c-9f1b-6c2d9a8e1f5b}"
: "${A:=issue-a-demo-001}"
: "${B:=issue-b-demo-002}"
: "${C:=issue-c-demo-003}"

# ── Issue atomics ────────────────────────────────────────────────

# SR-130: List issues
run_sample "SR-130" "issue-list" \
  "raps issue list $PROJECT_ID || true" \
  "Expected: Lists issues" \
  "Review: Contains IDs, titles, statuses"

# SR-131: List issue types
run_sample "SR-131" "issue-types" \
  "raps issue types $PROJECT_ID || true" \
  "Expected: Lists issue types" \
  "Review: Contains type names"

# SR-132: Create an issue
run_sample "SR-132" "issue-create" \
  "raps issue create $PROJECT_ID --title \"Cracked concrete on Level 2\" --description \"Visible crack near column C4\" || true" \
  "Expected: Creates issue" \
  "Review: Exit 0; contains issue ID"

# SR-133: Update an issue
run_sample "SR-133" "issue-update" \
  "raps issue update $PROJECT_ID $ISSUE_ID --title \"Cracked concrete on Level 2 - URGENT\" || true" \
  "Expected: Updates issue" \
  "Review: Exit 0"

# SR-134: Transition issue status
run_sample "SR-134" "issue-transition" \
  "raps issue transition $PROJECT_ID $ISSUE_ID --to \"in_review\" || true" \
  "Expected: Transitions status" \
  "Review: Exit 0"

# SR-135: Add a comment
run_sample "SR-135" "issue-comment-add" \
  "raps issue comment add $PROJECT_ID $ISSUE_ID --body \"Structural engineer notified\" || true" \
  "Expected: Adds comment" \
  "Review: Exit 0"

# SR-136: List comments
run_sample "SR-136" "issue-comment-list" \
  "raps issue comment list $PROJECT_ID $ISSUE_ID || true" \
  "Expected: Lists comments" \
  "Review: Contains bodies and authors"

# SR-137: Delete a comment
run_sample "SR-137" "issue-comment-delete" \
  "raps issue comment delete $PROJECT_ID $ISSUE_ID $COMMENT_ID --yes || true" \
  "Expected: Deletes comment" \
  "Review: Exit 0"

# SR-138: List attachments
run_sample "SR-138" "issue-attachments" \
  "raps issue attachments $PROJECT_ID $ISSUE_ID || true" \
  "Expected: Lists attachments" \
  "Review: List output"

# SR-139: Delete an issue
run_sample "SR-139" "issue-delete" \
  "raps issue delete $PROJECT_ID $ISSUE_ID --yes || true" \
  "Expected: Deletes issue" \
  "Review: Exit 0"

# ── Lifecycles ───────────────────────────────────────────────────

# SR-140: Field engineer reports and tracks a defect
lifecycle_start "SR-140" "issue-full-lifecycle" "Field engineer reports and tracks a defect"
lifecycle_step 1 "raps issue types $PROJECT_ID || true"
lifecycle_step 2 "raps issue create $PROJECT_ID --title \"Water damage in corridor B\" || true"
lifecycle_step 3 "raps issue list $PROJECT_ID || true"
lifecycle_step 4 "raps issue comment add $PROJECT_ID $ID --body \"Photo attached via mobile\" || true"
lifecycle_step 5 "raps issue comment list $PROJECT_ID $ID || true"
lifecycle_step 6 "raps issue update $PROJECT_ID $ID --title \"Water damage in corridor B - assigned\" || true"
lifecycle_step 7 "raps issue transition $PROJECT_ID $ID --to \"in_review\" || true"
lifecycle_step 8 "raps issue transition $PROJECT_ID $ID --to \"closed\" || true"
lifecycle_step 9 "raps issue delete $PROJECT_ID $ID --yes || true"
lifecycle_end

# SR-141: QA lead triages multiple issues
lifecycle_start "SR-141" "issue-triage-workflow" "QA lead triages multiple issues"
lifecycle_step 1 "raps issue create $PROJECT_ID --title \"Issue A\" || true"
lifecycle_step 2 "raps issue create $PROJECT_ID --title \"Issue B\" || true"
lifecycle_step 3 "raps issue create $PROJECT_ID --title \"Issue C\" || true"
lifecycle_step 4 "raps issue list $PROJECT_ID --output json || true"
lifecycle_step 5 "raps issue update $PROJECT_ID $A --title \"Issue A - assigned\" || true"
lifecycle_step 6 "raps issue update $PROJECT_ID $B --title \"Issue B - assigned\" || true"
lifecycle_step 7 "raps issue transition $PROJECT_ID $C --to \"void\" || true"
lifecycle_step 8 "raps issue list $PROJECT_ID || true"
lifecycle_end

section_end
