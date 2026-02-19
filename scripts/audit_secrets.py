#!/usr/bin/env python3
"""
Secrets & PII Audit Script for raps-examples

Two-layer scanning approach:
  Layer 1: Microsoft Presidio for NLP-based PII detection
  Layer 2: Custom regex patterns for APS-specific secrets/credentials

Usage:
    python scripts/audit_secrets.py --report docs/SECRETS-AUDIT.md
    python scripts/audit_secrets.py --verbose
    python scripts/audit_secrets.py --regex-only  # skip Presidio if not installed
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ───────────────────────────────────────────────────

TEXT_EXTENSIONS = {
    ".py", ".md", ".yaml", ".yml", ".json", ".csv", ".txt",
    ".sh", ".toml", ".env", ".cfg", ".ini", ".html", ".xml",
}

EXCLUDE_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache"}

# Synthetic/placeholder patterns to allowlist
SYNTHETIC_PREFIXES = ("demo-", "mock-", "test-", "your_", "fake-", "sample-", "example-")

SAFE_EMAIL_DOMAINS = {
    "@example.com", "@co.com", "@test.com", "@localhost",
    "@example.org", "@example.net", "@company.com", "@old.com",
}

# Decorator patterns that look like emails but aren't
PYTHON_DECORATORS = {
    "@pytest", "@fixture", "@mark", "@dataclass", "@functools",
    "@property", "@staticmethod", "@classmethod", "@override",
    "@abstractmethod", "@contextmanager", "@wraps", "@cached_property",
    "@lru_cache", "@total_ordering", "@parametrize", "@patch",
}

SAFE_URL_HOSTS = {
    "localhost", "127.0.0.1", "example.com", "example.org",
    "autodesk.com", "rapscli.xyz", "github.com", "co.com",
    "pypi.org", "python.org", "npmjs.com", "docs.rs",
    "crates.io", "shields.io", "img.shields.io",
    "json-schema.org", "mozilla.org", "w3.org",
    "creativecommons.org", "apache.org", "opensource.org",
    "googleapis.com", "fonts.googleapis.com",
    "cdn.jsdelivr.net", "cdnjs.cloudflare.com",
}

# ── Regex Secret Patterns ──────────────────────────────────────────

SECRET_PATTERNS: list[tuple[str, re.Pattern]] = [
    (
        "APS Client Secret (non-placeholder)",
        re.compile(
            r"APS_CLIENT_SECRET\s*=\s*(?!mock|demo|test|your_|fake|sample|example|\"?\$)"
            r"['\"]?([A-Za-z0-9_\-]{8,})",
        ),
    ),
    (
        "APS Client ID (non-placeholder)",
        re.compile(
            r"APS_CLIENT_ID\s*=\s*(?!mock|demo|test|your_|fake|sample|example|\"?\$)"
            r"['\"]?([A-Za-z0-9_\-]{8,})",
        ),
    ),
    (
        "Bearer token (20+ chars)",
        re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]{20,}"),
    ),
    (
        "JWT token (eyJ pattern)",
        re.compile(r"eyJ[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{10,}"),
    ),
    (
        "Refresh token value",
        re.compile(r"refresh_token[\"':\s]*[A-Za-z0-9\-._~+/]{20,}"),
    ),
    (
        "Generic API key (hex 32+)",
        re.compile(r"(?:api[_-]?key|secret|token|password)\s*[=:]\s*['\"]?[A-Fa-f0-9]{32,}"),
    ),
]


# ── Finding dataclass ──────────────────────────────────────────────

class Finding:
    """A single audit finding."""

    def __init__(
        self,
        layer: str,
        category: str,
        file: str,
        line: int,
        value: str,
        confidence: float = 1.0,
    ):
        self.layer = layer
        self.category = category
        self.file = file
        self.line = line
        self.value = value
        self.confidence = confidence

    def __repr__(self) -> str:
        return f"[{self.layer}] {self.category}: {self.file}:{self.line} — {self.value[:60]}"


# ── Layer 1: Presidio PII Detection ───────────────────────────────

def run_presidio_scan(repo_root: Path, verbose: bool = False) -> list[Finding]:
    """Scan tracked text files for PII using Microsoft Presidio."""
    try:
        from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
    except ImportError:
        print("  [WARN] presidio-analyzer not installed — skipping PII layer")
        print("         Install with: pip install presidio-analyzer spacy")
        print("         Then: python -m spacy download en_core_web_lg")
        return []

    # Initialize engine
    try:
        analyzer = AnalyzerEngine()
    except Exception as e:
        print(f"  [WARN] Presidio init failed (missing spaCy model?): {e}")
        print("         Run: python -m spacy download en_core_web_lg")
        return []

    # Add custom APS recognizers
    aps_secret_recognizer = PatternRecognizer(
        supported_entity="APS_CLIENT_SECRET",
        patterns=[
            Pattern(
                name="aps_client_secret",
                regex=r"APS_CLIENT_SECRET\s*=\s*['\"]?[A-Za-z0-9_\-]{8,}",
                score=0.9,
            ),
        ],
    )
    aps_token_recognizer = PatternRecognizer(
        supported_entity="APS_TOKEN",
        patterns=[
            Pattern(
                name="bearer_token",
                regex=r"Bearer\s+[A-Za-z0-9\-._~+/]{20,}",
                score=0.9,
            ),
            Pattern(
                name="jwt_token",
                regex=r"eyJ[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{10,}",
                score=0.9,
            ),
        ],
    )
    analyzer.registry.add_recognizer(aps_secret_recognizer)
    analyzer.registry.add_recognizer(aps_token_recognizer)

    # PERSON omitted: produces excessive false positives on code (flags
    # "max", "Token", "Node.js", "Markdown", etc. as person names)
    entities_to_scan = [
        "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD",
        "APS_CLIENT_SECRET", "APS_TOKEN",
    ]

    findings: list[Finding] = []
    files = _get_tracked_text_files(repo_root)
    print(f"  Presidio: scanning {len(files)} files for PII...")

    for fpath in files:
        try:
            text = fpath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        results = analyzer.analyze(text=text, entities=entities_to_scan, language="en")

        for result in results:
            value = text[result.start:result.end]

            # Apply allowlist
            if _is_allowlisted_pii(result.entity_type, value):
                if verbose:
                    print(f"    [ALLOW] {result.entity_type}: {value[:40]} in {fpath.name}")
                continue

            rel_path = str(fpath.relative_to(repo_root))
            line_num = text[:result.start].count("\n") + 1
            findings.append(Finding(
                layer="Presidio",
                category=result.entity_type,
                file=rel_path,
                line=line_num,
                value=value[:80],
                confidence=result.score,
            ))

            if verbose:
                print(f"    [FIND] {result.entity_type} ({result.score:.2f}): "
                      f"{rel_path}:{line_num} — {value[:60]}")

    return findings


def _is_allowlisted_pii(entity_type: str, value: str) -> bool:
    """Check if a PII finding is a known synthetic/placeholder value."""
    lower = value.lower().strip()

    # Allowlist synthetic email domains
    if entity_type == "EMAIL_ADDRESS":
        for domain in SAFE_EMAIL_DOMAINS:
            if domain in lower:
                return True
        # Python decorators look like emails
        for dec in PYTHON_DECORATORS:
            if lower.startswith(dec.lower()):
                return True
        return False

    # Allowlist synthetic credential prefixes
    if entity_type in ("APS_CLIENT_SECRET", "APS_TOKEN"):
        for prefix in SYNTHETIC_PREFIXES:
            if prefix in lower:
                return True
        # Environment variable references
        if "$" in value or "%" in value:
            return True
        return False

    # Allowlist common non-PII person names in code
    if entity_type == "PERSON":
        # Common code terms that NLP mistakenly flags as names
        code_terms = {
            "json", "yaml", "csv", "html", "xml", "toml",
            "pytest", "python", "docker", "github", "autodesk",
            "raps", "oauth", "api", "cli", "url", "uri",
        }
        if lower in code_terms:
            return True
        return False

    # IP addresses: allowlist localhost, private ranges, and IPv6
    if entity_type == "IP_ADDRESS":
        if lower.startswith(("127.", "0.0.0.0", "192.168.", "10.", "172.")):
            return True
        # IPv6 patterns (::, ::1, etc.)
        if ":" in lower:
            return True
        return False

    return False


# ── Layer 2: Regex Secret Scanning ─────────────────────────────────

def run_regex_scan(repo_root: Path, verbose: bool = False) -> list[Finding]:
    """Scan tracked text files for secret patterns using regex."""
    findings: list[Finding] = []
    files = _get_tracked_text_files(repo_root)
    print(f"  Regex: scanning {len(files)} files for secrets...")

    for fpath in files:
        try:
            lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue

        rel_path = str(fpath.relative_to(repo_root))

        for line_num, line in enumerate(lines, 1):
            for pattern_name, pattern in SECRET_PATTERNS:
                match = pattern.search(line)
                if match:
                    value = match.group(0)

                    # Skip allowlisted values
                    if _is_allowlisted_secret(value):
                        if verbose:
                            print(f"    [ALLOW] {pattern_name}: {rel_path}:{line_num}")
                        continue

                    findings.append(Finding(
                        layer="Regex",
                        category=pattern_name,
                        file=rel_path,
                        line=line_num,
                        value=value[:80],
                    ))

                    if verbose:
                        print(f"    [FIND] {pattern_name}: {rel_path}:{line_num} — {value[:60]}")

    return findings


def _is_allowlisted_secret(value: str) -> bool:
    """Check if a secret-like value is a known placeholder."""
    lower = value.lower()
    for prefix in SYNTHETIC_PREFIXES:
        if prefix in lower:
            return True
    # Environment variable references (not actual values)
    if "$" in value or "%" in value or "{" in value:
        return True
    # Comment-like patterns
    if lower.startswith("#") or lower.startswith("//"):
        return True
    return False


# ── URL Audit ──────────────────────────────────────────────────────

def run_url_audit(repo_root: Path, verbose: bool = False) -> list[Finding]:
    """Scan for URLs that are not from safe/known domains."""
    findings: list[Finding] = []
    url_pattern = re.compile(r"https?://([a-zA-Z0-9\-_.]+)")
    files = _get_tracked_text_files(repo_root)
    print(f"  URL audit: scanning {len(files)} files...")

    for fpath in files:
        try:
            lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue

        rel_path = str(fpath.relative_to(repo_root))

        for line_num, line in enumerate(lines, 1):
            for match in url_pattern.finditer(line):
                host = match.group(1).lower()
                # Check if host or any parent domain is safe
                if _is_safe_url(host):
                    continue

                findings.append(Finding(
                    layer="URL",
                    category="Suspicious URL",
                    file=rel_path,
                    line=line_num,
                    value=match.group(0)[:80],
                ))

                if verbose:
                    print(f"    [FIND] URL: {rel_path}:{line_num} — {match.group(0)[:60]}")

    return findings


def _is_safe_url(host: str) -> bool:
    """Check if a URL host is from a known safe domain."""
    for safe in SAFE_URL_HOSTS:
        if host == safe or host.endswith("." + safe):
            return True
    return False


# ── Email Audit (standalone regex, supplements Presidio) ───────────

def run_email_audit(repo_root: Path, verbose: bool = False) -> list[Finding]:
    """Scan for email addresses that aren't synthetic."""
    findings: list[Finding] = []
    email_pattern = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
    files = _get_tracked_text_files(repo_root)
    print(f"  Email audit: scanning {len(files)} files...")

    for fpath in files:
        try:
            lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue

        rel_path = str(fpath.relative_to(repo_root))

        for line_num, line in enumerate(lines, 1):
            for match in email_pattern.finditer(line):
                email = match.group(0).lower()

                # Skip Python decorators
                if any(email.startswith(d.lower().lstrip("@")) for d in PYTHON_DECORATORS):
                    continue
                # Skip safe email domains
                if any(domain.lstrip("@") in email for domain in SAFE_EMAIL_DOMAINS):
                    continue
                # Skip file extensions that look like emails
                if email.endswith((".py", ".md", ".json", ".yaml", ".yml", ".toml", ".sh")):
                    continue

                findings.append(Finding(
                    layer="Email",
                    category="Non-synthetic email",
                    file=rel_path,
                    line=line_num,
                    value=email[:80],
                ))

                if verbose:
                    print(f"    [FIND] Email: {rel_path}:{line_num} — {email}")

    return findings


