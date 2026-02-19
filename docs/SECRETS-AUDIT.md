# Secrets & PII Audit Report

**Date**: 2026-02-18 19:20 UTC
**Status**: **CLEAN**
**Tool**: audit_secrets.py (Presidio unknown + regex)

## Scan Scope

- **Files scanned**: 87
- **File types**: .cfg, .csv, .env, .html, .ini, .json, .md, .py, .sh, .toml, .txt, .xml, .yaml, .yml
- **Git history**: Scanned

## Layers

| Layer | Tool | Detects |
|-------|------|---------|
| PII | Microsoft Presidio + spaCy NLP | Emails, person names, phone numbers, credit cards, IP addresses |
| Secrets | Custom regex patterns | APS credentials, Bearer tokens, JWTs, refresh tokens, hex API keys |
| URLs | Regex + domain allowlist | Non-safe URLs (not localhost/example.com/autodesk.com/etc.) |
| Emails | Regex + domain allowlist | Non-synthetic email addresses |
| Git History | git log -S + regex | Secrets in commit diffs, .env files ever committed |
| .env Protection | File checks | .gitignore coverage, tracked .env files |

## Regex Patterns

| Pattern | Targets |
|---------|---------|
| `APS_CLIENT_SECRET=<non-placeholder>` | Real client secrets |
| `APS_CLIENT_ID=<non-placeholder>` | Real client IDs |
| `Bearer <20+ chars>` | OAuth bearer tokens |
| `eyJ<10+>.<10+>` | JWT tokens |
| `refresh_token<20+ chars>` | Refresh tokens |
| `api_key/secret/token=<hex 32+>` | Generic API keys |

## Allowlist

The following patterns are allowlisted as synthetic/placeholder:

- **Email domains**: @co.com, @company.com, @example.com, @example.net, @example.org, @localhost, @old.com, @test.com
- **Value prefixes**: demo-, mock-, test-, your_, fake-, sample-, example-
- **URL hosts**: localhost, example.com, autodesk.com, rapscli.xyz, github.com, etc.
- **Environment variables**: Values containing $, %, or { (references, not values)

## Findings

**Zero findings.** No real credentials, PII, or sensitive data detected.

All scanned values are synthetic placeholders (demo-, mock-, test-, @example.com, etc.).

## Conclusion

Audit status: **CLEAN**
