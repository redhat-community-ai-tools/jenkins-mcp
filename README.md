# jenkins-mcp

MCP Server for multiple Jenkins instances

## Overview

This MCP (Model Context Protocol) server allows you to interact with multiple Jenkins instances from a single server. Unlike traditional setups, this server extracts the Jenkins URL and API token from each request's headers, enabling true multi-tenancy.

- **Multi-tenancy**: Serve multiple Jenkins instances from a single MCP server.
- **Header-based authentication**: Jenkins URL and token are provided per request via headers.
- **Parity with official Jenkins MCP plugin**: Implements the same core tools as the [official Jenkins MCP Server Plugin](https://plugins.jenkins.io/mcp-server/).

## Running the Jenkins MCP Server

You can run the server with either `stdio` (for local/CLI use) or a network transport (e.g., SSE for remote clients).

### Environment Variables (stdio mode)
- `JENKINS_URL`: The Jenkins instance URL (used only in stdio mode)
- `JENKINS_TOKEN`: The Jenkins API token (used only in stdio mode)
- `MCP_TRANSPORT`: Set to `stdio` (default) or another transport (e.g., `sse`)

#### Example MCP Client Configuration

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
        "-e", "JENKINS_TOKEN",
        "-e", "MCP_TRANSPORT",
        "quay.io/redhat-ai-tools/jenkins-mcp:latest"
      ],
      "env": {
        "JENKINS_URL": "https://jenkins.example.com/",
        "JENKINS_TOKEN": "REDACTED",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

Replace `REDACTED` with your Jenkins API token, which you can generate from your Jenkins user account settings.

### Header-based Authentication (non-stdio mode)
For non-stdio transports, the Jenkins URL and token must be provided in each request's headers:
- `Jenkins-Url`: The Jenkins instance URL
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
        "Jenkins-Token": "REDACTED"
      }
    }
  }
}
```

## Available Tools

The following tools are implemented, matching the official Jenkins MCP plugin:

- `getAllJobs`: Get a list of all Jenkins jobs.
- `getJob(full_path)`: Get a Jenkins job by its full path.
- `getBuild(full_path, build_number=None)`: Retrieve a specific build or the last build of a Jenkins job.
- `triggerBuild(full_path)`: Trigger a build of a job.
- `getBuildLog(full_path, build_number=None, start=0)`: Retrieve log lines for a specific build or the last build of a Jenkins job (supports pagination).

## Usage

- For each request, provide the Jenkins URL and token in the headers (unless using stdio mode, where they are read from environment variables).
- The server will use these credentials to interact with the specified Jenkins instance.

## References
- [Official Jenkins MCP Server Plugin](https://plugins.jenkins.io/mcp-server/)
- [Jenkins API Token Documentation](https://www.jenkins.io/blog/2018/07/02/new-api-token-system/)

---

*This project is not affiliated with the official Jenkins MCP plugin, but aims for feature parity and interoperability.*
