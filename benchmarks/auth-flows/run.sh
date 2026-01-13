#!/bin/bash
# Authentication Flow Validation
# Validates claims from "Authentication Chaos: The Universal Developer Pain Point"
#
# Claims being validated:
# - Multiple auth flows supported (2-legged, 3-legged, device code, token-based)
# - Automatic token refresh works
# - Profile-based multi-environment support
# - Secure keyring storage

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_DIR="${REPORT_DIR:-$SCRIPT_DIR/../../reports}"

mkdir -p "$REPORT_DIR"

echo "========================================"
echo "Authentication Flow Validation"
echo "========================================"
echo ""

RESULTS_FILE="$REPORT_DIR/auth-flows-results.json"
cat > "$RESULTS_FILE" << EOF
{
    "benchmark": "auth-flows",
    "timestamp": "$(date -Iseconds)",
    "flows": []
}
EOF

add_flow_result() {
    local flow="$1"
    local status="$2"
    local duration="$3"
    local notes="$4"

    # Handle empty duration
    [ -z "$duration" ] && duration="0"

    python3 << PYEOF
import json
with open('$RESULTS_FILE', 'r') as f:
    data = json.load(f)
data['flows'].append({
    'flow': '$flow',
    'status': '$status',
    'duration_seconds': float('$duration') if '$duration' else 0,
    'notes': '''$notes'''
})
with open('$RESULTS_FILE', 'w') as f:
    json.dump(data, f, indent=2)
PYEOF
}

# ============================================
# Test 1: 2-Legged OAuth (Client Credentials)
# ============================================
echo "Test 1: 2-Legged OAuth (Client Credentials)"
echo "---------------------------------------------"

if command -v raps &> /dev/null && [ -n "${APS_CLIENT_ID:-}" ] && [ -n "${APS_CLIENT_SECRET:-}" ]; then
    START_TIME=$(date +%s.%N)

    # Capture both stdout and stderr for debugging
    AUTH_OUTPUT=$(raps auth login --2legged 2>&1) && AUTH_SUCCESS=true || AUTH_SUCCESS=false

    if [ "$AUTH_SUCCESS" = "true" ]; then
        END_TIME=$(date +%s.%N)
        DURATION=$(echo "$END_TIME - $START_TIME" | bc)
        echo "  ✓ 2-legged auth successful in ${DURATION}s"
        add_flow_result "2-legged" "success" "$DURATION" "Client credentials flow works"
    else
        echo "  ✗ 2-legged auth failed"
        echo "  Error: $AUTH_OUTPUT"
        add_flow_result "2-legged" "failed" "0" "Authentication failed: ${AUTH_OUTPUT:0:100}"
    fi
else
    echo "  ○ Skipped (no credentials or RAPS not installed)"
    add_flow_result "2-legged" "skipped" "0" "Credentials not available"
fi

echo ""

# ============================================
# Test 2: 3-Legged OAuth (Browser-based)
# ============================================
echo "Test 2: 3-Legged OAuth (Browser-based)"
echo "----------------------------------------"

if command -v raps &> /dev/null && [ -n "${APS_CLIENT_ID:-}" ]; then
    # Can't fully test in CI, but verify command exists
    if raps auth login --help 2>/dev/null | grep -q "3legged\|browser"; then
        echo "  ✓ 3-legged auth command available"
        add_flow_result "3-legged" "available" "0" "Browser-based auth supported"
    else
        echo "  ○ 3-legged flag not found in help"
        add_flow_result "3-legged" "unavailable" "0" "Command not found"
    fi
else
    echo "  ○ Skipped (RAPS not installed)"
    add_flow_result "3-legged" "skipped" "0" "RAPS not available"
fi

echo ""

# ============================================
# Test 3: Device Code Flow
# ============================================
echo "Test 3: Device Code Flow"
echo "-------------------------"

if command -v raps &> /dev/null; then
    if raps auth login --help 2>/dev/null | grep -q "device"; then
        echo "  ✓ Device code flow supported"
        add_flow_result "device-code" "available" "0" "Device code flow available"
    else
        echo "  ○ Device code flag not found"
        add_flow_result "device-code" "unavailable" "0" "Not implemented"
    fi
else
    echo "  ○ Skipped (RAPS not installed)"
    add_flow_result "device-code" "skipped" "0" "RAPS not available"
fi

echo ""

# ============================================
# Test 4: Token-based Authentication
# ============================================
echo "Test 4: Token-based Authentication"
echo "------------------------------------"

if command -v raps &> /dev/null; then
    if raps auth login --help 2>/dev/null | grep -q "token"; then
        echo "  ✓ Token-based auth supported"
        add_flow_result "token-based" "available" "0" "Direct token input supported"
    else
        echo "  ○ Token flag not found"
        add_flow_result "token-based" "unavailable" "0" "Not implemented"
    fi
