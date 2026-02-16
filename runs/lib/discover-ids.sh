#!/bin/bash
# discover-ids.sh — Auto-discover real hub/project/account IDs for test harness
#
# Sets environment variables used by all section scripts:
#   RAPS_HUB_ID          - BIM360/ACC hub ID (e.g., b.01fb...)
#   RAPS_ACCOUNT_ID      - Account UUID for admin APIs (hub ID without b. prefix)
#   RAPS_PROJECT_ID      - Project GUID for ACC APIs (issues, rfis, etc.)
#   RAPS_PROJECT_FULL_ID - Full project ID with prefix (for DM APIs)
#   RAPS_USER_EMAIL      - Current user email
#   RAPS_USER_ID         - Current user APS ID
#
# Discovery is cached: runs once, exports for all child processes.
# Requires: 3-legged auth active.

# Skip if already discovered
if [ -n "${_RAPS_IDS_DISCOVERED:-}" ]; then
  return 0 2>/dev/null || exit 0
fi

_discover_ids() {
  # Discover hubs - prefer BIM360 hub for ACC functionality
  local hubs_json
  hubs_json=$(raps hub list --output json --quiet 2>/dev/null || echo "[]")

  # Find BIM360 hub first, then any hub
  RAPS_HUB_ID=$(echo "$hubs_json" | python3 -c "
import sys, json
hubs = json.load(sys.stdin)
# Prefer BIM 360 hub
for h in hubs:
    if h.get('extension_type') == 'BIM 360':
        print(h['id']); exit()
# Fall back to any ACC hub
for h in hubs:
    if h['id'].startswith('b.'):
        print(h['id']); exit()
# Fall back to first hub
if hubs:
    print(hubs[0]['id'])
" 2>/dev/null || echo "")

  # Extract account ID (hub ID without b. prefix)
  if [[ "$RAPS_HUB_ID" == b.* ]]; then
    RAPS_ACCOUNT_ID="${RAPS_HUB_ID#b.}"
  else
    RAPS_ACCOUNT_ID=""
  fi

  # Discover first project in the hub
  if [ -n "$RAPS_HUB_ID" ]; then
    local projects_json
    projects_json=$(raps project list "$RAPS_HUB_ID" --output json --quiet 2>/dev/null || echo "[]")

    RAPS_PROJECT_FULL_ID=$(echo "$projects_json" | python3 -c "
import sys, json
projects = json.load(sys.stdin)
if projects:
    print(projects[0]['id'])
" 2>/dev/null || echo "")

    # Extract project GUID (without b. prefix) for ACC APIs
    if [[ "$RAPS_PROJECT_FULL_ID" == b.* ]]; then
      RAPS_PROJECT_ID="${RAPS_PROJECT_FULL_ID#b.}"
    else
      RAPS_PROJECT_ID="$RAPS_PROJECT_FULL_ID"
    fi
  fi

  # Discover current user
  local whoami_json
  whoami_json=$(raps auth whoami --output json --quiet 2>/dev/null || echo "{}")
  RAPS_USER_EMAIL=$(echo "$whoami_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('email',''))" 2>/dev/null || echo "")
  RAPS_USER_ID=$(echo "$whoami_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('aps_id',''))" 2>/dev/null || echo "")

  export RAPS_HUB_ID RAPS_ACCOUNT_ID RAPS_PROJECT_ID RAPS_PROJECT_FULL_ID
  export RAPS_USER_EMAIL RAPS_USER_ID
  export _RAPS_IDS_DISCOVERED=1
}

_discover_ids
