# Claude Agent Quick Reference Guide

This guide is specifically for Claude AI agents to quickly understand and use the Dashboard Build Analyzer.

## 🎯 Primary Goal

Analyze RHOAI/ODH nightly Cypress E2E test builds from Jenkins, automatically rerun failing tests to check for flakiness, and generate comprehensive reports.

## 📋 Job Structure (Updated Dec 2025)

Nightly E2E tests now use a two-job structure:

1. **`devops/rhoai-test-flow`** - Parent orchestrator job
   - Handles cluster setup and configuration
   - Deploys RHOAI/ODH operators
   - Verifies dashboard readiness
   - Triggers `dashboard-tests` as downstream job
   - Nightly crons start here (2 AM RHOAI, 3 AM ODH)

2. **`cypress/dashboard-tests`** - Cypress E2E test job
   - Runs the actual Cypress tests
   - Contains test results and artifacts
   - This is what we analyze for test failures

**Important:** Test results are in `dashboard-tests`, but deployment failures may be in `rhoai-test-flow`.
The analyzer automatically finds and links the parent build for nightly crons.

## 📍 Quick Commands

### Find and Analyze Latest Build (Simplest Method)

```bash
cd /Users/acoughli/dashboard-build-analyzer
venv/bin/python scripts/analyze_job.py --job "cypress/dashboard-tests" --build latest
```

**This automatically:**
- ✅ Finds the latest build number
- ✅ Fetches all test results
- ✅ **Reruns all failing tests** to check for flakiness
- ✅ Generates analysis report

### Full Analysis for RHOAI/ODH (Recommended for Nightly Builds)

```bash
cd /Users/acoughli/dashboard-build-analyzer

# Step 1: Find latest build number
venv/bin/python scripts/analyze_job.py --job "cypress/dashboard-tests" --build latest | grep "Build #"
# Output: "Build #3695: https://..."

# Step 2: Run comprehensive analysis with that build number
venv/bin/python scripts/comprehensive_analysis.py 3695 rhoai
# OR for ODH:
venv/bin/python scripts/comprehensive_analysis.py 3691 odh
```

## 📂 Report Locations

After running analysis, reports are saved to:

- **RHOAI:** `reports/current/RHOAI/latest-build-{number}.md`
- **ODH:** `reports/current/ODH/latest-build-{number}.md`
- **Historical:** `reports/historical/{date}-{variant}-build-{number}-v2.md`
- **Generic Jobs:** `reports/analysis-{job-name}-{number}.md`

## 🔍 What Each Script Does

### `analyze_job.py` - Generic Job Analyzer

**Use when:** You want to quickly analyze ANY Jenkins job, or automatically find the latest build.

```bash
# Analyze latest build (finds build number automatically)
venv/bin/python scripts/analyze_job.py --job "cypress/dashboard-tests" --build latest

# Analyze specific build
venv/bin/python scripts/analyze_job.py --job "cypress/dashboard-tests" --build 3695
```

**Features:**
- ✅ Automatic latest build discovery
- ✅ Test result parsing
- ✅ **Automatic test reruns** for failing tests
- ✅ Jira issue searching
- ✅ Basic report generation
- ✅ Works with any Jenkins job

**Does NOT include:**
- ❌ Image deployment tracking
- ❌ Dashboard commit sync detection
- ❌ GitLab Jenkins repo correlation
- ❌ Trend analysis

### `comprehensive_analysis.py` - Full RHOAI/ODH Analyzer

**Use when:** You need complete analysis with image tracking and sync detection for RHOAI/ODH builds.

```bash
# Requires explicit build number and variant
venv/bin/python scripts/comprehensive_analysis.py 3695 rhoai
venv/bin/python scripts/comprehensive_analysis.py 3691 odh

# With trend analysis (compares to previous build)
venv/bin/python scripts/comprehensive_analysis.py 3695 rhoai --enable-trend
```

**Features:**
- ✅ Everything from `analyze_job.py` PLUS:
- ✅ Deployed image tracking (FBC fragment, IIB, Dashboard)
- ✅ Dashboard commit synchronization detection
- ✅ GitLab Jenkins repo commit correlation
- ✅ Pipeline failure step identification ("Post Actions", "Install ODH Operator", etc.)
- ✅ **Parent build tracking** - Links to rhoai-test-flow for nightly crons
- ✅ **Parent failure detection** - Shows if failure was in setup vs tests
- ✅ Test/code sync issue detection
- ✅ Trend analysis (with `--enable-trend`)
- ✅ More detailed Jira correlation

