# Trivy Node.js Demo

This is a small intentionally vulnerable Node.js project for testing Trivy in a Jenkins CI/CD pipeline.

## Why lodash 4.17.15?

The project deliberately pins an old lodash version so Trivy has a dependency to analyze.

Do not use this dependency version in a real application.

## Local test

1. Check Node/npm:

```bash
node --version
npm --version
```

2. Install dependencies:

```bash
npm install
```

3. Run Trivy:

```bash
trivy fs --scanners vuln .
```

4. Test the Jenkins-style gate:

```bash
trivy fs --scanners vuln --severity HIGH,CRITICAL --exit-code 1 .
```

A matching HIGH/CRITICAL vulnerability should make Trivy return exit code 1.

## Jenkins

Push all files to GitHub and create a Jenkins Pipeline job using "Pipeline script from SCM".

The Jenkinsfile performs:

GitHub -> Checkout -> Trivy scan -> npm install -> Node syntax check

The pipeline is intentionally expected to fail at the Trivy stage while the vulnerable lodash version remains in the project.

## Important

This is a security-testing demo only. Replace the vulnerable dependency with a current supported version before using the application in production.