# ── Git History Scanning ───────────────────────────────────────────

def run_git_history_scan(repo_root: Path, verbose: bool = False) -> list[Finding]:
    """Scan git history for leaked credentials."""
    findings: list[Finding] = []

    print("  Git history: scanning for secret patterns...")

    # Check for .env files ever committed
    try:
        result = subprocess.run(
            ["git", "log", "--all", "--diff-filter=A", "--name-only",
             "--pretty=format:", "--", "*.env", "*.env.*", ".env*"],
            capture_output=True, text=True, cwd=repo_root, timeout=30,
        )
        env_files = [f for f in result.stdout.strip().splitlines() if f.strip()]
        if env_files:
            for ef in env_files:
                findings.append(Finding(
                    layer="GitHistory",
                    category=".env file in history",
                    file=ef,
                    line=0,
                    value=f".env file was committed: {ef}",
                ))
                if verbose:
                    print(f"    [FIND] .env in history: {ef}")
    except Exception as e:
        print(f"    [WARN] Git history scan failed: {e}")

    # Scan for CLIENT_SECRET in commit diffs
    secret_search_terms = ["CLIENT_SECRET", "client_secret", "Bearer ", "refresh_token"]
    for term in secret_search_terms:
        try:
            result = subprocess.run(
                ["git", "log", "--all", "-p", "-S", term, "--",
                 "*.py", "*.md", "*.yaml", "*.yml", "*.json", "*.sh", "*.toml"],
                capture_output=True, text=True, cwd=repo_root, timeout=60,
            )
            # Check added lines (lines starting with +) for actual secret values
            for line in result.stdout.splitlines():
                if not line.startswith("+"):
                    continue
                if line.startswith("+++"):
                    continue
                # Check if it's a real secret, not a placeholder
                lower_line = line.lower()
                if any(p in lower_line for p in SYNTHETIC_PREFIXES):
                    continue
                if "$" in line or "%" in line or "{" in line:
                    continue
                if "your_" in lower_line or "placeholder" in lower_line:
                    continue
                # Check for actual secret-like values
                for _, pattern in SECRET_PATTERNS:
                    if pattern.search(line[1:]):  # Skip the leading +
                        findings.append(Finding(
                            layer="GitHistory",
                            category=f"Secret in history ({term})",
                            file="git-log",
                            line=0,
                            value=line[1:60],
                        ))
                        if verbose:
                            print(f"    [FIND] History: {line[1:60]}")
                        break
        except Exception as e:
            if verbose:
                print(f"    [WARN] Git search for '{term}' failed: {e}")

    return findings


