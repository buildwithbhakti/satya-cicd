# CI/CD Examples

This document provides practical examples for integrating Satya CI into various CI/CD systems.

## GitHub Actions

### Workflow for Pull Requests

```yaml
name: Accessibility Check

on:
  pull_request:
    branches: [main, develop]
    paths:
      - '**.html'
      - '**.js'
      - '**.ts'
      - '**.jsx'
      - '**.tsx'

jobs:
  a11y-test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build application
        run: npm run build

      - name: Start local server
        run: npx serve -p 3000 build &
        env:
          CI: true

      - name: Wait for server
        run: npx wait-on http://localhost:3000

      - name: Run accessibility tests
        run: npx satya-ci --target http://localhost:3000 --threshold 0 --output ./a11y-reports

      - name: Upload reports
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: a11y-reports
          path: a11y-reports/
```

### Workflow for Deploy Preview (Vercel/Netlify)

```yaml
name: Deploy Preview A11y Check

on:
  deployment_status

jobs:
  a11y-test:
    if: github.event.deployment_status.state == 'success'
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Install satya-ci
        run: npm install -g satya-ci

      - name: Run tests on preview URL
        env:
          PREVIEW_URL: ${{ github.event.deployment_status.target_url }}
        run: |
          satya-ci \
            --target $PREVIEW_URL \
            --threshold 0 \
            --output ./a11y-reports \
            --config .satyarc.json

      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: a11y-reports
          path: a11y-reports/
          retention-days: 14

      - name: Comment PR with results
        uses: actions/github-script@v6
        if: failure()
        with:
          script: |
            const { execSync } = require('child_process');
            const report = execSync('cat a11y-reports/satya-report.json').toString();
            const data = JSON.parse(report);
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## ♿ Accessibility Test Failed\n\n${data.summary.totalViolations} violations found on ${data.summary.url}\n\nSee attached reports for details.`
            });
```

## GitLab CI

### Basic Pipeline

```yaml
# .gitlab-ci.yml
stages:
  - test
  - deploy

a11y_test:
  stage: test
  image: node:18
  services:
    - name: nginx:alpine
      alias: web
  before_script:
    - npm ci
    - npm run build
    - cp -r build /usr/share/nginx/html/
    - nginx -c /etc/nginx/nginx.conf
  script:
    - |
      # Wait for nginx to be ready
      while ! curl -s http://web > /dev/null; do sleep 1; done

      # Run accessibility tests
      npx satya-ci --target http://web --threshold 0 --output ./a11y-reports

      # Generate JUnit-style report for GitLab (optional)
      npx satya-ci --target http://web --output ./a11y-reports || true
  artifacts:
    paths:
      - a11y-reports/
    expire_in: 1 week
    reports:
      accessibility: a11y-reports/satya-report.json
  only:
    - merge_requests
    - main
```

### Using Docker Executor

```yaml
a11y_test:
  stage: test
  image: satya-ci:latest
  services:
    - name: your-app:latest
      alias: app
  script:
    - satya-ci --target http://app:8080 --threshold 0
  artifacts:
    paths:
      - reports/
  only:
    - merge_requests
```

## Jenkins

### Declarative Pipeline

```groovy
// Jenkinsfile
pipeline {
  agent any

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Install') {
      steps {
        sh 'npm ci'
      }
    }

    stage('Build') {
      steps {
        sh 'npm run build'
      }
    }

    stage('Start Server') {
      steps {
        sh '''
          npx serve -p 3000 build &
          echo $! > server.pid
          npx wait-on http://localhost:3000
        '''
      }
    }

    stage('Accessibility Test') {
      steps {
        sh '''
          npx satya-ci \
            --target http://localhost:3000 \
            --threshold 0 \
            --output a11y-reports
        '''
      }
      post {
        always {
          publishHTML([
            allowMissing: false,
            alwaysLinkToLastBuild: true,
            keepAll: true,
            reportDir: 'a11y-reports',
            reportFiles: 'satya-report.html',
            reportName: 'A11y Report'
          ])
        }
      }
    }
  }

  post {
    always {
      sh 'kill $(cat server.pid) || true'
      archiveArtifacts artifacts: 'a11y-reports/**', fingerprint: true
    }
  }
}
```

## CircleCI

### Config

```yaml
# .circleci/config.yml
version: 2.1

