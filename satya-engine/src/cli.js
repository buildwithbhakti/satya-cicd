#!/usr/bin/env node
const { Command } = require("commander");
const path = require("path");
const fs = require("fs");
const chalk = require("chalk");
const { runAccessibilityTest } = require("./puppeteer-runner");
const {
  generateHtmlReport,
  generateJsonReport,
} = require("./report-generator");

/**
 * Full rule catalogue derived from scripts/satya.min.js (108 rules).
 * Kept in a separate module so cli.js stays readable and the list
 * can be regenerated when the engine is updated.
 */
const ALL_AVAILABLE_RULES = require("./all-rules");

const program = new Command();
program
  .name("satya-ci")
  .description("CI/CD integration tool for Satya accessibility engine")
  .version("1.0.0")
  .requiredOption(
    "-t, --target <path>",
    "Target URL or local directory path to test",
  )
  .option(
    "--threshold <number>",
    "Maximum allowed critical errors (default: 0)",
    "0",
  )
  .option(
    "--config <path>",
    "Path to .satyarc.json config file (default: .satyarc.json in project root)",
  )
  .option(
    "--output <dir>",
    "Output directory for reports (default: ./reports)",
    "./reports",
  )
  .option("--ignore-dom <selector>", "Comma-separated CSS selectors to ignore")
  .option(
    "--all",
    "Enable all known rules. Use rules.<name>.enabled=false in config to disable individual rules.",
  )
  .parse(process.argv);

const options = program.opts();

async function main() {
  console.log(chalk.blue.bold("\n🧪 Satya CI - Accessibility Testing\n"));

  // ── Load config ──────────────────────────────────────────────────────────
  let config = {};
  let configPath = options.config || path.join(process.cwd(), ".satyarc.json");
  if (fs.existsSync(configPath)) {
    try {
      config = JSON.parse(fs.readFileSync(configPath, "utf8"));
      console.log(chalk.green(`✓ Loaded config from ${configPath}`));
    } catch (err) {
      console.error(chalk.red(`✗ Failed to parse config: ${err.message}`));
      process.exit(1);
    }
  } else {
    console.log(
      chalk.yellow(`⚠ Config file not found at ${configPath}. Using defaults.`),
    );
  }

  // ── Expand "all rules" if requested ──────────────────────────────────────
  const includeAllRules = options.all || config.includeAllRules === true;
  if (includeAllRules) {
    const allRules = {};
    for (const rule of ALL_AVAILABLE_RULES) {
      allRules[rule] = { enabled: true };
    }
    // User's explicit rule entries win (e.g. to disable a rule or change severity)
    if (config.rules && typeof config.rules === "object") {
      for (const [rule, userSettings] of Object.entries(config.rules)) {
        if (userSettings && typeof userSettings === "object") {
          allRules[rule] = { ...allRules[rule], ...userSettings };
        }
      }
    }
    config = { ...config, rules: allRules };
    console.log(
      chalk.cyan(
        `📋 All-rules mode active: ${Object.keys(allRules).length} rules enabled`,
      ),
    );
  }

  const threshold = parseInt(options.threshold, 10) || 0;
  const ignoreDom = options.ignoreDom
    ? options.ignoreDom.split(",").map((s) => s.trim())
    : config.ignoreDom || [];
  const target = options.target;

  // Determine if target is URL or local path
  const isLocalPath =
    !target.startsWith("http://") && !target.startsWith("https://");

  let testResults;
  try {
    console.log(chalk.cyan(`\n🚀 Running accessibility test on: ${target}`));
    testResults = await runAccessibilityTest(target, {
      isLocalPath,
      config,
      ignoreDom,
      threshold,
    });
  } catch (err) {
    console.error(chalk.red(`\n✗ Test execution failed: ${err.message}`));
    process.exit(1);
  }

  // Generate reports directory
  const outputDir = path.resolve(options.output);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // Generate JSON report
  const jsonReportPath = path.join(outputDir, "satya-report.json");
  generateJsonReport(testResults, jsonReportPath);
  console.log(chalk.green(`✓ JSON report saved: ${jsonReportPath}`));

  // Generate HTML report
  const htmlReportPath = path.join(outputDir, "satya-report.html");
  generateHtmlReport(testResults, htmlReportPath);
  console.log(chalk.green(`✓ HTML report saved: ${htmlReportPath}`));

  // Print violations table
  printResultsTable(testResults);

  // Determine exit code based on threshold
  const violationsCount = testResults.violations.length;
  const passed = violationsCount <= threshold;
  console.log(
    chalk.bold(
      `\n📊 Results: ${violationsCount} violations (threshold: ${threshold})`,
    ),
  );
  if (passed) {
    console.log(chalk.green.bold("\n✅ Build passed!\n"));
    process.exit(0);
  } else {
    console.log(
      chalk.red.bold("\n❌ Build failed - violations exceed threshold!\n"),
    );
    process.exit(1);
  }
}