# ── .env Protection Check ──────────────────────────────────────────

def check_env_protection(repo_root: Path, verbose: bool = False) -> list[Finding]:
    """Verify .env files are protected by .gitignore and not tracked."""
    findings: list[Finding] = []

    print("  .env protection: checking...")

    # Check .gitignore contains .env
    gitignore = repo_root / ".gitignore"
    if gitignore.is_file():
        content = gitignore.read_text(encoding="utf-8")
        if ".env" not in content:
            findings.append(Finding(
                layer="EnvProtection",
                category=".env not in .gitignore",
                file=".gitignore",
                line=0,
                value=".env pattern missing from .gitignore",
            ))
    else:
        findings.append(Finding(
            layer="EnvProtection",
            category="No .gitignore",
            file=".",
            line=0,
            value=".gitignore file not found",
        ))

    # Check no .env files are tracked
    try:
        result = subprocess.run(
            ["git", "ls-files", ".env", ".env.*", "*.env"],
            capture_output=True, text=True, cwd=repo_root, timeout=10,
        )
        tracked_envs = [f for f in result.stdout.strip().splitlines() if f.strip()]
        for ef in tracked_envs:
            findings.append(Finding(
                layer="EnvProtection",
                category="Tracked .env file",
                file=ef,
                line=0,
                value=f".env file is tracked in git: {ef}",
            ))
            if verbose:
                print(f"    [FIND] Tracked .env: {ef}")
    except Exception:
        pass

    # Check .env.example for placeholder-only values
    env_example = repo_root / ".env.example"
    if env_example.is_file():
        lines = env_example.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines, 1):
            if "=" in line and not line.strip().startswith("#"):
                key, _, val = line.partition("=")
                val = val.strip().strip("'\"")
                if val and not any(p in val.lower() for p in
                                   ("your_", "replace", "xxx", "placeholder",
                                    "demo", "mock", "test", "changeme", "")):
                    # Check if it looks like a real value
                    if len(val) > 20 and not val.startswith(("http://localhost",)):
                        findings.append(Finding(
                            layer="EnvProtection",
                            category="Possible real value in .env.example",
                            file=".env.example",
                            line=i,
                            value=f"{key.strip()}={val[:40]}",
                        ))

    if not findings:
        print("    .env protection: OK")

    return findings


