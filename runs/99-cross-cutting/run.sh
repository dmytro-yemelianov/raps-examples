#!/bin/bash
# Section 99 — Cross-Cutting
# Runs: SR-500 through SR-544
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

section_start "99-cross-cutting" "Cross-Cutting"

# --- Pre-seed demo environment variables (override with real values) ---
: "${PROJECT_ID:=b.demo-project-001}"
: "${ACCOUNT_ID:=demo-account-001}"

# ── Output format matrix: bucket list ────────────────────────────

# SR-500: bucket list --output table
run_sample "SR-500" "bucket-list-table" \
  "raps bucket list --output table" \
  "Expected: Table-formatted bucket list" \
  "Review: Aligned columns with headers"

# SR-501: bucket list --output json
run_sample "SR-501" "bucket-list-json" \
  "raps bucket list --output json" \
  "Expected: JSON-formatted bucket list" \
  "Review: Valid JSON array"

# SR-502: bucket list --output yaml
run_sample "SR-502" "bucket-list-yaml" \
  "raps bucket list --output yaml" \
  "Expected: YAML-formatted bucket list" \
  "Review: Valid YAML document"

# SR-503: bucket list --output csv
run_sample "SR-503" "bucket-list-csv" \
  "raps bucket list --output csv" \
  "Expected: CSV-formatted bucket list" \
  "Review: Header row followed by data rows"

# SR-504: bucket list --output plain
run_sample "SR-504" "bucket-list-plain" \
  "raps bucket list --output plain" \
  "Expected: Plain-text bucket list" \
  "Review: Simple text output"

# ── Output format matrix: issue list ─────────────────────────────

# SR-505: issue list --output table
run_sample "SR-505" "issue-list-table" \
  "raps issue list \$PROJECT_ID --output table" \
  "Expected: Table-formatted issue list" \
  "Review: Aligned columns with headers"

# SR-506: issue list --output json
run_sample "SR-506" "issue-list-json" \
  "raps issue list \$PROJECT_ID --output json" \
  "Expected: JSON-formatted issue list" \
  "Review: Valid JSON array"

# SR-507: issue list --output yaml
run_sample "SR-507" "issue-list-yaml" \
  "raps issue list \$PROJECT_ID --output yaml" \
  "Expected: YAML-formatted issue list" \
  "Review: Valid YAML document"

# SR-508: issue list --output csv
run_sample "SR-508" "issue-list-csv" \
  "raps issue list \$PROJECT_ID --output csv" \
  "Expected: CSV-formatted issue list" \
  "Review: Header row followed by data rows"

# SR-509: issue list --output plain
run_sample "SR-509" "issue-list-plain" \
  "raps issue list \$PROJECT_ID --output plain" \
  "Expected: Plain-text issue list" \
  "Review: Simple text output"

# ── Output format matrix: admin user list ────────────────────────

# SR-510: admin user list --output table
run_sample "SR-510" "admin-user-list-table" \
  "raps admin user list -a \$ACCOUNT_ID --output table" \
  "Expected: Table-formatted user list" \
  "Review: Aligned columns with headers"

# SR-511: admin user list --output json
run_sample "SR-511" "admin-user-list-json" \
  "raps admin user list -a \$ACCOUNT_ID --output json" \
  "Expected: JSON-formatted user list" \
  "Review: Valid JSON array"

# SR-512: admin user list --output yaml
run_sample "SR-512" "admin-user-list-yaml" \
  "raps admin user list -a \$ACCOUNT_ID --output yaml" \
  "Expected: YAML-formatted user list" \
  "Review: Valid YAML document"

# SR-513: admin user list --output csv
run_sample "SR-513" "admin-user-list-csv" \
  "raps admin user list -a \$ACCOUNT_ID --output csv" \
  "Expected: CSV-formatted user list" \
  "Review: Header row followed by data rows"

# SR-514: admin user list --output plain
run_sample "SR-514" "admin-user-list-plain" \
  "raps admin user list -a \$ACCOUNT_ID --output plain" \
  "Expected: Plain-text user list" \
  "Review: Simple text output"

# ── Output format matrix: hub list ───────────────────────────────

# SR-515: hub list --output table
run_sample "SR-515" "hub-list-table" \
  "raps hub list --output table" \
  "Expected: Table-formatted hub list" \
  "Review: Aligned columns with headers"

# SR-516: hub list --output json
run_sample "SR-516" "hub-list-json" \
  "raps hub list --output json" \
  "Expected: JSON-formatted hub list" \
  "Review: Valid JSON array"

# SR-517: hub list --output yaml
run_sample "SR-517" "hub-list-yaml" \
  "raps hub list --output yaml" \
  "Expected: YAML-formatted hub list" \
  "Review: Valid YAML document"

# SR-518: hub list --output csv
run_sample "SR-518" "hub-list-csv" \
  "raps hub list --output csv" \
  "Expected: CSV-formatted hub list" \
  "Review: Header row followed by data rows"

# SR-519: hub list --output plain
run_sample "SR-519" "hub-list-plain" \
  "raps hub list --output plain" \
  "Expected: Plain-text hub list" \
  "Review: Simple text output"

# ── Output format matrix: da engines ─────────────────────────────

# SR-520: da engines --output table
run_sample "SR-520" "da-engines-table" \
  "raps da engines --output table" \
  "Expected: Table-formatted engine list" \
  "Review: Aligned columns with headers"

# SR-521: da engines --output json
run_sample "SR-521" "da-engines-json" \
  "raps da engines --output json" \
  "Expected: JSON-formatted engine list" \
  "Review: Valid JSON array"

# SR-522: da engines --output yaml
run_sample "SR-522" "da-engines-yaml" \
  "raps da engines --output yaml" \
  "Expected: YAML-formatted engine list" \
  "Review: Valid YAML document"

# SR-523: da engines --output csv
run_sample "SR-523" "da-engines-csv" \
  "raps da engines --output csv" \
  "Expected: CSV-formatted engine list" \
  "Review: Header row followed by data rows"

# SR-524: da engines --output plain
run_sample "SR-524" "da-engines-plain" \
  "raps da engines --output plain" \
  "Expected: Plain-text engine list" \
  "Review: Simple text output"

# ── No-color ─────────────────────────────────────────────────────

# SR-530: No-color bucket list
run_sample "SR-530" "no-color-bucket-list" \
  "raps bucket list --no-color" \
  "Expected: Bucket list without ANSI colors" \
  "Review: No escape sequences in output"

# SR-531: No-color issue list
run_sample "SR-531" "no-color-issue-list" \
  "raps issue list \$PROJECT_ID --no-color" \
  "Expected: Issue list without ANSI colors" \
  "Review: No escape sequences in output"

# ── Help & version ───────────────────────────────────────────────

# SR-540: Top-level help
run_sample "SR-540" "help-top-level" \
  "raps --help" \
  "Expected: Top-level help text" \
  "Review: Contains subcommands and usage info"

# SR-541: Auth help
run_sample "SR-541" "help-auth" \
  "raps auth --help" \
  "Expected: Auth subcommand help" \
  "Review: Contains auth subcommands"

# SR-542: Admin help
run_sample "SR-542" "help-admin" \
  "raps admin --help" \
  "Expected: Admin subcommand help" \
  "Review: Contains admin subcommands"

# SR-543: Admin user help
run_sample "SR-543" "help-admin-user" \
  "raps admin user --help" \
  "Expected: Admin user subcommand help" \
  "Review: Contains user management subcommands"

# SR-544: Version
run_sample "SR-544" "help-version" \
  "raps --version" \
  "Expected: Version string" \
  "Review: Contains semver version number"

section_end
