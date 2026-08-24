# Configuration Reference

The Satya CI tool uses a `.satyarc.json` configuration file to customize testing behavior. This file should be placed in your project root.

## Configuration Schema

### `rules`

Object containing rule configurations. Each rule can be enabled/disabled and have a custom severity level.

**Example:**

```json
{
  "rules": {
    "color-contrast": {
      "enabled": true,
      "severity": "critical"
    },
    "image-alt": {
      "enabled": false,
      "severity": "high"
    }
  }
}
```

**Rule Properties:**

| Property | Type   | Description                    |
|----------|--------|--------------------------------|
| enabled  | bool   | Enable or disable this rule   |
| severity | string | Severity level (low/medium/high/critical) |

### `ignoreDom`

Array of CSS selectors. Elements matching these selectors will be excluded from accessibility checks.

**Example:**

```json
{
  "ignoreDom": [
    ".debug-console",
    "#test-banner",
    ".dev-tools-panel"
  ]
}
```

### `viewport`

Viewport dimensions for the headless browser.

**Example:**

```json
{
  "viewport": {
    "width": 1280,
    "height": 800
  }
}
```

| Property | Type   | Description                |
|----------|--------|----------------------------|
| width    | number | Viewport width in pixels   |
| height   | number | Viewport height in pixels  |

### `timeout`

Maximum time (in milliseconds) to wait for page navigation.

**Default:** `30000`

### `waitAfterNavigation`

Time (in milliseconds) to wait after navigation before running tests. Useful for SPAs that load content dynamically.

**Default:** `2000`

### `puppeteerArgs` (Optional)

Additional command-line arguments to pass to Puppeteer's launch options.

**Example:**

```json
{
  "puppeteerArgs": [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage"
  ]
}
```

### `output` (Optional)

Default output directory for reports. Overrides the `--output` CLI flag if set.

**Example:**

```json
{
  "output": "./a11y-reports"
}
```

### `thresholds` (Advanced)

Override the global threshold with severity-specific thresholds.

**Example:**

```json
{
  "thresholds": {
    "critical": 0,
    "high": 2,
    "medium": 5,
    "low": 10
  }
}
```

## Complete Example

```json
{
  "rules": {
    "color-contrast": {
      "enabled": true,
      "severity": "critical"
    },
    "image-alt": {
      "enabled": true,
      "severity": "high"
    },
    "button-name": {
      "enabled": true,
      "severity": "medium"
    },
    "heading-order": {
      "enabled": true,
      "severity": "low"
    }
  },
  "ignoreDom": [
    ".debugging-ui",
    "#admin-toolbar"
  ],
  "viewport": {
    "width": 1920,
    "height": 1080
  },
  "timeout": 45000,
  "waitAfterNavigation": 3000,
  "output": "./reports/accessibility"
}
```

## Defaults

If `.satyarc.json` is not found, the tool uses these defaults:

- All rules enabled with default severities
- No ignored DOM selectors
- Viewport: 1280x800
- Timeout: 30000ms
- Wait after navigation: 2000ms
- Output: `./reports`
- Threshold: 0 (from CLI)

## Tip

Keep `.satyarc.json` in your project root and commit it to version control to ensure consistent accessibility testing across all environments (local, CI, staging, production).