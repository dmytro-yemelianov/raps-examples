#!/usr/bin/env python3
"""
generate-run-report.py — Generate an interactive HTML report from sample run results.

Reads JSON logs produced by run-all.sh and creates a single-file HTML dashboard
with section summaries, pass/fail counts, and per-run details.

Usage:
    python generate-run-report.py <LOG_DIR> [-o report.html]
    python generate-run-report.py C:/github/raps/logs/2026-02-15-11-50

If no LOG_DIR given, uses the most recent directory under ../logs/ relative to this script.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Strip ANSI escape sequences (colors, bold, etc.)
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text):
    return _ANSI_RE.sub("", text)


def find_latest_log_dir(base):
    """Find the most recent log directory by name."""
    dirs = sorted(
        [d for d in base.iterdir() if d.is_dir()],
        key=lambda d: d.name,
        reverse=True,
    )
    return dirs[0] if dirs else None


def load_sections(log_dir):
    """Load all section JSON files from a log directory."""
    sections = []
    for f in sorted(log_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            # Also load the companion .log file if it exists
            log_file = f.with_suffix(".log")
            if log_file.exists():
                content = log_file.read_text(encoding="utf-8", errors="replace")
                content = strip_ansi(content)
                # Cap log at 50KB to keep report size manageable
                if len(content) > 50_000:
                    content = (
                        content[:50_000]
                        + "\n\n--- LOG TRUNCATED (original: {:,} chars) ---\n".format(
                            len(content)
                        )
                    )
                data["_log_content"] = content
            else:
                data["_log_content"] = ""
            sections.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return sections


def compute_summary(sections):
    """Compute aggregate stats across all sections."""
    total_runs = 0
    total_ok = 0
    total_fail = 0
    total_timeout = 0
    total_skip = 0
    total_duration = 0.0
    section_summaries = []

    for sec in sections:
        runs = sec.get("runs", [])
        ok = sum(
            1
            for r in runs
            if r.get("exit_code") == 0
            and not r.get("command", "").startswith("(skipped")
        )
        skip = sum(1 for r in runs if r.get("command", "").startswith("(skipped"))
        timeout = sum(1 for r in runs if r.get("exit_code") == 124)
        fail = len(runs) - ok - skip
        sec_duration = sum(r.get("duration_seconds", 0) for r in runs)
        total_runs += len(runs)
        total_ok += ok
        total_fail += fail
        total_timeout += timeout
        total_skip += skip
        total_duration += sec_duration
        section_summaries.append(
            {
                "section": sec.get("section", "unknown"),
                "title": sec.get("title", sec.get("section", "Unknown")),
                "target": sec.get("target", "real"),
                "timestamp": sec.get("timestamp", ""),
                "total": len(runs),
                "ok": ok,
                "fail": fail,
                "skip": skip,
                "timeout": timeout,
                "duration": round(sec_duration, 1),
                "runs": runs,
                "log": sec.get("_log_content", ""),
            }
        )

    return {
        "total_runs": total_runs,
        "total_ok": total_ok,
        "total_fail": total_fail,
        "total_timeout": total_timeout,
        "total_skip": total_skip,
        "total_duration": round(total_duration, 1),
        "pass_rate": round(total_ok / total_runs * 100, 1) if total_runs else 0,
        "sections": section_summaries,
    }


def generate_html(summary, log_dir_name):
    """Generate a self-contained HTML report with embedded logs."""
    # Escape </script> in JSON to prevent breaking the HTML parser
    sections_json = json.dumps(summary["sections"]).replace("</", "<\\/")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    return _build_html(summary, log_dir_name, now, sections_json)


def _fmt_duration(secs):
    """Format seconds as human-readable string."""
    if secs < 60:
        return f"{secs:.1f}s"
    m = int(secs // 60)
    s = secs % 60
    return f"{m}m {s:.0f}s"


def _build_html(summary, log_dir_name, now, sections_json):
    """Build HTML using placeholder replacement for safe JSON embedding."""
    PLACEHOLDER = "___SECTIONS_DATA_PLACEHOLDER___"
    dur = _fmt_duration(summary["total_duration"])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RAPS Sample Runs Report — {log_dir_name}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');
  :root {{
    --bg: #0a0c10; --surface: #13161d; --surface2: #1c2029;
    --border: #262b3a; --border-hover: #3b4259; --text: #e4e4e7; --dim: #7a7f94;
    --green: #22c55e; --red: #ef4444; --yellow: #eab308;
    --blue: #3b82f6; --purple: #a78bfa; --cyan: #06b6d4;
    --orange: #f97316; --green-bg: rgba(34,197,94,0.08);
    --red-bg: rgba(239,68,68,0.08); --cyan-bg: rgba(6,182,212,0.08);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    background: var(--bg); color: var(--text);
    line-height: 1.6; min-height: 100vh;
  }}
  .container {{ max-width: 1440px; margin: 0 auto; padding: 24px 32px; }}

  /* Header */
  .header {{
    background: linear-gradient(135deg, #141926 0%, #0d1019 100%);
    border: 1px solid var(--border); border-radius: 16px;
    padding: 28px 32px; margin-bottom: 20px;
    display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;
  }}
  .header h1 {{ font-size: 22px; font-weight: 700; letter-spacing: -0.3px; }}
  .header h1 span {{ color: var(--cyan); }}
  .header-meta {{ color: var(--dim); font-size: 13px; text-align: right; }}
  .header-meta strong {{ color: var(--text); }}

  /* Summary cards */
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin-bottom: 20px; }}
  .card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 16px 12px; text-align: center;
  }}
  .card-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--dim); margin-bottom: 6px; }}
  .card-value {{ font-size: 32px; font-weight: 800; letter-spacing: -1px; }}
  .card-value.ok {{ color: var(--green); }}
  .card-value.fail {{ color: var(--red); }}
  .card-value.timeout {{ color: var(--yellow); }}
  .card-value.skip {{ color: var(--orange); }}
  .card-value.rate {{ color: var(--cyan); }}
  .card-value.total {{ color: var(--text); }}
  .card-value.dur {{ color: var(--purple); font-size: 22px; }}
  .progress {{ width: 100%; height: 6px; background: var(--surface2); border-radius: 3px; overflow: hidden; margin-top: 6px; }}
  .progress-fill {{ height: 100%; border-radius: 3px; }}
  .progress-fill.green {{ background: var(--green); }}

  /* Sections grid */
  .sections-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; margin-bottom: 20px; }}
  .section-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 16px 18px; cursor: pointer;
    transition: border-color 0.15s, transform 0.1s, box-shadow 0.15s;
  }}
  .section-card:hover {{ border-color: var(--border-hover); transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.3); }}
  .section-card.active {{ border-color: var(--cyan); box-shadow: 0 0 0 1px var(--cyan), 0 4px 16px rgba(6,182,212,0.1); }}
  .section-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }}
  .section-name {{ font-weight: 700; font-size: 14px; font-family: 'JetBrains Mono', monospace; }}
  .section-title {{ font-size: 12px; color: var(--dim); margin-bottom: 10px; }}
  .section-badge {{
    font-size: 10px; font-weight: 700; padding: 2px 8px;
    border-radius: 20px; letter-spacing: 0.5px;
  }}
  .section-badge.perfect {{ background: rgba(34,197,94,0.12); color: var(--green); }}
  .section-badge.partial {{ background: rgba(234,179,8,0.12); color: var(--yellow); }}
  .section-badge.bad {{ background: rgba(239,68,68,0.12); color: var(--red); }}
  .section-badge.empty {{ background: rgba(122,127,148,0.12); color: var(--dim); }}
  .section-stats {{ display: flex; gap: 12px; font-size: 12px; color: var(--dim); flex-wrap: wrap; align-items: center; }}
  .section-stats .s-ok {{ color: var(--green); }}
  .section-stats .s-fail {{ color: var(--red); }}
  .section-stats .s-to {{ color: var(--yellow); }}
  .section-stats .s-skip {{ color: var(--orange); }}
  .section-stats .s-dur {{ color: var(--purple); }}
  .section-bar {{ margin-top: 8px; height: 3px; background: var(--surface2); border-radius: 2px; overflow: hidden; display: flex; }}
  .section-bar .bar-ok {{ background: var(--green); }}
  .section-bar .bar-fail {{ background: var(--red); }}
  .section-bar .bar-to {{ background: var(--yellow); }}
  .section-bar .bar-skip {{ background: var(--orange); }}

  /* Detail panel */
  .detail-panel {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 24px; margin-bottom: 20px;
    display: none;
  }}
  .detail-panel.visible {{ display: block; }}
  .detail-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 8px; }}
  .detail-title {{ font-size: 17px; font-weight: 700; }}
  .detail-title span {{ color: var(--dim); font-weight: 400; font-size: 13px; margin-left: 8px; }}
  .detail-close {{
    background: var(--surface2); border: 1px solid var(--border); color: var(--dim);
    border-radius: 6px; padding: 4px 12px; font-size: 13px; cursor: pointer;
    transition: all 0.15s;
  }}
  .detail-close:hover {{ border-color: var(--red); color: var(--red); }}

  /* Tabs */
  .tab-bar {{ display: flex; gap: 2px; margin-bottom: 16px; background: var(--surface2); border-radius: 8px; padding: 3px; width: fit-content; }}
  .tab-btn {{
    background: transparent; border: none;
    color: var(--dim); border-radius: 6px; padding: 6px 16px;
    font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.15s;
  }}
  .tab-btn:hover {{ color: var(--text); }}
  .tab-btn.active {{ background: var(--surface); color: var(--cyan); box-shadow: 0 1px 3px rgba(0,0,0,0.3); }}
  .tab-content {{ display: none; }}
  .tab-content.visible {{ display: block; }}

  /* Filters */
  .filters {{ display: flex; gap: 6px; margin-bottom: 12px; flex-wrap: wrap; }}
  .filter-btn {{
    background: transparent; border: 1px solid var(--border);
    color: var(--dim); border-radius: 6px; padding: 4px 12px;
    font-size: 12px; cursor: pointer; transition: all 0.15s;
  }}
  .filter-btn:hover {{ border-color: var(--border-hover); color: var(--text); }}
  .filter-btn.active {{ background: var(--cyan-bg); border-color: var(--cyan); color: var(--cyan); }}

  /* Runs table */
  .runs-table {{ width: 100%; border-collapse: collapse; }}
  .runs-table th {{
    text-align: left; padding: 8px 10px; font-size: 10px;
    text-transform: uppercase; letter-spacing: 1px; color: var(--dim);
    border-bottom: 1px solid var(--border); position: sticky; top: 0; background: var(--surface);
  }}
  .runs-table td {{
    padding: 8px 10px; border-bottom: 1px solid var(--border);
    font-size: 13px; vertical-align: middle;
  }}
  .runs-table tr {{ cursor: pointer; transition: background 0.1s; }}
  .runs-table tr:hover {{ background: var(--surface2); }}
  .runs-table tr.selected {{ background: var(--cyan-bg); }}
  .run-id {{ color: var(--cyan); font-family: 'JetBrains Mono', monospace; font-weight: 600; font-size: 12px; white-space: nowrap; }}
  .run-slug {{ font-size: 13px; }}
  .run-cmd {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--dim); max-width: 420px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .run-cmd:hover {{ white-space: normal; word-break: break-all; }}
  .exit-pill {{
    display: inline-block; padding: 1px 8px; border-radius: 10px;
    font-size: 11px; font-weight: 700; font-family: 'JetBrains Mono', monospace;
  }}
  .exit-pill.e0 {{ background: rgba(34,197,94,0.12); color: var(--green); }}
  .exit-pill.e124 {{ background: rgba(234,179,8,0.12); color: var(--yellow); }}
  .exit-pill.skip {{ background: rgba(249,115,22,0.12); color: var(--orange); }}
  .exit-pill.lifecycle {{ background: rgba(167,139,250,0.12); color: var(--purple); }}
  .exit-pill.err {{ background: rgba(239,68,68,0.12); color: var(--red); }}
  .run-dur {{ font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--dim); white-space: nowrap; }}

  /* Log viewer (both section-level and per-run) */
  .log-viewer {{
    background: #0b0e14; border: 1px solid var(--border); border-radius: 8px;
    padding: 16px; font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 12px; line-height: 1.6; color: #c9d1d9;
    max-height: 600px; overflow: auto; white-space: pre-wrap; word-break: break-all;
  }}
  .log-viewer .log-ok {{ color: var(--green); }}
  .log-viewer .log-err {{ color: var(--red); }}
  .log-viewer .log-warn {{ color: var(--yellow); }}
  .log-viewer .log-info {{ color: var(--cyan); }}
  .log-viewer .log-skip {{ color: var(--orange); }}
  .log-viewer .log-bold {{ font-weight: 700; color: var(--text); }}
  .log-viewer .log-dim {{ color: #555b70; }}
  .log-empty {{ color: var(--dim); font-style: italic; padding: 24px; text-align: center; }}

  /* Run log drawer (below the table) */
  .run-log-drawer {{
    background: #0b0e14; border: 1px solid var(--border); border-radius: 8px;
    margin-top: 12px; overflow: hidden; display: none;
  }}
  .run-log-drawer.visible {{ display: block; }}
  .run-log-header {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 10px 16px; background: var(--surface2); border-bottom: 1px solid var(--border);
  }}
  .run-log-header-id {{ font-family: 'JetBrains Mono', monospace; font-weight: 700; color: var(--cyan); font-size: 13px; }}
  .run-log-header-slug {{ color: var(--dim); font-size: 13px; margin-left: 8px; }}
  .run-log-close {{
    background: none; border: none; color: var(--dim); font-size: 18px;
    cursor: pointer; padding: 2px 6px; line-height: 1;
  }}
  .run-log-close:hover {{ color: var(--red); }}
  .run-log-body {{
    padding: 14px 16px; font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 12px; line-height: 1.6; color: #c9d1d9;
    max-height: 400px; overflow: auto; white-space: pre-wrap; word-break: break-all;
  }}

  /* Search */
  .search-box {{
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 8px; padding: 7px 12px; color: var(--text);
    font-size: 13px; width: 280px; margin-bottom: 12px;
  }}
  .search-box:focus {{ outline: none; border-color: var(--cyan); }}
  .toolbar {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-bottom: 12px; }}

  /* Footer */
  .footer {{ text-align: center; color: var(--dim); font-size: 12px; padding: 20px 0; }}
  .footer a {{ color: var(--cyan); text-decoration: none; }}
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <div>
      <h1><span>RAPS</span> Sample Runs Report</h1>
    </div>
    <div class="header-meta">
      <div>Run: <strong>{log_dir_name}</strong></div>
      <div>Generated: <strong>{now}</strong></div>
    </div>
  </div>

  <div class="cards">
    <div class="card">
      <div class="card-label">Total Runs</div>
      <div class="card-value total">{summary['total_runs']}</div>
    </div>
    <div class="card">
      <div class="card-label">Passed</div>
      <div class="card-value ok">{summary['total_ok']}</div>
    </div>
    <div class="card">
      <div class="card-label">Failed</div>
      <div class="card-value fail">{summary['total_fail']}</div>
    </div>
    <div class="card">
      <div class="card-label">Skipped</div>
      <div class="card-value skip">{summary['total_skip']}</div>
    </div>
    <div class="card">
      <div class="card-label">Timeouts</div>
      <div class="card-value timeout">{summary['total_timeout']}</div>
    </div>
    <div class="card">
      <div class="card-label">Duration</div>
      <div class="card-value dur">{dur}</div>
    </div>
    <div class="card">
      <div class="card-label">Pass Rate</div>
      <div class="card-value rate">{summary['pass_rate']}%</div>
      <div class="progress">
        <div class="progress-fill green" style="width:{summary['pass_rate']}%"></div>
      </div>
    </div>
  </div>

  <div class="sections-grid" id="sectionsGrid"></div>

  <div class="detail-panel" id="detailPanel">
    <div class="detail-header">
      <div class="detail-title" id="detailTitle"></div>
      <button class="detail-close" onclick="closeDetail()">&times; Close</button>
    </div>
    <div class="tab-bar" id="tabBar">
      <button class="tab-btn active" data-tab="results" onclick="switchTab('results')">Results</button>
      <button class="tab-btn" data-tab="logs" onclick="switchTab('logs')">Full Log</button>
    </div>
    <div class="tab-content visible" id="tabResults">
      <div class="toolbar">
        <input type="text" class="search-box" id="searchBox" placeholder="Filter runs...">
        <div class="filters" id="filters">
          <button class="filter-btn active" data-filter="all">All</button>
          <button class="filter-btn" data-filter="ok">Passed</button>
          <button class="filter-btn" data-filter="fail">Failed</button>
          <button class="filter-btn" data-filter="skip">Skipped</button>
          <button class="filter-btn" data-filter="timeout">Timeout</button>
        </div>
      </div>
      <table class="runs-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Slug</th>
            <th>Command</th>
            <th>Exit</th>
            <th>Duration</th>
          </tr>
        </thead>
        <tbody id="runsBody"></tbody>
      </table>
      <div class="run-log-drawer" id="runLogDrawer">
        <div class="run-log-header">
          <div><span class="run-log-header-id" id="drawerRunId"></span><span class="run-log-header-slug" id="drawerRunSlug"></span></div>
          <button class="run-log-close" onclick="closeDrawer()">&times;</button>
        </div>
        <div class="run-log-body" id="drawerLogBody"></div>
      </div>
    </div>
    <div class="tab-content" id="tabLogs">
      <div class="log-viewer" id="logViewer"></div>
    </div>
  </div>

  <div class="footer">
    RAPS CLI Sample Runs &middot; <a href="https://rapscli.xyz">rapscli.xyz</a>
  </div>

</div>

<script>
const DATA = ___SECTIONS_DATA_PLACEHOLDER___;

let activeSection = null;
let activeFilter = 'all';
let activeTab = 'results';
let selectedRunId = null;

function init() {{
  renderSections();
  document.getElementById('searchBox').addEventListener('input', renderRuns);
  document.getElementById('filters').addEventListener('click', (e) => {{
    if (e.target.classList.contains('filter-btn')) {{
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');
      activeFilter = e.target.dataset.filter;
      renderRuns();
    }}
  }});
}}

function switchTab(tab) {{
  activeTab = tab;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
  document.getElementById('tabResults').classList.toggle('visible', tab === 'results');
  document.getElementById('tabLogs').classList.toggle('visible', tab === 'logs');
  if (tab === 'logs') renderLog();
}}

function fmtDur(s) {{
  if (s == null) return '-';
  if (s < 60) return s.toFixed(1) + 's';
  return Math.floor(s / 60) + 'm ' + Math.round(s % 60) + 's';
}}

function renderSections() {{
  const grid = document.getElementById('sectionsGrid');
  grid.innerHTML = DATA.map((sec, i) => {{
    const skipCount = sec.skip || 0;
    const executed = sec.total - skipCount;
    const pct = executed ? Math.round(sec.ok / executed * 100) : (sec.total === 0 ? 100 : 0);
    const failPct = sec.total ? Math.round(sec.fail / sec.total * 100) : 0;
    const toPct = sec.total ? Math.round(sec.timeout / sec.total * 100) : 0;
    const skipPct = sec.total ? Math.round(skipCount / sec.total * 100) : 0;
    const okPct = 100 - failPct - toPct - skipPct;
    let badge, badgeText;
    if (sec.total === 0) {{ badge = 'empty'; badgeText = 'EMPTY'; }}
    else if (sec.fail === 0 && skipCount === 0) {{ badge = 'perfect'; badgeText = 'PERFECT'; }}
    else if (pct >= 50) {{ badge = 'partial'; badgeText = pct + '%'; }}
    else {{ badge = 'bad'; badgeText = pct + '%'; }}
    return `
      <div class="section-card" data-idx="${{i}}" onclick="selectSection(${{i}})">
        <div class="section-head">
          <div class="section-name">${{sec.section}}</div>
          <div class="section-badge ${{badge}}">${{badgeText}}</div>
        </div>
        <div class="section-title">${{escHtml(sec.title || '')}}</div>
        <div class="section-stats">
          <span>${{sec.total}} runs</span>
          <span class="s-ok">${{sec.ok}} ok</span>
          ${{sec.fail > 0 ? `<span class="s-fail">${{sec.fail}} fail</span>` : ''}}
          ${{skipCount > 0 ? `<span class="s-skip">${{skipCount}} skip</span>` : ''}}
          ${{sec.timeout > 0 ? `<span class="s-to">${{sec.timeout}} timeout</span>` : ''}}
          <span class="s-dur">${{fmtDur(sec.duration)}}</span>
        </div>
        <div class="section-bar">
          <div class="bar-ok" style="width:${{okPct}}%"></div>
          <div class="bar-fail" style="width:${{failPct}}%"></div>
          <div class="bar-skip" style="width:${{skipPct}}%"></div>
          <div class="bar-to" style="width:${{toPct}}%"></div>
        </div>
      </div>`;
  }}).join('');
}}

function selectSection(idx) {{
  activeSection = idx;
  selectedRunId = null;
  document.querySelectorAll('.section-card').forEach((c, i) => {{
    c.classList.toggle('active', i === idx);
  }});
  const sec = DATA[idx];
  const panel = document.getElementById('detailPanel');
  panel.classList.add('visible');
  document.getElementById('detailTitle').innerHTML =
    `${{escHtml(sec.title || sec.section)}} <span>${{sec.total}} runs &middot; ${{fmtDur(sec.duration)}} &middot; ${{sec.target}}</span>`;
  document.getElementById('searchBox').value = '';
  activeFilter = 'all';
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.toggle('active', b.dataset.filter === 'all'));
  switchTab('results');
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === 'results'));
  closeDrawer();
  renderRuns();
  panel.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
}}

function closeDetail() {{
  document.getElementById('detailPanel').classList.remove('visible');
  document.querySelectorAll('.section-card').forEach(c => c.classList.remove('active'));
  activeSection = null;
}}

function colorizeLog(text) {{
  return escHtml(text).split('\\n').map(line => {{
    if (/Exit: 0|-> exit 0|complete \\(/.test(line))
      return `<span class="log-ok">${{line}}</span>`;
    if (/SKIP:|skipped/.test(line))
      return `<span class="log-skip">${{line}}</span>`;
    if (/Exit: [^0]|TIMEOUT|FAIL|-> exit [^0]|Error:/.test(line))
      return `<span class="log-err">${{line}}</span>`;
    if (/Warning:/.test(line))
      return `<span class="log-warn">${{line}}</span>`;
    if (/\\[SR-/.test(line) || /Lifecycle:/.test(line))
      return `<span class="log-info">${{line}}</span>`;
    if (/^={3,}|^-{{3,}}/.test(line))
      return `<span class="log-dim">${{line}}</span>`;
    if (/^\\s+(Command:|Expects:|Review:)/.test(line))
      return `<span class="log-dim">${{line}}</span>`;
    return line;
  }}).join('\\n');
}}

function renderLog() {{
  if (activeSection === null) return;
  const sec = DATA[activeSection];
  const viewer = document.getElementById('logViewer');
  const log = sec.log || '';
  if (!log.trim()) {{
    viewer.innerHTML = '<div class="log-empty">No log output available for this section.</div>';
    return;
  }}
  viewer.innerHTML = colorizeLog(log);
}}

/* Extract log lines for a specific run ID from the section log */
function extractRunLog(log, runId) {{
  if (!log) return null;
  const lines = log.split('\\n');
  const pattern = `[${{runId}}]`;
  let startIdx = -1;
  for (let i = 0; i < lines.length; i++) {{
    if (lines[i].includes(pattern)) {{
      startIdx = i;
      break;
    }}
  }}
  if (startIdx === -1) return null;
  /* Capture until next [SR-xxx] header or section separator */
  let endIdx = lines.length;
  for (let i = startIdx + 1; i < lines.length; i++) {{
    if (/^\\[SR-/.test(lines[i].trim()) || /^Lifecycle SR-/.test(lines[i].trim()) || /^-{{20,}}/.test(lines[i].trim()) || /^Section /.test(lines[i].trim())) {{
      endIdx = i;
      break;
    }}
  }}
  return lines.slice(startIdx, endIdx).join('\\n').trimEnd();
}}

function openDrawer(runId, slug) {{
  const sec = DATA[activeSection];
  const log = extractRunLog(sec.log || '', runId);
  selectedRunId = runId;
  document.getElementById('drawerRunId').textContent = runId;
  document.getElementById('drawerRunSlug').textContent = ' — ' + slug;
  const body = document.getElementById('drawerLogBody');
  if (log) {{
    body.innerHTML = colorizeLog(log);
  }} else {{
    body.innerHTML = '<span class="log-empty">No log excerpt found for this run.</span>';
  }}
  document.getElementById('runLogDrawer').classList.add('visible');
  /* Highlight selected row */
  document.querySelectorAll('.runs-table tr[data-rid]').forEach(tr => {{
    tr.classList.toggle('selected', tr.dataset.rid === runId);
  }});
  document.getElementById('runLogDrawer').scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
}}

function closeDrawer() {{
  selectedRunId = null;
  document.getElementById('runLogDrawer').classList.remove('visible');
  document.querySelectorAll('.runs-table tr').forEach(tr => tr.classList.remove('selected'));
}}

function renderRuns() {{
  if (activeSection === null) return;
  const sec = DATA[activeSection];
  const q = document.getElementById('searchBox').value.toLowerCase();
  const tbody = document.getElementById('runsBody');

  const filtered = sec.runs.filter(r => {{
    const isSkip = r.command && r.command.startsWith('(skipped');
    const isLifecycle = r.command && r.command.startsWith('(lifecycle');
    if (activeFilter === 'ok' && (r.exit_code !== 0 || isSkip)) return false;
    if (activeFilter === 'fail' && (r.exit_code === 0 || isSkip)) return false;
    if (activeFilter === 'skip' && !isSkip) return false;
    if (activeFilter === 'timeout' && r.exit_code !== 124) return false;
    if (q) {{
      const hay = `${{r.id}} ${{r.slug}} ${{r.command}}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }}
    return true;
  }});

  tbody.innerHTML = filtered.map(r => {{
    const isSkip = r.command && r.command.startsWith('(skipped');
    const isLifecycle = r.command && r.command.startsWith('(lifecycle');
    let cls, label;
    if (isSkip) {{ cls = 'skip'; label = 'SKIP'; }}
    else if (isLifecycle) {{ cls = r.exit_code === 0 ? 'lifecycle' : 'err'; label = isLifecycle ? 'LC' : r.exit_code; }}
    else if (r.exit_code === 0) {{ cls = 'e0'; label = '0'; }}
    else if (r.exit_code === 124) {{ cls = 'e124'; label = 'TIMEOUT'; }}
    else {{ cls = 'err'; label = r.exit_code; }}
    const dur = typeof r.duration_seconds === 'number' && !isSkip ? r.duration_seconds.toFixed(1) + 's' : '-';
    const sel = r.id === selectedRunId ? ' selected' : '';
    return `
      <tr data-rid="${{r.id}}" class="${{sel}}" onclick="openDrawer('${{r.id}}', '${{escAttr(r.slug)}}')">
        <td class="run-id">${{r.id}}</td>
        <td class="run-slug">${{escHtml(r.slug)}}</td>
        <td class="run-cmd" title="${{escAttr(r.command)}}">${{escHtml(r.command)}}</td>
        <td><span class="exit-pill ${{cls}}">${{label}}</span></td>
        <td class="run-dur">${{dur}}</td>
      </tr>`;
  }}).join('');
}}

function escHtml(s) {{
  if (!s) return '';
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}}

function escAttr(s) {{
  if (!s) return '';
  return s.replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/'/g,'&#39;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}

init();
</script>
</body>
</html>"""

    return html.replace(PLACEHOLDER, sections_json)


