# Dashboard Build Analyzer

Comprehensive analysis tool for dashboard builds on OpenShift clusters. Analyzes Cypress E2E test results, cluster health, and pipeline status for RHOAI/ODH dashboard builds. Connects to Jenkins, inspects cluster resources, and generates detailed reports with actionable recommendations.

## 📚 Documentation

- **[CLAUDE_AGENT_GUIDE.md](docs/CLAUDE_AGENT_GUIDE.md)** - 🤖 **Quick reference for AI agents** - Start here!
- **[JIRA_SEARCH_PATTERNS.md](docs/JIRA_SEARCH_PATTERNS.md)** - Intelligent Jira search patterns

## Features

- **Automated Jenkins Integration**: Fetches latest nightly build results from Jenkins
- **Artifact Parsing**: Parses Cypress test results from build logs and JSON artifacts
- **Cluster Health Inspection**: Read-only inspection of OpenShift cluster resources (pods, events, deployments)
- **Intelligent Failure Analysis**: Categorizes failures and correlates with cluster state
- **Daily Reports**: Generates detailed markdown reports with actionable recommendations
- **Read-Only Cluster Access**: Never modifies cluster resources - strictly a debug agent

## Architecture

```
scripts/
├── comprehensive_analysis.py  # PRIMARY: Full analysis with all features
├── analyze_job.py             # Generic job analyzer (any Jenkins job)
├── nightly_analyzer.py        # Scheduled orchestrator
└── run.sh                     # Convenience runner script
analyzer/
├── config.py                  # Configuration management
├── jenkins_client.py          # Jenkins API wrapper
├── artifact_parser.py         # Parse test results and logs
├── cluster_inspector.py       # Read-only cluster inspection
├── failure_analyzer.py        # Analyze and categorize failures
├── jira_client.py            # Jira integration
├── jira_search_patterns.py   # Intelligent Jira search
└── report_generator.py       # Generate markdown reports
mcp/
└── server.py                  # MCP server for AI agents
```

## Prerequisites

- Python 3.8+
- Jenkins API token
- Access to RHOAI and ODH clusters
- `oc` CLI tool installed and in PATH

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd dashboard-build-analyzer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp env.template .env
# Edit .env with your credentials (see Configuration section)
```

4. Verify configuration:
```bash
python -c "from analyzer.config import Config; Config.validate()"
```

## Configuration

### Environment Variables

**IMPORTANT**: All sensitive credentials must be configured via environment variables.

1. Copy the template to create your `.env` file:
```bash
cp env.template .env
```

2. Edit `.env` and fill in your actual credentials:

```bash
# Required
JENKINS_URL=https://your-jenkins-instance.example.com
JENKINS_USER=your-username
JENKINS_TOKEN=your-api-token

# Required for Jira integration
JIRA_URL=https://issues.redhat.com
JIRA_TOKEN=your-jira-api-token

# Required for GitLab commit analysis
GITLAB_URL=https://gitlab.cee.redhat.com
GITLAB_TOKEN=your-gitlab-personal-access-token

# Required - Path to odh-dashboard repository
FRONTEND_REPO_PATH=/path/to/your/odh-dashboard

# Required - Cluster credentials
RHOAI_API_SERVER=https://api.your-rhoai-cluster.example.com:6443
RHOAI_USERNAME=your-cluster-username
RHOAI_PASSWORD=your-cluster-password

ODH_API_SERVER=https://api.your-odh-cluster.example.com:6443
ODH_USERNAME=your-cluster-username
ODH_PASSWORD=your-cluster-password

# Optional
REPORT_OUTPUT_DIR=./reports
RHOAI_TEST_VARIABLES=/path/to/rhoai/test-variables.yml
ODH_TEST_VARIABLES=/path/to/odh/test-variables.yml
TRACER_PATH=/path/to/tracer/tracer.sh
```

3. **Never commit the `.env` file** - it's in `.gitignore` for security

4. **Optional: Jenkins MCP Server**
   ```bash
   # OPTIONAL: MCP Server URL (leave empty for direct HTTP API - recommended)
   # JENKINS_MCP_URL=https://your-jenkins-mcp.com/sse
   ```
   
   **Note**: The Red Hat internal MCP server currently has bugs preventing job access.
   Direct HTTP API is recommended and works reliably. See `MCP_STATUS.md` for details.

## Usage

### 🤖 Quick Start for Claude Agents

**To analyze the latest RHOAI or ODH nightly build:**

```bash
# Activate virtual environment
cd /Users/acoughli/dashboard-build-analyzer
source venv/bin/activate

