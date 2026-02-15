# Section 99 — Cross-Cutting
# Runs: SR-500 through SR-544
. "$PSScriptRoot\..\lib\common.ps1"

Start-Section -Name "99-cross-cutting" -Title "Cross-Cutting"

# -- Output format matrix: bucket list ------------------------------------

# SR-500: bucket list --output table
Invoke-Sample -Id "SR-500" -Slug "bucket-list-table" `
  -Command "raps bucket list --output table" `
  -Expects "Expected: Table-formatted bucket list" `
  -Review "Review: Aligned columns with headers"

# SR-501: bucket list --output json
Invoke-Sample -Id "SR-501" -Slug "bucket-list-json" `
  -Command "raps bucket list --output json" `
  -Expects "Expected: JSON-formatted bucket list" `
  -Review "Review: Valid JSON array"

# SR-502: bucket list --output yaml
Invoke-Sample -Id "SR-502" -Slug "bucket-list-yaml" `
  -Command "raps bucket list --output yaml" `
  -Expects "Expected: YAML-formatted bucket list" `
  -Review "Review: Valid YAML document"

# SR-503: bucket list --output csv
Invoke-Sample -Id "SR-503" -Slug "bucket-list-csv" `
  -Command "raps bucket list --output csv" `
  -Expects "Expected: CSV-formatted bucket list" `
  -Review "Review: Header row followed by data rows"

# SR-504: bucket list --output plain
Invoke-Sample -Id "SR-504" -Slug "bucket-list-plain" `
  -Command "raps bucket list --output plain" `
  -Expects "Expected: Plain-text bucket list" `
  -Review "Review: Simple text output"

# -- Output format matrix: issue list -------------------------------------

# SR-505: issue list --output table
Invoke-Sample -Id "SR-505" -Slug "issue-list-table" `
  -Command "raps issue list $env:PROJECT_ID --output table" `
  -Expects "Expected: Table-formatted issue list" `
  -Review "Review: Aligned columns with headers"

# SR-506: issue list --output json
Invoke-Sample -Id "SR-506" -Slug "issue-list-json" `
  -Command "raps issue list $env:PROJECT_ID --output json" `
  -Expects "Expected: JSON-formatted issue list" `
  -Review "Review: Valid JSON array"

# SR-507: issue list --output yaml
Invoke-Sample -Id "SR-507" -Slug "issue-list-yaml" `
  -Command "raps issue list $env:PROJECT_ID --output yaml" `
  -Expects "Expected: YAML-formatted issue list" `
  -Review "Review: Valid YAML document"

# SR-508: issue list --output csv
Invoke-Sample -Id "SR-508" -Slug "issue-list-csv" `
  -Command "raps issue list $env:PROJECT_ID --output csv" `
  -Expects "Expected: CSV-formatted issue list" `
  -Review "Review: Header row followed by data rows"

# SR-509: issue list --output plain
Invoke-Sample -Id "SR-509" -Slug "issue-list-plain" `
  -Command "raps issue list $env:PROJECT_ID --output plain" `
  -Expects "Expected: Plain-text issue list" `
  -Review "Review: Simple text output"

# -- Output format matrix: admin user list --------------------------------

# SR-510: admin user list --output table
Invoke-Sample -Id "SR-510" -Slug "admin-user-list-table" `
  -Command "raps admin user list -a $env:ACCOUNT_ID --output table" `
  -Expects "Expected: Table-formatted user list" `
  -Review "Review: Aligned columns with headers"

# SR-511: admin user list --output json
Invoke-Sample -Id "SR-511" -Slug "admin-user-list-json" `
  -Command "raps admin user list -a $env:ACCOUNT_ID --output json" `
  -Expects "Expected: JSON-formatted user list" `
  -Review "Review: Valid JSON array"

# SR-512: admin user list --output yaml
Invoke-Sample -Id "SR-512" -Slug "admin-user-list-yaml" `
  -Command "raps admin user list -a $env:ACCOUNT_ID --output yaml" `
  -Expects "Expected: YAML-formatted user list" `
  -Review "Review: Valid YAML document"

# SR-513: admin user list --output csv
Invoke-Sample -Id "SR-513" -Slug "admin-user-list-csv" `
  -Command "raps admin user list -a $env:ACCOUNT_ID --output csv" `
  -Expects "Expected: CSV-formatted user list" `
  -Review "Review: Header row followed by data rows"