jobs:
  a11y-test:
    docker:
      - image: cimg/node:18
    steps:
      - checkout

      - restore_cache:
          keys:
            - v1-dependencies-{{ checksum "package-lock.json" }}
            - v1-dependencies-

      - run: npm ci

      - save_cache:
          paths:
            - node_modules
          key: v1-dependencies-{{ checksum "package-lock.json" }}

      - run: npm run build

      - run:
          name: Start server
          command: npx serve -p 3000 build &

      - run:
          name: Wait for server
          command: npx wait-on http://localhost:3000

      - run:
          name: Run accessibility tests
          command: npx satya-ci --target http://localhost:3000 --threshold 0 --output ./a11y-reports

      - store_artifacts:
          path: a11y-reports
          destination: a11y-reports

      - store_test_results:
          path: a11y-reports

workflows:
  version: 2
  test:
    jobs:
      - a11y-test
```

## Azure DevOps

### YAML Pipeline

```yaml
# azure-pipelines.yml
trigger:
  - main
  - develop

pr:
  - main
  - develop

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: NodeTool@0
    inputs:
      versionSpec: '18.x'
    displayName: 'Install Node.js'

  - script: |
      npm ci
    displayName: 'Install dependencies'

  - script: |
      npm run build
    displayName: 'Build'

  - script: |
      npx serve -p 8080 build &
      npx wait-on http://localhost:8080
      npx satya-ci --target http://localhost:8080 --threshold 0 --output a11y-reports
    displayName: 'Run accessibility tests'

  - task: PublishBuildArtifacts@1
    condition: always()
    inputs:
      PathtoPublish: 'a11y-reports'
      ArtifactName: 'a11y-reports'
```

## Bitbucket Pipelines

### bitbucket-pipelines.yml

```yaml
image: node:18

pipelines:
  default:
    - parallel:
        - step:
            name: Build and Test
            caches:
              - node
            script:
              - npm ci
              - npm run build
              - npx serve -p 8000 build &
              - npx wait-on http://localhost:8000
              - npx satya-ci --target http://localhost:8000 --threshold 0 --output a11y-reports
            artifacts:
              - a11y-reports/**

  pull-requests:
    '**':
      - step:
          name: Accessibility Check
          caches:
            - node
          script:
            - npm ci
            - npm run build
            - npx serve -p 8000 build &
            - npx wait-on http://localhost:8000
            - npx satya-ci --target http://localhost:8000 --threshold 0
          deployment: test
```

## Strategy: Passing vs Failing Builds

### Strict Mode (Fail on any violation)

```bash
satya-ci --target https://example.com --threshold 0
```

### Baseline Mode (Allow existing issues)

```bash
# Run once to establish baseline
satya-ci --target https://example.com --threshold 999 > baseline.json

# Extract the number and use it as your threshold
satya-ci --target https://example.com --threshold 42
```

### Severity-Based Thresholds

```bash
# Custom script to enforce different thresholds per severity
#!/bin/bash
THRESHOLD_CRITICAL=0
THRESHOLD_HIGH=2
THRESHOLD_MEDIUM=5

REPORT=$(npx satya-ci --target https://example.com --output ./reports)
VIOLATIONS=$(jq '.violations' ./reports/satya-report.json)

CRITICAL=$(echo $VIOLATIONS | jq '[.[] | select(.severity=="critical")] | length')
HIGH=$(echo $VIOLATIONS | jq '[.[] | select(.severity=="high")] | length')
MEDIUM=$(echo $VIOLATIONS | jq '[.[] | select(.severity=="medium")] | length')

if [ $CRITICAL -gt $THRESHOLD_CRITICAL ] || [ $HIGH -gt $THRESHOLD_HIGH ] || [ $MEDIUM -gt $THRESHOLD_MEDIUM ]; then
  echo "Accessibility thresholds exceeded!"
  exit 1
fi
```

## Docker Integration Tips

### Multi-stage Build for CI

```dockerfile
# Build stage
FROM node:18 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Test stage
FROM satya-ci:latest
COPY --from=builder /app/build /app/build
WORKDIR /app
CMD ["satya-ci", "--target", "http://localhost:3000", "--threshold", "0"]
```

### Using with Docker Compose in CI

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "3000:3000"

  a11y:
    image: satya-ci:latest
    depends_on:
      - app
    environment:
      - TARGET_URL=http://app:3000
    command: satya-ci --target $TARGET_URL --threshold 0 --output /reports
    volumes:
      - ./a11y-reports:/reports
```

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [Jenkins Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/)
- [CircleCI Configuration Reference](https://circleci.com/docs/configuration-reference/)
- [Azure Pipelines YAML Reference](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema)
- [Bitbucket Pipelines Configuration](https://support.atlassian.com/bitbucket-cloud/docs/configure-bitbucket-pipelinesymls/)