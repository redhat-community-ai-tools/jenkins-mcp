"""
Jira Search Patterns - Intelligently map test failures to Jira queries
"""
import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class JiraSearchPattern:
    """Pattern for mapping test failures to Jira searches"""
    name: str
    file_patterns: List[str]  # Regex patterns to match test file paths
    test_name_patterns: List[str]  # Regex patterns to match test names
    error_patterns: List[str]  # Regex patterns to match error messages
    jira_keywords: List[str]  # Keywords to search in Jira
    jira_components: List[str]  # Jira components to filter by
    priority: int  # Search priority (1 = highest)


# Define search patterns for different test categories
SEARCH_PATTERNS = [
    # Model Registry Tests
    JiraSearchPattern(
        name="Model Registry - Archive/Restore",
        file_patterns=[
            r"modelRegistry.*archive",
            r"testArchiveModels",
        ],
        test_name_patterns=[
            r"archive.*model",
            r"restore.*model",
            r"archive.*version",
        ],
        error_patterns=[
            r"timeout.*model.*registry",
            r"ContextProperty",
            r"model.*registration.*timeout",
        ],
        jira_keywords=[
            "model registry archive",
            "model registry restore",
            "model archive timeout",
            "model registration timeout",
        ],
        jira_components=["Model Registry"],
        priority=1
    ),

    JiraSearchPattern(
        name="Model Registry - Registration",
        file_patterns=[
            r"modelRegistry.*register",
            r"testRegister.*Model",
        ],
        test_name_patterns=[
            r"register.*model",
            r"create.*model",
        ],
        error_patterns=[
            r"registration.*failed",
            r"object storage.*timeout",
            r"model.*not.*created",
        ],
        jira_keywords=[
            "model registration",
            "register model failed",
            "model registry object storage",
        ],
        jira_components=["Model Registry"],
        priority=1
    ),

    JiraSearchPattern(
        name="Model Registry - Database",
        file_patterns=[
            r"modelRegistry",
        ],
        test_name_patterns=[],
        error_patterns=[
            r"database.*schema",
            r"ContextProperty",
            r"MySQL.*error",
            r"table.*not.*exist",
        ],
        jira_keywords=[
            "model registry database",
            "model registry schema",
            "ContextProperty table",
            "model registry MySQL",
        ],
        jira_components=["Model Registry"],
        priority=1
    ),

    # Pipelines Tests
    JiraSearchPattern(
        name="Pipelines - Creation/Execution",
        file_patterns=[
            r"[Pp]ipelines?/",
            r"[Pp]ipeline.*\.cy\.ts",
        ],
        test_name_patterns=[
            r"pipeline.*create",
            r"pipeline.*run",
            r"pipeline.*execute",
        ],
        error_patterns=[
            r"pipeline.*failed",
            r"pipeline.*timeout",
            r"pipeline.*not.*found",
        ],
        jira_keywords=[
            "pipeline creation",
            "pipeline execution",
            "pipeline failed",
            "pipeline timeout",
        ],
        jira_components=["Pipelines", "Data Science Pipelines"],
        priority=1
    ),

    JiraSearchPattern(
        name="Pipelines - Scheduling",
        file_patterns=[
            r"testSchedulePipeline",
            r"pipeline.*schedule",
        ],
        test_name_patterns=[
            r"schedule.*pipeline",
            r"cron.*pipeline",
            r"recurring.*pipeline",
        ],
        error_patterns=[
            r"schedule.*failed",
            r"cron.*error",
            r"trigger.*failed",
        ],
        jira_keywords=[
            "pipeline schedule",
            "scheduled pipeline",
            "pipeline trigger",
            "pipeline cron",
        ],
        jira_components=["Pipelines"],
        priority=1
    ),

    # Workbench Tests
    JiraSearchPattern(
        name="Workbench - Creation",
        file_patterns=[
            r"workbench.*[Cc]reation",
            r"testWorkbenchCreation",
        ],
        test_name_patterns=[
            r"create.*workbench",
            r"launch.*workbench",
        ],
        error_patterns=[
            r"workbench.*failed.*create",
            r"workbench.*timeout",
        ],
        jira_keywords=[
            "workbench creation",
            "create workbench failed",
            "workbench timeout",
        ],
        jira_components=["Workbenches", "Notebooks"],
        priority=1
    ),

    JiraSearchPattern(
        name="Workbench - Images",
        file_patterns=[
            r"workbench.*[Ii]mages?",
        ],
        test_name_patterns=[
            r"workbench.*image",
            r"notebook.*image",
        ],
        error_patterns=[
            r"image.*not.*found",
            r"image.*pull.*failed",
        ],
        jira_keywords=[
            "workbench image",
            "notebook image",
            "image not found",
        ],
        jira_components=["Workbenches", "Notebooks"],
        priority=1
    ),

    # Storage Tests
    JiraSearchPattern(
        name="Storage - Cluster Storage",
        file_patterns=[
            r"clusterStorage",
            r"storageClasses",
        ],
        test_name_patterns=[
            r"cluster.*storage",
            r"storage.*class",
            r"PVC",
        ],
        error_patterns=[
            r"storage.*failed",
            r"PVC.*error",
            r"volume.*failed",
        ],
        jira_keywords=[
            "cluster storage",
            "storage class",
            "PVC failed",
            "volume error",
        ],
        jira_components=["Storage", "Cluster Storage"],
        priority=2
    ),

    # Authentication/Login Tests
    JiraSearchPattern(
        name="Authentication - User Login",
        file_patterns=[
            r"testUserLogin",
            r"authentication",
        ],
        test_name_patterns=[
            r"login",
            r"auth",
            r"sign.*in",
        ],
        error_patterns=[
            r"login.*failed",
            r"auth.*error",
            r"unauthorized",
            r"403",
            r"401",
        ],
        jira_keywords=[
            "login failed",
            "authentication error",
            "OAuth error",
            "LDAP login",
        ],
        jira_components=["Authentication", "Dashboard"],
        priority=1
    ),

    # Dashboard/Navigation Tests
    JiraSearchPattern(
        name="Dashboard - Navigation",
        file_patterns=[
            r"dashboardNavigation",
            r"navigation",
        ],
        test_name_patterns=[
            r"navigate",
            r"menu",
            r"link",
        ],
        error_patterns=[
            r"element.*not.*found",
            r"navigation.*failed",
            r"link.*broken",
        ],
        jira_keywords=[
            "dashboard navigation",
            "UI element not found",
            "navigation failed",
        ],
        jira_components=["Dashboard", "UI"],
        priority=2
    ),

    # Distributed Workload/Metrics Tests
    JiraSearchPattern(
        name="Distributed Workload Metrics",
        file_patterns=[
            r"distributedWorkload",
            r"workloadMetrics",
        ],
        test_name_patterns=[
            r"metrics",
            r"distributed.*workload",
        ],
        error_patterns=[
            r"metrics.*not.*loaded",
            r"prometheus.*error",
        ],
        jira_keywords=[
            "distributed workload",
            "workload metrics",
            "metrics dashboard",
        ],
        jira_components=["Distributed Workloads", "Metrics"],
        priority=2
    ),

    # Model Serving Tests
    JiraSearchPattern(
        name="Model Serving - Deployment",
        file_patterns=[
            r"testDeploy.*Model",
            r"modelServing",
        ],
        test_name_patterns=[
            r"deploy.*model",
            r"model.*serving",
        ],
        error_patterns=[
            r"deployment.*failed",
            r"model.*not.*deployed",
            r"serving.*error",
        ],
        jira_keywords=[
            "model serving",
            "model deployment",
            "deploy model failed",
        ],
        jira_components=["Model Serving", "KServe"],
        priority=1
    ),

    # NIM (NVIDIA Inference) Tests
    JiraSearchPattern(
        name="NIM - NVIDIA Inference",
        file_patterns=[
            r"nim/",
            r"testEnableNIM",
        ],
        test_name_patterns=[
            r"NIM",
            r"NVIDIA.*inference",
        ],
        error_patterns=[
            r"NIM.*failed",
            r"NGC.*error",
        ],
        jira_keywords=[
            "NIM",
            "NVIDIA inference",
            "NGC API",
        ],
        jira_components=["NIM", "Model Serving"],
        priority=2
    ),

    # Generic Timeout Pattern (Low Priority)
    JiraSearchPattern(
        name="Generic - Timeout",
        file_patterns=[],
        test_name_patterns=[],
        error_patterns=[
            r"timeout",
            r"timed out",
        ],
        jira_keywords=[
            "timeout",
            "UI timeout",
            "element timeout",
        ],
        jira_components=["Dashboard", "UI"],
        priority=3
    ),

    # Generic Element Not Found (Low Priority)
    JiraSearchPattern(
        name="Generic - Element Not Found",
        file_patterns=[],
        test_name_patterns=[],
        error_patterns=[
            r"element.*not.*found",
            r"selector.*not.*found",
        ],
        jira_keywords=[
            "element not found",
            "UI element missing",
        ],
        jira_components=["Dashboard", "UI"],
        priority=3
    ),

    # Operator Installation Issues
    JiraSearchPattern(
        name="Operator - Installation",
        file_patterns=[],
        test_name_patterns=[],
        error_patterns=[
            r"operator.*install.*failed",
            r"namespace.*terminating",
            r"cleanup\.sh.*failed",
            r"setup\.sh.*failed",
        ],
        jira_keywords=[
            "operator installation",
            "namespace terminating",
            "operator cleanup",
            "ODH operator install",
        ],
        jira_components=["Operator", "Installation"],
        priority=1
    ),
]


