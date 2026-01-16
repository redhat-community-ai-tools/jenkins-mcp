"""
Artifact Parser - Parse Jenkins artifacts and test results
"""
import json
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class TestFailure:
    """Represents a failed test"""
    test_name: str
    test_file: str
    error_message: str
    stack_trace: str
    suite: str
    duration: Optional[float] = None
    screenshot_path: Optional[str] = None
    video_path: Optional[str] = None


@dataclass
class TestResult:
    """Represents a test run result"""
    job_name: str
    build_number: int
    build_url: str
    timestamp: int
    status: str  # SUCCESS, FAILURE, UNSTABLE
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    duration: float
    failures: List[TestFailure]


class ArtifactParser:
    """Parser for Jenkins artifacts and Cypress test results"""

    def parse_build_log(self, log_content: str) -> Dict[str, Any]:
        """
        Parse Jenkins build log to extract test information

        Returns structured data about test execution
        """
        result = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'failures': [],
            'errors': [],
            'warnings': []
        }

        # Common Cypress patterns
        test_summary_pattern = r'(\d+) passing.*?(\d+) failing'
        test_failure_pattern = r'\d+\)\s+(.+?):\s*\n\s+(.+?)(?=\n\n|\n\s+at|\Z)'
        error_pattern = r'Error:\s+(.+?)(?=\n|$)'

        # Extract test summary
        summary_match = re.search(test_summary_pattern, log_content, re.MULTILINE)
        if summary_match:
            result['passed_tests'] = int(summary_match.group(1))
            result['failed_tests'] = int(summary_match.group(2))
            result['total_tests'] = result['passed_tests'] + result['failed_tests']

        # Extract failure details
        for match in re.finditer(test_failure_pattern, log_content, re.MULTILINE | re.DOTALL):
            test_name = match.group(1).strip()
            error_msg = match.group(2).strip()
            result['failures'].append({
                'test': test_name,
                'error': error_msg
            })

        # Extract general errors
        for match in re.finditer(error_pattern, log_content):
            result['errors'].append(match.group(1))

        return result

    def parse_cypress_json_results(self, json_content: str) -> Dict[str, Any]:
        """
        Parse Cypress JSON test results

        Cypress typically outputs results in mochawesome format
        """
        try:
            data = json.loads(json_content)

            result = {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'skipped_tests': 0,
                'pending_tests': 0,
                'duration': 0,
                'failures': []
            }

            # Handle mochawesome format
            if 'stats' in data:
                stats = data['stats']
                result['total_tests'] = stats.get('tests', 0)
                result['passed_tests'] = stats.get('passes', 0)
                result['failed_tests'] = stats.get('failures', 0)
                result['skipped_tests'] = stats.get('skipped', 0)
                result['pending_tests'] = stats.get('pending', 0)
                result['duration'] = stats.get('duration', 0)

            # Extract failure details
            if 'results' in data:
                for suite_result in data['results']:
                    self._extract_failures_from_suite(suite_result, result['failures'])

            return result

        except json.JSONDecodeError:
            return {'error': 'Invalid JSON format'}

    def _extract_failures_from_suite(self, suite: Dict[str, Any], failures: List[Dict[str, Any]]):
        """Recursively extract failures from test suites"""
        # Process tests in this suite
        for test in suite.get('tests', []):
            if test.get('fail', False) or test.get('state') == 'failed':
                failure = {
                    'title': test.get('title', 'Unknown'),
                    'fullTitle': test.get('fullTitle', test.get('title', 'Unknown')),
                    'suite': suite.get('title', 'Unknown Suite'),
                    'file': suite.get('file', 'Unknown'),
                    'duration': test.get('duration', 0),
                    'error': test.get('err', {}).get('message', 'No error message'),
                    'stack': test.get('err', {}).get('stack', ''),
                }
                failures.append(failure)

        # Process nested suites
        for nested_suite in suite.get('suites', []):
            self._extract_failures_from_suite(nested_suite, failures)

    def parse_junit_xml(self, xml_content: str) -> Dict[str, Any]:
        """
        Parse JUnit XML test results using proper XML parsing

        Handles both <testsuites> (root) and nested <testsuite> elements
        """
        result = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'failures': []
        }

        try:
            root = ET.fromstring(xml_content)

            # Get totals from root <testsuites> element
            if root.tag == 'testsuites':
                result['total_tests'] = int(root.get('tests', 0))
                result['failed_tests'] = int(root.get('failures', 0))
                result['skipped_tests'] = int(root.get('skipped', 0))
            elif root.tag == 'testsuite':
                result['total_tests'] = int(root.get('tests', 0))
                result['failed_tests'] = int(root.get('failures', 0))
                result['skipped_tests'] = int(root.get('skipped', 0))

            result['passed_tests'] = result['total_tests'] - result['failed_tests'] - result['skipped_tests']

            # Extract all failures from all testsuites
            for testsuite in root.findall('.//testsuite'):
                suite_name = testsuite.get('name', 'Unknown Suite')

                for testcase in testsuite.findall('testcase'):
                    failure_elem = testcase.find('failure')

                    if failure_elem is not None:
                        test_name = testcase.get('name', 'Unknown Test')
                        classname = testcase.get('classname', '')

                        # Get failure message and CDATA content
                        failure_message = failure_elem.get('message', '')
                        failure_text = failure_elem.text or ''

                        # Combine message and text for full error
                        full_error = failure_message
                        if failure_text:
                            full_error += '\n' + failure_text

                        result['failures'].append({
                            'test': test_name,
                            'fullTitle': f"{suite_name} {test_name}",
                            'suite': suite_name,
                            'class': classname,
                            'error': full_error.strip(),
                            'stack': failure_text,
                            'file': testcase.get('file', '')
                        })

            return result

        except ET.ParseError as e:
            print(f"XML Parse Error: {e}")
            return {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'skipped_tests': 0,
                'failures': [],
                'error': f'XML Parse Error: {e}'
            }

    def extract_test_file_path(self, test_name: str, failure_message: str, file_attr: str = "") -> Optional[str]:
        """
        Extract the test file path from test name, failure message, or file attribute

        Example: "modelRegistry/testArchiveModels.cy.ts" -> "cypress/tests/e2e/modelRegistry/testArchiveModels.cy.ts"
        """
        # First try the file attribute from XML
        if file_attr and '.cy.ts' in file_attr:
            return file_attr

        # Pattern to find .cy.ts files
        file_pattern = r'([a-zA-Z0-9_/-]+\.cy\.ts)'
        combined_text = test_name + ' ' + failure_message + ' ' + file_attr

        match = re.search(file_pattern, combined_text)

        if match:
            file_path = match.group(1)
            # If it doesn't have the full path, construct it
            if not file_path.startswith('cypress/'):
                return f"cypress/tests/e2e/{file_path}"
            return file_path

        # Try to infer from suite name
        # Example: "Verify that models and versions can be archived" -> modelRegistry
        suite_keywords = {
            'model registry': 'modelRegistry',
            'pipeline': 'pipelines',
            'workbench': 'workbenches',
            'storage': 'storage',
            'notebook': 'notebooks'
        }

        for keyword, folder in suite_keywords.items():
            if keyword in test_name.lower():
                return f"cypress/tests/e2e/{folder}/unknown.cy.ts"

        return None

    def categorize_failure(self, failure: Dict[str, Any]) -> str:
        """
        Categorize the type of failure based on error message

        Categories:
        - timeout: Test timed out
        - assertion: Assertion failure
        - element_not_found: Element not found in DOM
        - network: Network/API error
        - auth: Authentication/permission error
        - resource: Cluster resource issue
        - unknown: Unknown error
        """
        error_msg = failure.get('error', '').lower()
        stack = failure.get('stack', '').lower()
        combined = error_msg + ' ' + stack

        if 'timeout' in combined or 'timed out' in combined:
            return 'timeout'
        elif 'expected' in combined and ('to' in combined or 'should' in combined):
            return 'assertion'
        elif 'not found' in combined or 'does not exist' in combined or 'could not find' in combined:
            return 'element_not_found'
        elif 'network' in combined or 'fetch' in combined or 'xhr' in combined or 'api' in combined:
            return 'network'
        elif 'auth' in combined or 'permission' in combined or 'unauthorized' in combined:
            return 'auth'
        elif 'pod' in combined or 'deployment' in combined or 'service' in combined or 'namespace' in combined:
            return 'resource'
        else:
            return 'unknown'

    def build_test_result(
        self,
        job_name: str,
        build_number: int,
        build_url: str,
        build_data: Dict[str, Any],
        parsed_results: Dict[str, Any]
    ) -> TestResult:
        """Build a TestResult object from parsed data"""
        failures = []

        for failure_data in parsed_results.get('failures', []):
            test_file = self.extract_test_file_path(
                failure_data.get('fullTitle', failure_data.get('test', '')),
                failure_data.get('error', ''),
                failure_data.get('file', '')
            )

            failure = TestFailure(
                test_name=failure_data.get('fullTitle', failure_data.get('test', 'Unknown')),
                test_file=test_file or 'cypress/tests/e2e/modelRegistry/testArchiveModels.cy.ts',
                error_message=failure_data.get('error', 'No error message'),
                stack_trace=failure_data.get('stack', ''),
                suite=failure_data.get('suite', 'Unknown Suite'),
                duration=failure_data.get('duration')
            )
            failures.append(failure)

        return TestResult(
            job_name=job_name,
            build_number=build_number,
            build_url=build_url,
            timestamp=build_data.get('timestamp', 0),
            status=build_data.get('result', 'UNKNOWN'),
            total_tests=parsed_results.get('total_tests', 0),
            passed_tests=parsed_results.get('passed_tests', 0),
            failed_tests=parsed_results.get('failed_tests', 0),
            skipped_tests=parsed_results.get('skipped_tests', 0),
            duration=parsed_results.get('duration', 0),
            failures=failures
        )
