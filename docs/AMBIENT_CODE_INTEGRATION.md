# Integrating Dashboard Build Analyzer with Ambient Code Platform

## Executive Summary

This document analyzes how to integrate the **Dashboard Build Analyzer** into the **Ambient Code Platform** (https://github.com/ambient-code/platform) to run as an autonomous Claude Agent that automatically analyzes RHOAI/ODH nightly builds.

## Ambient Code Platform Overview

The Ambient Code Platform is a **Kubernetes-native AI automation platform** that orchestrates intelligent agentic sessions through containerized microservices. It provides:

### Core Architecture

```
User Request → Backend API → K8s Custom Resource (AgenticSession) →
Operator watches CR → Creates Job Pod → Claude Code Runner executes →
Results stored in CR → Status updates via WebSocket
```

### Key Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | NextJS + Shadcn | Web UI for session management |
| **Backend** | Go + Gin | REST API managing K8s Custom Resources |
| **Operator** | Go | K8s controller watching CRs, creating Jobs |
| **Runner** | Python | Job pods executing Claude Code CLI |

### Existing Agent Types

The platform already has several agent personas in `agents/`:
- **Amber** - Background automation agent (PR creation, issue triage)
- **Stella** - Staff Engineer (technical leadership)
- **Parker** - Product Manager
- **Ryan** - UX Researcher
- **Steve** - UX Designer
- **Terry** - Technical Writer

## Integration Options

### Option 1: New Agent Persona (Recommended)

Create a new agent persona specifically for build analysis:

**File: `agents/jenkins-analyst.md`**

```markdown
---
name: Jenkins Build Analyst
description: Automated E2E test analyzer for RHOAI/ODH dashboard builds
tools: Read, Write, Edit, Bash, Glob, Grep, WebSearch
model: sonnet
---

You are the Jenkins Build Analyst, an expert in analyzing Cypress E2E test failures for RHOAI/ODH dashboards. Your primary responsibilities:

## Core Capabilities

1. **Build Analysis**
   - Fetch latest Jenkins build artifacts
   - Parse JUnit XML test results
   - Identify pipeline vs test failures
   - Extract screenshots and error logs

2. **Test Reruns**
   - Automatically rerun failing tests to detect flakiness
   - Compare original vs rerun results
   - Categorize failures (flaky, consistent, timeout, auth, etc.)

3. **Commit Correlation**
   - Check recent GitHub Dashboard commits
   - Check recent GitLab Jenkins pipeline commits
   - Correlate failures with code changes

4. **Report Generation**
   - Generate comprehensive Markdown reports
   - Include failure screenshots
   - Provide Jira issue links
   - Suggest remediation actions

## Usage Pattern

When triggered:
1. Login to target cluster (RHOAI or ODH)
2. Fetch latest build from Jenkins
3. Parse test results and identify failures
4. Rerun failing tests
5. Generate report with findings
6. Optionally create Jira issues for consistent failures
```

### Option 2: Amber Extension

Extend the existing **Amber** agent to include build analysis capabilities by updating `agents/amber.md` with Jenkins analysis expertise.

### Option 3: Scheduled Background Job

Create a Kubernetes CronJob that triggers an AgenticSession for build analysis:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: nightly-build-analyzer
  namespace: ambient-code
spec:
  schedule: "0 10 * * 1-5"  # 10 AM Mon-Fri (after nightly builds complete)
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: trigger
            image: curlimages/curl
            command:
            - /bin/sh
            - -c
            - |
              curl -X POST https://vteam-backend/api/projects/rhoai-qa/agentic-sessions \
                -H "Authorization: Bearer $BOT_TOKEN" \
                -d '{
                  "name": "nightly-analysis-$(date +%Y%m%d)",
                  "prompt": "Analyze the latest RHOAI and ODH nightly builds",
                  "interactive": false,
                  "timeout": 1800
                }'
