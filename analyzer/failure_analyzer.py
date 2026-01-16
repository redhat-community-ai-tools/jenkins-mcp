"""
Failure Analyzer - Analyze test failures and correlate with cluster state
"""
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from .artifact_parser import TestFailure, TestResult, ArtifactParser
from .cluster_inspector import ClusterInspector
from .jira_search_patterns import JiraSearchMatcher


@dataclass
class FailureAnalysis:
    """Analysis result for a test failure"""
    failure: TestFailure
    category: str  # timeout, assertion, element_not_found, network, auth, resource, unknown
    likely_cause: str
    cluster_correlation: Optional[Dict[str, Any]] = None
    recommended_actions: List[str] = None
    rerun_command: Optional[str] = None
    rerun_result: Optional[Dict[str, Any]] = None  # Result of rerunning the test
    jira_issues: List[Dict[str, Any]] = None
    jira_queries: List[Dict[str, Any]] = None  # Generated Jira search queries


class FailureAnalyzer:
    """Analyze test failures and provide insights"""

    def __init__(self, jira_client=None, enable_test_rerun=True, frontend_repo_path=None):
        self.parser = ArtifactParser()
        self.jira_client = jira_client
        self.jira_matcher = JiraSearchMatcher()
        self.enable_test_rerun = enable_test_rerun
        self.frontend_repo_path = frontend_repo_path or os.getenv("FRONTEND_REPO_PATH", "/path/to/odh-dashboard")

    def categorize_failure(self, failure: TestFailure) -> str:
        """
        Categorize the type of failure

        Categories:
        - timeout: Test timed out
        - assertion: Assertion failure
        - element_not_found: Element not found in DOM
        - network: Network/API error
        - auth: Authentication/permission error
        - resource: Cluster resource issue
        - unknown: Unknown error
        """
        error_msg = failure.error_message.lower()
        stack = failure.stack_trace.lower()
        combined = error_msg + ' ' + stack

        if 'timeout' in combined or 'timed out' in combined:
            return 'timeout'
        elif 'expected' in combined and ('to' in combined or 'should' in combined):
            return 'assertion'
        elif 'not found' in combined or 'does not exist' in combined or 'could not find' in combined:
            return 'element_not_found'
        elif 'network' in combined or 'fetch' in combined or 'xhr' in combined or 'api' in combined or '404' in combined or '500' in combined:
            return 'network'
        elif 'auth' in combined or 'permission' in combined or 'unauthorized' in combined or '401' in combined or '403' in combined:
            return 'auth'
        elif 'pod' in combined or 'deployment' in combined or 'service' in combined or 'namespace' in combined:
            return 'resource'
        else:
            return 'unknown'

    async def analyze_failure(
        self,
        failure: TestFailure,
        cluster_analysis: Optional[Dict[str, Any]] = None,
        cluster_name: str = "odh"
    ) -> FailureAnalysis:
        """
        Analyze a single test failure and provide recommendations

        Args:
            failure: The test failure to analyze
            cluster_analysis: Optional cluster state analysis from ClusterInspector
            cluster_name: Name of cluster (odh or rhoai) for rerun command
        """
        category = self.categorize_failure(failure)
        likely_cause = self._determine_likely_cause(failure, category, cluster_analysis)
        recommended_actions = self._get_recommended_actions(category, failure, cluster_analysis)
        cluster_correlation = self._find_cluster_correlation(failure, cluster_analysis)

        # Generate rerun command for display in reports (no password - safe for logs)
        rerun_command = self.generate_rerun_command(failure, cluster_name)

        # Actually rerun the test if enabled (handles authentication securely)
        rerun_result = None
        if self.enable_test_rerun:
            rerun_result = await self.rerun_failed_test(failure, cluster_name)

        # Generate intelligent Jira search queries based on test failure
        jira_queries = self.jira_matcher.generate_jira_queries(
            test_file=failure.test_file,
            test_name=failure.test_name,
            error_message=failure.error_message,
            max_queries=5
        )

        # Search Jira for related issues using generated queries
        jira_issues = []
        if self.jira_client and jira_queries:
            print(f"\n  [JIRA] Searching for related issues...")
            for query_info in jira_queries[:3]:  # Use top 3 queries
                try:
                    print(f"  [JIRA] Query: {query_info['name']}")
                    results = await self.jira_client.search_issues(query_info['query'], max_results=3)
                    if results:
                        # Add query context to results
                        for result in results:
                            result['matched_query'] = query_info['name']
                        jira_issues.extend(results)
                        print(f"  [JIRA] Found {len(results)} issue(s)")

                    # If we found issues, no need to try more queries
                    if jira_issues:
                        break
                except Exception as e:
                    print(f"  [JIRA] Search failed for '{query_info['name']}': {e}")

            if jira_issues:
                print(f"  [JIRA] ✓ Total {len(jira_issues)} related issue(s) found")
            else:
                print(f"  [JIRA] No related issues found")

        return FailureAnalysis(
            failure=failure,
            category=category,
            likely_cause=likely_cause,
            cluster_correlation=cluster_correlation,
            recommended_actions=recommended_actions,
            rerun_command=rerun_command,
            rerun_result=rerun_result,
            jira_issues=jira_issues,
            jira_queries=jira_queries
        )

    def _determine_likely_cause(
        self,
        failure: TestFailure,
        category: str,
        cluster_analysis: Optional[Dict[str, Any]]
    ) -> str:
        """Determine the most likely cause of the failure"""
        if category == 'timeout':
            if cluster_analysis and cluster_analysis.get('pod_health', {}).get('has_issues'):
                return "Timeout likely due to cluster resource issues (pods not ready or failing)"
            return "Test operation timed out waiting for expected condition"

        elif category == 'assertion':
            return "Assertion failed - actual result did not match expected result"

        elif category == 'element_not_found':
            return "UI element was not found in the DOM - possible race condition or UI regression"

        elif category == 'network':
            if cluster_analysis:
                pod_issues = cluster_analysis.get('pod_health', {}).get('problems', [])
                if pod_issues:
                    return f"Network error possibly due to backend pod issues: {pod_issues[0].get('issue', 'Unknown')}"
            return "Network or API request failed"

        elif category == 'auth':
            return "Authentication or authorization failure"

        elif category == 'resource':
            if cluster_analysis:
                return f"Cluster resource issue detected in namespace {cluster_analysis.get('namespace', 'unknown')}"
            return "Cluster resource issue"

        else:
            return "Unknown failure cause - manual investigation required"

    def _get_recommended_actions(
        self,
        category: str,
        failure: TestFailure,
        cluster_analysis: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Get recommended actions based on failure category"""
        actions = []

        if category == 'timeout':
            actions.append("Check if cluster pods are in Running state")
            actions.append("Review pod logs for errors or slow startup")
            actions.append("Verify network connectivity to cluster services")
            actions.append("Consider increasing timeout values if operation is legitimately slow")
            actions.append("Rerun the specific test to check if it's intermittent")

        elif category == 'assertion':
            actions.append("Review test expectations - may need updating if UI/API changed")
            actions.append("Check if recent code changes affected the tested functionality")
            actions.append("Verify test data setup is correct")
            actions.append("Rerun test to rule out race conditions")

        elif category == 'element_not_found':
            actions.append("Check if UI component is rendered conditionally")
            actions.append("Verify the test selector is correct and element exists")
            actions.append("Add explicit waits before interacting with element")
            actions.append("Review recent UI changes that may have changed element structure")

        elif category == 'network':
            actions.append("Check backend pod status and logs")
            actions.append("Verify API endpoints are accessible")
            actions.append("Review network policies and service configurations")
            actions.append("Check for recent deployments that may have broken APIs")

        elif category == 'auth':
            actions.append("Verify test credentials in test-variables.yml")
            actions.append("Check if RBAC permissions changed")
            actions.append("Confirm authentication service is running properly")

        elif category == 'resource':
            actions.append("Inspect cluster resources with 'oc get pods'")
            actions.append("Review cluster events for resource issues")
            actions.append("Check pod logs for application errors")
            actions.append("Verify required CRDs and operators are installed")

        else:
            actions.append("Review full error message and stack trace")
            actions.append("Check build artifacts for additional context")
            actions.append("Review recent code and configuration changes")

        # Always suggest rerunning
        actions.append("Rerun the failed test to determine if failure is consistent")

        return actions

    def _find_cluster_correlation(
        self,
        failure: TestFailure,
        cluster_analysis: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Find correlations between test failure and cluster state"""
        if not cluster_analysis:
            return None

        correlation = {}

        # Check for pod issues
        pod_health = cluster_analysis.get('pod_health', {})
        if pod_health.get('problems'):
            correlation['pod_issues'] = pod_health['problems']

        # Check for recent errors
        recent_errors = cluster_analysis.get('recent_errors', [])
        if recent_errors:
            # Filter errors that might be related to the test
            relevant_errors = []
            for error in recent_errors[:10]:  # Limit to 10 most recent
                if any(keyword in error.get('message', '').lower() for keyword in
                       ['error', 'failed', 'crash', 'timeout', 'unavailable']):
                    relevant_errors.append(error)

            if relevant_errors:
                correlation['recent_errors'] = relevant_errors

        return correlation if correlation else None

    async def analyze_test_result(
        self,
        test_result: TestResult,
        cluster_analysis: Optional[Dict[str, Any]] = None,
        cluster_name: str = "odh"
    ) -> Dict[str, Any]:
        """
        Analyze a complete test result

        Returns summary with categorized failures and recommendations
        """
        failure_analyses = []

        for failure in test_result.failures:
            analysis = await self.analyze_failure(failure, cluster_analysis, cluster_name)
            failure_analyses.append(analysis)

        # Categorize failures
        categories = {}
        for analysis in failure_analyses:
            cat = analysis.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(analysis)

        # Generate summary
        summary = {
            'job_name': test_result.job_name,
            'build_number': test_result.build_number,
            'build_url': test_result.build_url,
            'total_failures': len(failure_analyses),
            'categories': {cat: len(analyses) for cat, analyses in categories.items()},
            'failure_analyses': failure_analyses,
            'cluster_correlation': cluster_analysis,
            'overall_health': self._assess_overall_health(test_result, cluster_analysis)
        }

        return summary

    def _assess_overall_health(
        self,
        test_result: TestResult,
        cluster_analysis: Optional[Dict[str, Any]]
    ) -> str:
        """Assess overall health based on test results and cluster state"""
        failure_rate = test_result.failed_tests / test_result.total_tests if test_result.total_tests > 0 else 0

        if failure_rate == 0:
            return "healthy"
        elif failure_rate < 0.1:
            return "mostly_healthy"
        elif failure_rate < 0.3:
            return "degraded"
        else:
            return "critical"

    def generate_rerun_command(
        self,
        failure: TestFailure,
        cluster: str,
        test_variables_path: str = "test-variables.yml"
    ) -> str:
        """
        Generate command to rerun a specific failed test

        Args:
            failure: The failed test
            cluster: "rhoai" or "odh"
            test_variables_path: Path to test-variables.yml
        """
        # Extract test file relative to cypress directory
        # Example: frontend/src/__tests__/cypress/cypress/tests/e2e/modelServing/modelRegistry.cy.ts
        # -> modelServing/modelRegistry.cy.ts

        test_file = failure.test_file

        # Handle cases where test file path is partial or contains unknown.cy.ts
        if 'unknown.cy.ts' in test_file:
            # Try to find the actual test file based on test name
            if 'archive' in failure.test_name.lower() and 'model' in failure.test_name.lower():
                spec_file = 'modelRegistry/testArchiveModels.cy.ts'
            else:
                spec_file = test_file.replace('unknown.cy.ts', '*.cy.ts')
        elif 'e2e/' in test_file:
            spec_file = test_file.split('e2e/')[1]
        else:
            spec_file = test_file

        # Generate full path to test-variables.yml
        # NOTE: Cypress tests are in packages/cypress
        # Use provided test_variables_path or look in dashboard-build-analyzer/test-variables/
        cypress_dir = f"{self.frontend_repo_path}/packages/cypress"
        
        # Determine test variables path
        if test_variables_path:
            test_vars_full_path = test_variables_path
        else:
            # Default to our build-analyzer test-variables based on cluster
            analyzer_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            test_vars_full_path = os.path.join(analyzer_dir, 'test-variables', f'{cluster.lower()}-test-variables.yml')

        # Extract just the test name for grep filtering (remove file path)
        # Use the test name from the failure object for grep filtering
        # Note: Using grep instead of --spec because Cypress has issues finding spec files
        # Note: NOT setting CY_MOCK because any value (including "0") makes it truthy in JS
        
        # Get cluster credentials from environment (for display purposes only - no password!)
        if cluster.lower() == 'rhoai':
            api_server = os.getenv('RHOAI_API_SERVER', 'https://api.dash-e2e-rhoai.osp.rh-ods.com:6443')
            username = os.getenv('RHOAI_USERNAME', 'htpasswd-cluster-admin-user')
        else:  # odh
            api_server = os.getenv('ODH_API_SERVER', 'https://api.dash-e2e-odh.osp.rh-ods.com:6443')
            username = os.getenv('ODH_USERNAME', 'htpasswd-cluster-admin-user')
        
        # SECURITY: Password is NOT included in command string for reports/logs
        # When actually running, use rerun_failed_test() which handles auth securely
        oc_login_display = f"oc login -u {username} --server={api_server} --insecure-skip-tls-verify=true"
        
        # Use grep to filter to specific test by name
        cypress_cmd = f"cd {cypress_dir} && export CY_TEST_CONFIG='{test_vars_full_path}' && npx cypress run --env '{{\"grep\":\"{failure.test_name}\",\"grepFilterSpecs\":true}}' --browser electron"
        
        # Return command WITHOUT password - safe for reports and logs
        # Note: Actual execution via rerun_failed_test() handles authentication securely
        cmd = f"# First, login to cluster (password provided via environment):\n{oc_login_display}\n# Then run the test:\n{cypress_cmd}"

        return cmd

    async def rerun_failed_test(
        self,
        failure: TestFailure,
        cluster: str,
        test_variables_path: str = None,
        timeout: int = 300000  # 5 minutes default
    ) -> Dict[str, Any]:
        """
        Execute test rerun with secure authentication handling.
        
        SECURITY: Password is passed via stdin to oc login, never exposed in
        command line arguments or logs.

        Args:
            failure: The failed test
            cluster: "rhoai" or "odh"
            test_variables_path: Path to test-variables.yml
            timeout: Timeout in milliseconds

        Returns:
            Dict with rerun results including success/failure and output
        """
        import subprocess
        import time

        print(f"\n  [RERUN] Attempting to rerun test: {failure.test_name[:60]}...")

        result = {
            'attempted': True,
            'success': False,
            'exit_code': None,
            'output': '',
            'duration': 0,
            'timestamp': time.time()
        }

        # Get cluster credentials securely from environment
        if cluster.lower() == 'rhoai':
            api_server = os.getenv('RHOAI_API_SERVER', 'https://api.dash-e2e-rhoai.osp.rh-ods.com:6443')
            username = os.getenv('RHOAI_USERNAME', 'htpasswd-cluster-admin-user')
            password = os.getenv('RHOAI_PASSWORD', '')
        else:  # odh
            api_server = os.getenv('ODH_API_SERVER', 'https://api.dash-e2e-odh.osp.rh-ods.com:6443')
            username = os.getenv('ODH_USERNAME', 'htpasswd-cluster-admin-user')
            password = os.getenv('ODH_PASSWORD', '')

        try:
            start_time = time.time()

            # Step 1: Login to cluster securely (password via stdin)
            print(f"  [RERUN] Logging into {cluster.upper()} cluster...")
            login_cmd = [
                "oc", "login",
                "-u", username,
                "--server", api_server,
                "--insecure-skip-tls-verify=true"
            ]
            
            login_process = subprocess.run(
                login_cmd,
                input=f"{password}\n",
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if login_process.returncode != 0:
                result['output'] = f"Cluster login failed: {login_process.stderr}"
                result['exit_code'] = login_process.returncode
                print(f"  [RERUN] ✗ Cluster login failed")
                return result

            # Step 2: Run the Cypress test
            cypress_dir = f"{self.frontend_repo_path}/packages/cypress"
            
            # Determine test variables path
            if test_variables_path:
                test_vars_full_path = test_variables_path
            else:
                analyzer_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                test_vars_full_path = os.path.join(analyzer_dir, 'test-variables', f'{cluster.lower()}-test-variables.yml')

            # Build cypress command (no shell=True for security)
            cypress_env = os.environ.copy()
            cypress_env['CY_TEST_CONFIG'] = test_vars_full_path
            
            cypress_cmd = [
                "npx", "cypress", "run",
                "--env", f'{{"grep":"{failure.test_name}","grepFilterSpecs":true}}',
                "--browser", "electron"
            ]

            print(f"  [RERUN] Running Cypress test...")
            process = subprocess.run(
                cypress_cmd,
                capture_output=True,
                text=True,
                timeout=timeout / 1000,
                cwd=cypress_dir,
                env=cypress_env
            )

            duration = time.time() - start_time

            result['exit_code'] = process.returncode
            # Sanitize output - ensure no passwords leaked
            output = process.stdout + process.stderr
            if password and password in output:
                output = output.replace(password, "[REDACTED]")
            result['output'] = output
            result['duration'] = duration
            result['success'] = (process.returncode == 0)

            if result['success']:
                print(f"  [RERUN] ✓ Test PASSED on rerun! (took {duration:.1f}s)")
            else:
                print(f"  [RERUN] ✗ Test FAILED on rerun (exit code {process.returncode})")

        except subprocess.TimeoutExpired:
            result['output'] = f"Test timed out after {timeout/1000}s"
            result['exit_code'] = -1
            print(f"  [RERUN] ✗ Test timed out after {timeout/1000}s")

        except Exception as e:
            result['output'] = f"Error running test: {str(e)}"
            result['exit_code'] = -1
            print(f"  [RERUN] ✗ Error: {str(e)}")

        return result

    def compare_builds(
        self,
        current_result: TestResult,
        previous_result: TestResult
    ) -> Dict[str, Any]:
        """
        Compare two test results to identify new failures or regressions

        Args:
            current_result: Latest test result
            previous_result: Previous test result for comparison

        Returns:
            Comparison summary with new failures and resolved issues
        """
        current_failures = {f.test_name for f in current_result.failures}
        previous_failures = {f.test_name for f in previous_result.failures}

        new_failures = current_failures - previous_failures
        resolved_failures = previous_failures - current_failures
        recurring_failures = current_failures & previous_failures

        return {
            'new_failures': list(new_failures),
            'resolved_failures': list(resolved_failures),
            'recurring_failures': list(recurring_failures),
            'new_failure_count': len(new_failures),
            'resolved_count': len(resolved_failures),
            'recurring_count': len(recurring_failures),
            'trend': 'improving' if len(new_failures) < len(resolved_failures) else 'degrading' if len(new_failures) > len(resolved_failures) else 'stable'
        }