class JiraSearchMatcher:
    """Match test failures to appropriate Jira search patterns"""

    def __init__(self):
        self.patterns = sorted(SEARCH_PATTERNS, key=lambda p: p.priority)

    def match_failure(
        self,
        test_file: str = "",
        test_name: str = "",
        error_message: str = ""
    ) -> List[JiraSearchPattern]:
        """
        Match a test failure to relevant Jira search patterns

        Args:
            test_file: Path to the test file (e.g., "modelRegistry/testArchiveModels.cy.ts")
            test_name: Name of the test (e.g., "Verify that models can be archived")
            error_message: Error message from the test failure

        Returns:
            List of matching JiraSearchPattern objects, sorted by priority and relevance
        """
        matches = []

        for pattern in self.patterns:
            score = 0

            # Check file patterns
            if test_file and pattern.file_patterns:
                for file_pattern in pattern.file_patterns:
                    if re.search(file_pattern, test_file, re.IGNORECASE):
                        score += 10
                        break

            # Check test name patterns
            if test_name and pattern.test_name_patterns:
                for name_pattern in pattern.test_name_patterns:
                    if re.search(name_pattern, test_name, re.IGNORECASE):
                        score += 5
                        break

            # Check error patterns
            if error_message and pattern.error_patterns:
                for error_pattern in pattern.error_patterns:
                    if re.search(error_pattern, error_message, re.IGNORECASE):
                        score += 8
                        break

            if score > 0:
                matches.append((score, pattern))

        # Sort by score (descending) then by priority (ascending)
        matches.sort(key=lambda x: (-x[0], x[1].priority))

        return [pattern for score, pattern in matches]

    def generate_jira_queries(
        self,
        test_file: str = "",
        test_name: str = "",
        error_message: str = "",
        max_queries: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate Jira search queries based on test failure

        Returns:
            List of dictionaries with 'name', 'query', and 'components'
        """
        matched_patterns = self.match_failure(test_file, test_name, error_message)

        queries = []
        seen_keywords = set()

        for pattern in matched_patterns[:max_queries]:
            # Generate queries for each keyword
            for keyword in pattern.jira_keywords[:2]:  # Top 2 keywords per pattern
                if keyword in seen_keywords:
                    continue

                seen_keywords.add(keyword)

                # Build Jira query
                components_filter = ""
                if pattern.jira_components:
                    comp_list = ", ".join(f'"{c}"' for c in pattern.jira_components)
                    components_filter = f" AND component in ({comp_list})"

                query = {
                    "name": f"{pattern.name}",
                    "description": f"Search for: {keyword}",
                    "query": keyword,
                    "jql": f"project = RHOAIENG AND type = Bug AND text ~ \"{keyword}\"{components_filter} ORDER BY priority DESC, updated DESC",
                    "components": pattern.jira_components,
                    "priority": pattern.priority
                }

                queries.append(query)

        # If no specific matches, add generic search
        if not queries and error_message:
            # Extract key words from error message
            error_words = re.findall(r'\b\w{4,}\b', error_message)[:3]
            if error_words:
                keyword = " ".join(error_words)
                queries.append({
                    "name": "Generic Error Search",
                    "description": f"Search for error: {keyword}",
                    "query": keyword,
                    "jql": f"project = RHOAIENG AND text ~ \"{keyword}\" ORDER BY priority DESC, updated DESC",
                    "components": [],
                    "priority": 5
                })

        return queries[:max_queries]


# Example usage
if __name__ == "__main__":
    matcher = JiraSearchMatcher()

    # Example 1: Model Registry test
    print("="*70)
    print("Example 1: Model Registry Archive Test")
    print("="*70)
    queries = matcher.generate_jira_queries(
        test_file="cypress/tests/e2e/modelRegistry/testArchiveModels.cy.ts",
        test_name="Verify that models and versions can be archived and restored via model registry",
        error_message="Timed out retrying after 10000ms: expected false to be true at modelRegistryUtils.ts:18"
    )

    for i, q in enumerate(queries, 1):
        print(f"\nQuery {i}: {q['name']}")
        print(f"  Description: {q['description']}")
        print(f"  Keyword: {q['query']}")
        print(f"  Components: {', '.join(q['components']) if q['components'] else 'None'}")
        print(f"  JQL: {q['jql']}")

    # Example 2: Pipeline test
    print("\n" + "="*70)
    print("Example 2: Pipeline Scheduling Test")
    print("="*70)
    queries = matcher.generate_jira_queries(
        test_file="cypress/tests/e2e/Pipelines/testSchedulePipeline.cy.ts",
        test_name="Schedule a pipeline to run daily",
        error_message="Pipeline schedule failed: cron expression invalid"
    )

    for i, q in enumerate(queries, 1):
        print(f"\nQuery {i}: {q['name']}")
        print(f"  Description: {q['description']}")
        print(f"  Keyword: {q['query']}")
        print(f"  Components: {', '.join(q['components']) if q['components'] else 'None'}")

    # Example 3: Workbench test
    print("\n" + "="*70)
    print("Example 3: Workbench Creation Test")
    print("="*70)
    queries = matcher.generate_jira_queries(
        test_file="cypress/tests/e2e/dataScienceProjects/workbenches/testWorkbenchCreation.cy.ts",
        test_name="Create a new workbench with custom image",
        error_message="Error: Image jupyter-minimal-notebook:latest not found"
    )

    for i, q in enumerate(queries, 1):
        print(f"\nQuery {i}: {q['name']}")
        print(f"  Description: {q['description']}")
        print(f"  Keyword: {q['query']}")