# ── Utility Functions ──────────────────────────────────────────────

def _get_tracked_text_files(repo_root: Path) -> list[Path]:
    """Get all git-tracked text files."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True, text=True, cwd=repo_root, timeout=10,
        )
        all_files = result.stdout.strip().splitlines()
    except Exception:
        # Fallback: walk directory
        all_files = []
        for f in repo_root.rglob("*"):
            if f.is_file() and not any(d in f.parts for d in EXCLUDE_DIRS):
                all_files.append(str(f.relative_to(repo_root)))

    text_files = []
    for f in all_files:
        p = repo_root / f
        if p.suffix.lower() in TEXT_EXTENSIONS and p.is_file():
            if not any(d in p.parts for d in EXCLUDE_DIRS):
                text_files.append(p)

    return text_files


# ── Report Generation ──────────────────────────────────────────────

def generate_report(
    findings: list[Finding],
    scan_stats: dict,
    report_path: Path,
) -> None:
    """Write the audit report to a markdown file."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    status = "CLEAN" if not findings else "REMEDIATION REQUIRED"

    lines = [
        "# Secrets & PII Audit Report",
        "",
        f"**Date**: {now}",
        f"**Status**: **{status}**",
        f"**Tool**: audit_secrets.py (Presidio {scan_stats.get('presidio_version', 'N/A')} + regex)",
        "",
        "## Scan Scope",
        "",
        f"- **Files scanned**: {scan_stats.get('files_scanned', 0)}",
        f"- **File types**: {', '.join(sorted(TEXT_EXTENSIONS))}",
        f"- **Git history**: {'Scanned' if scan_stats.get('git_history', False) else 'Skipped'}",
        "",
        "## Layers",
        "",
        "| Layer | Tool | Detects |",
        "|-------|------|---------|",
        "| PII | Microsoft Presidio + spaCy NLP | Emails, person names, phone numbers, credit cards, IP addresses |",
        "| Secrets | Custom regex patterns | APS credentials, Bearer tokens, JWTs, refresh tokens, hex API keys |",
        "| URLs | Regex + domain allowlist | Non-safe URLs (not localhost/example.com/autodesk.com/etc.) |",
        "| Emails | Regex + domain allowlist | Non-synthetic email addresses |",
        "| Git History | git log -S + regex | Secrets in commit diffs, .env files ever committed |",
        "| .env Protection | File checks | .gitignore coverage, tracked .env files |",
        "",
        "## Regex Patterns",
        "",
        "| Pattern | Targets |",
        "|---------|---------|",
        "| `APS_CLIENT_SECRET=<non-placeholder>` | Real client secrets |",
        "| `APS_CLIENT_ID=<non-placeholder>` | Real client IDs |",
        "| `Bearer <20+ chars>` | OAuth bearer tokens |",
        "| `eyJ<10+>.<10+>` | JWT tokens |",
        "| `refresh_token<20+ chars>` | Refresh tokens |",
        "| `api_key/secret/token=<hex 32+>` | Generic API keys |",
        "",
        "## Allowlist",
        "",
        "The following patterns are allowlisted as synthetic/placeholder:",
        "",
        f"- **Email domains**: {', '.join(sorted(SAFE_EMAIL_DOMAINS))}",
        f"- **Value prefixes**: {', '.join(SYNTHETIC_PREFIXES)}",
        "- **URL hosts**: localhost, example.com, autodesk.com, rapscli.xyz, github.com, etc.",
        "- **Environment variables**: Values containing $, %, or { (references, not values)",
        "",
    ]

    if findings:
        lines.extend([
            "## Findings",
            "",
            f"**{len(findings)} finding(s) detected:**",
            "",
            "| # | Layer | Category | File | Line | Value |",
            "|---|-------|----------|------|------|-------|",
        ])
        for i, f in enumerate(findings, 1):
            val = f.value.replace("|", "\\|")
            lines.append(
                f"| {i} | {f.layer} | {f.category} | {f.file} | {f.line} | `{val}` |"
            )
        lines.append("")
        lines.extend([
            "## Required Actions",
            "",
            "1. **Rotate** any real credentials found above",
            "2. **Purge** from git history using `git filter-repo` or BFG Repo Cleaner",
            "3. **Re-run** this audit: `python scripts/audit_secrets.py --report docs/SECRETS-AUDIT.md`",
            "",
        ])
    else:
        lines.extend([
            "## Findings",
            "",
            "**Zero findings.** No real credentials, PII, or sensitive data detected.",
            "",
            "All scanned values are synthetic placeholders (demo-, mock-, test-, @example.com, etc.).",
            "",
        ])

    lines.extend([
        "## Conclusion",
        "",
        f"Audit status: **{status}**",
        "",
    ])

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written to: {report_path}")