**Requirements:**
- Must specify build number (cannot use "latest")
- Must specify variant (rhoai or odh)

## 🤖 Typical Claude Agent Workflow

### Scenario 1: "Analyze last night's build"

```bash
cd /Users/acoughli/dashboard-build-analyzer

# Quick method - one command does everything
venv/bin/python scripts/analyze_job.py --job "cypress/dashboard-tests" --build latest

# Read the report (path shown in output)
cat reports/analysis-cypress-dashboard-tests-3695.md
```

### Scenario 2: "Full RHOAI analysis with all features"

```bash
cd /Users/acoughli/dashboard-build-analyzer

# Step 1: Find latest build
BUILD_NUM=$(venv/bin/python scripts/analyze_job.py --job "cypress/dashboard-tests" --build latest 2>&1 | grep "Build #" | grep -oP '\d+' | head -1)

# Step 2: Run comprehensive analysis
venv/bin/python scripts/comprehensive_analysis.py $BUILD_NUM rhoai

# Step 3: Read the comprehensive report
cat reports/current/RHOAI/latest-build-${BUILD_NUM}.md
```

### Scenario 3: "Compare today's build to yesterday's"

```bash
cd /Users/acoughli/dashboard-build-analyzer

# Use --enable-trend flag for automated nightly analysis
venv/bin/python scripts/comprehensive_analysis.py 3695 rhoai --enable-trend

# This adds trend analysis comparing with previous build
```

## 📋 Report Contents

Each report includes:

1. **Quick Status Overview** - Pass/fail summary, test counts
2. **Parent Build Link** - For nightly crons, links to rhoai-test-flow build
3. **Parent Pipeline Failure** (if applicable) - Details about failures in rhoai-test-flow:
   - Which setup stage failed
   - Stages completed before failure
   - Whether tests could run
4. **Deployment & Image Information** - Deployed images, commit tracking
5. **Pipeline Failure Details** - Which step failed in dashboard-tests
6. **Test Failures** - Detailed failure analysis with:
   - Test name (e.g., `testRegisterModel`, not long describe/it chains)
   - Error message and stack trace
   - Rerun results (passed on rerun = flaky, failed on rerun = consistent)
   - Related Jira issues
   - Category (timeout, auth, resource, etc.)
7. **Recent Commits** - Separated into:
   - GitLab Jenkins changes (can break pipeline)
   - GitHub Dashboard changes (can break E2E tests only)
8. **Cluster Health** - Pod status, events, warnings

## 🔑 Key Features

### Automatic Test Reruns

**All failing tests are automatically rerun** to determine if they're flaky or consistently failing.

- ✅ Passed on rerun = **Intermittent/Flaky** test
- ❌ Failed on rerun = **Consistently failing** test

This happens automatically - no flags needed.

### Test Name Display

Test names are shown as clean filenames, not long describe/it chains:

- ✅ `testRegisterModel`
- ✅ `testClusterStorageCreation`
- ❌ NOT: "Verify the filters on Resources page Verify the filters on Resources page Test whether enabled..."

### Pipeline Failure Detection

Correctly identifies which pipeline step failed, including parent job failures:

**Parent Job (rhoai-test-flow) failures:**
- ✅ "Configure Cluster"
- ✅ "Deploy RHOAI Operator" / "Deploy ODH Operator"
- ✅ "Verify Dashboard is Ready" (before tests)

**Dashboard-tests job failures:**
- ✅ "Post Actions" (failures after tests complete)
- ✅ "Run Cypress Tests"

**Reports show:**
- Parent build link and status for nightly crons
- Which stages completed vs failed
- Whether failure occurred before tests could run

### Commit Categorization

Commits are separated by impact:

- **GitLab Jenkins commits** - Can break the pipeline itself
- **GitHub Dashboard commits** - Can only break E2E tests, not the pipeline

## ⚠️ Common Issues

### Issue: "ModuleNotFoundError: No module named 'X'"

**Solution:** Always use `venv/bin/python` not just `python`

```bash
# Wrong
python scripts/analyze_job.py

# Correct
venv/bin/python scripts/analyze_job.py
```

### Issue: "Missing required environment variables"

