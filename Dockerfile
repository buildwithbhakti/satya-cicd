# Dockerfile for Satya CI - Accessibility Testing Tool
# Based on lean Node.js slim image with minimal required shared libraries for Chrome

FROM node:18-slim

# Set environment variables for production and explicit Puppeteer caching
ENV NODE_ENV=production
ENV PUPPETEER_CACHE_DIR=/app/.cache/puppeteer

# Set working directory
WORKDIR /app

# Install minimal system shared libraries required for headless Chrome
# We explicitly do NOT install system-wide chromium to keep the image lean and deterministic
RUN apt-get update && apt-get install -y --no-install-recommends \
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
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy package manifests and Puppeteer configuration first to leverage Docker layer caching
COPY package*.json .puppeteerrc.cjs ./

# Install production Node dependencies
RUN npm ci --only=production

# Deterministically provision the pinned Chrome browser binary in the cache directory
RUN npx puppeteer browsers install chrome

# Copy application source code and engine scripts
COPY src/ ./src/
COPY scripts/ ./scripts/

# Create default output directory for reports
RUN mkdir -p reports

# Prevent CRLF shebang breaks if the image is built on a Windows host
RUN sed -i 's/\r$//' src/cli.js && chmod +x src/cli.js

# Execute cli.js directly using Node to bypass OS shebang wrapper limits
ENTRYPOINT ["node", "src/cli.js"]

# Default command displays help instructions
CMD ["--help"]
