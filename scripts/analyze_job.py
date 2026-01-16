#!/usr/bin/env python3
"""
Generic Jenkins Job Analyzer

Analyzes ANY Jenkins job - not just hardcoded RHOAI/ODH builds.
User specifies job path and build number, tool does the rest.

Usage:
    python analyze_job.py --job "cypress/dashboard-tests" --build 3597
    python analyze_job.py --job "your/custom/job" --build latest
    python analyze_job.py --job "your/job" --build latest --cluster-optional
"""
import asyncio
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer import (
    jenkins_client,
    artifact_parser,
    failure_analyzer,
    jira_client,
    cluster_inspector,
    report_generator
)
from analyzer.config import Config


class GenericJobAnalyzer:
    """Analyze any Jenkins job, with optional cluster inspection"""
    
    def __init__(self):
        Config.validate()
        
        self.jenkins = jenkins_client.JenkinsClient(
            Config.JENKINS_URL,
            Config.JENKINS_TOKEN,
            Config.JENKINS_USERNAME,
            Config.JENKINS_PASSWORD
        )
        
        self.parser = artifact_parser.ArtifactParser()
        self.jira = jira_client.JiraClient() if Config.JIRA_TOKEN else None
        self.analyzer = failure_analyzer.FailureAnalyzer(
            jira_client=self.jira,
            enable_test_rerun=True,  # Enable test reruns for proper analysis
            frontend_repo_path=Config.FRONTEND_REPO_PATH
        )
        
        self.report_dir = Path(Config.REPORT_OUTPUT_DIR)
        self.report_dir.mkdir(parents=True, exist_ok=True)
    
    async def analyze_job(
        self,
        job_path: str,
        build_number: int = None,
        cluster_config: dict = None,
        namespace: str = None
    ):
        """
        Analyze any Jenkins job
        
        Args:
            job_path: Jenkins job path (e.g., "cypress/dashboard-tests")
            build_number: Build number or None for latest
            cluster_config: Optional cluster config dict with keys:
                           {name, api_server, username, password, namespace}
            namespace: Optional namespace to inspect
        """
        print(f"\n{'='*60}")
        print(f"Analyzing Jenkins Job: {job_path}")
        print(f"{'='*60}\n")
        
        # Get build info
        try:
            if build_number is None:
                print("Fetching latest build...")
                build_data = await self.jenkins.get_build(job_path)
                build_number = build_data['number']
            else:
                print(f"Fetching build #{build_number}...")
                build_data = await self.jenkins.get_build(job_path, build_number)
            
            build_url = build_data['url']
            build_result = build_data.get('result', 'UNKNOWN')
            
            print(f"Build #{build_number}: {build_url}")
            print(f"Status: {build_result}")
            
            build_time = datetime.fromtimestamp(build_data['timestamp'] / 1000)
            hours_ago = (datetime.now() - build_time).total_seconds() / 3600
            print(f"Build time: {build_time} ({hours_ago:.1f} hours ago)")
            
        except Exception as e:
            print(f"❌ Error fetching build: {e}")
            return None
        
        # Get console log
        print("\nFetching console output...")
        try:
            console_log = await self.jenkins.get_console_output(job_path, build_number)
        except Exception as e:
            print(f"⚠️  Could not fetch console: {e}")
            console_log = ""
        
        # Parse test results
        print("Parsing test results...")
        parsed_results = self.parser.parse_build_log(console_log)
        
        # Try to get artifacts
        print("Checking for artifacts...")
        try:
            artifacts = await self.jenkins.list_artifacts(job_path, build_number)
            print(f"  Found {len(artifacts)} artifact(s)")
            
            # Look for test result XML
            for artifact in artifacts:
                rel_path = artifact.get('relativePath', '')
                if 'results.xml' in rel_path or 'test-output' in rel_path:
                    print(f"  Found test results: {rel_path}")
                    try:
                        xml_content = await self.jenkins.get_artifact_content(
                            job_path, build_number, rel_path
                        )
                        xml_results = self.parser.parse_junit_xml(xml_content)
                        if xml_results.get('total_tests', 0) > parsed_results.get('total_tests', 0):
                            parsed_results = xml_results
                            print(f"  ✓ Parsed {xml_results['total_tests']} tests from XML")
                    except Exception as e:
                        print(f"  ⚠️  Could not parse XML: {e}")
        except Exception as e:
            print(f"  ⚠️  Could not fetch artifacts: {e}")
        
        # Build TestResult object
        test_result = self.parser.build_test_result(
            job_name=job_path.split('/')[-1],
            build_number=build_number,
            build_url=build_url,
            build_data=build_data,
            parsed_results=parsed_results
        )
        
        print(f"\nTest Results:")
        print(f"  Total: {test_result.total_tests}")
        print(f"  Passed: {test_result.passed_tests}")
        print(f"  Failed: {test_result.failed_tests}")
        print(f"  Skipped: {test_result.skipped_tests}")
        
        # Optional cluster inspection
        cluster_analysis = None
        if cluster_config and test_result.failed_tests > 0:
            print(f"\n{'='*60}")
            print(f"Cluster Inspection (Optional)")
            print(f"{'='*60}\n")
            
            try:
                config = cluster_inspector.ClusterConfig(
                    name=cluster_config['name'],
                    api_server=cluster_config['api_server'],
                    username=cluster_config['username'],
                    password=cluster_config['password']
                )
                
                inspector = cluster_inspector.ClusterInspector(config)
                
                if await inspector.login():
                    print(f"✓ Connected to {cluster_config['name']} cluster")
                    
                    ns = namespace or cluster_config.get('namespace', 'default')
                    cluster_analysis = await inspector.analyze_test_environment(ns)
                    
                    print(f"\nCluster Health:")
                    print(f"  Namespace: {ns}")
                    print(f"  Total Pods: {cluster_analysis['pod_health']['total']}")
                    print(f"  Running: {cluster_analysis['pod_health']['running']}")
                    print(f"  Failed: {cluster_analysis['pod_health']['failed']}")
                    
                    await inspector.logout()
                else:
                    print(f"⚠️  Could not connect to cluster")
            
            except Exception as e:
                print(f"⚠️  Cluster inspection failed: {e}")
        
        # Analyze failures
        if test_result.failed_tests > 0:
            print(f"\n{'='*60}")
            print(f"Failure Analysis")
            print(f"{'='*60}\n")
            
            analysis = await self.analyzer.analyze_test_result(
                test_result,
                cluster_analysis,
                cluster_name=cluster_config['name'] if cluster_config else 'unknown'
            )
            
            print(f"Analyzed {analysis['total_failures']} failure(s)")
            print(f"Categories: {analysis['categories']}")
            
            # Generate report
            report_content = self._generate_report(
                job_path,
                build_number,
                build_url,
                test_result,
                analysis,
                cluster_analysis
            )
            
            # Save report
            job_name = job_path.replace('/', '-')
            report_filename = f"analysis-{job_name}-{build_number}.md"
            report_path = self.report_dir / report_filename
            
            with open(report_path, 'w') as f:
                f.write(report_content)
            
            print(f"\n✅ Report saved: {report_path}")
            
            return analysis
        else:
            print(f"\n✅ All tests passed!")
            return None
    
    def _generate_report(self, job_path, build_number, build_url, test_result, analysis, cluster_analysis):
        """Generate markdown report"""
        lines = []
        
        lines.append(f"# Jenkins Job Analysis: {job_path}")
        lines.append(f"\n**Build:** [{build_number}]({build_url})")
        lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"\n## Test Results")
        lines.append(f"\n- Total: {test_result.total_tests}")
        lines.append(f"- Passed: {test_result.passed_tests}")
        lines.append(f"- Failed: {test_result.failed_tests}")
        lines.append(f"- Skipped: {test_result.skipped_tests}")
        
        if test_result.failed_tests > 0:
            lines.append(f"\n## Failed Tests")
            
            for i, fa in enumerate(analysis['failure_analyses'], 1):
                lines.append(f"\n### {i}. {fa.failure.test_name}")
                lines.append(f"\n**File:** `{fa.failure.test_file}`")
                lines.append(f"\n**Category:** {fa.category}")
                lines.append(f"\n**Error:**")
                lines.append("```")
                lines.append(fa.failure.error_message[:500])
                lines.append("```")
                
                # Add rerun results
                if hasattr(fa, 'rerun_result') and fa.rerun_result and fa.rerun_result.get('attempted'):
                    rerun = fa.rerun_result
                    if rerun.get('success'):
                        lines.append(f"\n**✓ Rerun Result:** PASSED on rerun (took {rerun.get('duration', 0):.1f}s)")
                        lines.append(f"\n> **Note:** This appears to be an intermittent/flaky test since it passed when rerun")
                    else:
                        lines.append(f"\n**✗ Rerun Result:** FAILED on rerun (exit code: {rerun.get('exit_code', 'N/A')})")
                        lines.append(f"\n> **Note:** Test consistently fails - not intermittent")
                
                if fa.jira_issues:
                    lines.append(f"\n**Related Jira Issues:**")
                    for issue in fa.jira_issues[:3]:
                        lines.append(f"- [{issue['key']}]({issue['url']}) - {issue['status']}")
        
        if cluster_analysis:
            lines.append(f"\n## Cluster Health")
            lines.append(f"\n- Total Pods: {cluster_analysis['pod_health']['total']}")
            lines.append(f"- Running: {cluster_analysis['pod_health']['running']}")
            lines.append(f"- Failed: {cluster_analysis['pod_health']['failed']}")
        
        return "\n".join(lines)