```

## Implementation Roadmap

### Phase 1: Containerize Dashboard Build Analyzer

1. **Create Dockerfile**

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install oc CLI
RUN curl -L https://mirror.openshift.com/pub/openshift-v4/clients/ocp/stable/openshift-client-linux.tar.gz | \
    tar -xz -C /usr/local/bin oc kubectl

# Install Node.js for Cypress
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# Copy analyzer code
WORKDIR /app
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt

# Create non-root user
RUN useradd -m analyzer
USER analyzer

ENTRYPOINT ["python", "scripts/comprehensive_analysis.py"]
```

2. **Build and Push Image**

```bash
podman build -t quay.io/ambient_code/build-analyzer:latest .
podman push quay.io/ambient_code/build-analyzer:latest
```

### Phase 2: Create Custom Runner

Extend `components/runners/` with a build-analyzer runner:

**File: `components/runners/build-analyzer/wrapper.py`**

```python
#!/usr/bin/env python3
"""
Build Analyzer Runner for Ambient Code Platform.
Wraps the dashboard-build-analyzer for K8s Job execution.
"""

import asyncio
import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, '/app/runner-shell')
from runner_shell.core.shell import RunnerShell
from runner_shell.core.context import RunnerContext


class BuildAnalyzerAdapter:
    """Adapter for dashboard-build-analyzer integration."""
    
    def __init__(self):
        self.context = None
        self.shell = None
        
    async def initialize(self, context: RunnerContext):
        """Initialize with context from CR."""
        self.context = context
        
        # Extract configuration from CR spec
        self.variant = context.get_env("CLUSTER_VARIANT", "rhoai")
        self.build_number = context.get_env("BUILD_NUMBER", "latest")
        self.enable_rerun = context.get_env("ENABLE_RERUN", "true")
        
    async def run(self):
        """Execute the build analysis."""
        try:
            # Construct command
            cmd = [
                "python", "/app/scripts/comprehensive_analysis.py",
                self.build_number,
                self.variant
            ]
            
            if self.enable_rerun == "true":
                cmd.append("--enable-rerun")
            
            # Execute analysis
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes
            )
            
            # Send results back
            await self._send_results(result)
            
            return {"success": result.returncode == 0}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def _send_results(self, result):
        """Send analysis results via WebSocket."""
        # Read generated report
        report_path = Path(f"/app/reports/current/{self.variant.upper()}/latest.md")
        if report_path.exists():
            report_content = report_path.read_text()
            await self.shell.send_message({
                "type": "result",
                "content": report_content
            })
```

### Phase 3: Define Custom Resource

Create a CRD for build analysis sessions:

```yaml
apiVersion: vteam.ambient-code/v1alpha1
kind: BuildAnalysisSession
metadata:
  name: nightly-2025-12-12
  namespace: rhoai-qa
spec:
  cluster: rhoai  # or "odh"
  buildNumber: "latest"  # or specific number like "3695"
  enableRerun: true
  enableTrend: false
  jiraIntegration: true
status:
  phase: Completed
  testResults:
    total: 145
    passed: 142
    failed: 3
    skipped: 0
  failingTests:
    - name: testRegisterModel
      category: timeout
      rerunPassed: false
  reportPath: reports/current/RHOAI/latest-build-3695.md
```

### Phase 4: Operator Watch Handler

Add a handler in `components/operator/internal/handlers/`:

```go
// build_analysis.go
package handlers

import (
    "context"
    "k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

func HandleBuildAnalysisSession(ctx context.Context, obj *unstructured.Unstructured) error {
    name := obj.GetName()
    namespace := obj.GetNamespace()
    
    spec, _, _ := unstructured.NestedMap(obj.Object, "spec")
    status, _, _ := unstructured.NestedMap(obj.Object, "status")
    
    phase, _ := status["phase"].(string)
    if phase != "" && phase != "Pending" {
        return nil // Already processed
    }
    
    // Create Job for build analysis
    cluster, _ := spec["cluster"].(string)
    buildNumber, _ := spec["buildNumber"].(string)
    
    job := createBuildAnalysisJob(namespace, name, cluster, buildNumber)
    
    // ... create job and update status
    return nil
}
```

### Phase 5: GitHub Actions Integration

Add a workflow to trigger analysis from GitHub:

**File: `.github/workflows/build-analysis.yml`**