# Analyze latest RHOAI build (automatically finds the latest build number)
python scripts/analyze_job.py --job "cypress/dashboard-tests" --build latest

# OR use comprehensive_analysis.py with a specific build number
# (Use this for full image tracking, sync detection, and all features)
python scripts/comprehensive_analysis.py 3695 rhoai
```

**What this does automatically:**
- ✅ Finds the latest build number (when using `--build latest`)
- ✅ Fetches all test results and console logs
- ✅ **Automatically reruns all failing tests** to check for flakiness
- ✅ Tracks deployed images (FBC, IIB, Dashboard)
- ✅ Detects test/code synchronization issues
- ✅ Analyzes pipeline failures with specific step identification
- ✅ Correlates with recent GitHub Dashboard and GitLab Jenkins commits
- ✅ Searches Jira for related issues
- ✅ Inspects cluster health (if credentials are configured)
- ✅ Generates comprehensive markdown report

**Reports are saved to:**
- `reports/current/RHOAI/latest-build-{number}.md`
- `reports/current/ODH/latest-build-{number}.md`
- `reports/historical/{date}-{variant}-build-{number}-v2.md`

**Important Notes:**
- The tool **always reruns failing tests** as part of the analysis (no flag needed)
- Use `comprehensive_analysis.py` for RHOAI/ODH builds (full features)
- Use `analyze_job.py --build latest` for any other Jenkins job
- All credentials are loaded from the `.env` file

**Recommended Workflow for Claude Agents:**

```bash
# Step 1: Navigate to the analyzer directory
cd /Users/acoughli/dashboard-build-analyzer

# Step 2: Find the latest RHOAI build and analyze it
python venv/bin/python scripts/analyze_job.py --job "cypress/dashboard-tests" --build latest

# The output will show:
# "Build #3695: https://jenkins.../3695/"
# "Status: FAILURE"
# "Build time: 2025-12-10 03:52:00 (5.5 hours ago)"
# ... (full analysis with reruns)

# Step 3 (Optional): For more detailed RHOAI/ODH specific analysis
# Extract the build number from Step 2 output and run:
python venv/bin/python scripts/comprehensive_analysis.py 3695 rhoai

# This provides additional features:
# - Image deployment tracking (FBC, IIB, Dashboard)
# - Dashboard commit sync detection
# - GitLab Jenkins repo commit correlation
# - More detailed pipeline failure analysis
# - Trend analysis (when --enable-trend is used)
```

**Which script should I use?**

| Scenario | Use This | Why |
|----------|----------|-----|
| Just need latest build analysis | `analyze_job.py --build latest` | Automatically finds latest build, includes reruns |
| RHOAI/ODH specific features needed | `comprehensive_analysis.py <build#> <variant>` | Full image tracking, sync detection, GitLab correlation |
| Analyzing any other Jenkins job | `analyze_job.py --job <path> --build <#>` | Generic job analyzer for any pipeline |

### Option 1: Generic Job Analysis

Analyze **any** Jenkins job - perfect for finding the latest build:

```bash
# Basic analysis (no cluster needed)
python scripts/analyze_job.py --job "cypress/dashboard-tests" --build 3597

# Latest build
python scripts/analyze_job.py --job "your/team/pipeline" --build latest

# With optional cluster inspection
python scripts/analyze_job.py \
  --job "cypress/dashboard-tests" \
  --build 3597 \
  --cluster-api "https://api.cluster.com:6443" \
  --cluster-user "admin" \
  --cluster-pass "secret" \
  --namespace "my-namespace"
```

**Perfect for central agent** - works without cluster credentials!