async def main():
    parser = argparse.ArgumentParser(description="Analyze any Jenkins job")
    parser.add_argument('--job', required=True, help='Jenkins job path (e.g., cypress/dashboard-tests)')
    parser.add_argument('--build', default='latest', help='Build number or "latest"')
    parser.add_argument('--cluster-name', help='Cluster name (optional)')
    parser.add_argument('--cluster-api', help='Cluster API server (optional)')
    parser.add_argument('--cluster-user', help='Cluster username (optional)')
    parser.add_argument('--cluster-pass', help='Cluster password (optional)')
    parser.add_argument('--namespace', help='Namespace to inspect (optional)')
    
    args = parser.parse_args()
    
    # Parse and validate build number
    if args.build.lower() == 'latest':
        build_number = None
    else:
        if not args.build.isdigit():
            print(f"❌ Error: Invalid build number '{args.build}'")
            print("   Build number must be a positive integer or 'latest'")
            return
        build_number = int(args.build)
        if build_number <= 0:
            print(f"❌ Error: Build number must be a positive integer, got {build_number}")
            return
    
    # Optional cluster config
    cluster_config = None
    if args.cluster_api:
        cluster_config = {
            'name': args.cluster_name or 'custom',
            'api_server': args.cluster_api,
            'username': args.cluster_user,
            'password': args.cluster_pass,
            'namespace': args.namespace
        }
    
    # Run analysis
    analyzer = GenericJobAnalyzer()
    await analyzer.analyze_job(
        job_path=args.job,
        build_number=build_number,
        cluster_config=cluster_config,
        namespace=args.namespace
    )


if __name__ == "__main__":
    asyncio.run(main())