const Table = require("cli-table3");

function printResultsTable(testResults) {
  const { violations, url, testEnvironment } = testResults;

  // ── Determine Target and Filename ───────────────────────────────────────
  let targetDisplay = url || options.target || "Unknown Target";
  let fileNameDisplay = "N/A (Remote URL)";

  // If it's a local file path or file:// URL, pull out the exact file name
  if (
    options.target &&
    !options.target.startsWith("http://") &&
    !options.target.startsWith("https://")
  ) {
    const resolvedPath = path.resolve(options.target);
    if (fs.existsSync(resolvedPath)) {
      const stat = fs.statSync(resolvedPath);
      if (stat.isDirectory()) {
        const folderName = path.basename(resolvedPath);
        // Serving a local directory defaults to index.html in the static server
        fileNameDisplay = `${folderName} (index.html)`;
      } else {
        fileNameDisplay = path.basename(options.target);
      }
    } else {
      fileNameDisplay = path.basename(options.target);
    }
  } else if (targetDisplay.startsWith("file://")) {
    fileNameDisplay = path.basename(targetDisplay.replace("file://", ""));
  }

  console.log(chalk.gray("─".repeat(process.stdout.columns || 90)));
  console.log(
    `${chalk.bold("🎯 Target Page:")}   ${chalk.cyan(targetDisplay)}`,
  );
  console.log(
    `${chalk.bold("📄 File Name:")}     ${chalk.yellow(fileNameDisplay)}`,
  );
  if (options.config) {
    console.log(
      `${chalk.bold("🛠️  Config File:")}   ${chalk.gray(path.basename(options.config))}`,
    );
  }
  console.log(chalk.gray("─".repeat(process.stdout.columns || 90)) + "\n");

  if (!violations || violations.length === 0) {
    console.log(chalk.green.bold("🎉 No accessibility violations found!\n"));
    return;
  }

  console.log(chalk.white.bold("📋 Accessibility Violations Details:\n"));

  // ── Build the Table Layout ──────────────────────────────────────────────
  const table = new Table({
    head: [
      chalk.bold.white("ID"),
      chalk.bold.white("Impact"),
      chalk.bold.white("Rule Details / Remedy"),
      chalk.bold.white("Violated Code Snippet"),
    ],
    colWidths: [6, 12, 42, 50],
    wordWrap: true,
    style: {
      head: [],
      border: ["gray"],
    },
  });

  let counter = 1;

  violations.forEach((v) => {
    // Fallback to "serious" if impact is undefined
    const impact = (v.impact || "serious").toLowerCase();
    const severityColor = getSeverityColor(impact);

    // Fallback description options mapped directly from Satya's metadata catalog
    const ruleDescription =
      v.description ||
      (v.metadata && v.metadata.description) ||
      "No description provided.";
    const helpRemedy =
      v.help || (v.metadata && v.metadata.help) || ruleDescription;

    const nodes = v.nodes || [];

    if (nodes.length === 0) {
      // If the engine flagged a violation rule but nodes didn't populate for some reason,
      // print the rule instance anyway so the build failure makes contextual sense to the user.
      const idCell = chalk.gray(`#${counter++}`);
      const impactCell = severityColor.bold(` ${impact.toUpperCase()} `);
      const detailsCell = `${chalk.bold.cyan(v.id || v.rule || "unknown")}\n${chalk.white(helpRemedy)}`;
      const codeCell = chalk.italic.gray(
        "No specific element DOM node snippet captured.",
      );

      table.push([idCell, impactCell, detailsCell, codeCell]);
    } else {
      // Loop through individual node instances captured by the rule engine
      nodes.forEach((node) => {
        const idCell = chalk.gray(`#${counter++}`);
        const impactCell = severityColor.bold(` ${impact.toUpperCase()} `);

        // Extract targeted element selector pointer if available
        const targetSelector =
          node.target && node.target[0] ? node.target[0] : "N/A";

        // Dynamic summary messages from individual node evaluations
        const finalRemedy = node.failureSummary || helpRemedy;
        const codeSnippet = node.html || "N/A";

        const detailsCell =
          `${chalk.bold.cyan(v.id || v.rule || "unknown")}\n` +
          `${chalk.white(finalRemedy)}\n` +
          `${chalk.gray("Selector:")} ${chalk.yellow(truncateString(targetSelector, 80))}`;

        const highlightedCode = highlightCodeSnippet(codeSnippet);

        table.push([idCell, impactCell, detailsCell, highlightedCode]);
      });
    }
  });

  console.log(table.toString());
}

