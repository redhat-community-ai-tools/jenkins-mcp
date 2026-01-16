"""
Report Generator - Generate daily analysis reports
"""
from typing import Dict, List, Any
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from .artifact_parser import TestResult
from .failure_analyzer import FailureAnalysis


class ReportGenerator:
    """Generate formatted reports for test analysis"""

    def __init__(self):
        self.console = Console()

    def generate_daily_report(
        self,
        rhoai_analysis: Dict[str, Any],
        odh_analysis: Dict[str, Any],
        date: datetime
    ) -> str:
        """
        Generate comprehensive daily report for both clusters

        Args:
            rhoai_analysis: Analysis results for RHOAI cluster
            odh_analysis: Analysis results for ODH cluster
            date: Date of the analysis

        Returns:
            Markdown formatted report
        """
        report_lines = []

        # Header
        report_lines.append(f"# Nightly E2E Test Analysis Report")
        report_lines.append(f"**Date:** {date.strftime('%Y-%m-%d')}")
        report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S GMT')}")
        report_lines.append("")

        # TLDR Section
        report_lines.append("## TL;DR")
        report_lines.append("")
        report_lines.extend(self._generate_tldr(rhoai_analysis, odh_analysis))
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Executive Summary
        report_lines.append("## Executive Summary")
        report_lines.append("")
        report_lines.extend(self._generate_executive_summary(rhoai_analysis, odh_analysis))
        report_lines.append("")

        # RHOAI Results
        report_lines.append("## RHOAI E2E Results")
        report_lines.append("")
        report_lines.extend(self._generate_cluster_section(rhoai_analysis, "RHOAI"))
        report_lines.append("")

        # ODH Results
        report_lines.append("## ODH E2E Results")
        report_lines.append("")
        report_lines.extend(self._generate_cluster_section(odh_analysis, "ODH"))
        report_lines.append("")

        # Recommendations
        report_lines.append("## Recommended Actions")
        report_lines.append("")
        report_lines.extend(self._generate_recommendations(rhoai_analysis, odh_analysis))

        return "\n".join(report_lines)

    def _generate_tldr(
        self,
        rhoai_analysis: Dict[str, Any],
        odh_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate TL;DR section with key highlights"""
        lines = []

        rhoai_failures = rhoai_analysis.get('total_failures', 0)
        odh_failures = odh_analysis.get('total_failures', 0)
        total_failures = rhoai_failures + odh_failures

        # Overall status emoji
        if total_failures == 0:
            status_emoji = "[PASS]"
            status_text = "All tests passing"
        elif total_failures <= 2:
            status_emoji = "[WARN]"
            status_text = f"{total_failures} test failure(s) - Investigation needed"
        else:
            status_emoji = "[FAIL]"
            status_text = f"{total_failures} test failures - Immediate attention required"

        lines.append(f"{status_emoji} **{status_text}**")
        lines.append("")

        # Key points
        if rhoai_failures > 0:
            lines.append(f"- **RHOAI**: {rhoai_failures} failure(s)")
            # Get top failure category
            if rhoai_analysis.get('failure_analyses'):
                top_failure = rhoai_analysis['failure_analyses'][0]
                lines.append(f"  - Test: {top_failure.failure.test_name}")
                lines.append(f"  - Category: {top_failure.category}")

        if odh_failures > 0:
            lines.append(f"- **ODH**: {odh_failures} failure(s)")
            # Get top failure category
            if odh_analysis.get('failure_analyses'):
                top_failure = odh_analysis['failure_analyses'][0]
                lines.append(f"  - Test: {top_failure.failure.test_name}")
                lines.append(f"  - Category: {top_failure.category}")
                # Check for Jira queries
                if hasattr(top_failure, 'jira_queries') and top_failure.jira_queries:
                    lines.append(f"  - Jira: Search for '{top_failure.jira_queries[0]['query']}'")

        if total_failures == 0:
            lines.append(f"- **RHOAI**: All tests passed [PASS]")
            lines.append(f"- **ODH**: All tests passed [PASS]")

        return lines

    def _generate_executive_summary(
        self,
        rhoai_analysis: Dict[str, Any],
        odh_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate executive summary section"""
        lines = []

        rhoai_health = rhoai_analysis.get('overall_health', 'unknown')
        odh_health = odh_analysis.get('overall_health', 'unknown')

        rhoai_failures = rhoai_analysis.get('total_failures', 0)
        odh_failures = odh_analysis.get('total_failures', 0)

        # Overall status
        if rhoai_health == 'healthy' and odh_health == 'healthy':
            lines.append(" **Status:** All tests passing on both clusters")
        elif rhoai_health == 'critical' or odh_health == 'critical':
            lines.append("=4 **Status:** Critical failures detected")
        elif rhoai_failures > 0 or odh_failures > 0:
            lines.append(" **Status:** Some test failures detected")
        else:
            lines.append(" **Status:** Healthy")

        lines.append("")

        # Quick stats
        lines.append(f"- **RHOAI:** {rhoai_failures} failures ({rhoai_health})")
        lines.append(f"- **ODH:** {odh_failures} failures ({odh_health})")

        return lines

    def _generate_cluster_section(
        self,
        analysis: Dict[str, Any],
        cluster_name: str
    ) -> List[str]:
        """Generate detailed section for a cluster"""
        lines = []

        job_name = analysis.get('job_name', 'Unknown')
        build_number = analysis.get('build_number', 'N/A')
        build_url = analysis.get('build_url', '')
        total_failures = analysis.get('total_failures', 0)

        lines.append(f"**Build:** [{job_name} #{build_number}]({build_url})")
        lines.append("")

        if total_failures == 0:
            lines.append(" All tests passed!")
            return lines

        # Failure summary by category
        lines.append(f"**Total Failures:** {total_failures}")
        lines.append("")
        lines.append("### Failures by Category")
        lines.append("")

        categories = analysis.get('categories', {})
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            emoji = self._get_category_emoji(category)
            lines.append(f"- {emoji} **{category.replace('_', ' ').title()}:** {count}")

        lines.append("")

        # Detailed failure analysis
        lines.append("### Detailed Failure Analysis")
        lines.append("")

        failure_analyses: List[FailureAnalysis] = analysis.get('failure_analyses', [])

        for i, fa in enumerate(failure_analyses[:20], 1):  # Limit to top 20
            lines.append(f"#### {i}. {fa.failure.test_name}")
            lines.append("")
            lines.append(f"**Test File:** `{fa.failure.test_file}`")
            lines.append(f"**Category:** {fa.category}")
            lines.append(f"**Likely Cause:** {fa.likely_cause}")
            lines.append("")
            lines.append(f"**Error Message:**")
            lines.append(f"```")
            lines.append(fa.failure.error_message[:500])  # Truncate long errors
            lines.append(f"```")
            lines.append("")

            # Add rerun command and results if available
            if hasattr(fa, 'rerun_command') and fa.rerun_command:
                lines.append("**Rerun This Test:**")
                lines.append("```bash")
                lines.append(fa.rerun_command)
                lines.append("```")

                # Show rerun results if test was actually executed
                if hasattr(fa, 'rerun_result') and fa.rerun_result and fa.rerun_result.get('attempted'):
                    rerun = fa.rerun_result
                    if rerun.get('success'):
                        lines.append(f"**Rerun Result:** :white_check_mark: **PASSED** on rerun (took {rerun.get('duration', 0):.1f}s)")
                        lines.append("> **Note:** This appears to be an intermittent/flaky test since it passed when rerun")
                    else:
                        lines.append(f"**Rerun Result:** :x: **FAILED** on rerun (exit code: {rerun.get('exit_code', 'N/A')})")
                        lines.append("> **Note:** Test consistently fails - not intermittent")
                lines.append("")

            # Add Jira search results if available
            if hasattr(fa, 'jira_issues') and fa.jira_issues:
                lines.append("**Related Jira Issues Found:**")
                for idx, issue in enumerate(fa.jira_issues[:5], 1):  # Top 5 issues
                    issue_key = issue.get('key', 'N/A')
                    summary = issue.get('summary', 'No summary')
                    status = issue.get('status', 'Unknown')
                    matched_query = issue.get('matched_query', 'N/A')
                    lines.append(f"{idx}. **[{issue_key}]({issue.get('url', '#')})** - {status}")
                    lines.append(f"   - {summary}")
                    lines.append(f"   - Matched via: {matched_query}")
                lines.append("")

            # Add Jira search queries (even if no issues found, show queries for manual search)
            if hasattr(fa, 'jira_queries') and fa.jira_queries:
                if not (hasattr(fa, 'jira_issues') and fa.jira_issues):
                    lines.append("**Jira Search Queries** (No issues found automatically - try these manually):")
                else:
                    lines.append("**Additional Jira Search Queries:**")
                for idx, query in enumerate(fa.jira_queries[:3], 1):  # Top 3 queries
                    priority_text = " (HIGHEST PRIORITY)" if query['priority'] == 1 else ""
                    lines.append(f"{idx}. **{query['name']}**{priority_text}")
                    lines.append(f"   - Search: `{query['query']}`")
                    lines.append(f"   - Component: {', '.join(query['components']) if query['components'] else 'N/A'}")
                    lines.append(f"   - [Search in Jira]({query.get('url', '#')})")
                lines.append("")

            if fa.recommended_actions:
                lines.append("**Recommended Actions:**")
                for action in fa.recommended_actions[:5]:  # Top 5 actions
                    lines.append(f"- {action}")
                lines.append("")

            if fa.cluster_correlation:
                lines.append("**Cluster Correlation:**")
                if 'pod_issues' in fa.cluster_correlation:
                    lines.append("- Pod issues detected:")
                    for issue in fa.cluster_correlation['pod_issues'][:3]:
                        lines.append(f"  - {issue.get('pod')}: {issue.get('issue')}")
                lines.append("")

            lines.append("---")
            lines.append("")

        # Cluster health
        cluster_analysis = analysis.get('cluster_correlation')
        if cluster_analysis:
            lines.append("### Cluster Health")
            lines.append("")

            pod_health = cluster_analysis.get('pod_health', {})
            lines.append(f"**Namespace:** {cluster_analysis.get('namespace', 'unknown')}")
            lines.append(f"- Total Pods: {pod_health.get('total', 0)}")
            lines.append(f"- Running: {pod_health.get('running', 0)}")
            lines.append(f"- Failed: {pod_health.get('failed', 0)}")
            lines.append(f"- Crash Looping: {pod_health.get('crash_looping', 0)}")
            lines.append("")

            if pod_health.get('problems'):
                lines.append("**Pod Issues:**")
                for problem in pod_health['problems'][:5]:
                    lines.append(f"- {problem.get('pod')}: {problem.get('issue')}")
                lines.append("")

        return lines

    def _generate_recommendations(
        self,
        rhoai_analysis: Dict[str, Any],
        odh_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations section"""
        lines = []

        # Collect all unique recommendations
        all_recommendations = set()

        for analysis in [rhoai_analysis, odh_analysis]:
            for fa in analysis.get('failure_analyses', []):
                if fa.recommended_actions:
                    all_recommendations.update(fa.recommended_actions[:3])

        if not all_recommendations:
            lines.append("No specific recommendations at this time.")
            return lines

        # Prioritize recommendations
        priority_keywords = {
            'cluster': 1,
            'pod': 1,
            'resource': 1,
            'rerun': 3,
            'check': 2,
            'verify': 2,
            'review': 2
        }

        def get_priority(rec: str) -> int:
            rec_lower = rec.lower()
            for keyword, priority in priority_keywords.items():
                if keyword in rec_lower:
                    return priority
            return 4

        sorted_recs = sorted(all_recommendations, key=get_priority)

        for i, rec in enumerate(sorted_recs[:10], 1):
            lines.append(f"{i}. {rec}")

        return lines

    def _get_category_emoji(self, category: str) -> str:
        """Get emoji for failure category"""
        emoji_map = {
            'timeout': '[TIMEOUT]',
            'assertion': '[ASSERT]',
            'element_not_found': '[NOT_FOUND]',
            'network': '[NETWORK]',
            'auth': '[AUTH]',
            'resource': '[RESOURCE]',
            'unknown': '[UNKNOWN]'
        }
        return emoji_map.get(category, '[UNKNOWN]')

    def print_console_report(
        self,
        rhoai_analysis: Dict[str, Any],
        odh_analysis: Dict[str, Any],
        date: datetime
    ):
        """Print a rich console report"""
        self.console.print("")
        self.console.print(Panel.fit(
            f"[bold cyan]Nightly E2E Test Analysis Report[/bold cyan]\n"
            f"Date: {date.strftime('%Y-%m-%d')}\n"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S GMT')}",
            title="Report",
            border_style="cyan"
        ))
        self.console.print("")

        # Summary table
        table = Table(title="Summary", show_header=True, header_style="bold magenta")
        table.add_column("Cluster", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Failures", justify="right", style="red")
        table.add_column("Health", style="yellow")

        rhoai_failures = rhoai_analysis.get('total_failures', 0)
        odh_failures = odh_analysis.get('total_failures', 0)
        rhoai_health = rhoai_analysis.get('overall_health', 'unknown')
        odh_health = odh_analysis.get('overall_health', 'unknown')

        rhoai_status = "" if rhoai_failures == 0 else "L"
        odh_status = "" if odh_failures == 0 else "L"

        table.add_row("RHOAI", rhoai_status, str(rhoai_failures), rhoai_health)
        table.add_row("ODH", odh_status, str(odh_failures), odh_health)

        self.console.print(table)
        self.console.print("")

        # Category breakdown
        if rhoai_failures > 0 or odh_failures > 0:
            self.console.print("[bold yellow]Failure Categories:[/bold yellow]")
            self.console.print("")

            for cluster_name, analysis in [("RHOAI", rhoai_analysis), ("ODH", odh_analysis)]:
                if analysis.get('total_failures', 0) > 0:
                    self.console.print(f"[cyan]{cluster_name}:[/cyan]")
                    categories = analysis.get('categories', {})
                    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                        emoji = self._get_category_emoji(category)
                        self.console.print(f"  {emoji} {category.replace('_', ' ').title()}: {count}")
                    self.console.print("")

    def save_report(self, report_content: str, output_path: str):
        """Save report to file"""
        with open(output_path, 'w') as f:
            f.write(report_content)