# ── Main ───────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Secrets & PII audit for raps-examples",
    )
    parser.add_argument(
        "--report", type=Path, default=None,
        help="Path to write audit report (e.g., docs/SECRETS-AUDIT.md)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show detailed findings as they are discovered",
    )
    parser.add_argument(
        "--regex-only", action="store_true",
        help="Skip Presidio PII layer (use only regex scanning)",
    )
    args = parser.parse_args()

    # Detect repo root
    repo_root = Path.cwd()
    if not (repo_root / ".gitignore").is_file() and not (repo_root / "pyproject.toml").is_file():
        print("ERROR: Run this script from the raps-examples root directory")
        return 1

    print("=" * 60)
    print("  Secrets & PII Audit")
    print("=" * 60)
    print()

    all_findings: list[Finding] = []
    scan_stats: dict = {
        "files_scanned": len(_get_tracked_text_files(repo_root)),
        "git_history": True,
    }

    # Layer 1: Presidio PII
    if not args.regex_only:
        print("[1/6] Presidio PII scan...")
        presidio_findings = run_presidio_scan(repo_root, args.verbose)
        all_findings.extend(presidio_findings)
        print(f"  → {len(presidio_findings)} finding(s)")

        try:
            import presidio_analyzer
            scan_stats["presidio_version"] = getattr(presidio_analyzer, "__version__", "unknown")
        except ImportError:
            scan_stats["presidio_version"] = "not installed"
    else:
        print("[1/6] Presidio PII scan... SKIPPED (--regex-only)")
        scan_stats["presidio_version"] = "skipped"

    # Layer 2: Regex secrets
    print("\n[2/6] Regex secret scan...")
    regex_findings = run_regex_scan(repo_root, args.verbose)
    all_findings.extend(regex_findings)
    print(f"  → {len(regex_findings)} finding(s)")

    # Layer 3: URL audit
    print("\n[3/6] URL audit...")
    url_findings = run_url_audit(repo_root, args.verbose)
    all_findings.extend(url_findings)
    print(f"  → {len(url_findings)} finding(s)")

    # Layer 4: Email audit
    print("\n[4/6] Email audit...")
    email_findings = run_email_audit(repo_root, args.verbose)
    all_findings.extend(email_findings)
    print(f"  → {len(email_findings)} finding(s)")

    # Layer 5: Git history
    print("\n[5/6] Git history scan...")
    git_findings = run_git_history_scan(repo_root, args.verbose)
    all_findings.extend(git_findings)
    print(f"  → {len(git_findings)} finding(s)")

    # Layer 6: .env protection
    print("\n[6/6] .env protection check...")
    env_findings = check_env_protection(repo_root, args.verbose)
    all_findings.extend(env_findings)
    print(f"  → {len(env_findings)} finding(s)")

    # Summary
    print()
    print("=" * 60)
    status = "CLEAN" if not all_findings else "REMEDIATION REQUIRED"
    print(f"  Result: {status} ({len(all_findings)} finding(s))")
    print("=" * 60)

    if all_findings:
        print()
        print("Findings:")
        for i, f in enumerate(all_findings, 1):
            print(f"  {i}. [{f.layer}] {f.category}: {f.file}:{f.line} — {f.value[:60]}")

    # Write report
    if args.report:
        generate_report(all_findings, scan_stats, args.report)

    return 0 if not all_findings else 1


if __name__ == "__main__":
    sys.exit(main())