# SR-514: admin user list --output plain
Invoke-Sample -Id "SR-514" -Slug "admin-user-list-plain" `
  -Command "raps admin user list -a $env:ACCOUNT_ID --output plain" `
  -Expects "Expected: Plain-text user list" `
  -Review "Review: Simple text output"

# -- Output format matrix: hub list ---------------------------------------

# SR-515: hub list --output table
Invoke-Sample -Id "SR-515" -Slug "hub-list-table" `
  -Command "raps hub list --output table" `
  -Expects "Expected: Table-formatted hub list" `
  -Review "Review: Aligned columns with headers"

# SR-516: hub list --output json
Invoke-Sample -Id "SR-516" -Slug "hub-list-json" `
  -Command "raps hub list --output json" `
  -Expects "Expected: JSON-formatted hub list" `
  -Review "Review: Valid JSON array"

# SR-517: hub list --output yaml
Invoke-Sample -Id "SR-517" -Slug "hub-list-yaml" `
  -Command "raps hub list --output yaml" `
  -Expects "Expected: YAML-formatted hub list" `
  -Review "Review: Valid YAML document"

# SR-518: hub list --output csv
Invoke-Sample -Id "SR-518" -Slug "hub-list-csv" `
  -Command "raps hub list --output csv" `
  -Expects "Expected: CSV-formatted hub list" `
  -Review "Review: Header row followed by data rows"

# SR-519: hub list --output plain
Invoke-Sample -Id "SR-519" -Slug "hub-list-plain" `
  -Command "raps hub list --output plain" `
  -Expects "Expected: Plain-text hub list" `
  -Review "Review: Simple text output"

# -- Output format matrix: da engines ------------------------------------

# SR-520: da engines --output table
Invoke-Sample -Id "SR-520" -Slug "da-engines-table" `
  -Command "raps da engines --output table" `
  -Expects "Expected: Table-formatted engine list" `
  -Review "Review: Aligned columns with headers"

# SR-521: da engines --output json
Invoke-Sample -Id "SR-521" -Slug "da-engines-json" `
  -Command "raps da engines --output json" `
  -Expects "Expected: JSON-formatted engine list" `
  -Review "Review: Valid JSON array"

# SR-522: da engines --output yaml
Invoke-Sample -Id "SR-522" -Slug "da-engines-yaml" `
  -Command "raps da engines --output yaml" `
  -Expects "Expected: YAML-formatted engine list" `
  -Review "Review: Valid YAML document"

# SR-523: da engines --output csv
Invoke-Sample -Id "SR-523" -Slug "da-engines-csv" `
  -Command "raps da engines --output csv" `
  -Expects "Expected: CSV-formatted engine list" `
  -Review "Review: Header row followed by data rows"

# SR-524: da engines --output plain
Invoke-Sample -Id "SR-524" -Slug "da-engines-plain" `
  -Command "raps da engines --output plain" `
  -Expects "Expected: Plain-text engine list" `
  -Review "Review: Simple text output"

# -- No-color -------------------------------------------------------------

# SR-530: No-color bucket list
Invoke-Sample -Id "SR-530" -Slug "no-color-bucket-list" `
  -Command "raps bucket list --no-color" `
  -Expects "Expected: Bucket list without ANSI colors" `
  -Review "Review: No escape sequences in output"

# SR-531: No-color issue list
Invoke-Sample -Id "SR-531" -Slug "no-color-issue-list" `
  -Command "raps issue list $env:PROJECT_ID --no-color" `
  -Expects "Expected: Issue list without ANSI colors" `
  -Review "Review: No escape sequences in output"

# -- Help & version -------------------------------------------------------

# SR-540: Top-level help
Invoke-Sample -Id "SR-540" -Slug "help-top-level" `
  -Command "raps --help" `
  -Expects "Expected: Top-level help text" `
  -Review "Review: Contains subcommands and usage info"

# SR-541: Auth help
Invoke-Sample -Id "SR-541" -Slug "help-auth" `
  -Command "raps auth --help" `
  -Expects "Expected: Auth subcommand help" `
  -Review "Review: Contains auth subcommands"

# SR-542: Admin help
Invoke-Sample -Id "SR-542" -Slug "help-admin" `
  -Command "raps admin --help" `
  -Expects "Expected: Admin subcommand help" `
  -Review "Review: Contains admin subcommands"

# SR-543: Admin user help
Invoke-Sample -Id "SR-543" -Slug "help-admin-user" `
  -Command "raps admin user --help" `
  -Expects "Expected: Admin user subcommand help" `
  -Review "Review: Contains user management subcommands"

# SR-544: Version
Invoke-Sample -Id "SR-544" -Slug "help-version" `
  -Command "raps --version" `
  -Expects "Expected: Version string" `
  -Review "Review: Contains semver version number"

End-Section