### Option 2: Comprehensive Analysis (For RHOAI/ODH Nightly)

Run the comprehensive analysis with image tracking, sync detection, and full cluster health.

**Step 1: Find the latest build number**

You can use `analyze_job.py` to automatically find the latest build:

```bash
# This will print the latest build number in the output
python scripts/analyze_job.py --job "cypress/dashboard-tests" --build latest
```

Look for the line: `Build #XXXX: https://jenkins...` - this is your build number.

**Step 2: Run comprehensive analysis**

```bash
# For RHOAI (manual analysis, no trend comparison)
python scripts/comprehensive_analysis.py 3695 rhoai

# For ODH
python scripts/comprehensive_analysis.py 3691 odh

# For automated nightly analysis (with trend comparison)
python scripts/comprehensive_analysis.py 3695 rhoai --enable-trend
```

**Usage:**
- `<build_number>`: Jenkins build number to analyze (required - use the number from Step 1)
- `[odh|rhoai]`: Cluster variant (required - specify "odh" or "rhoai")
- `--enable-trend`: Enable trend analysis comparing with previous build (optional - use for automated nightly runs, omit for manual analysis)

This generates the reports in `reports/current/` and includes:
- Pipeline failure detection
- Image deployment tracking (FBC fragment, IIB, Dashboard)
- Dashboard commit sync detection
- Test failure analysis with Jira searches
- Cluster health inspection
- Screenshot capture for failures
- GitLab commit correlation
- Trend analysis (when `--enable-trend` is used)

### Option 3: Scheduled Analysis

Use the scheduler for automatic daily analysis:

```bash
python scripts/nightly_analyzer.py --mode run-now    # Run immediately
python scripts/nightly_analyzer.py --mode schedule   # Run on schedule

# Or use the convenience script
./scripts/run.sh run-now
./scripts/run.sh schedule
```

### Example Output

```
============================================================
NIGHTLY E2E TEST ANALYSIS
Date: 2025-01-14 09:30:00 GMT
============================================================

============================================================
Analyzing dash-e2e-rhoai
============================================================

Build #3507: https://jenkins.../job/cypress/job/dashboard-tests/3507/
Status: FAILURE
Build time: 2025-01-14 03:15:42 (6.2 hours ago)

Fetching build log...
Parsing test results...
Fetching build artifacts...

Test Results:
  Total: 145
  Passed: 142
  Failed: 3
  Skipped: 0

🔍 Inspecting RHOAI cluster health...
✅ Logged into RHOAI cluster

Cluster Health Summary:
  Namespace: redhat-ods-applications
  Total Pods: 45
  Running: 43
  Failed: 2
  Crash Looping: 0

📊 Analyzing failures...

Failure Breakdown:
  timeout: 2
  assertion: 1

============================================================
GENERATING REPORT
============================================================

✅ Report saved to: ./reports/nightly-report-2025-01-14.md
✅ Latest report updated: ./reports/latest.md
```

## Reports

Reports are saved in the `REPORT_OUTPUT_DIR` (default: `./reports/`):

- `nightly-report-YYYY-MM-DD.md` - Daily report
- `latest.md` - Always points to the most recent report

### Report Contents

Each report includes:

1. **Executive Summary**: Overall health status across both clusters
2. **RHOAI E2E Results**: Detailed failure analysis for RHOAI cluster
3. **ODH E2E Results**: Detailed failure analysis for ODH cluster
4. **Failure Categories**: Breakdown by type (timeout, assertion, network, etc.)
5. **Cluster Health**: Pod status and recent cluster events
6. **Recommended Actions**: Prioritized list of debugging steps

### Failure Categories

Failures are automatically categorized as:

- **timeout**: Test timed out waiting for condition
- **assertion**: Assertion failed (expected vs actual mismatch)
- **element_not_found**: UI element not found in DOM
- **network**: Network/API request failure
- **auth**: Authentication/authorization issue
- **resource**: Cluster resource problem (pods, deployments)
- **unknown**: Uncategorized failure requiring manual review

## How It Works

### Job Structure (Updated Dec 2025)

Nightly E2E tests use a two-job structure:

1. **`devops/rhoai-test-flow`** - Parent orchestrator (handles setup, triggers tests)
2. **`cypress/dashboard-tests`** - Cypress E2E tests (contains test results)

### 1. Fetch Latest Builds

The analyzer connects to Jenkins and finds the latest nightly builds for:
- `cypress/dashboard-tests` (with description containing `dash-e2e-rhoai` or `dash-e2e-odh`)

For nightly cron builds, it also finds the parent `rhoai-test-flow` build to track deployment failures.

It verifies these are recent (< 24 hours) and ran during nightly window (2-4 AM).

### 2. Parse Test Results

Extracts test results from:
- Build console logs (using regex patterns)
- JSON artifacts (mochawesome format)
- JUnit XML (if available)

Identifies:
- Total/passed/failed/skipped counts
- Individual test failures with error messages and stack traces
- Test file paths

### 3. Inspect Cluster Health

For builds with failures, logs into the respective cluster (read-only) and checks:
- Pod health (running, failed, crash-looping)
- Recent cluster events (warnings, errors)
- Deployment and service status

Correlates cluster issues with test failures.

### 4. Analyze Failures

For each failure:
- Categorizes by type
- Determines likely cause
- Finds cluster correlations
- Generates recommended actions
- Creates rerun command

### 5. Generate Report

Creates comprehensive markdown report with:
- Executive summary
- Detailed failure analysis
- Cluster health status
- Actionable recommendations

## Read-Only Cluster Access

The cluster inspector is **strictly read-only**:

```python
# Only these oc commands are allowed:
- get
- describe
- logs
- whoami
- version
- status
```

Any attempt to run destructive commands (apply, delete, patch, etc.) will raise an error. This ensures the tool can never modify cluster state.

## Test Discovery

The analyzer understands Cypress test structure from:
- Test location: `frontend/src/__tests__/cypress/cypress/tests/e2e/`
- Test naming: `*.cy.ts` files
- Cypress rules: `.cursor/rules/cypress-e2e.mdc`

This allows it to:
- Map failures to source files
- Generate rerun commands
- Understand test organization

## Rerunning Failed Tests

The analyzer can generate commands to rerun specific failed tests:

```bash
cd frontend && npm run cy:run:safe -- --spec 'src/__tests__/cypress/cypress/tests/e2e/modelServing/modelRegistry.cy.ts'
```

You'll need to provide the test-variables.yml for the respective cluster.

## Security Best Practices

🔒 **Important Security Guidelines:**

1. **Never commit credentials** to version control
   - The `.env` file is in `.gitignore` - keep it that way
   - Use `env.template` as a reference template

2. **Rotate credentials regularly**
   - Jenkins API tokens
   - Jira API tokens
   - GitLab tokens
   - Cluster passwords

3. **Use least-privilege access**
   - Jenkins: Read-only access is sufficient
   - Clusters: Read-only service accounts recommended
   - Jira: Read-only API token

4. **Protect your environment**
   - Set proper file permissions: `chmod 600 .env`
   - Don't share `.env` files via email/chat
   - Use secret management tools in production (Vault, AWS Secrets Manager, etc.)

## Troubleshooting

### Missing Required Configuration

```bash
# Validate your configuration
python -c "from analyzer.config import Config; Config.validate()"
```

If you see errors about missing environment variables, check that:
1. Your `.env` file exists
2. All required variables are set
3. Values don't have quotes (unless the value itself contains spaces)

### Jenkins Connection Issues

```bash
# Test Jenkins connectivity
curl -u "$JENKINS_USER:$JENKINS_TOKEN" \
  "$JENKINS_URL/api/json"
```

### Cluster Login Failures

```bash
# Manually test cluster login
oc login -u "$RHOAI_USERNAME" \
  -p "$RHOAI_PASSWORD" \
  --server="$RHOAI_API_SERVER"
```

### Missing Build Artifacts

The analyzer works with or without JSON artifacts - it can parse results from console logs alone.

### Timezone Issues

The scheduler uses GMT. Current time is displayed when analyzer runs. To run in a different timezone, set `SCHEDULE_TIME` in your `.env` file.

