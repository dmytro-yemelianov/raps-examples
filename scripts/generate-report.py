#!/usr/bin/env python3
"""
Report Generator for RAPS Examples

Generates HTML and Markdown reports from benchmark results.
"""

import json
import os
from datetime import datetime
from pathlib import Path


REPORT_DIR = os.environ.get('REPORT_DIR', 'reports')


def load_results():
    """Load all benchmark results."""
    combined_path = Path(REPORT_DIR) / 'combined-results.json'

    if combined_path.exists():
        with open(combined_path) as f:
            return json.load(f)

    # Fallback: load individual result files
    results = {
        'benchmark_run': {
            'timestamp': datetime.now().isoformat(),
            'platform': os.uname().sysname if hasattr(os, 'uname') else 'unknown'
        },
        'suites': {}
    }

    for result_file in Path(REPORT_DIR).glob('*-results.json'):
        if result_file.name == 'combined-results.json':
            continue
        with open(result_file) as f:
            data = json.load(f)
            suite_name = data.get('benchmark', result_file.stem)
            results['suites'][suite_name] = data

    # Calculate aggregate summary
    total_passed = 0
    total_failed = 0
    total_claims = 0

    for suite in results['suites'].values():
        if 'claims' in suite:
            for claim in suite['claims']:
                total_claims += 1
                if claim.get('passed'):
                    total_passed += 1
                else:
                    total_failed += 1
        elif 'tests' in suite:
            for test in suite['tests']:
                total_claims += 1
                status = test.get('status', 'unknown')
                if status in ['success', 'mock', 'available', 'expected', 'documented', 'confirmed']:
                    total_passed += 1
                elif status == 'skipped':
                    pass
                else:
                    total_failed += 1
        elif 'flows' in suite:
            for flow in suite['flows']:
                total_claims += 1
                status = flow.get('status', 'unknown')
                if status in ['success', 'available', 'detected', 'documented']:
                    total_passed += 1
                else:
                    total_failed += 1

    results['summary'] = {
        'passed': total_passed,
        'failed': total_failed,
        'total_claims_validated': total_claims,
        'pass_rate': round(total_passed / total_claims * 100, 1) if total_claims > 0 else 0
    }

    return results


