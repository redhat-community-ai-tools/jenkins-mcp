import os
from typing import Any, Optional
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("jenkins")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")


def get_jenkins_context() -> tuple[str, str]:
    ctx = mcp.get_context().request_context.request
    jenkins_url = (
        os.environ["JENKINS_URL"]
        if MCP_TRANSPORT == "stdio"
        else ctx.headers["Jenkins-Url"]
    )
    jenkins_token = (
        os.environ["JENKINS_TOKEN"]
        if MCP_TRANSPORT == "stdio"
        else ctx.headers["Jenkins-Token"]
    )
    if not jenkins_url or not jenkins_token:
        raise Exception("Missing Jenkins URL or Token in headers")
    return jenkins_url, jenkins_token


async def jenkins_api_call(
    api_path: str, method: str = "GET", data: dict[str, Any] = None
) -> dict[str, Any] | None:
    async with httpx.AsyncClient(verify=False) as client:
        jenkins_url, jenkins_token = get_jenkins_context()
        url = f"{jenkins_url.rstrip('/')}/{api_path.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {jenkins_token}",
            "Accept": "application/json",
        }
        if method.upper() == "GET":
            response = await client.request(method, url, headers=headers, params=data)
        else:
            response = await client.request(method, url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def getAllJobs() -> Any:
    """Get a list of all Jenkins jobs."""
    return await jenkins_api_call("api/json")


@mcp.tool()
async def getJob(full_path: str) -> Any:
    """Get a Jenkins job by its full path."""
    return await jenkins_api_call(f"job/{full_path}/api/json")


@mcp.tool()
async def getBuild(full_path: str, build_number: Optional[int] = None) -> Any:
    """Retrieve a specific build or the last build of a Jenkins job."""
    if build_number is not None:
        endpoint = f"job/{full_path}/{build_number}/api/json"
    else:
        endpoint = f"job/{full_path}/lastBuild/api/json"
    return await jenkins_api_call(endpoint)


@mcp.tool()
async def triggerBuild(full_path: str) -> str:
    """Trigger a build of a job."""
    await jenkins_api_call(f"job/{full_path}/build", method="POST")
    return f"Build triggered for job: {full_path}"


@mcp.tool()
async def getBuildLog(
    full_path: str, build_number: Optional[int] = None, start: int = 0
) -> Any:
    """Retrieve log lines for a specific build or the last build of a Jenkins job. Supports pagination via 'start'."""
    if build_number is not None:
        endpoint = f"job/{full_path}/{build_number}/logText/progressiveText"
    else:
        endpoint = f"job/{full_path}/lastBuild/logText/progressiveText"
    params = {"start": start}
    return await jenkins_api_call(endpoint, params=params)


if __name__ == "__main__":
    mcp.run(transport=os.environ.get("MCP_TRANSPORT", "stdio"))