## Development

### Project Structure

```
dashboard-build-analyzer/
├── scripts/                       # Executable entry points
│   ├── comprehensive_analysis.py  # PRIMARY: Full analysis tool
│   ├── analyze_job.py             # Generic job analyzer
│   ├── nightly_analyzer.py        # Scheduled orchestrator
│   └── run.sh                     # Convenience runner
├── analyzer/                      # Core library modules
│   ├── __init__.py
│   ├── config.py                  # Configuration management
│   ├── jenkins_client.py          # Jenkins API client
│   ├── artifact_parser.py         # Test result parsing
│   ├── cluster_inspector.py       # Cluster health checks
│   ├── failure_analyzer.py        # Failure categorization
│   ├── jira_client.py            # Jira integration
│   ├── jira_search_patterns.py   # Intelligent Jira search
│   └── report_generator.py       # Report generation
├── mcp/                           # MCP server
│   ├── __init__.py
│   └── server.py                  # MCP server for AI agents
├── env.template                   # Environment variables template
├── requirements.txt               # Python dependencies
├── Containerfile                  # Container build file
├── docs/                          # Documentation
│   └── JIRA_SEARCH_PATTERNS.md   # Jira search documentation
└── reports/                       # Generated reports
    ├── current/                   # Latest reports
    │   ├── ODH/
    │   └── RHOAI/
    └── historical/                # Historical reports
```

### Adding New Failure Categories

Edit `analyzer/failure_analyzer.py`:

```python
def categorize_failure(self, failure: TestFailure) -> str:
    # Add new category logic
    if 'your-pattern' in combined:
        return 'your_category'
```

### Adding Cluster Checks

Edit `analyzer/cluster_inspector.py`:

```python
async def your_new_check(self, namespace: str) -> Dict[str, Any]:
    # Add new read-only cluster check
    result = await self._run_oc_command('get', 'resource', '-n', namespace)
    return result
```

## Related Projects

- [jenkins-mcp](https://github.com/redhat-community-ai-tools/jenkins-mcp) - Base MCP server for Jenkins
- [odh-dashboard](https://github.com/opendatahub-io/odh-dashboard) - Dashboard with E2E tests

## Jenkins MCP Server Integration

### Option 1: Direct HTTP API (Default - Works Great!)

**Default mode** - uses direct Jenkins REST API:

```bash
# Leave JENKINS_MCP_URL empty in .env
# JENKINS_MCP_URL=
```

**Benefits**:
- ✅ Works with any Jenkins
- ✅ No additional setup
- ✅ Fast and reliable
- ✅ Already working!

### Option 2: Local MCP Server (For Advanced Use)

**For ambient tool integration**, run MCP server locally:

```bash
# Clone and run locally
git clone https://github.com/bdattoma/rhoai-jenkins-mcp.git
cd rhoai-jenkins-mcp && uv run main.py

# Update .env
JENKINS_MCP_URL=http://localhost:8000/sse
```

**Benefits**:
- ✅ MCP protocol for AI agents
- ✅ Can reach internal Jenkins
- ✅ Standardized tool interfaces

**Note**: Public MCP servers cannot reach internal Jenkins instances. Run locally if needed.

### Option 2: Direct HTTP API (Fallback)

If no `JENKINS_MCP_URL` is configured, uses direct HTTP API:
- ✅ Works with any Jenkins
- ✅ No MCP server needed
- ✅ Simple and reliable

### Option 3: Our MCP Server (For External AI Agents)

We also include `mcp/server.py` to expose **our** analysis tools to AI agents:
- Runs locally via stdio
- Provides analysis tools (not just Jenkins access)
- For your ambient tool to call our analyzer

```bash
python mcp/server.py
```

---

## License

This project inherits the license from the jenkins-mcp project.

## Contributing

Contributions welcome! This is a debug-only tool - ensure any changes maintain the read-only nature of cluster operations.

## Support

For issues or questions:
- Jenkins access: Contact your Jenkins administrator
- Cluster access: Contact OpenShift cluster team
- Tool issues: Open an issue in this repository
