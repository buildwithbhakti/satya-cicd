# Satya CI - Accessibility Testing for CI/CD

> 🎯 **Integrate Satya accessibility engine into your CI/CD pipeline**

Satya CI is a command-line tool that automates accessibility testing using the Satya engine. It's designed for CI/CD environments and can test both remote URLs and local directories.

## Features

- ✅ **CLI-based** - Easy to integrate into any CI/CD system
- ✅ **Headless testing** - Uses Puppeteer/Chromium for real browser testing
- ✅ **Local directory support** - Automatically starts a static file server
- ✅ **Configurable** - `.satyarc.json` for project-specific rules and thresholds
- ✅ **Multiple outputs** - JSON (machine-readable) and HTML (human-readable) reports
- ✅ **Exit codes** - Returns 0/1 for pass/fail in automated pipelines
- ✅ **Docker ready** - Includes Dockerfile with all dependencies
- ✅ **Ignore selectors** - Skip known issues or development elements

## Quick Start

### Installation

```bash
npm install satya-engine-ci
```

### Run a test

```bash
# Test a URL
npx satya-ci --target https://example.com --threshold 0

# Test a local directory
npx satya-ci --target ./dist --threshold 5
```

### View results

Reports are generated in `./reports/` by default:

```
reports/
├── satya-report.json    # Machine-readable
└── satya-report.html    # Human-readable
```

## CLI Options

| Option | Description |
|--------|-------------|
| `-t, --target <path>` | Target URL or local directory (required) |
| `--threshold <number>` | Max allowed violations before failing (default: 0) |
| `--config <path>` | Path to .satyarc.json config file |
| `--output <dir>` | Output directory for reports (default: ./reports) |
| `--ignore-dom <selectors>` | Comma-separated CSS selectors to ignore |

## Project Structure

```
satya-engine-ci/
├── src/
│   ├── cli.js              # Main CLI entry point
│   ├── puppeteer-runner.js # Browser automation
│   └── report-generator.js # Report generation
├── scripts/
│   └── satya.min.js        # Satya accessibility engine
├── docs/                   # Documentation
│   ├── setup.md           # Setup guide
│   ├── configuration.md   # Config reference
│   └── ci-cd-examples.md  # CI/CD integration
├── .satyarc.json.example  # Example config
├── Dockerfile             # Container image
├── package.json
└── README.md
```

## Configuration

Create `.satyarc.json` in your project root:

```json
{
  "rules": {
    "color-contrast": { "enabled": true, "severity": "critical" },
    "image-alt": { "enabled": true, "severity": "high" }
  },
  "ignoreDom": [".debug-mode"],
  "viewport": { "width": 1280, "height": 800 },
  "timeout": 30000,
  "waitAfterNavigation": 2000
}
```

See [Configuration Reference](docs/configuration.md) for all options.

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run accessibility tests
  run: npx satya-ci --target ${{ github.event.deployment_status.target_url }} --threshold 0

- name: Upload reports
  uses: actions/upload-artifact@v3
  with:
    name: a11y-reports
    path: reports/
```

See [CI/CD Examples](docs/ci-cd-examples.md) for GitLab, Jenkins, CircleCI, Azure DevOps, and Bitbucket.

## Docker

```bash
# Build image
docker build -t satya-ci .

# Run
docker run --rm satya-ci --target https://example.com --threshold 0

# Save reports
docker run --rm -v $(pwd)/reports:/app/reports satya-ci --target https://example.com
```

## Exit Codes

| Code | Condition |
|------|-----------|
| 0 | Test passed (violations ≤ threshold) |
| 1 | Test failed (violations > threshold) |

This allows you to fail CI builds when accessibility thresholds are exceeded.

## Requirements

- Node.js 18+
- Chromium dependencies (included in Docker)

## Documentation

- [Setup Guide](docs/setup.md)
- [Integration Guide](docs/integration-guide.md)
- [Configuration Reference](docs/configuration.md)
- [CI/CD Examples](docs/ci-cd-examples.md)

## License

ISC

## Author

shashwat@cdacmumbai