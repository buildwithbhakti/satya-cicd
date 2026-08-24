const puppeteer = require("puppeteer");
const path = require("path");
const fs = require("fs");
const http = require("http");
const os = require("os");
const { execSync } = require("child_process");

async function runAccessibilityTest(target, options) {
  const { isLocalPath, config, ignoreDom, threshold } = options;
  let localServer = null;
  let serverUrl = target;

  try {
    // If target is a local directory, spin up a static server
    if (isLocalPath) {
      const resolvedPath = path.resolve(target);
      if (!fs.existsSync(resolvedPath)) {
        throw new Error(`Local path does not exist: ${resolvedPath}`);
      }
      // Check if it's a file or directory
      const stat = fs.statSync(resolvedPath);
      let serveDirectory;
      let urlPath = "";

      if (stat.isFile()) {
        // If it's a file, serve its parent directory and navigate to the file
        serveDirectory = path.dirname(resolvedPath);
        const relativePath = path.relative(serveDirectory, resolvedPath);
        urlPath = "/" + relativePath.replace(/\\/g, "/");
      } else {
        // It's a directory, serve it and navigate to root
        serveDirectory = resolvedPath;
        urlPath = "/";
      }

      // Create a static file server
      localServer = await createStaticServer(serveDirectory);
      const port = localServer.address().port;
      serverUrl = `http://localhost:${port}${urlPath}`;
      console.log(
        `📁 Serving local ${stat.isFile() ? "file" : "directory"} at: ${serverUrl}`,
      );
    } else {
    }

    // Launch Puppeteer and run tests
    const launchOptions = {
      headless: "new",
      args: [
        "--disable-dev-shm-usage",
        "--disable-accelerated-2d-canvas",
        "--disable-gpu",
      ],
    };

    // Environment/Sandbox detection for container and restricted environments
    const isDocker =
      fs.existsSync("/.dockerenv") ||
      process.env.SATYA_NO_SANDBOX === "true" ||
      (process.platform === "linux" && process.env.USER === "root");
    if (isDocker || process.env.NO_SANDBOX === "true") {
      launchOptions.args.push("--no-sandbox");
      launchOptions.args.push("--disable-setuid-sandbox");
      console.log(
        "🐳 Container/restricted environment detected: enabled --no-sandbox",
      );
    }

    // Support manual path overrides if absolutely needed
    if (process.env.PUPPETEER_EXECUTABLE_PATH) {
      launchOptions.executablePath = process.env.PUPPETEER_EXECUTABLE_PATH;
      console.log(
        `🖥️ Using custom browser path: ${launchOptions.executablePath}`,
      );
    } else {
      console.log(
        "🔍 Resolving browser automatically from Puppeteer local cache...",
      );
    }

    const browser = await puppeteer.launch(launchOptions);
    try {
      const page = await browser.newPage();

      // Set viewport from config or default
      const viewport = config.viewport || { width: 1280, height: 800 };
      await page.setViewport(viewport);

      // Listen for console messages (optional debug)
      page.on("console", (msg) => {
        if (msg.type() === "error") {
          console.error("Page error:", msg.text());
        }
      });

      // Navigate to the target
      console.log(`🌐 Navigating to: ${serverUrl}`);
      const timeout = config.timeout || 30000;
      await page.goto(serverUrl, {
        waitUntil: "networkidle0",
        timeout,
      });

      // Wait a bit for any dynamic content to render
      const waitAfterNavigation = config.waitAfterNavigation || 2000;
      await new Promise((resolve) => setTimeout(resolve, waitAfterNavigation));

      // Inject the Satya engine
      const satyaScriptPath = path.resolve(
        __dirname,
        "..",
        "scripts",
        "satya.min.js",
      );
      const satyaScript = fs.readFileSync(satyaScriptPath, "utf8");

      // Evaluate Satya in the page context
      const results = await page.evaluate(
        (script, customRules, ignoreSelectors) => {
          // Inject the Satya engine
          eval(script);

          // Set custom rules if provided
          if (customRules && typeof customRules === "object" && window.satya) {
            window.satya.config = window.satya.config || {};
            if (customRules.rules) {
              window.satya.config.rules = {
                ...window.satya.config.rules,
                ...customRules.rules,
              };
            }
          }

          // Run the accessibility audit
          const satyaResults = window.satya
            ? window.satya.run()
            : { violations: [], passed: false };

          // Filter out ignored DOM nodes
          if (
            ignoreSelectors &&
            ignoreSelectors.length > 0 &&
            satyaResults.violations
          ) {
            satyaResults.violations = satyaResults.violations.filter(
              (violation) => {
                const element = violation.element || violation.node;
                if (!element) return true;
                return !ignoreSelectors.some((selector) => {
                  try {
                    const matches =
                      element.matches && element.matches(selector);
                    const closest =
                      element.closest && element.closest(selector);
                    return matches || closest;
                  } catch (e) {
                    return false;
                  }
                });
              },
            );
          }
          return satyaResults;
        },
        satyaScript,
        config.rules || null,
        ignoreDom,
      );

      // Format results
      const formattedResults = {
        url: serverUrl,
        timestamp: new Date().toISOString(),
        threshold,
        passed: (results.violations || []).length <= threshold,
        violations: (results.violations || []).map((v) => ({
          ...v,
          severity: v.severity || "medium",
          rule: v.rule || v.id || "unknown",
          element: v.element || v.selector || "",
          message: v.message || v.description || "",
          impact: v.impact || "",
        })),
      };

      return formattedResults;
    } finally {
      await browser.close();
    }
  } finally {
    // Clean up local server if we started one
    if (localServer) {
      localServer.close();
      console.log("🛑 Local server stopped");
    }
  }
}

// Simple static file server using Node.js built-in modules
function createStaticServer(directory) {
  return new Promise((resolve, reject) => {
    const server = http.createServer((req, res) => {
      // Parse URL and get the path
      let filePath = path.join(
        directory,
        req.url === "/" ? "/index.html" : req.url,
      );

      // Security: prevent directory traversal
      filePath = path.normalize(filePath);
      if (!filePath.startsWith(directory)) {
        res.statusCode = 403;
        res.end("Forbidden");
        return;
      }

      // Check if file exists
      fs.stat(filePath, (err, stats) => {
        if (err || !stats.isFile()) {
          res.statusCode = 404;
          res.end("Not Found");
          return;
        }

        // Determine content type
        const ext = path.extname(filePath).toLowerCase();
        const mimeTypes = {
          ".html": "text/html",
          ".js": "text/javascript",
          ".css": "text/css",
          ".json": "application/json",
          ".png": "image/png",
          ".jpg": "image/jpeg",
          ".jpeg": "image/jpeg",
          ".gif": "image/gif",
          ".svg": "image/svg+xml",
          ".ico": "image/x-icon",
          ".woff": "font/woff",
          ".woff2": "font/woff2",
        };
        const contentType = mimeTypes[ext] || "application/octet-stream";

        // Set headers
        res.setHeader("Content-Type", contentType);
        res.setHeader("Cache-Control", "no-cache, no-store, must-revalidate");

        // Read and stream file
        const readStream = fs.createReadStream(filePath);
        readStream.pipe(res);
      });
    });

    server.on("listening", () => {
      resolve(server);
    });
    server.on("error", (err) => {
      reject(err);
    });

    // Listen on a random available port
    server.listen(0, "127.0.0.1");
  });
}

module.exports = { runAccessibilityTest };