def main():
    parser = argparse.ArgumentParser(
        description="Generate HTML report from sample run logs"
    )
    parser.add_argument(
        "log_dir", nargs="?", help="Path to log directory (default: latest)"
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output HTML path (default: <log_dir>/report.html)",
    )
    args = parser.parse_args()

    # Resolve log directory
    script_dir = Path(__file__).parent
    logs_base = script_dir.parent / "logs"

    # Also check parent-level logs
    parent_logs = Path(script_dir).parent.parent / "logs"

    if args.log_dir:
        log_dir = Path(args.log_dir)
    else:
        # Try raps-examples/logs first, then parent logs
        log_dir = None
        for base in [logs_base, parent_logs]:
            if base.exists():
                log_dir = find_latest_log_dir(base)
                if log_dir:
                    break
        if not log_dir:
            print("ERROR: No log directories found", file=sys.stderr)
            sys.exit(1)

    if not log_dir.exists():
        print(f"ERROR: Log directory not found: {log_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading results from: {log_dir}")
    sections = load_sections(log_dir)
    if not sections:
        print("ERROR: No JSON result files found", file=sys.stderr)
        sys.exit(1)

    print(f"  Found {len(sections)} sections")
    summary = compute_summary(sections)
    print(
        f"  Total: {summary['total_runs']} runs, {summary['total_ok']} ok, {summary['total_fail']} fail ({summary['pass_rate']}%)"
    )

    html = generate_html(summary, log_dir.name)

    output_path = Path(args.output) if args.output else (log_dir / "report.html")
    output_path.write_text(html, encoding="utf-8")
    print(f"  Report: {output_path}")
    print(f"\nOpen in browser: file:///{output_path.resolve().as_posix()}")


if __name__ == "__main__":
    main()