def generate_html_report(results: dict) -> str:
    """Generate HTML report."""
    summary = results.get('summary', {})
    run_info = results.get('benchmark_run', {})

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAPS Examples - Benchmark Report</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1, h2, h3 {{ color: #333; }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{ margin: 0; }}
        .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .card h3 {{ margin: 0 0 10px 0; color: #666; font-size: 14px; text-transform: uppercase; }}
        .card .value {{ font-size: 36px; font-weight: bold; color: #333; }}
        .card.success .value {{ color: #22c55e; }}
        .card.warning .value {{ color: #f59e0b; }}
        .card.error .value {{ color: #ef4444; }}
        .suite {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .suite h2 {{ margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .status {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        .status.success {{ background: #dcfce7; color: #166534; }}
        .status.failed {{ background: #fee2e2; color: #991b1b; }}
        .status.skipped {{ background: #fef3c7; color: #92400e; }}
        .status.mock {{ background: #e0e7ff; color: #3730a3; }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 14px;
        }}
        .pass-rate {{
            width: 100%;
            height: 20px;
            background: #eee;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 10px;
        }}
        .pass-rate-fill {{
            height: 100%;
            background: linear-gradient(90deg, #22c55e, #16a34a);
            border-radius: 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>RAPS Examples - Benchmark Report</h1>
        <p>Generated: {run_info.get('timestamp', 'Unknown')} | Platform: {run_info.get('platform', 'Unknown')}</p>
    </div>

    <div class="summary-cards">
        <div class="card success">
            <h3>Validations Passed</h3>
            <div class="value">{summary.get('passed', 0)}</div>
        </div>
        <div class="card {'error' if summary.get('failed', 0) > 0 else 'success'}">
            <h3>Validations Failed</h3>
            <div class="value">{summary.get('failed', 0)}</div>
        </div>
        <div class="card">
            <h3>Total Validations</h3>
            <div class="value">{summary.get('total_claims_validated', 0)}</div>
        </div>
        <div class="card {'success' if summary.get('pass_rate', 0) >= 80 else 'warning'}">
            <h3>Pass Rate</h3>
            <div class="value">{summary.get('pass_rate', 0)}%</div>
            <div class="pass-rate">
                <div class="pass-rate-fill" style="width: {summary.get('pass_rate', 0)}%"></div>
            </div>
        </div>
    </div>
"""

    # Add suite details
    for suite_name, suite_data in results.get('suites', {}).items():
        html += f"""
    <div class="suite">
        <h2>{suite_name.replace('-', ' ').title()}</h2>
"""

        # Handle different result formats
        if 'claims' in suite_data:
            html += """
        <table>
            <thead>
                <tr>
                    <th>Claim</th>
                    <th>Expected</th>
                    <th>Actual</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
"""
            for claim in suite_data['claims']:
                status_class = 'success' if claim.get('passed') else 'failed'
                status_text = 'Passed' if claim.get('passed') else 'Failed'
                html += f"""
                <tr>
                    <td>{claim.get('claim', 'Unknown')}</td>
                    <td>{claim.get('expected', '-')}</td>
                    <td>{claim.get('actual', '-')}</td>
                    <td><span class="status {status_class}">{status_text}</span></td>
                </tr>
"""
            html += """
            </tbody>
        </table>
"""

        elif 'tests' in suite_data:
            html += """
        <table>
            <thead>
                <tr>
                    <th>Test</th>
                    <th>Duration</th>
                    <th>Memory</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
"""
            for test in suite_data['tests']:
                status = test.get('status', 'unknown')
                status_class = 'success' if status in ['success', 'mock', 'available', 'expected', 'documented', 'confirmed'] else 'failed' if status == 'crashed' else 'skipped'
                html += f"""
                <tr>
                    <td>{test.get('name', 'Unknown')}</td>
                    <td>{test.get('duration_seconds', '-')}s</td>
                    <td>{test.get('memory_mb', '-')} MB</td>
                    <td><span class="status {status_class}">{status}</span></td>
                </tr>
"""
            html += """
            </tbody>
        </table>
"""

        elif 'flows' in suite_data:
            html += """
        <table>
            <thead>
                <tr>
                    <th>Flow</th>
                    <th>Duration</th>
                    <th>Status</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>
"""
            for flow in suite_data['flows']:
                status = flow.get('status', 'unknown')
                status_class = 'success' if status in ['success', 'available', 'detected', 'documented'] else 'skipped' if status == 'skipped' else 'failed'
                html += f"""
                <tr>
                    <td>{flow.get('flow', 'Unknown')}</td>
                    <td>{flow.get('duration_seconds', '-')}s</td>
                    <td><span class="status {status_class}">{status}</span></td>
                    <td>{flow.get('notes', '-')}</td>
                </tr>
"""
            html += """
            </tbody>
        </table>
"""

        html += """
    </div>
"""

    html += """
    <div class="footer">
        <p>Generated by RAPS Examples | <a href="https://rapscli.xyz">rapscli.xyz</a></p>
    </div>
</body>
</html>
"""
    return html


def generate_markdown_report(results: dict) -> str:
    """Generate Markdown report."""
    summary = results.get('summary', {})
    run_info = results.get('benchmark_run', {})

    md = f"""# RAPS Examples - Benchmark Report

**Generated:** {run_info.get('timestamp', 'Unknown')}
**Platform:** {run_info.get('platform', 'Unknown')}

## Summary

| Metric | Value |
|--------|-------|
| Validations Passed | {summary.get('passed', 0)} |
| Validations Failed | {summary.get('failed', 0)} |
| Total Validations | {summary.get('total_claims_validated', 0)} |
| Pass Rate | {summary.get('pass_rate', 0)}% |

"""

    for suite_name, suite_data in results.get('suites', {}).items():
        md += f"## {suite_name.replace('-', ' ').title()}\n\n"

        if 'claims' in suite_data:
            md += "| Claim | Expected | Actual | Status |\n"
            md += "|-------|----------|--------|--------|\n"
            for claim in suite_data['claims']:
                status = "✓" if claim.get('passed') else "✗"
                md += f"| {claim.get('claim', 'Unknown')} | {claim.get('expected', '-')} | {claim.get('actual', '-')} | {status} |\n"
            md += "\n"

        elif 'tests' in suite_data:
            md += "| Test | Duration | Memory | Status |\n"
            md += "|------|----------|--------|--------|\n"
            for test in suite_data['tests']:
                status = test.get('status', 'unknown')
                status_icon = "✓" if status in ['success', 'mock', 'available', 'expected', 'documented', 'confirmed'] else "✗" if status == 'crashed' else "○"
                md += f"| {test.get('name', 'Unknown')} | {test.get('duration_seconds', '-')}s | {test.get('memory_mb', '-')} MB | {status_icon} |\n"
            md += "\n"

        elif 'flows' in suite_data:
            md += "| Flow | Status | Notes |\n"
            md += "|------|--------|-------|\n"
            for flow in suite_data['flows']:
                status = flow.get('status', 'unknown')
                status_icon = "✓" if status in ['success', 'available', 'detected', 'documented'] else "○" if status == 'skipped' else "✗"
                md += f"| {flow.get('flow', 'Unknown')} | {status_icon} {status} | {flow.get('notes', '-')} |\n"
            md += "\n"

    md += """---

*Generated by [RAPS Examples](https://rapscli.xyz)*
"""
    return md


def main():
    print("Generating reports...")

    # Load results
    results = load_results()

    # Generate HTML report
    html_report = generate_html_report(results)
    html_path = Path(REPORT_DIR) / 'metrics-report.html'
    html_path.write_text(html_report)
    print(f"  HTML report: {html_path}")

    # Generate Markdown report
    md_report = generate_markdown_report(results)
    md_path = Path(REPORT_DIR) / 'metrics-report.md'
    md_path.write_text(md_report)
    print(f"  Markdown report: {md_path}")

    print("\nReports generated successfully!")


if __name__ == '__main__':
    main()
