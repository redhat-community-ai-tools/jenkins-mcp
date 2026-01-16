#!/usr/bin/env python3
"""
Nightly E2E Test Analyzer

This tool analyzes nightly Cypress E2E test results from Jenkins,
inspects cluster health, and generates comprehensive reports.

It runs on a schedule (Mon-Fri at 9:30 AM GMT) to analyze the previous night's test runs.
"""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
import schedule
import time
import httpx
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.config import Config
from analyzer.jenkins_client import JenkinsClient
from analyzer.artifact_parser import ArtifactParser, TestResult
from analyzer.cluster_inspector import ClusterInspector, ClusterConfig
from analyzer.failure_analyzer import FailureAnalyzer
from analyzer.report_generator import ReportGenerator
from analyzer.jira_client import JiraClient


class NightlyAnalyzer:
    """Main analyzer orchestrator"""

    def __init__(self):
        Config.validate()

        self.jenkins_client = JenkinsClient(
            Config.JENKINS_URL,
            Config.JENKINS_TOKEN,
            Config.JENKINS_USERNAME,
            Config.JENKINS_PASSWORD
        )
        self.parser = ArtifactParser()
        self.jira_client = JiraClient()
        self.analyzer = FailureAnalyzer(jira_client=self.jira_client)
        self.reporter = ReportGenerator()

        # Setup output directory
        self.report_dir = Path(Config.REPORT_OUTPUT_DIR)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    async def find_overnight_builds(self):
        """Find builds from last night (between midnight and 6 AM)"""
        job_path = Config.PARENT_JOB_PATH
        
        print(f"Searching for overnight builds in {job_path}...")
        
        # Get recent builds
        async with httpx.AsyncClient(verify=Config.SSL_VERIFY, timeout=120.0) as client:
            url = f"{self.jenkins_client.jenkins_url}/job/cypress/job/dashboard-tests/api/json?tree=builds[number,timestamp,result,description,displayName]{{0,20}}"
            if ':' in self.jenkins_client.jenkins_token:
                username, token = self.jenkins_client.jenkins_token.split(':', 1)
                auth = (username, token)
                response = await client.get(url, auth=auth)
            else:
                headers = {"Authorization": f"Bearer {self.jenkins_client.jenkins_token}"}
                response = await client.get(url, headers=headers)
            
            response.raise_for_status()
            data = response.json()
            
            # Filter builds from last night (last 24 hours, between 00:00-06:00)
            overnight_builds = {'rhoai': None, 'odh': None}
            
            for build in data.get('builds', []):
                build_time = datetime.fromtimestamp(build['timestamp'] / 1000)
                hours_ago = (datetime.now() - build_time).total_seconds() / 3600
                
                # Check if it's from last 24 hours and overnight (00:00-06:00)
                if hours_ago <= 24 and 0 <= build_time.hour <= 6:
                    description = build.get('description', '').lower()
                    
                    if 'dash-e2e-rhoai' in description and not overnight_builds['rhoai']:
                        overnight_builds['rhoai'] = build
                        print(f"  Found RHOAI build: #{build['number']} at {build_time}")
                    elif 'dash-e2e-odh' in description and not overnight_builds['odh']:
                        overnight_builds['odh'] = build
                        print(f"  Found ODH build: #{build['number']} at {build_time}")
                    
                    # Stop if we found both
                    if overnight_builds['rhoai'] and overnight_builds['odh']:
                        break
            
            return overnight_builds

    async def analyze_job_build(
        self,
        job_name: str,
        cluster_config: ClusterConfig,
        namespace: str = "opendatahub",
        build_number: int = None
    ):
        """
        Analyze a single job build

        Args:
            job_name: Name of the target ("dash-e2e-rhoai" or "dash-e2e-odh")
            cluster_config: Cluster configuration
            namespace: Namespace to inspect for cluster health
            build_number: Specific build number to analyze
        """
        print(f"\n{'='*60}")
        print(f"Analyzing {job_name}")
        print(f"{'='*60}\n")

        # Use the parent job path (not nested)
        full_job_path = Config.PARENT_JOB_PATH

        try:
            latest_build = await self.jenkins_client.get_build(full_job_path, build_number)
            build_number = latest_build['number']
            build_url = latest_build['url']

            print(f"Build #{build_number}: {build_url}")
            print(f"Status: {latest_build.get('result', 'UNKNOWN')}")

            # Check if it's a recent nightly build
            build_time = datetime.fromtimestamp(latest_build['timestamp'] / 1000)
            hours_ago = (datetime.now() - build_time).total_seconds() / 3600

            print(f"Build time: {build_time} ({hours_ago:.1f} hours ago)")

            if hours_ago > 24:
                print("  Warning: Build is more than 24 hours old")

            # Get build log
            print("\nFetching build log...")
            build_log = await self.jenkins_client.get_build_log(full_job_path, build_number)

            # Parse log for test results
            print("Parsing test results...")
            parsed_results = self.parser.parse_build_log(build_log)

            # Try to fetch JSON artifacts if available
            print("Fetching build artifacts...")
            artifacts = await self.jenkins_client.list_artifacts(full_job_path, build_number)

            for artifact in artifacts:
                artifact_path = artifact['relativePath']
                if artifact_path.endswith('.json') and 'results' in artifact_path.lower():
                    print(f"  Found JSON results: {artifact_path}")
                    try:
                        json_content = await self.jenkins_client.get_artifact_content(
                            full_job_path, build_number, artifact_path
                        )
                        json_results = self.parser.parse_cypress_json_results(json_content)
                        # Merge with log results
                        if json_results.get('total_tests', 0) > parsed_results.get('total_tests', 0):
                            parsed_results = json_results
                    except Exception as e:
                        print(f"  Error parsing JSON artifact: {e}")

            # Build TestResult object
            test_result = self.parser.build_test_result(
                job_name=job_name,
                build_number=build_number,
                build_url=build_url,
                build_data=latest_build,
                parsed_results=parsed_results
            )

            print(f"\nTest Results:")
            print(f"  Total: {test_result.total_tests}")
            print(f"  Passed: {test_result.passed_tests}")
            print(f"  Failed: {test_result.failed_tests}")
            print(f"  Skipped: {test_result.skipped_tests}")

            # Analyze cluster health
            cluster_analysis = None
            if test_result.failed_tests > 0:
                print(f"\nInspecting {cluster_config.name} cluster health...")
                inspector = ClusterInspector(cluster_config)

                try:
                    login_success = await inspector.login()

                    if login_success:
                        print(f"Logged into {cluster_config.name} cluster")

                        # Analyze test environment
                        cluster_analysis = await inspector.analyze_test_environment(namespace)

                        print(f"\nCluster Health Summary:")
                        print(f"  Namespace: {namespace}")
                        print(f"  Total Pods: {cluster_analysis['pod_health']['total']}")
                        print(f"  Running: {cluster_analysis['pod_health']['running']}")
                        print(f"  Failed: {cluster_analysis['pod_health']['failed']}")
                        print(f"  Crash Looping: {cluster_analysis['pod_health']['crash_looping']}")

                        if cluster_analysis['has_issues']:
                            print("  Cluster issues detected!")
                            for problem in cluster_analysis['pod_health']['problems'][:5]:
                                print(f"    - {problem['pod']}: {problem['issue']}")

                        await inspector.logout()
                    else:
                        print(f"Failed to login to {cluster_config.name} cluster")

                except Exception as e:
                    print(f"Error inspecting cluster: {e}")

            # Analyze failures
            print("\nAnalyzing failures...")
            analysis = await self.analyzer.analyze_test_result(test_result, cluster_analysis)

            # Print summary
            if analysis['total_failures'] > 0:
                print(f"\nFailure Breakdown:")
                for category, count in analysis['categories'].items():
                    print(f"  {category}: {count}")

            return analysis

        except Exception as e:
            print(f"Error analyzing {job_name}: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def run_daily_analysis(self):
        """Run the daily analysis for both clusters"""
        print("\n" + "="*60)
        print("NIGHTLY E2E TEST ANALYSIS")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S GMT')}")
        print("="*60)

        # Find overnight builds
        try:
            overnight_builds = await self.find_overnight_builds()
        except Exception as e:
            print(f"Error finding overnight builds: {e}")
            print("\n" + "="*60)
            print("ANALYSIS COMPLETE")
            print("="*60 + "\n")
            return

        # Analyze RHOAI
        rhoai_analysis = None
        if overnight_builds['rhoai']:
            rhoai_config = ClusterConfig(
                name="RHOAI",
                api_server=Config.RHOAI_API_SERVER,
                username=Config.RHOAI_USERNAME,
                password=Config.RHOAI_PASSWORD
            )

            rhoai_analysis = await self.analyze_job_build(
                Config.RHOAI_JOB_NAME,
                rhoai_config,
                namespace="redhat-ods-applications",
                build_number=overnight_builds['rhoai']['number']
            )
        else:
            print("\n⚠ No RHOAI build found from last night")

        # Analyze ODH
        odh_analysis = None
        if overnight_builds['odh']:
            odh_config = ClusterConfig(
                name="ODH",
                api_server=Config.ODH_API_SERVER,
                username=Config.ODH_USERNAME,
                password=Config.ODH_PASSWORD
            )

            odh_analysis = await self.analyze_job_build(
                Config.ODH_JOB_NAME,
                odh_config,
                namespace="opendatahub",
                build_number=overnight_builds['odh']['number']
            )
        else:
            print("\n⚠ No ODH build found from last night")

        # Generate report
        if rhoai_analysis and odh_analysis:
            print("\n" + "="*60)
            print("GENERATING REPORT")
            print("="*60 + "\n")

            # Console report
            self.reporter.print_console_report(
                rhoai_analysis,
                odh_analysis,
                datetime.now()
            )

            # Markdown report
            report_content = self.reporter.generate_daily_report(
                rhoai_analysis,
                odh_analysis,
                datetime.now()
            )

            # Save report
            report_filename = f"nightly-report-{datetime.now().strftime('%Y-%m-%d')}.md"
            report_path = self.report_dir / report_filename
            self.reporter.save_report(report_content, str(report_path))

            print(f"\nReport saved to: {report_path}")

            # Also save as latest.md
            latest_path = self.report_dir / "latest.md"
            self.reporter.save_report(report_content, str(latest_path))

            print(f"Latest report updated: {latest_path}")

        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60 + "\n")


