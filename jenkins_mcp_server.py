import json
import os
import re
import urllib3
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

mcp = FastMCP("jenkins")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
JENKINS_CONFIG_PATH = Path.home() / ".jenkins" / "config.json"


def _load_file_config() -> dict:
    """Load credentials from ~/.jenkins/config.json if it exists."""
    if JENKINS_CONFIG_PATH.exists():
        with open(JENKINS_CONFIG_PATH) as f:
            return json.load(f)
    return {}


_file_cfg = _load_file_config()


def get_jenkins_context() -> tuple[str, str, str]:
    """Get Jenkins URL, username, and token for the current request.

    In stdio mode, reads from ~/.jenkins/config.json, .env file, or env vars.
    In network mode, reads from request headers with env/file fallback.
    """
    if MCP_TRANSPORT == "stdio":
        jenkins_url = _file_cfg.get("jenkins_url", "") or os.environ.get("JENKINS_URL", "")
        jenkins_user = _file_cfg.get("jenkins_user", "") or os.environ.get("JENKINS_USER", "")
        jenkins_token = _file_cfg.get("jenkins_token", "") or os.environ.get("JENKINS_TOKEN", "")
    else:
        ctx = mcp.get_context().request_context.request
        jenkins_url = ctx.headers.get("Jenkins-Url", "") or _file_cfg.get("jenkins_url", "") or os.environ.get("JENKINS_URL", "")
        jenkins_user = ctx.headers.get("Jenkins-User", "") or _file_cfg.get("jenkins_user", "") or os.environ.get("JENKINS_USER", "")
        jenkins_token = ctx.headers.get("Jenkins-Token", "") or _file_cfg.get("jenkins_token", "") or os.environ.get("JENKINS_TOKEN", "")

    if not jenkins_url or not jenkins_token:
        raise Exception("Missing Jenkins URL or Token")
    return jenkins_url.rstrip("/"), jenkins_user, jenkins_token


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def normalize_job_path(job_path: str) -> str:
    """Convert slash-separated path to Jenkins API format.

    'folder/sub/job' -> 'job/folder/job/sub/job/job'
    Paths already containing 'job/' segments are returned as-is.
    """
    if not job_path:
        return job_path
    job_path = job_path.strip("/")
    if job_path.startswith("job/"):
        return job_path
    parts = job_path.split("/")
    return "/".join(f"job/{p}" for p in parts)


def parse_jenkins_url(url: str) -> tuple[str, str, Optional[int]]:
    """Parse a full Jenkins build URL into (base_url, job_api_path, build_number).

    Example:
        https://jenkins.example.com/job/CI/job/main/42/
        -> ("https://jenkins.example.com", "job/CI/job/main", 42)
    """
    parsed = urlparse(url.rstrip("/"))
    path = parsed.path.rstrip("/")

    build_number: Optional[int] = None
    segments = path.split("/")
    if segments and segments[-1].isdigit():
        build_number = int(segments[-1])
        segments = segments[:-1]

    path_str = "/".join(segments)
    match = re.search(r"(/?job/.+)$", path_str)
    job_api_path = match.group(1).lstrip("/") if match else ""

    base_url = f"{parsed.scheme}://{parsed.netloc}"
    return base_url, job_api_path, build_number


async def jenkins_api(
    api_path: str,
    method: str = "GET",
    data: dict[str, Any] | None = None,
    expect_json: bool = True,
) -> dict[str, Any] | str | None:
    """Authenticated Jenkins API call.

    Uses HTTP Basic auth when jenkins_user is available (standard Jenkins API
    token flow), otherwise falls back to Bearer token.
    """
    jenkins_url, jenkins_user, jenkins_token = get_jenkins_context()

    auth = None
    extra_headers: dict[str, str] = {}
    if jenkins_user:
        auth = httpx.BasicAuth(jenkins_user, jenkins_token)
    else:
        extra_headers["Authorization"] = f"Bearer {jenkins_token}"
    if expect_json:
        extra_headers["Accept"] = "application/json"

    async with httpx.AsyncClient(verify=False, auth=auth, timeout=60.0) as client:
        url = f"{jenkins_url}/{api_path.lstrip('/')}"
        if method.upper() == "GET":
            resp = await client.request(method, url, headers=extra_headers, params=data)
        else:
            resp = await client.request(method, url, headers=extra_headers, data=data)
        resp.raise_for_status()
        return resp.json() if expect_json else resp.text


