#!/bin/bash
# Run All Benchmarks
# Master script that executes all benchmark suites and aggregates results

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
REPORT_DIR="${REPORT_DIR:-$WORKSPACE_DIR/reports}"
DATA_DIR="${DATA_DIR:-$WORKSPACE_DIR/data/generated}"

mkdir -p "$REPORT_DIR" "$DATA_DIR"

echo "========================================"
echo "RAPS Examples - Full Benchmark Suite"
echo "========================================"
echo ""
echo "Report directory: $REPORT_DIR"
echo "Data directory:   $DATA_DIR"
echo ""

# Track overall results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Benchmark suites to run
BENCHMARKS=(
    "feature-validation"
    "automation-timing"
    "auth-flows"
    "rust-vs-nodejs"
)

# Initialize combined results
COMBINED_RESULTS="$REPORT_DIR/combined-results.json"
cat > "$COMBINED_RESULTS" << EOF
{
    "benchmark_run": {
        "timestamp": "$(date -Iseconds)",
        "platform": "$(uname -s)",
        "arch": "$(uname -m)"
    },
    "suites": {}
}
EOF

# ============================================
# Generate Test Data (if needed)
# ============================================
echo "Step 1: Generating test data..."
echo "-------------------------------"

# Generate all required test files
# Small (100MB) - quick baseline
if [ ! -f "$DATA_DIR/small-metadata.json" ]; then
    echo "Generating small-metadata.json (100MB)..."
    python3 "$SCRIPT_DIR/generate-test-data.py" \
        --output "$DATA_DIR" \
        --size 100mb \
        --name "small-metadata"
fi

# Medium (500MB) - shows memory pressure
if [ ! -f "$DATA_DIR/medium-metadata.json" ]; then
    echo "Generating medium-metadata.json (500MB)..."
    python3 "$SCRIPT_DIR/generate-test-data.py" \
        --output "$DATA_DIR" \
        --size 500mb \
        --name "medium-metadata"
fi

# Large (1GB) - significant stress test
if [ ! -f "$DATA_DIR/large-metadata.json" ]; then
    echo "Generating large-metadata.json (1GB)..."
    python3 "$SCRIPT_DIR/generate-test-data.py" \
        --output "$DATA_DIR" \
        --size 1gb \
        --name "large-metadata"
fi

echo "Test data ready."
ls -lh "$DATA_DIR"/*.json 2>/dev/null | grep -v meta || echo "No data files found"
echo ""

# ============================================
# Run Each Benchmark Suite
# ============================================
for benchmark in "${BENCHMARKS[@]}"; do
    echo "========================================"
    echo "Running: $benchmark"
    echo "========================================"

    BENCHMARK_SCRIPT="$WORKSPACE_DIR/benchmarks/$benchmark/run.sh"

    if [ -f "$BENCHMARK_SCRIPT" ]; then
        # Run benchmark and capture output
        if bash "$BENCHMARK_SCRIPT"; then
            echo ""
            echo "✓ $benchmark completed successfully"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo ""
            echo "✗ $benchmark failed"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
    else
        echo "○ $benchmark script not found, skipping"
        SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
    fi

    echo ""
done

# ============================================
# Aggregate Results
# ============================================
echo "========================================"
echo "Aggregating Results"
echo "========================================"

python3 << AGGREGATE
import json
import os
import glob

report_dir = "$REPORT_DIR"
combined_file = "$COMBINED_RESULTS"

# Load combined results
with open(combined_file, 'r') as f:
    combined = json.load(f)

# Find all result files
result_files = glob.glob(os.path.join(report_dir, '*-results.json'))

for result_file in result_files:
    if result_file == combined_file:
        continue

    try:
        with open(result_file, 'r') as f:
            data = json.load(f)

        suite_name = data.get('benchmark', os.path.basename(result_file))
        combined['suites'][suite_name] = data
        print(f"  Added: {suite_name}")
    except Exception as e:
        print(f"  Error reading {result_file}: {e}")

# Calculate summary
total_claims = 0
passed_claims = 0

for suite_name, suite_data in combined['suites'].items():
    if 'claims' in suite_data:
        for claim in suite_data['claims']:
            total_claims += 1
            if claim.get('passed'):
                passed_claims += 1
    elif 'tests' in suite_data:
        for test in suite_data['tests']:
            total_claims += 1
            if test.get('status') in ['success', 'mock']:
                passed_claims += 1
    elif 'flows' in suite_data:
        for flow in suite_data['flows']:
            total_claims += 1
            if flow.get('status') in ['success', 'available', 'detected']:
                passed_claims += 1

combined['summary'] = {
    'total_claims_validated': total_claims,
    'passed': passed_claims,
    'failed': total_claims - passed_claims,
    'pass_rate': round(passed_claims / total_claims * 100, 1) if total_claims > 0 else 0
}

# Save combined results
with open(combined_file, 'w') as f:
    json.dump(combined, f, indent=2)

print()
print(f"Combined results saved to: {combined_file}")
print(f"Total validations: {total_claims}")
print(f"Passed: {passed_claims} ({combined['summary']['pass_rate']}%)")
AGGREGATE

echo ""

# ============================================
# Generate Reports
# ============================================
echo "========================================"
echo "Generating Reports"
echo "========================================"

if [ -f "$SCRIPT_DIR/generate-report.py" ]; then
    python3 "$SCRIPT_DIR/generate-report.py"
else
    echo "Report generator not found, skipping HTML report"
fi

echo ""

# ============================================
# Final Summary
# ============================================
echo "========================================"
echo "Benchmark Run Complete"
echo "========================================"
echo ""
echo "Suites run:    $TOTAL_TESTS"
echo "Passed:        $PASSED_TESTS"
echo "Failed:        $FAILED_TESTS"
echo "Skipped:       $SKIPPED_TESTS"
echo ""
echo "Reports generated in: $REPORT_DIR"
echo ""
echo "Files:"
ls -la "$REPORT_DIR"/*.json 2>/dev/null || echo "  No JSON reports found"
ls -la "$REPORT_DIR"/*.html 2>/dev/null || echo "  No HTML reports found"
ls -la "$REPORT_DIR"/*.md 2>/dev/null || echo "  No Markdown reports found"

# Exit with failure if any tests failed
if [ "$FAILED_TESTS" -gt 0 ]; then
    exit 1
fi
