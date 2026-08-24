const fs = require("fs");
const path = require("path");

function generateJsonReport(results, outputPath) {
  const report = {
    summary: {
      url: results.url,
      timestamp: results.timestamp,
      totalViolations: results.violations.length,
      passed: results.passed,
      threshold: results.threshold,
    },
    violations: results.violations,
  };

  const content = JSON.stringify(report, null, 2);
  fs.writeFileSync(outputPath, content, "utf8");
}

function generateHtmlReport(results, outputPath) {
  const { violations, url, timestamp, passed, threshold } = results;

  const severityCounts = {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
  };

  violations.forEach((v) => {
    const severity = (v.severity || "medium").toLowerCase();
    if (severityCounts[severity] !== undefined) {
      severityCounts[severity]++;
    } else {
      severityCounts.medium++;
    }
  });

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Satya Accessibility Report</title>
  <style>
    :root {
      --color-critical: #dc2626;
      --color-high: #ea580c;
      --color-medium: #ca8a04;
      --color-low: #2563eb;
      --color-pass: #16a34a;
      --color-fail: #dc2626;
      --bg-primary: #ffffff;
      --bg-secondary: #f8fafc;
      --text-primary: #1e293b;
      --text-secondary: #64748b;
      --border-color: #e2e8f0;
    }

    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      line-height: 1.6;
      color: var(--text-primary);
      background-color: var(--bg-secondary);
      padding: 2rem;
    }

    .container {
      max-width: 1200px;
      margin: 0 auto;
      background: var(--bg-primary);
      border-radius: 8px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      overflow: hidden;
    }

    header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 2rem;
    }

    h1 {
      font-size: 1.75rem;
      margin-bottom: 0.5rem;
    }

    .summary {
      margin-top: 1rem;
    }

    .summary-item {
      display: inline-block;
      margin-right: 2rem;
      font-size: 0.9rem;
    }

    .summary-label {
      opacity: 0.9;
    }

    .status-badge {
      display: inline-block;
      padding: 0.25rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.875rem;
      font-weight: 600;
      margin-top: 0.5rem;
    }

    .status-pass {
      background: var(--color-pass);
      color: white;
    }

    .status-fail {
      background: var(--color-fail);
      color: white;
    }

    main {
      padding: 2rem;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }

    .stat-card {
      padding: 1.5rem;
      border-radius: 8px;
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
    }

    .stat-card h3 {
      font-size: 0.875rem;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 0.5rem;
    }

    .stat-card .value {
      font-size: 2rem;
      font-weight: 700;
    }

    .stat-card critical .value { color: var(--color-critical); }
    .stat-card high .value { color: var(--color-high); }
    .stat-card medium .value { color: var(--color-medium); }
    .stat-card low .value { color: var(--color-low); }

    .violations-section {
      margin-top: 2rem;
    }

    h2 {
      font-size: 1.25rem;
      margin-bottom: 1rem;
      color: var(--text-primary);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 1rem;
    }

    th, td {
      text-align: left;
      padding: 0.75rem 1rem;
      border-bottom: 1px solid var(--border-color);
    }

    th {
      background: var(--bg-secondary);
      font-weight: 600;
      color: var(--text-secondary);
      font-size: 0.875rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    tr:hover {
      background: var(--bg-secondary);
    }

    .severity-critical { color: var(--color-critical); font-weight: 600; }
    .severity-high { color: var(--color-high); font-weight: 600; }
    .severity-medium { color: var(--color-medium); font-weight: 600; }
    .severity-low { color: var(--color-low); font-weight: 600; }

    .element-code {
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      font-size: 0.85rem;
      background: var(--bg-secondary);
      padding: 0.125rem 0.375rem;
      border-radius: 4px;
      color: #d946ef;
      max-width: 300px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .message {
      max-width: 400px;
    }

    .no-violations {
      text-align: center;
      padding: 3rem;
      color: var(--color-pass);
      font-size: 1.25rem;
    }

    footer {
      padding: 1.5rem 2rem;
      background: var(--bg-secondary);
      border-top: 1px solid var(--border-color);
      text-align: center;
      color: var(--text-secondary);
      font-size: 0.875rem;
    }

    @media (max-width: 768px) {
      body { padding: 1rem; }
      .summary-item { display: block; margin-bottom: 0.5rem; }
      table { display: block; overflow-x: auto; }
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>♿ Satya Accessibility Report</h1>
      <div class="summary">
        <div class="summary-item">
          <span class="summary-label">URL:</span> <strong>${escapeHtml(url)}</strong>
        </div>
        <div class="summary-item">
          <span class="summary-label">Generated:</span> <strong>${new Date(timestamp).toLocaleString()}</strong>
        </div>
      </div>
      <span class="status-badge ${passed ? "status-pass" : "status-fail"}">
        ${passed ? "✓ PASSED" : "✗ FAILED"}
      </span>
    </header>

    <main>
      <div class="stats-grid">
        <div class="stat-card critical">
          <h3>Critical</h3>
          <div class="value">${severityCounts.critical}</div>
        </div>
        <div class="stat-card high">
          <h3>High</h3>
          <div class="value">${severityCounts.high}</div>
        </div>
        <div class="stat-card medium">
          <h3>Medium</h3>
          <div class="value">${severityCounts.medium}</div>
        </div>
        <div class="stat-card low">
          <h3>Low</h3>
          <div class="value">${severityCounts.low}</div>
        </div>
      </div>

      <div class="violations-section">
        <h2>Violations (${violations.length})</h2>
        ${
          violations.length === 0
            ? `
          <div class="no-violations">🎉 No accessibility violations found!</div>
        `
            : `
          <table>
            <thead>
              <tr>
                <th>Severity</th>
                <th>Rule</th>
                <th>Element</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              ${violations
                .map(
                  (v) => `
                <tr>
                  <td class="severity-${(v.severity || "medium").toLowerCase()}">${escapeHtml(v.severity || "medium")}</td>
                  <td>${escapeHtml(v.rule)}</td>
                  <td><code class="element-code">${escapeHtml(v.element)}</code></td>
                  <td class="message">${escapeHtml(v.message)}</td>
                </tr>
              `,
                )
                .join("")}
            </tbody>
          </table>
        `
        }
      </div>
    </main>

    <footer>
      Generated by Satya CI • Accessibility Testing Engine
    </footer>
  </div>

  <script>
    function escapeHtml(text) {
      if (!text) return '';
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }
  </script>
</body>
</html>`;

  fs.writeFileSync(outputPath, html, "utf8");
}

function escapeHtml(text) {
  if (!text) return "";
  const map = {
    "&": "&",
    "<": "<",
    ">": ">",
    '"': '"',
    "'": "&apos;",
  };
  return text.replace(/[&<>"']/g, (m) => map[m]);
}

// Add escapeHtml to module.exports for internal use
module.exports = {
  generateJsonReport,
  generateHtmlReport,
  escapeHtml,
};
