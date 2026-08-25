# ============================================================
# Satya Accessibility CI
# Node.js + Puppeteer
# ============================================================

FROM node:20-bookworm

# ------------------------------------------------------------
# Application directory
# ------------------------------------------------------------
WORKDIR /app

# ------------------------------------------------------------
# Copy dependency files first
# This allows Docker to cache npm dependencies
# ------------------------------------------------------------
COPY package.json package-lock.json ./

# ------------------------------------------------------------
# Install Node.js dependencies
# Puppeteer will install its required browser
# ------------------------------------------------------------
RUN npm ci

# ------------------------------------------------------------
# Copy application source
# ------------------------------------------------------------
COPY src ./src
COPY scripts ./scripts
COPY .satyarc.json ./
COPY src/puppeteer-runner.js ./

# ------------------------------------------------------------
# Environment variables
# ------------------------------------------------------------
ENV NODE_ENV=production
ENV NO_SANDBOX=true
ENV SATYA_NO_SANDBOX=true
ENV FORCE_COLOR=0

# Puppeteer browser cache
ENV PUPPETEER_CACHE_DIR=/root/.cache/puppeteer

# ------------------------------------------------------------
# Create directory for scan reports
# ------------------------------------------------------------
RUN mkdir -p /app/reports

# ------------------------------------------------------------
# Run Satya accessibility scanner
# ------------------------------------------------------------
ENTRYPOINT ["node", "src/cli.js"]
