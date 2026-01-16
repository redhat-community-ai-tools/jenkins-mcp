"""
Configuration for Dashboard Build Analyzer
"""
import os
from pathlib import Path

# Load .env file if it exists (look in project root)
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value


class Config:
    """Configuration settings"""

    # SSL Verification - set to "false" for internal CAs or self-signed certs
    # Default: True (secure)
    SSL_VERIFY = os.getenv("SSL_VERIFY", "true").lower() == "true"

    # Jenkins Configuration
    JENKINS_URL = os.getenv("JENKINS_URL")
    JENKINS_TOKEN = os.getenv("JENKINS_TOKEN", "")
    JENKINS_USERNAME = os.getenv("JENKINS_USER", "")
    JENKINS_PASSWORD = os.getenv("JENKINS_TOKEN", "")  # Token is used as password
    
    # Jenkins MCP Server (if available)
    JENKINS_MCP_URL = os.getenv("JENKINS_MCP_URL", "")  # e.g., https://jenkins.com/mcp/sse

    # Jira Configuration
    JIRA_URL = os.getenv("JIRA_URL", "https://issues.redhat.com")
    JIRA_TOKEN = os.getenv("JIRA_TOKEN", "")

    # GitLab Configuration
    GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab.cee.redhat.com")
    GITLAB_TOKEN = os.getenv("GITLAB_TOKEN", "")

    # Repository Paths
    FRONTEND_REPO_PATH = os.getenv("FRONTEND_REPO_PATH", "")  # GitHub
    JENKINS_REPO_PATH = os.getenv("JENKINS_REPO_PATH", "")    # GitLab

    # Job Configuration
    # The rhoai-test-flow job is the parent orchestrator that handles install/setup
    # and then triggers dashboard-tests as a downstream job for Cypress E2E tests
    RHOAI_TEST_FLOW_JOB_PATH = "devops/rhoai-test-flow"
    # dashboard-tests job runs the actual Cypress tests
    DASHBOARD_TESTS_JOB_PATH = "cypress/dashboard-tests"
    # Legacy alias for backward compatibility
    PARENT_JOB_PATH = DASHBOARD_TESTS_JOB_PATH
    # Nightly cron cluster names (used to identify nightly builds)
    RHOAI_NIGHTLY_CLUSTER = "dash-e2e-rhoai"
    ODH_NIGHTLY_CLUSTER = "dash-e2e-odh"
    RHOAI_JOB_NAME = "dash-e2e-rhoai"
    ODH_JOB_NAME = "dash-e2e-odh"

    # Cluster Configuration
    RHOAI_API_SERVER = os.getenv("RHOAI_API_SERVER", "")
    RHOAI_USERNAME = os.getenv("RHOAI_USERNAME", "")
    RHOAI_PASSWORD = os.getenv("RHOAI_PASSWORD", "")

    ODH_API_SERVER = os.getenv("ODH_API_SERVER", "")
    ODH_USERNAME = os.getenv("ODH_USERNAME", "")
    ODH_PASSWORD = os.getenv("ODH_PASSWORD", "")

    # Default namespaces to check
    DEFAULT_NAMESPACES = [
        "opendatahub",
        "redhat-ods-applications",
        "redhat-ods-monitoring",
        "rhods-notebooks"
    ]

    # Scheduler Configuration
    SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "09:30")  # GMT
    SCHEDULE_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday"]

    # Report Configuration
    REPORT_OUTPUT_DIR = os.getenv("REPORT_OUTPUT_DIR", "./reports")

    # Test variables paths
    RHOAI_TEST_VARIABLES = os.getenv("RHOAI_TEST_VARIABLES", "")
    ODH_TEST_VARIABLES = os.getenv("ODH_TEST_VARIABLES", "")

    # Tracer tool path (for image analysis)
    TRACER_PATH = os.getenv("TRACER_PATH", "/path/to/tracer/tracer.sh")

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_vars = {
            "JENKINS_URL": cls.JENKINS_URL,
            "JENKINS_TOKEN": cls.JENKINS_TOKEN,
            "FRONTEND_REPO_PATH": cls.FRONTEND_REPO_PATH,
        }
        
        missing = [name for name, value in required_vars.items() if not value]
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please create a .env file based on .env.example"
            )