def run_analysis_sync():
    """Synchronous wrapper for scheduled execution"""
    analyzer = NightlyAnalyzer()
    asyncio.run(analyzer.run_daily_analysis())


def run_scheduler():
    """Run the scheduler"""
    print("Starting Nightly E2E Test Analyzer Scheduler")
    print(f"Schedule: Mon-Fri at {Config.SCHEDULE_TIME} GMT")
    print("Press Ctrl+C to stop\n")

    # Schedule for each weekday
    schedule.every().monday.at(Config.SCHEDULE_TIME).do(run_analysis_sync)
    schedule.every().tuesday.at(Config.SCHEDULE_TIME).do(run_analysis_sync)
    schedule.every().wednesday.at(Config.SCHEDULE_TIME).do(run_analysis_sync)
    schedule.every().thursday.at(Config.SCHEDULE_TIME).do(run_analysis_sync)
    schedule.every().friday.at(Config.SCHEDULE_TIME).do(run_analysis_sync)

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Nightly E2E Test Analyzer")
    parser.add_argument(
        "--mode",
        choices=["run-now", "schedule"],
        default="run-now",
        help="Run mode: 'run-now' for immediate analysis, 'schedule' for scheduled execution"
    )

    args = parser.parse_args()

    if args.mode == "run-now":
        # Run analysis immediately
        analyzer = NightlyAnalyzer()
        asyncio.run(analyzer.run_daily_analysis())
    else:
        # Run on schedule
        run_scheduler()


if __name__ == "__main__":
    main()
