# Project Setup Guide

This guide covers setting up the Satya CI accessibility testing tool for local development and CI/CD integration.

## Prerequisites

- Node.js 18.0.0 or higher
- npm, yarn, or pnpm package manager
- Docker (optional, for containerized runs)

## Local Installation

### 1. Clone and Install

```bash
# Navigate to project root
cd /path/to/satya-engine-ci

# Install dependencies
npm install
```

### 2. Link the CLI Globally (Optional)

To use `satya-ci` from anywhere on your system:

```bash
npm link
```

Now you can run `satya-ci` from any directory.

### 3. Verify Installation

```bash
satya-ci --help
```

You should see the help output with available options.

## Docker Installation

### Build the Docker Image

```bash
docker build -t satya-ci:latest .
```

### Run with Docker

```bash
docker run --rm satya-ci:latest --target https://example.com
```

### Mount Local Directory for Reports

```bash
docker run --rm -v $(pwd)/reports:/app/reports satya-ci:latest --target https://example.com
```

## Configuration

The tool automatically looks for a `.satyarc.json` configuration file in the current working directory. You can also specify a custom config path with `--config`.

### Minimal Configuration

If no config file is found, the tool uses sensible defaults. However, it's recommended to create a configuration:

```bash
cp .satyarc.json.example .satyarc.json
```

Edit `.satyarc.json` to customize:
- Which rules are enabled/disabled
- Severity thresholds
- DOM elements to ignore
- Viewport size and timeouts

See [Configuration Reference](./configuration.md) for all options.

## Testing Locally

### Test a Local Directory

If you have a static site or HTML files to test locally:

```bash
satya-ci --target ./my-website --threshold 5
```

The tool will:
1. Start a static file server on a random port
2. Navigate to each HTML file found
3. Run accessibility tests
4. Generate reports in `./reports/` (default)

### Test a Remote URL

```bash
satya-ci --target https://example.com --threshold 0 --output ./a11y-reports
```

### Custom Ignore Selectors

```bash
satya-ci --target https://example.com --ignore-dom ".debug-mode,#dev-tools,.testing"
```

## Troubleshooting

### Chromium/Puppeteer Issues

If you encounter Puppeteer errors about missing libraries, ensure all system dependencies are installed. On Debian/Ubuntu:

```bash
sudo apt-get install -y \
  ca-certificates \
  fonts-liberation \
  libasound2 \
  libatk-bridge2.0-0 \
  libatk1.0-0 \
  libc6 \
  libcairo2 \
  libcups2 \
  libdbus-1-3 \
  libexpat1 \
  libfontconfig1 \
  libgbm1 \
  libgcc1 \
  libglib2.0-0 \
  libgtk-3-0 \
  libnspr4 \
  libnss3 \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libstdc++6 \
  libx11-6 \
  libx11-xcb1 \
  libxcb1 \
  libxcomposite1 \
  libxcursor1 \
  libxdamage1 \
  libxext6 \
  libxfixes3 \
  libxi6 \
  libxrandr2 \
  libxrender1 \
  libxss1 \
  libxtst6 \
  lsb-release \
  wget \
  xdg-utils
```

### Port Conflicts

When testing local directories, the tool uses port `0` to get an available port automatically. If you need to specify a port (for debugging), you can modify the config.

### Memory Issues in CI

If Puppeteer crashes due to memory limits in CI, add these launch arguments:

```json
{
  "puppeteerArgs": [
    "--disable-dev-shm-usage",
    "--disable-accelerated-2d-canvas",
    "--no-sandbox",
    "--disable-setuid-sandbox"
  ]
}
```

## NPM Local Packaging & Verification

Before publishing `satya-engine-ci` to the public NPM registry, you should bundle and verify the distribution package locally to ensure all required assets (CLI source files, injected engine scripts, manifests) are correctly packaged and function as expected.

### Step 1: Generate the Tarball
Run `npm pack` in the root of the project. This command dry-runs the packaging lifecycle and bundles everything defined in the `"files"` field of `package.json` into a portable, versioned tarball (e.g., `satya-engine-ci-1.0.0.tgz`):

```bash
npm pack
```

### Step 2: Inspect Package Contents
To ensure no unnecessary files (like test caches or development credentials) are included, inspect the tarball's file manifest:

```bash
# On Unix-like systems (Linux/macOS)
tar -ztf satya-engine-ci-1.0.0.tgz

# On Windows (PowerShell)
tar -tf satya-engine-ci-1.0.0.tgz
```

Ensure the output matches the expected runtime structure:
- `package/package.json`
- `package/src/cli.js`
- `package/src/puppeteer-runner.js`
- `package/src/report-generator.js`
- `package/scripts/satya.min.js`
- `package/Dockerfile`
- `package/docs/` (all guides)

### Step 3: Verify Installation Locally
Verify that the package installs and executes cleanly without any relative path dependency breaks:

```bash
# 1. Create an isolated temporary test folder outside the project root
mkdir ../satya-test-sandbox && cd ../satya-test-sandbox

# 2. Initialize a dummy Node project
npm init -y

# 3. Install the packaged tarball locally
npm install ../satya-engine-ci/satya-engine-ci-1.0.0.tgz

# 4. Execute the CLI via npx to confirm Chrome provisions and tests execute
npx satya-ci --target https://example.com --threshold 5
```

If the execution finishes successfully and generates reports inside `./reports`, the NPM package is ready for distribution!

## Next Steps

- Learn about [Configuration Options](./configuration.md)
- Learn about the [Integration Guide](./integration-guide.md)
- Integrate with [CI/CD Systems](./ci-cd-examples.md)