```yaml
name: Nightly Build Analysis

on:
  schedule:
    - cron: '0 10 * * 1-5'  # 10 AM UTC Mon-Fri
  workflow_dispatch:
    inputs:
      variant:
        description: 'Cluster variant (rhoai/odh)'
        required: true
        default: 'rhoai'
      build_number:
        description: 'Build number (or "latest")'
        required: true
        default: 'latest'

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Trigger Analysis via Amber
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          cat > /tmp/analysis-prompt.md << 'EOF'
          Analyze the latest ${{ inputs.variant || 'rhoai' }} nightly build.
          
          Steps:
          1. Run: python scripts/comprehensive_analysis.py ${{ inputs.build_number || 'latest' }} ${{ inputs.variant || 'rhoai' }}
          2. Read the generated report
          3. If there are consistent failures, create Jira issues
          4. Post summary to #dashboard-qa Slack channel
          EOF
          
          cat /tmp/analysis-prompt.md | claude --print --dangerously-skip-permissions
```

## Required Environment Variables

For the runner to work, these secrets need to be configured:

```yaml
# In ProjectSettings CR or K8s Secret
apiVersion: v1
kind: Secret
metadata:
  name: build-analyzer-secrets
  namespace: rhoai-qa
stringData:
  JENKINS_URL: "https://your-jenkins.example.com"
  JENKINS_USER: "jenkins-user"
  JENKINS_TOKEN: "jenkins-api-token"
  JIRA_URL: "https://issues.redhat.com"
  JIRA_TOKEN: "jira-api-token"
  GITLAB_URL: "https://gitlab.cee.redhat.com"
  GITLAB_TOKEN: "gitlab-token"
  RHOAI_API_SERVER: "https://api.dash-e2e-rhoai.osp.rh-ods.com:6443"
  RHOAI_USERNAME: "htpasswd-cluster-admin-user"
  RHOAI_PASSWORD: "cluster-password"
  ODH_API_SERVER: "https://api.dash-e2e-odh.osp.rh-ods.com:6443"
  ODH_USERNAME: "htpasswd-cluster-admin-user"
  ODH_PASSWORD: "cluster-password"
```

## Integration with Existing Amber Workflows

### Issue-to-Analysis Flow

When someone creates a GitHub issue like:
```
Title: [Build Analysis] Investigate RHOAI nightly failures 2025-12-12
Labels: amber:execute
Body: 
  Analyze RHOAI build 3695 and identify root causes for failures.
  Create Jira issues for consistent failures.
```

Amber can:
1. Trigger the build analyzer
2. Generate the report
3. Create follow-up Jira issues
4. Comment on the GitHub issue with findings

### Proactive Monitoring

Amber can monitor Jenkins and proactively:
1. Detect failed nightly builds
2. Create GitHub issues with analysis
3. Tag relevant team members
4. Track issue resolution

## Estimated Implementation Effort

| Phase | Effort | Dependencies |
|-------|--------|--------------|
| Phase 1: Containerization | 1-2 days | None |
| Phase 2: Custom Runner | 2-3 days | Phase 1 |
| Phase 3: CRD Definition | 1 day | Phase 2 |
| Phase 4: Operator Handler | 2-3 days | Phase 3 |
| Phase 5: GitHub Actions | 1 day | Phase 1 |

**Total: ~8-10 days**

## Next Steps

1. **Fork ambient-code/platform** to start development
2. **Create feature branch**: `feature/build-analyzer-integration`
3. **Implement Phase 1** (containerization) first
4. **Test locally** with minikube or CRC
5. **Submit PR** for review

## References

- [Ambient Code Platform README](https://github.com/ambient-code/platform)
- [CLAUDE.md](https://github.com/ambient-code/platform/blob/main/CLAUDE.md) - Project standards
- [Amber Agent](https://github.com/ambient-code/platform/blob/main/agents/amber.md) - Background agent patterns
- [Claude Code Runner](https://github.com/ambient-code/platform/blob/main/docs/CLAUDE_CODE_RUNNER.md) - Runner architecture
- [Cypress E2E Rules](https://github.com/opendatahub-io/odh-dashboard/blob/main/.cursor/rules/cypress-e2e.mdc) - Test execution patterns