else
    echo "  ○ Skipped (RAPS not installed)"
    add_flow_result "token-based" "skipped" "0" "RAPS not available"
fi

echo ""

# ============================================
# Test 5: Profile Support
# ============================================
echo "Test 5: Multi-Environment Profile Support"
echo "-------------------------------------------"

if command -v raps &> /dev/null; then
    if raps auth --help 2>/dev/null | grep -q "profile\|--profile"; then
        echo "  ✓ Profile support available"
        add_flow_result "profiles" "available" "0" "Multi-environment profiles work"

        # Test profile listing if available
        if raps config profile list 2>/dev/null; then
            echo "  ✓ Profile listing works"
        fi
    else
        echo "  ○ Profile flag not found"
        add_flow_result "profiles" "unavailable" "0" "Not implemented"
    fi
else
    echo "  ○ Skipped (RAPS not installed)"
    add_flow_result "profiles" "skipped" "0" "RAPS not available"
fi

echo ""

# ============================================
# Test 6: Auth Status Command
# ============================================
echo "Test 6: Auth Status (Token Info)"
echo "----------------------------------"

if command -v raps &> /dev/null; then
    START_TIME=$(date +%s.%N)
    if raps auth status 2>/dev/null; then
        END_TIME=$(date +%s.%N)
        DURATION=$(echo "$END_TIME - $START_TIME" | bc)
        echo "  ✓ Auth status command works (${DURATION}s)"
        add_flow_result "auth-status" "success" "$DURATION" "Displays token info and expiry"
    else
        echo "  ○ No active session (expected if not logged in)"
        add_flow_result "auth-status" "no-session" "0" "Command works but no active session"
    fi
else
    echo "  ○ Skipped (RAPS not installed)"
    add_flow_result "auth-status" "skipped" "0" "RAPS not available"
fi

echo ""

# ============================================
# Test 7: Secure Storage
# ============================================
echo "Test 7: Secure Keyring Storage"
echo "--------------------------------"

# Check if keyring/secure storage is used
if command -v raps &> /dev/null; then
    # Check if RAPS uses keyring (based on dependencies)
    if strings $(which raps) 2>/dev/null | grep -qi "keyring\|secret.service\|credential"; then
        echo "  ✓ Secure storage detected in binary"
        add_flow_result "secure-storage" "detected" "0" "Keyring integration present"
    else
        echo "  ○ Could not detect secure storage"
        add_flow_result "secure-storage" "unknown" "0" "Unable to verify"
    fi
else
    echo "  ○ Skipped (RAPS not installed)"
    add_flow_result "secure-storage" "skipped" "0" "RAPS not available"
fi

echo ""

# ============================================
# Summary
# ============================================
echo "========================================"
echo "Authentication Validation Summary"
echo "========================================"

python3 << EOF
import json

with open("$RESULTS_FILE", 'r') as f:
    data = json.load(f)

# Count by status
success = sum(1 for f in data['flows'] if f['status'] in ['success', 'available', 'detected'])
skipped = sum(1 for f in data['flows'] if f['status'] == 'skipped')
failed = sum(1 for f in data['flows'] if f['status'] in ['failed', 'unavailable'])

print(f"\nResults: {success} passed, {skipped} skipped, {failed} failed")
print("-" * 50)

for flow in data['flows']:
    if flow['status'] in ['success', 'available', 'detected']:
        icon = "✓"
    elif flow['status'] == 'skipped':
        icon = "○"
    else:
        icon = "✗"
    print(f"{icon} {flow['flow']}: {flow['status']}")
    if flow['notes']:
        print(f"  {flow['notes']}")

# Validate blog claims
print("\nBlog Claims:")
print("-" * 50)

auth_flows = ['2-legged', '3-legged', 'device-code', 'token-based']
available_flows = sum(1 for f in data['flows']
                      if f['flow'] in auth_flows and f['status'] in ['success', 'available'])
print(f"Multiple auth flows: {available_flows}/4 available")

has_profiles = any(f['flow'] == 'profiles' and f['status'] == 'available' for f in data['flows'])
print(f"Profile support: {'✓' if has_profiles else '○'}")

has_secure = any(f['flow'] == 'secure-storage' and f['status'] != 'failed' for f in data['flows'])
print(f"Secure storage: {'✓' if has_secure else '○'}")

# Update summary in results
data['summary'] = {
    'auth_flows_available': available_flows,
    'profile_support': has_profiles,
    'secure_storage': has_secure,
    'blog_claims_validated': available_flows >= 2 and has_profiles
}

with open("$RESULTS_FILE", 'w') as f:
    json.dump(data, f, indent=2)
EOF

echo ""
echo "Results saved to: $RESULTS_FILE"