# ------------------------------------------------------------------
# Tools
# ------------------------------------------------------------------


@mcp.tool()
async def get_all_jobs() -> Any:
    """List all Jenkins jobs at the root level with name, URL, and status color."""
    return await jenkins_api("api/json?tree=jobs[name,url,color]")


@mcp.tool()
async def get_job(job_path: str) -> Any:
    """Get details for a Jenkins job.

    Args:
        job_path: Slash-separated path (e.g. 'folder/subfolder/my-job').
    """
    return await jenkins_api(f"{normalize_job_path(job_path)}/api/json")


@mcp.tool()
async def get_build(job_path: str, build_number: Optional[int] = None) -> Any:
    """Get build information for a Jenkins job.

    Args:
        job_path: Slash-separated path.
        build_number: Build number, or omit for last build.
    """
    base = normalize_job_path(job_path)
    suffix = f"/{build_number}" if build_number is not None else "/lastBuild"
    return await jenkins_api(f"{base}{suffix}/api/json")


@mcp.tool()
async def trigger_build(
    job_path: str,
    parameters: Optional[dict[str, str]] = None,
) -> str:
    """Trigger a Jenkins build, optionally with parameters.

    Args:
        job_path: Slash-separated path.
        parameters: Build parameters as key-value pairs.
    """
    base = normalize_job_path(job_path)
    if parameters:
        await jenkins_api(f"{base}/buildWithParameters", method="POST", data=parameters, expect_json=False)
    else:
        await jenkins_api(f"{base}/build", method="POST", expect_json=False)
    return f"Build triggered: {job_path}"


@mcp.tool()
async def get_build_log(
    job_path: str,
    build_number: Optional[int] = None,
    start: int = 0,
    max_lines: int = 500,
) -> str:
    """Get console output for a build as plain text.

    Args:
        job_path: Slash-separated path.
        build_number: Build number, or omit for last build.
        start: Byte offset for pagination.
        max_lines: Max lines to return (default 500, 0 for unlimited).
    """
    base = normalize_job_path(job_path)
    suffix = f"/{build_number}" if build_number is not None else "/lastBuild"
    text = await jenkins_api(
        f"{base}{suffix}/consoleText", data={"start": start}, expect_json=False,
    )
    if not isinstance(text, str):
        return str(text)
    if max_lines > 0:
        lines = text.split("\n")
        if len(lines) > max_lines:
            return (
                "\n".join(lines[-max_lines:])
                + f"\n\n[Truncated: showing last {max_lines} of {len(lines)} lines]"
            )
    return text


@mcp.tool()
async def get_build_status(build_url: str) -> Any:
    """Quick status check from a full Jenkins build URL.

    Args:
        build_url: Full Jenkins build URL (e.g. https://jenkins.example.com/job/CI/job/main/42/).
    """
    _, job_api_path, build_number = parse_jenkins_url(build_url)
    suffix = f"/{build_number}" if build_number else "/lastBuild"
    return await jenkins_api(
        f"{job_api_path}{suffix}/api/json"
        "?tree=result,building,duration,estimatedDuration,displayName,timestamp",
    )


@mcp.tool()
async def get_pipeline_stages(
    job_path: str,
    build_number: Optional[int] = None,
) -> Any:
    """Get pipeline stage names, statuses, and durations via the Workflow API.

    Args:
        job_path: Slash-separated path.
        build_number: Build number, or omit for last build.
    """
    base = normalize_job_path(job_path)
    suffix = f"/{build_number}" if build_number is not None else "/lastBuild"
    return await jenkins_api(f"{base}{suffix}/wfapi/describe")


if __name__ == "__main__":
    mcp.run(transport=os.environ.get("MCP_TRANSPORT", "stdio"))