**Solution:** Ensure `.env` file exists and is configured

```bash
# Check if .env exists
ls -la /Users/acoughli/dashboard-build-analyzer/.env

# Verify config
venv/bin/python -c "from analyzer.config import Config; Config.validate()"
```

### Issue: "Cannot find build"

**Solution:** The build might not exist or Jenkins might be unreachable

```bash
# Test Jenkins connection
curl -u "$JENKINS_USER:$JENKINS_TOKEN" "$JENKINS_URL/api/json"
```

## 📖 Environment Variables

All credentials are loaded from `/Users/acoughli/dashboard-build-analyzer/.env`:

**Required:**
- `JENKINS_URL` - Jenkins instance URL
- `JENKINS_USER` - Jenkins username
- `JENKINS_TOKEN` - Jenkins API token
- `FRONTEND_REPO_PATH` - Path to odh-dashboard repo
- `JENKINS_REPO_PATH` - Path to Jenkins GitLab repo
- Cluster credentials (RHOAI_*, ODH_*)

**Optional:**
- `JIRA_TOKEN` - For Jira issue correlation
- `GITLAB_TOKEN` - For GitLab commit analysis
- `TRACER_PATH` - For image metadata extraction

## 🎓 Advanced Usage

### Analyzing Non-Nightly Builds

```bash
# Any build from any Jenkins job
venv/bin/python scripts/analyze_job.py \
  --job "your/team/pipeline" \
  --build 1234
```

### Scheduled Analysis

```bash
# Run immediately
venv/bin/python scripts/nightly_analyzer.py --mode run-now

# Run on schedule (Mon-Fri 9:30 AM GMT)
venv/bin/python scripts/nightly_analyzer.py --mode schedule
```

## 🔗 Related Documentation

- **Full README:** `README.md` - Complete documentation
- **Jira Search Patterns:** `docs/JIRA_SEARCH_PATTERNS.md` - How Jira searches work
- **Environment Template:** `env.template` - Configuration reference

---

## 🧪 Manual Test Rerun Commands

When you need to manually rerun a specific test:

### Setup (One-time)
```bash
# Ensure odh-dashboard repo has dependencies installed
cd ~/odh-dashboard && npm install

# Test-variables are stored in dashboard-build-analyzer:
# - RHOAI: /Users/acoughli/dashboard-build-analyzer/test-variables/rhoai-test-variables.yml
# - ODH: /Users/acoughli/dashboard-build-analyzer/test-variables/odh-test-variables.yml
```

### Login to Cluster
```bash
# For RHOAI
oc login -u htpasswd-cluster-admin-user -p 'rhodsPW#123456' \
  --server=https://api.dash-e2e-rhoai.osp.rh-ods.com:6443 \
  --insecure-skip-tls-verify=true

# For ODH
oc login -u htpasswd-cluster-admin-user -p 'rhodsPW#123456' \
  --server=https://api.dash-e2e-odh.osp.rh-ods.com:6443 \
  --insecure-skip-tls-verify=true
```

### Run Tests
```bash
cd ~/odh-dashboard/packages/cypress

# Run specific test file
export CY_TEST_CONFIG='/Users/acoughli/dashboard-build-analyzer/test-variables/rhoai-test-variables.yml'
npx cypress run --spec 'cypress/tests/e2e/dashboardNavigation/testUserLogin.cy.ts' --browser electron

# Run test by name (grep filter)
npx cypress run --env '{"grep":"Admin Users can login","grepFilterSpecs":true}' --browser electron

# Run all tests in a directory
npx cypress run --spec 'cypress/tests/e2e/modelRegistry/*.cy.ts' --browser electron
```

### Test File Locations
Tests are located at: `~/odh-dashboard/packages/cypress/cypress/tests/e2e/`

Common test directories:
- `dashboardNavigation/` - Login, navigation tests
- `modelServing/` - Model serving tests
- `modelRegistry/` - Model registry tests
- `pipelines/` - Data science pipelines tests
- `projects/` - Project management tests

## 🤖 Ambient Code Platform Integration

For running this analyzer as an autonomous Claude Agent, see:
- **[AMBIENT_CODE_INTEGRATION.md](./AMBIENT_CODE_INTEGRATION.md)** - Full integration guide

---

**Last Updated:** 2025-12-15

**Questions?** All functionality is self-contained - just run the commands and read the generated reports!




