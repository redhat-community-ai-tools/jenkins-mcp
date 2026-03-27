# jenkins-mcp

MCP Server for multiple Jenkins instances

## Overview

This MCP (Model Context Protocol) server allows you to interact with multiple Jenkins instances from a single server. Unlike traditional setups, this server extracts the Jenkins URL and an API token from each request's headers, enabling true multi-tenancy.

- **Multi-tenancy**: Serve multiple Jenkins instances from a single MCP server.
- **Header-based authentication**: Jenkins URL, username, and token are provided per request via headers.
- **Parity with official Jenkins MCP plugin**: Implements the same core tools as the [official Jenkins MCP Server Plugin](https://plugins.jenkins.io/mcp-server/), plus additional tools for pipeline and build analysis.

### Credential Loading (Priority Order)

1. **`~/.jenkins/config.json`** file (if it exists)
2. **`.env`** file in the project root (via python-dotenv)
3. **Environment variables** (`JENKINS_URL`, `JENKINS_USER`, `JENKINS_TOKEN`)
4. **Request headers** (non-stdio mode only: `Jenkins-Url`, `Jenkins-User`, `Jenkins-Token`)

## Running the Jenkins MCP Server

You can run the server with either `stdio` (for local/CLI use) or a network transport (e.g., SSE for remote clients).

### Environment Variables (stdio mode)
- `JENKINS_URL`: The Jenkins instance URL
- `JENKINS_USER`: The Jenkins username (for HTTP Basic auth)
- `JENKINS_TOKEN`: The Jenkins API token
- `MCP_TRANSPORT`: Set to `stdio` (default) or another transport (e.g., `sse`)

#### Using `~/.jenkins/config.json`

```json
{
  "jenkins_url": "https://jenkins.example.com",
  "jenkins_user": "your-username",
  "jenkins_token": "your-api-token"
}
```

#### Example MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "jenkins": {
      "command": "python",
      "args": ["jenkins_mcp_server.py"],
      "env": {
        "JENKINS_URL": "https://jenkins.example.com/",
        "JENKINS_USER": "your-username",
        "JENKINS_TOKEN": "REDACTED",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

#### Example MCP Client Configuration (container)

```json
{
  "mcpServers": {
    "jenkins-mcp": {
      "command": "podman",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e", "JENKINS_URL",
        "-e", "JENKINS_USER",
        "-e", "JENKINS_TOKEN",
        "-e", "MCP_TRANSPORT",
        "quay.io/redhat-ai-tools/jenkins-mcp:latest"
      ],
      "env": {
        "JENKINS_URL": "https://jenkins.example.com/",
        "JENKINS_USER": "your-username",
        "JENKINS_TOKEN": "REDACTED",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

Replace `REDACTED` with your Jenkins API token, which you can generate from your Jenkins user account settings.

### Header-based Authentication (non-stdio mode)
For non-stdio transports, credentials can be provided in each request's headers:
- `Jenkins-Url`: The Jenkins instance URL
- `Jenkins-User`: The Jenkins username
- `Jenkins-Token`: The Jenkins API token

This allows the server to route requests to different Jenkins instances per client/request.

#### Example MCP Client Configuration

```json
{
  "mcpServers": {
    "jenkins": {
      "url": "https://jenkins-mcp.example.com/sse",
      "headers": {
        "Jenkins-Url": "https://jenkins.example.com/",
        "Jenkins-User": "your-username",
        "Jenkins-Token": "REDACTED"
      }
    }
  }
}
```

## Available Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_all_jobs` | — | List all jobs at root level with name, URL, and status |
| `get_job` | `job_path` | Get details for a job by slash-separated path |
| `get_build` | `job_path`, `build_number?` | Get build info (specific number or last build) |
| `trigger_build` | `job_path`, `parameters?` | Trigger a build, optionally with parameters |
| `get_build_log` | `job_path`, `build_number?`, `start?`, `max_lines?` | Get console output (plain text, paginated, truncated) |
| `get_build_status` | `build_url` | Quick status check from a full build URL |
| `get_pipeline_stages` | `job_path`, `build_number?` | Get pipeline stage names, statuses, durations via Workflow API |

### Job Path Format

Jobs are referenced using slash-separated paths. The server handles conversion to the Jenkins API format automatically:

```
# Input                          -> Jenkins API path
"my-job"                         -> "job/my-job"
"folder/subfolder/my-job"        -> "job/folder/job/subfolder/job/my-job"
"job/already/job/formatted"      -> "job/already/job/formatted"  (unchanged)
```

## Usage

```python
# List all jobs
get_all_jobs()

# Get a specific job (nested folder support)
get_job("qe-acm-automation-poc/clc-e2e-pipeline")

# Get the last build
get_build("qe-acm-automation-poc/clc-e2e-pipeline")

# Trigger a build with parameters
trigger_build("my-folder/my-job", parameters={"BRANCH": "main", "ENV": "staging"})

# Get build log (last 500 lines)
get_build_log("qe-acm-automation-poc/clc-e2e-pipeline", build_number=3913)

# Quick status check from URL
get_build_status("https://jenkins.example.com/job/CI/job/main/42/")

# Pipeline stage details
get_pipeline_stages("qe-acm-automation-poc/clc-e2e-pipeline", build_number=3913)
```

## References
- [Official Jenkins MCP Server Plugin](https://plugins.jenkins.io/mcp-server/)
- [Jenkins API Token Documentation](https://www.jenkins.io/blog/2018/07/02/new-api-token-system/)

---

*This project is not affiliated with the official Jenkins MCP plugin, but aims for feature parity and interoperability.*