function getSeverityColor(severity) {
  switch (severity.toLowerCase()) {
    case "critical":
      return chalk.bgRed.white;
    case "serious":
    case "high":
      return chalk.red;
    case "moderate":
    case "medium":
    case "yellow":
      return chalk.yellow;
    case "minor":
    case "low":
      return chalk.cyan;
    default:
      return chalk.white;
  }
}

function truncateString(str, maxLength) {
  if (!str) return "";
  return str.length > maxLength ? str.substring(0, maxLength - 3) + "..." : str;
}

function highlightCodeSnippet(rawHtml) {
  if (!rawHtml || rawHtml === "N/A") return chalk.gray("N/A");

  return rawHtml
    .replace(/(<\/?[a-zA-Z0-9:-]+>)/g, chalk.magenta("$1")) // Tags
    .replace(/(\s[a-zA-Z0-9:-]+=)/g, chalk.green("$1")) // Attributes
    .replace(/(["'].*?["'])/g, chalk.yellow("$1")); // Values
}

function getSeverityColor(severity) {
  switch (severity.toLowerCase()) {
    case "critical":
      return chalk.bgRed.white; // High visibility background blocks
    case "serious":
    case "high":
      return chalk.red;
    case "moderate":
    case "medium":
      return chalk.yellow;
    case "minor":
    case "low":
      return chalk.cyan;
    default:
      return chalk.white;
  }
}

function truncateString(str, maxLength) {
  if (!str) return "";
  return str.length > maxLength ? str.substring(0, maxLength - 3) + "..." : str;
}

/**
 * Quick local utility regex to mimic low-overhead theme token highlights
 * for HTML code snippets directly inside your CLI.
 */
function highlightCodeSnippet(rawHtml) {
  if (!rawHtml || rawHtml === "N/A") return chalk.gray("N/A");

  return (
    rawHtml
      // Highlight elements/brackets
      .replace(/(<\/?[a-zA-Z0-9:-]+>)/g, chalk.magenta("$1"))
      // Highlight attributes
      .replace(/(\s[a-zA-Z0-9:-]+=)/g, chalk.green("$1"))
      // Highlight values
      .replace(/(["'].*?["'])/g, chalk.yellow("$1"))
  );
}
function getSeverityColor(severity) {
  switch (severity.toLowerCase()) {
    case "critical":
    case "high":
      return chalk.red;
    case "medium":
      return chalk.yellow;
    case "low":
      return chalk.cyan;
    default:
      return chalk.white;
  }
}

function truncateString(str, maxLength) {
  if (!str) return "";
  return str.length > maxLength ? str.substring(0, maxLength - 3) + "..." : str;
}

main().catch((err) => {
  console.error(chalk.red("Fatal error:"), err);
  process.exit(1);
});
