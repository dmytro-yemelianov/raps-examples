# RAPS Examples

This repository contains code that validates claims and statements from the [RAPS blog articles](https://rapscli.xyz/blog). Each benchmark and test is designed to run in Docker and produce metric reports as GitHub Actions artifacts.

## Blog Articles Validated

| Article | Validation Suite |
|---------|------------------|
| [The Manual Tax: What AEC Loses Without CI/CD](https://rapscli.xyz/blog/the-manual-tax) | `benchmarks/automation-timing/` |
| [CI/CD 101 for AEC Professionals](https://rapscli.xyz/blog/cicd-101-for-aec) | `benchmarks/pipeline-timing/` |
| [Authentication Chaos Across CAD Platforms](https://rapscli.xyz/blog/authentication-chaos) | `benchmarks/auth-flows/` |
| [File Translation Disasters](https://rapscli.xyz/blog/file-translation-disasters) | `benchmarks/translation-performance/` |
| [Why We Rewrote the Toolchain: Rust vs. Node.js](https://rapscli.xyz/blog/rust-vs-nodejs-5gb-files) | `benchmarks/rust-vs-nodejs/` |
| [SDK Version Hell](https://rapscli.xyz/blog/sdk-version-hell) | `benchmarks/version-compatibility/` |
| [Zero-Click Releases](https://rapscli.xyz/blog/zero-click-releases) | `benchmarks/design-automation/` |

## Key Claims Being Validated

### Performance Claims (from "Rust vs Node.js for 5GB Files")

| Claim | Test |
|-------|------|
| RAPS processes 3.4GB JSON in ~14 seconds | `rust-vs-nodejs/parse-large-json.sh` |
| RAPS uses ~100MB RAM (constant) | `rust-vs-nodejs/memory-profile.sh` |
| Node.js crashes on 3.4GB+ files | `rust-vs-nodejs/nodejs-baseline.js` |
| Batch processing: 5x 800MB in 42s | `rust-vs-nodejs/batch-process.sh` |

### Automation Claims (from "The Manual Tax" and "CI/CD 101")

| Claim | Test |
|-------|------|
| Automated pipeline vs manual timing | `automation-timing/compare.sh` |
| Upload + translate + notify pipeline | `pipeline-timing/full-pipeline.sh` |
| 13.45 hours/week savings calculation | `automation-timing/calculate-roi.py` |

### Feature Claims

| Claim | Test |
|-------|------|
| 15+ APS APIs supported | `feature-validation/count-apis.sh` |
| 100+ CLI commands | `feature-validation/count-commands.sh` |
| Multiple auth flows work | `auth-flows/test-all-flows.sh` |
| Cross-platform compatibility | GitHub Actions matrix build |

## Running Locally

### Prerequisites

- Docker and Docker Compose
- RAPS CLI installed (or use Docker image)
- APS credentials (for API tests)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/raps-examples.git
cd raps-examples

# Run all benchmarks (Docker)
docker compose up --build

# Run specific benchmark
docker compose run --rm benchmarks ./benchmarks/rust-vs-nodejs/run.sh

# Generate reports
docker compose run --rm reporter python scripts/generate-report.py
```

### Environment Variables

Create a `.env` file for API-dependent tests:

```env
APS_CLIENT_ID=your_client_id
APS_CLIENT_SECRET=your_client_secret
APS_CALLBACK_URL=http://localhost:8080/callback
```

## GitHub Actions

The workflows in `.github/workflows/` run automatically:

- **`benchmarks.yml`**: Runs all performance benchmarks on push/PR
- **`nightly.yml`**: Full validation suite nightly
- **`release-validation.yml`**: Validates claims against each RAPS release

### Artifacts Produced

Each workflow run produces:

- `benchmark-results.json` - Raw benchmark data
- `metrics-report.html` - Visual report with charts
- `metrics-report.md` - Markdown summary
- `memory-profiles/` - Memory usage graphs
- `comparison-tables/` - Performance comparison CSVs

## Directory Structure

```
raps-examples/
├── benchmarks/
│   ├── rust-vs-nodejs/        # Performance comparison tests
│   ├── automation-timing/     # Manual vs automated workflow timing
│   ├── pipeline-timing/       # CI/CD pipeline benchmarks
│   ├── auth-flows/            # Authentication flow validation
│   ├── translation-performance/ # Model translation benchmarks
│   ├── version-compatibility/ # Cross-version compatibility tests
│   ├── design-automation/     # DA workflow validation
│   └── feature-validation/    # Feature claim validation
├── scripts/
│   ├── generate-report.py     # Report generator
│   ├── generate-test-data.py  # Test data generator
│   └── utils/                 # Shared utilities
├── data/
│   ├── samples/               # Sample test files
│   └── generated/             # Generated test data (gitignored)
├── reports/                   # Generated reports (gitignored)
├── .github/workflows/         # GitHub Actions
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Contributing

1. Add new benchmark in `benchmarks/<category>/`
2. Create `run.sh` entry point
3. Output results to stdout in JSON format
4. Update this README with the new validation

## License

Apache 2.0 - Same as RAPS
