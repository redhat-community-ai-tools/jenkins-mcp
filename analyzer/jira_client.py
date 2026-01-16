"""
Jira Client - Search for related Jira issues for test failures
"""
import re
import os
from typing import List, Dict, Any, Optional
import httpx
import base64

from .config import Config


class JiraClient:
    """Client for searching Red Hat Jira"""

    def __init__(self, base_url: str = "https://issues.redhat.com",
                 api_token: str = ""):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token or os.getenv("JIRA_TOKEN", "")
        self.ssl_verify = Config.SSL_VERIFY

    async def search_issues(
        self,
        test_name: str,
        project: str = "RHOAIENG",
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for Jira issues related to a test failure

        Args:
            test_name: Name of the failing test
            project: Jira project key (default: RHOAIENG)
            max_results: Maximum number of results to return

        Returns:
            List of matching Jira issues
        """
        # Extract key terms from test name
        search_terms = self._extract_search_terms(test_name)

        if not search_terms:
            return []

        # Build JQL query
        jql = self._build_jql_query(search_terms, project)

        try:
            async with httpx.AsyncClient(verify=self.ssl_verify, timeout=30.0) as client:
                url = f"{self.base_url}/rest/api/2/search"

                headers = {
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json"
                }

                params = {
                    "jql": jql,
                    "maxResults": max_results,
                    "fields": "summary,status,priority,assignee,created,updated,description"
                }

                response = await client.get(url, headers=headers, params=params)

                if response.status_code == 200:
                    data = response.json()
                    return self._format_issues(data.get('issues', []))
                else:
                    print(f"Jira search failed: {response.status_code}")
                    return []

        except Exception as e:
            print(f"Error searching Jira: {e}")
            return []

    def _extract_search_terms(self, test_name: str) -> List[str]:
        """Extract meaningful search terms from test name"""
        # Remove common test prefixes/suffixes
        cleaned = test_name.replace('.cy.ts', '').replace('should ', '').replace('test ', '')

        # Extract camelCase and PascalCase words
        words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', cleaned)

        # Also split on common separators
        additional_words = re.split(r'[-_\s/]+', cleaned)

        all_words = words + additional_words

        # Filter out common/short words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'it', 'is', 'be'}
        meaningful_terms = [
            word.lower() for word in all_words
            if len(word) > 2 and word.lower() not in stopwords
        ]

        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in meaningful_terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)

        return unique_terms[:5]  # Limit to top 5 terms

    def _build_jql_query(self, search_terms: List[str], project: str) -> str:
        """Build JQL query from search terms - prioritize e2e/test-related issues, exclude CVEs"""
        if not search_terms:
            return f"project = {project} AND status != Closed AND summary !~ CVE ORDER BY updated DESC"

        # Create text search using 'text' which searches summary AND description AND comments
        # This is more comprehensive than searching individual fields
        text_conditions = []
        for term in search_terms:
            text_conditions.append(f'text ~ "{term}"')

        text_query = " OR ".join(text_conditions)

        # Combine with project filter and exclude CVEs
        # Can't use complex ORDER BY with conditions in JQL, so keep it simple
        jql = (f"project = {project} AND ({text_query}) "
               f"AND summary !~ CVE "
               f"ORDER BY updated DESC")

        return jql

    def _format_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format Jira issues for display"""
        formatted = []

        for issue in issues:
            fields = issue.get('fields', {})
            status = fields.get('status', {})
            priority = fields.get('priority', {})
            assignee = fields.get('assignee', {})

            formatted.append({
                'key': issue.get('key'),
                'summary': fields.get('summary', 'No summary'),
                'status': status.get('name', 'Unknown'),
                'priority': priority.get('name', 'Unknown'),
                'assignee': assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned',
                'created': fields.get('created'),
                'updated': fields.get('updated'),
                'url': f"{self.base_url}/browse/{issue.get('key')}"
            })

        return formatted

    async def get_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific Jira issue"""
        try:
            async with httpx.AsyncClient(verify=self.ssl_verify, timeout=30.0) as client:
                url = f"{self.base_url}/rest/api/2/issue/{issue_key}"

                headers = {
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json"
                }

                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    return self._format_issues([data])[0]
                else:
                    return None

        except Exception as e:
            print(f"Error fetching Jira issue {issue_key}: {e}")
            return None

    async def search_by_error_message(
        self,
        error_message: str,
        project: str = "RHOAIENG",
        max_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search for Jira issues by error message

        Useful for finding known issues with similar error signatures
        """
        # Extract key parts of error message
        error_parts = self._extract_error_signature(error_message)

        if not error_parts:
            return []

        # Build query
        text_conditions = []
        for part in error_parts:
            # Escape special JQL characters
            escaped = part.replace('"', '\\"')
            text_conditions.append(f'text ~ "{escaped}"')

        text_query = " OR ".join(text_conditions)
        jql = f"project = {project} AND ({text_query}) ORDER BY updated DESC"

        try:
            async with httpx.AsyncClient(verify=self.ssl_verify, timeout=30.0) as client:
                url = f"{self.base_url}/rest/api/2/search"

                headers = {
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json"
                }

                params = {
                    "jql": jql,
                    "maxResults": max_results,
                    "fields": "summary,status,priority,created,updated"
                }

                response = await client.get(url, headers=headers, params=params)

                if response.status_code == 200:
                    data = response.json()
                    return self._format_issues(data.get('issues', []))
                else:
                    return []

        except Exception as e:
            print(f"Error searching Jira by error: {e}")
            return []

    def _extract_error_signature(self, error_message: str) -> List[str]:
        """Extract distinctive parts of error message for searching"""
        # Limit message length
        error_message = error_message[:500]

        # Look for specific error patterns
        patterns = [
            r'Error:\s*([^\n]+)',
            r'Exception:\s*([^\n]+)',
            r'expected\s+(.+?)\s+(?:to|but)',
            r'Timed out\s+(.+)',
            r'failed\s+(.+)',
        ]

        signatures = []
        for pattern in patterns:
            match = re.search(pattern, error_message, re.IGNORECASE)
            if match:
                sig = match.group(1).strip()
                # Clean up the signature
                sig = re.sub(r'\s+', ' ', sig)  # Normalize whitespace
                sig = re.sub(r'[\'"`]', '', sig)  # Remove quotes
                if len(sig) > 10:  # Only meaningful signatures
                    signatures.append(sig)

        return signatures[:3]  # Top 3 signatures
