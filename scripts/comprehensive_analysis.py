"""
COMPREHENSIVE ANALYSIS V3 - Sync Detection Edition
Implements all requested improvements:
1. General pipeline failure parser (ANY stage failure)
2. High-level image extraction (FBC fragment, IIB, dashboard)
3. Tracer tool integration for all images
4. Screenshot detection and embedding (including retries)
5. Modern, exciting report template
6. "Tests not executed" vs "tests passed" distinction
7. Dashboard commit sync issue detection (CRITICAL!)
8. Image registry type analysis (production vs development)
9. Prominent sync status warnings in reports
10. Test/code mismatch alerts
"""
import asyncio
import httpx
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file if it exists
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

from analyzer import jenkins_client, artifact_parser, failure_analyzer, jira_client, cluster_inspector
from analyzer.config import Config


def extract_all_deployed_images(console_output: str) -> dict:
    """
    Extract ALL deployed images from console output.
    Looks for:
    - FBC fragment: quay.io/rhoai/rhoai-fbc-fragment@sha256:...
    - IIB: brew.registry.redhat.io/rh-osbs/iib:XXXXX
    - Dashboard: quay.io/rhoai/odh-dashboard-rhel8@sha256:...
    """
    images = {
        'fbc_fragment': None,
        'iib': None,
        'dashboard': None,
        'operator_bundle': None
    }

    if not console_output:
        return images

    # Pattern for quay.io images with sha256 digest
    quay_pattern = r'(quay\.io/rhoai/[^@\s]+@sha256:[a-f0-9]{64})'
    for match in re.finditer(quay_pattern, console_output):
        image_uri = match.group(1)

        if 'fbc-fragment' in image_uri:
            images['fbc_fragment'] = image_uri
        elif 'odh-dashboard' in image_uri:
            images['dashboard'] = image_uri
        elif 'operator-bundle' in image_uri:
            images['operator_bundle'] = image_uri

    # Pattern for brew IIB images
    iib_pattern = r'(brew\.registry\.redhat\.io/rh-osbs/iib:\d+)'
    match = re.search(iib_pattern, console_output)
    if match:
        images['iib'] = match.group(1)

    return images


def get_image_metadata_with_tracer(image_uri: str) -> dict:
    """
    Use tracer tool to get complete image metadata.
    Returns: build date, commit info, RHOAI version, etc.
    """
    tracer_path = os.getenv("TRACER_PATH", "/path/to/tracer/tracer.sh")

    metadata = {
        'full_image_uri': image_uri,
        'build_date': None,
        'rhoai_version': None,
        'commit_sha_full': None,
        'commit_url': None,
        'error': None,
        'raw_output': None
    }

    if not image_uri:
        metadata['error'] = "No image URI provided"
        return metadata

    if not os.path.exists(tracer_path):
        metadata['error'] = f"Tracer tool not found at {tracer_path}"
        return metadata

    try:
        # Run tracer with -c flag to show commit info
        result = subprocess.run(
            [tracer_path, '-i', image_uri, '-c'],
            capture_output=True,
            text=True,
            timeout=60
        )

        metadata['raw_output'] = result.stdout

        if result.returncode != 0:
            metadata['error'] = f"Tracer failed (exit code {result.returncode}): {result.stderr}"
            return metadata

        # Parse tracer output
        # Expected format:
        # Image-URI              quay.io/rhoai/...
        # Build-Date             2025-11-18T14:23:45Z
        # RHOAI-Version          2.17
        # odh-dashboard          https://github.com/.../tree/SHA

        for line in result.stdout.strip().split('\n'):
            parts = line.split(None, 1)  # Split on first whitespace only
            if len(parts) < 2:
                continue

            key = parts[0].strip()
            value = parts[1].strip()

            if key == 'Image-URI':
                metadata['full_image_uri'] = value
            elif key == 'Build-Date':
                metadata['build_date'] = value
            elif key == 'RHOAI-Version':
                metadata['rhoai_version'] = value
            elif key == 'odh-dashboard' or 'dashboard' in key.lower():
                # Format: https://github.com/opendatahub-io/odh-dashboard/tree/SHA
                metadata['commit_url'] = value
                if '/tree/' in value:
                    metadata['commit_sha_full'] = value.split('/tree/')[-1]

        return metadata

    except subprocess.TimeoutExpired:
        metadata['error'] = "Tracer command timed out after 60s"
    except Exception as e:
        metadata['error'] = f"Tracer error: {str(e)}"

    return metadata


def analyze_pipeline_failure_general(console_output: str, build_result: str) -> dict:
    """
    GENERAL pipeline failure detection - detects ANY failed stage dynamically.

    Parses console output for patterns:
    1. "script returned exit code X : <STAGE_NAME> : Shell Script"
    2. Java/Groovy exceptions from Jenkins pipeline

    This works for ALL pipeline stages, not just specific ones.
    """
    failure_info = {
        'is_deployment_failure': False,
        'failed_step': None,
        'error_details': None,
        'exception_type': None,
        'exception_message': None,
        'exception_location': None,
        'known_issue': None,
        'needs_cluster_analysis': False,
        'all_failed_stages': []  # Track ALL failures, not just the first
    }

    if build_result == 'SUCCESS':
        return failure_info

    if not console_output:
        return failure_info

    # PATTERN 1: Java/Groovy exceptions (most detailed, check first)
    # Look for "java.lang.Exception:" pattern
    # Use [a-zA-Z.]+ to match package names with dots (not \w which doesn't include dots)
    java_exception_pattern = r'(java\.[a-zA-Z.]+Exception):\s*(.+?)(?:\n|$)'
    java_match = re.search(java_exception_pattern, console_output)

    if java_match:
        exception_type = java_match.group(1)
        exception_message = java_match.group(2).strip()

        failure_info['is_deployment_failure'] = True
        failure_info['exception_type'] = exception_type
        failure_info['exception_message'] = exception_message

        # Extract the method/location from stack trace if available
        location_pattern = r'at\s+(\w+)\.call\(([^)]+)\)'
        location_matches = re.findall(location_pattern, console_output)
        if location_matches:
            # Get the most relevant ones (first 3)
            failure_info['exception_location'] = location_matches[:3]
            # Use the first location for failed_step
            failure_info['failed_step'] = location_matches[0][0] if location_matches else 'Unknown'

        failure_info['error_details'] = f'{exception_type}: {exception_message}'
        failure_info['needs_cluster_analysis'] = True

        # Check for known exception patterns
        if 'Cannot find cluster config' in exception_message:
            failure_info['known_issue'] = None  # No specific Jira issue for this yet
            failure_info['failed_step'] = 'Cluster Configuration'

    # PATTERN 2: Shell script exit code failures
    if not failure_info['is_deployment_failure']:
        pattern = r'script returned exit code (\d+) : ([^:]+) :'
        matches = re.findall(pattern, console_output)

        if matches:
            # Track all failures
            for exit_code, stage_name in matches:
                failure_info['all_failed_stages'].append({
                    'stage': stage_name.strip(),
                    'exit_code': int(exit_code)
                })

            # Use the LAST failure as the primary one (most relevant)
            exit_code, stage_name = matches[-1]
            failure_info['is_deployment_failure'] = True
            failure_info['failed_step'] = stage_name.strip()
            failure_info['error_details'] = f'Stage exited with code {exit_code}'
            failure_info['needs_cluster_analysis'] = True

            # Check if it's a KNOWN issue
            known_issues = {
                'Verify Dashboard is Ready': 'RHOAIENG-38766',
                'Verify Cluster is Ready': None,
                'Install ODH Operator': None,
                'Setup OpenShift Local Cluster': None,
                # Add more as discovered
            }

            failure_info['known_issue'] = known_issues.get(stage_name.strip())

    # PATTERN 3: Error signal messages with stage names
    if not failure_info['is_deployment_failure']:
        # Look for patterns like "failed, retrying : Install ODH Operator : Error signal"
        error_signal_pattern = r': ([^:]+?) : Error signal'
        matches = re.findall(error_signal_pattern, console_output)
        
        if matches:
            # Use the most common stage name mentioned
            stage_name = matches[-1].strip()
            failure_info['is_deployment_failure'] = True
            failure_info['failed_step'] = stage_name
            failure_info['error_details'] = f'Stage "{stage_name}" failed with error signal'
            failure_info['needs_cluster_analysis'] = True
            
            # Check if it's a KNOWN issue
            known_issues = {
                'Verify Dashboard is Ready': 'RHOAIENG-38766',
                'Verify Cluster is Ready': None,
                'Install ODH Operator': None,
                'Install RHOAI Operator': None,
                'Setup OpenShift Local Cluster': None,
            }
            failure_info['known_issue'] = known_issues.get(stage_name)

    # PATTERN 4: Post Actions failure (happens AFTER tests run)
    # Post Actions fails when tests fail - this is NOT a deployment/pipeline failure!
    # We should NOT show this as a "Pipeline Failure" - the tests ran, they just failed.
    if not failure_info['is_deployment_failure'] and 'Post Actions' in console_output:
        # Post Actions failure = tests ran but some failed
        # This is EXPECTED behavior when tests fail - don't mark as deployment failure
        failure_info['is_deployment_failure'] = False  # NOT a deployment failure!
        failure_info['failed_step'] = None  # No pipeline step failed
        failure_info['error_details'] = None
        failure_info['needs_cluster_analysis'] = False
        failure_info['is_post_test_failure'] = True  # Just flag it for reference
    
    # PATTERN 5: Generic build failure
    # Skip if this is a post-test failure (tests ran but failed - that's not a pipeline failure)
    if not failure_info['is_deployment_failure'] and not failure_info.get('is_post_test_failure') and build_result in ['FAILURE', 'UNSTABLE']:
        failure_info['is_deployment_failure'] = True
        failure_info['failed_step'] = 'Unknown pipeline step'
        failure_info['error_details'] = 'Build failed but specific step not identified'
        failure_info['needs_cluster_analysis'] = True

    return failure_info


def extract_test_keywords(filename: str) -> set:
    """
    Extract meaningful keywords from a test filename for fuzzy matching.
    
    Examples:
    - 'testWorkbenchCreation.cy.ts' -> {'workbench', 'creation'}
    - 'workbenches.cy.ts' -> {'workbench'}
    - 'testCreateConnectionTypes.cy.ts' -> {'create', 'connection', 'type'}
    - 'connectionTypes.cy.ts' -> {'connection', 'type'}
    """
    if not filename:
        return set()
    
    # Remove extension and path
    name = os.path.basename(filename).replace('.cy.ts', '').replace('.ts', '')
    
    # Remove common prefixes
    name = re.sub(r'^test', '', name, flags=re.IGNORECASE)
    
    # Split camelCase and snake_case
    # 'WorkbenchCreation' -> ['Workbench', 'Creation']
    words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', name)
    
    # Normalize to lowercase and singularize common plurals
    keywords = set()
    for word in words:
        word = word.lower()
        # Simple singularization
        if word.endswith('es') and len(word) > 3:
            keywords.add(word[:-2])  # workbenches -> workbench
        elif word.endswith('s') and len(word) > 3:
            keywords.add(word[:-1])  # types -> type
        keywords.add(word)
    
    # Filter out very short or common words
    keywords = {k for k in keywords if len(k) > 2 and k not in {'test', 'the', 'and', 'for'}}
    
    return keywords


def test_files_match(test_file: str, screenshot_file: str, test_name: str = "") -> bool:
    """
    Check if a test file matches a screenshot file using smart keyword matching.
    
    Returns True if:
    1. Exact basename match, OR
    2. Significant keyword overlap between files, OR
    3. Test name keywords match screenshot path
    """
    if not test_file or not screenshot_file:
        return False
    
    test_basename = os.path.basename(test_file)
    screenshot_basename = os.path.basename(screenshot_file)
    
    # 1. Exact match
    if test_basename == screenshot_basename:
        return True
    
    # 2. Keyword overlap matching
    test_keywords = extract_test_keywords(test_file)
    screenshot_keywords = extract_test_keywords(screenshot_file)
    
    if test_keywords and screenshot_keywords:
        # Check for significant overlap
        overlap = test_keywords & screenshot_keywords
        # Match if at least one significant keyword overlaps
        # (significant = longer than 4 chars to avoid matching 'test', 'type', etc. alone)
        significant_overlap = {k for k in overlap if len(k) > 4}
        if significant_overlap:
            return True
        # Also match if multiple shorter keywords overlap
        if len(overlap) >= 2:
            return True
    
    # 3. Check test name against screenshot path (fallback)
    if test_name:
        test_name_lower = test_name.lower()
        screenshot_lower = screenshot_file.lower()
        # Extract key concepts from test name
        key_concepts = ['workbench', 'connection', 'model', 'pipeline', 'storage', 
                       'project', 'registry', 'nim', 'serving', 'runtime']
        for concept in key_concepts:
            if concept in test_name_lower and concept in screenshot_lower:
                return True
    
    return False


async def get_test_failure_screenshots(jenkins_cli, job_path: str, build_num: int, test_name: str, test_file: str = None) -> list:
    """
    Find screenshots for a specific failed test, including retry attempts.
    Uses smart keyword matching to find screenshots even when file names differ slightly.

    Cypress saves screenshots as:
    - screenshots/<spec-name>/<test-name>.png
    - screenshots/<spec-name>/<test-name> (attempt 2).png
    - screenshots/<spec-name>/<test-name> (attempt 3).png
    """
    screenshots = []

    try:
        artifacts = await jenkins_cli.list_artifacts(job_path, build_num)

        for artifact in artifacts:
            rel_path = artifact.get('relativePath', '')

            # Look for screenshots directory
            if 'screenshots' in rel_path and rel_path.endswith('.png'):
                # Extract actual test file from screenshot path
                actual_test_file = None
                if '.cy.ts' in rel_path:
                    # Extract from path like: screenshots/dataScienceProjects/models/testModelStopStart.cy.ts/...
                    match = re.search(r'screenshots/(.+?\.cy\.ts)/', rel_path)
                    if match:
                        actual_test_file = f"cypress/tests/e2e/{match.group(1)}"
                
                # Smart matching: use keyword-based matching instead of strict basename comparison
                if test_file and actual_test_file:
                    if not test_files_match(test_file, actual_test_file, test_name):
                        continue  # Skip - doesn't match our test
                
                # Fallback: If no test_file provided, use loose name matching
                elif not test_file or 'unknown' in test_file:
                    test_normalized = test_name.lower().replace(' ', '_').replace('-', '_')
                    path_normalized = rel_path.lower().replace(' ', '_').replace('-', '_')
                    test_words = test_normalized.split('_')
                    if not any(word in path_normalized for word in test_words if len(word) > 4):
                        continue  # Skip - doesn't match test name

                # Build screenshot URL
                screenshot_url = f"{jenkins_cli.jenkins_url}/job/{job_path.replace('/', '/job/')}/{build_num}/artifact/{rel_path}"

                screenshots.append({
                    'path': rel_path,
                    'url': screenshot_url,
                    'name': os.path.basename(rel_path),
                    'is_retry': 'attempt' in rel_path.lower(),
                    'test_file': actual_test_file
                })

    except Exception as e:
        print(f"  Warning: Could not fetch screenshots: {e}")

    # Sort: original first, then retries
    screenshots.sort(key=lambda x: (x['is_retry'], x['name']))

    return screenshots


def extract_dashboard_commit(console_output: str) -> dict:
    """Extract dashboard commit info from Jenkins console (legacy fallback)"""
    commit_info = {
        'commit_hash': None,
        'commit_date': None,
        'branch': None
    }

    if not console_output:
        return commit_info

    # Look for git commit patterns
    for line in console_output.split('\n'):
        # Pattern: "Dashboard commit: abc123def"
        if 'dashboard' in line.lower() and ('commit' in line.lower() or 'sha' in line.lower()):
            match = re.search(r'([a-f0-9]{7,40})', line)
            if match:
                commit_info['commit_hash'] = match.group(1)[:8]

        # Pattern: "Branch: main" or "ref: refs/heads/main"
        if 'branch' in line.lower() or 'ref' in line.lower():
            if 'main' in line.lower():
                commit_info['branch'] = 'main'
            elif 'master' in line.lower():
                commit_info['branch'] = 'master'

    return commit_info


def check_git_diff_for_test(test_file: str, image_commit: str, repo_path: str) -> dict:
    """Check if test file changed between image commit and main"""
    result = {
        'file_changed': False,
        'commits_behind': 0,
        'main_commit': None,
        'quarantined': False,
        'needs_maintenance': False,
        'bug_references': [],
        'current_test_content': None,
        'image_test_content': None
    }

    try:
        # Get current main commit
        main_result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if main_result.returncode == 0:
            result['main_commit'] = main_result.stdout.strip()[:8]

        # If we have image commit, check diff
        if image_commit:
            # Count commits between image and main
            count_result = subprocess.run(
                ['git', 'rev-list', '--count', f'{image_commit}..HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if count_result.returncode == 0:
                result['commits_behind'] = int(count_result.stdout.strip())

            # Check if test file changed
            diff_result = subprocess.run(
                ['git', 'diff', '--name-only', image_commit, 'HEAD', '--', test_file],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if diff_result.returncode == 0 and diff_result.stdout.strip():
                result['file_changed'] = True

        # Read current test file content to check for tags
        full_test_path = os.path.join(repo_path, 'frontend/src/__tests__/cypress', test_file)
        if os.path.exists(full_test_path):
            with open(full_test_path, 'r') as f:
                content = f.read()
                result['current_test_content'] = content

                # Check for @Bug tag (product bug)
                if '@Bug' in content:
                    result['quarantined'] = True
                    bug_matches = re.findall(r'Product Bug[:\- ]+([A-Z]+-\d+)', content, re.IGNORECASE)
                    result['bug_references'].extend(bug_matches)

                # Check for @Maintain tag (automation bug)
                if '@Maintain' in content:
                    result['needs_maintenance'] = True
                    auto_matches = re.findall(r'Automation Bug[:\- ]+([A-Z]+-\d+)', content, re.IGNORECASE)
                    result['bug_references'].extend(auto_matches)

    except Exception as e:
        print(f"  Warning: Could not analyze git diff: {e}")

    return result


def extract_test_name_from_it_block(test_file_path: str) -> str:
    """
    Extract the actual test name from the it() or describe() block in the test file.
    
    Priority:
    1. Look for it() blocks with test names
    2. Look for describe() blocks as fallback
    3. Extract from file name as last resort (e.g., testClusterAdminSettings from testClusterAdminSettings.cy.ts)
    """
    try:
        if not os.path.exists(test_file_path):
            # If file doesn't exist, try to extract from path
            filename = os.path.basename(test_file_path)
            if filename.startswith('test') and filename.endswith('.cy.ts'):
                # Extract testClusterAdminSettings from testClusterAdminSettings.cy.ts
                return filename.replace('.cy.ts', '')
            return None
            
        with open(test_file_path, 'r') as f:
            content = f.read()
            
            # Try to find it() blocks first (most specific)
            # Handles: it('test name', () => {})
            it_patterns = [
                r'''it\s*\(\s*['"]([^'"]+)['"]''',  # Standard it('name')
                r'''it\.only\s*\(\s*['"]([^'"]+)['"]''',  # it.only('name')
                r'''it\.skip\s*\(\s*['"]([^'"]+)['"]''',  # it.skip('name')
            ]
            
            for pattern in it_patterns:
                match = re.search(pattern, content)
                if match:
                    return match.group(1)
            
            # Try describe() blocks as fallback
            describe_match = re.search(r'''describe\s*\(\s*['"]([^'"]+)['"]''', content)
            if describe_match:
                return describe_match.group(1)
            
            # Last resort: extract from filename
            filename = os.path.basename(test_file_path)
            if filename.startswith('test') and filename.endswith('.cy.ts'):
                # Extract testClusterAdminSettings from testClusterAdminSettings.cy.ts
                return filename.replace('.cy.ts', '')
                
    except Exception as e:
        print(f"  Warning: Could not extract test name from {test_file_path}: {e}")
        # Try to extract from path even on error
        try:
            filename = os.path.basename(test_file_path)
            if filename.startswith('test') and filename.endswith('.cy.ts'):
                return filename.replace('.cy.ts', '')
        except:
            pass
    
    return None


def improved_file_extraction(test_name: str, suite_name: str) -> str:
    """Better test file path extraction - comprehensive mapping for all test types"""
    combined = (test_name + ' ' + suite_name).lower()

    # Gen AI tests - MUST come FIRST (before connection tests, because "Gen AI...Connection" contains "connection")
    if 'gen ai' in combined or 'genai' in combined or 'llamastack' in combined or 'gen ai studio' in combined:
        return "cypress/tests/e2e/gen-ai/testGenAi.cy.ts"
    
    # Model stop/start tests - MUST come before general model tests
    if 'model' in combined and ('stop' in combined or 'start' in combined):
        return "cypress/tests/e2e/dataScienceProjects/models/testModelStopStart.cy.ts"
    
    # ISV/Explore tests
    if 'isv' in combined or 'explore' in combined:
        return "cypress/tests/e2e/applications/explore/testEnabledISVs.cy.ts"
    
    # Workbenches - tolerations tests (must come before general workbench tests)
    if 'workbench' in combined and 'toleration' in combined:
        return "cypress/tests/e2e/settings/hardwareProfiles/testWorkbenchTolerations.cy.ts"

    # Storage tests
    if 'cluster storage' in combined:
        if 'access mode' in combined:
            return "cypress/tests/e2e/dataScienceProjects/clusterStorage/testClusterStorageAccessModes.cy.ts"
        else:
            return "cypress/tests/e2e/dataScienceProjects/clusterStorage/testClusterStorageCreation.cy.ts"

    # Connection tests (must come after Gen AI tests)
    if 'connection' in combined:
        if 'type' in combined:
            return "cypress/tests/e2e/settings/connectionTypes/connectionTypes.cy.ts"
        else:
            return "cypress/tests/e2e/dataScienceProjects/connections/testConnectionCreation.cy.ts"

    # Workbench tests
    if 'workbench' in combined:
        if 'variable' in combined:
            return "cypress/tests/e2e/dataScienceProjects/workbenches/testWorkbenchVariables.cy.ts"
        elif 'storage' in combined:
            return "cypress/tests/e2e/dataScienceProjects/workbenches/testWorkbenchStorageClasses.cy.ts"
        elif 'creation' in combined:
            return "cypress/tests/e2e/dataScienceProjects/workbenches/testWorkbenchCreation.cy.ts"
        elif 'status' in combined:
            return "cypress/tests/e2e/dataScienceProjects/workbenches/testWorkbenchStatus.cy.ts"
        elif 'image' in combined:
            return "cypress/tests/e2e/dataScienceProjects/workbenches/testWorkbenchImages.cy.ts"
        elif 'control' in combined:
            return "cypress/tests/e2e/dataScienceProjects/workbenches/testWorkbenchControlSuite.cy.ts"
        elif 'negative' in combined:
            return "cypress/tests/e2e/dataScienceProjects/workbenches/testWorkbenchNegativeTests.cy.ts"
        else:
            return "cypress/tests/e2e/dataScienceProjects/workbenches/workbenches.cy.ts"

    # Model Registry tests
    if 'model' in combined or 'registry' in combined:
        if 'archive' in combined:
            return "cypress/tests/e2e/modelRegistry/testArchiveModels.cy.ts"
        elif 'register' in combined:
            return "cypress/tests/e2e/modelRegistry/testRegisterModel.cy.ts"
        elif 'deploy' in combined:
            return "cypress/tests/e2e/modelRegistry/testRegistryDeployModel.cy.ts"
        elif 'permission' in combined:
            return "cypress/tests/e2e/modelRegistry/testManageRegistryPermissions.cy.ts"
        elif 'create' in combined:
            return "cypress/tests/e2e/modelRegistry/testCreateModelRegistry.cy.ts"
        elif 'edit' in combined:
            return "cypress/tests/e2e/modelRegistry/testAdminEditRegistry.cy.ts"
        else:
            return "cypress/tests/e2e/modelRegistry/testArchiveModels.cy.ts"

    # Serving Runtime tests
    if 'serving' in combined or 'runtime' in combined:
        return "cypress/tests/e2e/settings/servingRuntimes/testSingleServingRuntimeCreation.cy.ts"

    # NIM tests
    if 'nim' in combined:
        return "cypress/tests/e2e/nim/testEnableNIM.cy.ts"

    # Pipeline tests
    if 'pipeline' in combined:
        return "cypress/tests/e2e/pipelines/createRunDeletePipeline.cy.ts"

    # Project tests
    if 'project' in combined:
        if 'edit' in combined:
            return "cypress/tests/e2e/dataScienceProjects/testProjectEditing.cy.ts"
        elif 'contributor' in combined or 'permission' in combined:
            return "cypress/tests/e2e/dataScienceProjects/testProjectContributorPermissions.cy.ts"
        else:
            return "cypress/tests/e2e/dataScienceProjects/testProjectEditing.cy.ts"

    # User Management tests
    if 'user' in combined or 'unauthorized' in combined or 'group' in combined:
        if 'spawn' in combined or 'notebook' in combined:
            return "cypress/tests/e2e/settings/userManagement/testUnauthorizedUserNotebookSpawnBlocked.cy.ts"
        elif 'permission' in combined:
            return "cypress/tests/e2e/settings/userManagement/testUnathorizedPermChange.cy.ts"
        elif 'removed' in combined or 'notification' in combined:
            return "cypress/tests/e2e/settings/userManagement/testUserGroupRemovedNotification.cy.ts"

    # Hardware Profile / Toleration tests
    if 'hardware' in combined or 'toleration' in combined:
        if 'workbench' in combined:
            return "cypress/tests/e2e/settings/hardwareProfiles/testWorkbenchTolerations.cy.ts"
        elif 'notebook' in combined:
            return "cypress/tests/e2e/settings/hardwareProfiles/testNotebookTolerations.cy.ts"
        elif 'serving' in combined:
            return "cypress/tests/e2e/settings/hardwareProfiles/testModelServingTolerations.cy.ts"
        else:
            return "cypress/tests/e2e/settings/hardwareProfiles/testHardwareProfiles.cy.ts"

    # Cluster Settings tests
    if 'cluster setting' in combined or 'data collection' in combined:
        if 'data collection' in combined:
            return "cypress/tests/e2e/settings/clusterSettings/testDataCollection.cy.ts"
        else:
            return "cypress/tests/e2e/settings/clusterSettings/testAdminClusterSettings.cy.ts"

    # Storage Classes tests
    if 'storage class' in combined:
        return "cypress/tests/e2e/storageClasses/storageClasses.cy.ts"

    # Distributed Workload tests
    if 'workload' in combined and 'metric' in combined:
        return "cypress/tests/e2e/distributedWorkloadMetrics/testWorkloadMetricsDefaultPageContents.cy.ts"

    # Application tests
    if 'application' in combined or 'about' in combined:
        return "cypress/tests/e2e/application.cy.ts"

    return "cypress/tests/e2e/unknown.cy.ts"


def compare_errors(original_error: str, rerun_error: str) -> dict:
    """Compare original and rerun errors to see if they're the same"""
    def normalize_error(error):
        if not error:
            return ""
        error = re.sub(r':\d+:\d+', '', error)
        error = re.sub(r'at \S+:\d+', '', error)
        return error.lower().strip()

    norm_original = normalize_error(original_error)
    norm_rerun = normalize_error(rerun_error)

    return {
        'same_error': norm_original == norm_rerun if norm_original and norm_rerun else False,
        'similarity': 'identical' if norm_original == norm_rerun else 'different'
    }


def extract_exception_type(error_message: str) -> str:
    """Extract the exception type from an error message for grouping"""
    if not error_message:
        return "UnknownError"

    # Common patterns
    if 'AssertionError' in error_message:
        return "AssertionError"
    elif 'TimeoutError' in error_message or 'Timed out' in error_message:
        return "TimeoutError"
    elif 'NetworkError' in error_message or 'ECONNREFUSED' in error_message:
        return "NetworkError"
    elif 'ElementNotFound' in error_message or 'Expected to find element' in error_message:
        return "ElementNotFoundError"
    elif 'CypressError' in error_message:
        return "CypressError"
    elif 'ReferenceError' in error_message:
        return "ReferenceError"
    elif 'TypeError' in error_message:
        return "TypeError"
    else:
        # Try to extract first line which usually contains the error type
        first_line = error_message.split('\n')[0].strip()
        if ':' in first_line:
            # Format like "AssertionError: message"
            potential_type = first_line.split(':')[0].strip()
            if 'Error' in potential_type:
                return potential_type
        return "GenericError"


def group_failures_by_exception(failures: list) -> dict:
    """Group test failures by their exception type"""
    groups = {}
    for failure in failures:
        exc_type = extract_exception_type(failure.error_message)
        if exc_type not in groups:
            groups[exc_type] = []
        groups[exc_type].append(failure)
    return groups


async def check_all_namespaces(inspector):
    """Check ALL namespaces for pod health"""
    import subprocess

    all_namespace_health = []

    try:
        result = subprocess.run(
            ['oc', 'get', 'namespaces', '-o', 'jsonpath={.items[*].metadata.name}'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            namespaces = result.stdout.strip().split()

            for ns in namespaces:
                pod_result = subprocess.run(
                    ['oc', 'get', 'pods', '-n', ns, '-o', 'json'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if pod_result.returncode == 0:
                    import json
                    pods_data = json.loads(pod_result.stdout)

                    total_pods = len(pods_data.get('items', []))
                    running_pods = 0
                    failed_pods = 0
                    problems = []

                    for pod in pods_data.get('items', []):
                        pod_name = pod['metadata']['name']
                        status = pod.get('status', {})
                        phase = status.get('phase', 'Unknown')

                        if phase == 'Running':
                            running_pods += 1
                        elif phase in ['Failed', 'CrashLoopBackOff', 'Error']:
                            failed_pods += 1
                            problems.append({
                                'pod': pod_name,
                                'issue': f"Phase: {phase}"
                            })

                    is_cypress_related = 'cypress' in ns.lower()

                    if total_pods > 0:
                        all_namespace_health.append({
                            'namespace': ns,
                            'total_pods': total_pods,
                            'running_pods': running_pods,
                            'failed_pods': failed_pods,
                            'problems': problems,
                            'is_cypress_related': is_cypress_related,
                            'needs_cleanup': is_cypress_related and total_pods > 0
                        })

    except Exception as e:
        print(f"  Warning: Could not check all namespaces: {e}")

    return all_namespace_health


def detect_commit_sync_issues(console_output: str) -> dict:
    """
    Detect when dashboard commit cannot be determined and tests fall back to main.
    This is a CRITICAL issue that causes test/code mismatch.
    """
    issues = {
        'commit_detection_failed': False,
        'fell_back_to_main': False,
        'deployed_image_registry': None,
        'branch_used_for_tests': None,
        'warning_message': None,
        'severity': 'none'
    }

    if not console_output:
        return issues

    # Look for ERROR message about commit detection failure
    if '[ERROR] ODH-Dashboard commit' in console_output and 'could not be determined' in console_output:
        issues['commit_detection_failed'] = True
        issues['severity'] = 'critical'

        # Extract the image URI from error message
        error_pattern = r'\[ERROR\] ODH-Dashboard commit of \'([^\']+)\' could not be determined'
        match = re.search(error_pattern, console_output)
        if match:
            image_uri = match.group(1)
            issues['deployed_image_registry'] = image_uri

            # Detect registry type
            if 'registry.redhat.io' in image_uri:
                issues['warning_message'] = 'Production registry image (registry.redhat.io) lacks commit metadata - tracer cannot extract commit info'
            elif 'quay.io' in image_uri:
                issues['warning_message'] = 'Quay.io image should have metadata - investigate why tracer failed'

    # Look for WARN message about fallback to main
    if 'Fallback to default Branch (main)' in console_output or 'No ODH-Dashboard commit identified' in console_output:
        issues['fell_back_to_main'] = True
        issues['branch_used_for_tests'] = 'main'

        if not issues['warning_message']:
            issues['warning_message'] = 'Tests running against main branch but deployed image commit unknown'

    # If both conditions met, it's a critical sync issue
    if issues['commit_detection_failed'] and issues['fell_back_to_main']:
        issues['severity'] = 'critical'
        issues['warning_message'] = 'CRITICAL: Test/code mismatch - tests run from main but deployed image age unknown!'

    return issues


def analyze_image_registry_type(image_uri: str) -> dict:
    """Determine if image is from production or development registry"""
    registry_info = {
        'registry_type': 'unknown',
        'has_metadata': None,
        'tracer_compatible': None,
        'notes': None
    }

    if not image_uri:
        return registry_info

    if 'registry.redhat.io' in image_uri:
        registry_info['registry_type'] = 'production'
        registry_info['has_metadata'] = False
        registry_info['tracer_compatible'] = False
        registry_info['notes'] = 'Production registry images lack commit metadata for tracer'
    elif 'quay.io' in image_uri:
        registry_info['registry_type'] = 'development'
        registry_info['has_metadata'] = True
        registry_info['tracer_compatible'] = True
        registry_info['notes'] = 'Development registry with full metadata support'
    elif 'brew.registry.redhat.io' in image_uri:
        registry_info['registry_type'] = 'brew'
        registry_info['has_metadata'] = True
        registry_info['tracer_compatible'] = True
        registry_info['notes'] = 'Brew registry for IIB images'

    return registry_info


def check_recent_commits_single_repo(repo_path: str, repo_name: str, hours_back: int = 24) -> list:
    """
    Check a single git repo for recent commits.

    Args:
        repo_path: Path to the git repository
        repo_name: Name/label for this repository (e.g., 'Dashboard', 'Jenkins')
        hours_back: How many hours back to check (default 24)

    Returns:
        List of recent commits with metadata
    """
    recent_commits = []

    try:
        # Get ALL commits (not just merges) with full info
        result = subprocess.run(
            ['git', 'log', f'--since={hours_back} hours ago',
             '--pretty=format:%H|%h|%an|%ae|%ai|%s|%b', '--no-decorate'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('|', 6)
                if len(parts) >= 6:
                    full_sha, short_sha, author, email, timestamp, subject = parts[:6]
                    body = parts[6] if len(parts) > 6 else ''

                    # Extract MR number from commit message if present
                    mr_number = None
                    mr_match = re.search(r'!(\d+)', subject)
                    if mr_match:
                        mr_number = mr_match.group(1)

                    # Check if commit relates to Jenkins/pipeline/tests
                    # For Jenkins repo: ALL commits are pipeline-related by definition
                    # For Dashboard repo: check for specific keywords
                    if repo_name == 'Jenkins':
                        # Jenkins config repo - everything is pipeline-related
                        is_pipeline_related = True
                    else:
                        # Dashboard repo - check for specific keywords
                        is_pipeline_related = any(keyword in subject.lower() or keyword in body.lower()
                                                 for keyword in ['jenkins', 'pipeline', 'ci', 'test', 'cypress',
                                                               'e2e', 'cluster', 'config', 'deploy', 'build'])

                    commit_info = {
                        'sha': short_sha,
                        'full_sha': full_sha,
                        'author': author,
                        'email': email,
                        'timestamp': timestamp,
                        'subject': subject,
                        'body': body[:200] if body else '',  # First 200 chars of body
                        'mr_number': mr_number,
                        'is_pipeline_related': is_pipeline_related,
                        'repository': repo_name  # Track which repo this commit is from
                    }

                    recent_commits.append(commit_info)

        return recent_commits

    except Exception as e:
        print(f"  Warning: Could not check {repo_name} repo: {e}")
        return []


def check_recent_gitlab_merges(dashboard_repo_path: str, jenkins_repo_path: str, hours_back: int = 24) -> list:
    """
    Check BOTH Dashboard and Jenkins repos for recent commits that might have caused pipeline issues.

    Args:
        dashboard_repo_path: Path to the dashboard git repository
        jenkins_repo_path: Path to the Jenkins configuration git repository
        hours_back: How many hours back to check (default 24)

    Returns:
        Combined list of recent commits from both repos, sorted by timestamp (newest first)
    """
    all_commits = []

    # Check Dashboard repository
    print(f"      Checking Dashboard repository...")
    dashboard_commits = check_recent_commits_single_repo(dashboard_repo_path, 'Dashboard', hours_back)
    all_commits.extend(dashboard_commits)
    if dashboard_commits:
        print(f"         Found {len(dashboard_commits)} commit(s) in Dashboard repo")

    # Check Jenkins repository
    print(f"      Checking Jenkins configuration repository...")
    jenkins_commits = check_recent_commits_single_repo(jenkins_repo_path, 'Jenkins', hours_back)
    all_commits.extend(jenkins_commits)
    if jenkins_commits:
        print(f"         Found {len(jenkins_commits)} commit(s) in Jenkins repo")

    # Sort by timestamp (newest first)
    all_commits.sort(key=lambda x: x['timestamp'], reverse=True)

    return all_commits


def is_nightly_cron_build(console_output: str) -> dict:
    """
    Detect if this build was triggered by a nightly cron via rhoai-test-flow.
    
    The nightly cron builds are identified by CLUSTER_NAME parameter:
    - dash-e2e-rhoai for RHOAI nightly
    - dash-e2e-odh for ODH nightly
    
    Returns:
        dict with:
        - is_nightly: True if this is a nightly cron build
        - cluster_name: The cluster name (dash-e2e-rhoai or dash-e2e-odh)
        - triggered_by_test_flow: True if triggered by rhoai-test-flow parent job
    """
    result = {
        'is_nightly': False,
        'cluster_name': None,
        'triggered_by_test_flow': False
    }
    
    if not console_output:
        return result
    
    # Look for CLUSTER_NAME parameter in console output
    cluster_patterns = [
        r'CLUSTER_NAME[=:]\s*["\']?(dash-e2e-rhoai)["\']?',
        r'CLUSTER_NAME[=:]\s*["\']?(dash-e2e-odh)["\']?',
        r'Running.*cluster.*["\']?(dash-e2e-rhoai)["\']?',
        r'Running.*cluster.*["\']?(dash-e2e-odh)["\']?',
    ]
    
    for pattern in cluster_patterns:
        match = re.search(pattern, console_output, re.IGNORECASE)
        if match:
            result['is_nightly'] = True
            result['cluster_name'] = match.group(1)
            break
    
    # Check if this was triggered by rhoai-test-flow
    if 'rhoai-test-flow' in console_output.lower():
        result['triggered_by_test_flow'] = True
    
    # Also check upstream cause
    upstream_pattern = r'Started by upstream project.*rhoai-test-flow'
    if re.search(upstream_pattern, console_output, re.IGNORECASE):
        result['triggered_by_test_flow'] = True
    
    return result


async def find_parent_test_flow_build(jenkins_cli, dashboard_build_num: int, dashboard_build_time: datetime) -> dict:
    """
    Find the parent rhoai-test-flow build that triggered a dashboard-tests build.
    
    Since the nightly crons now run via rhoai-test-flow which triggers dashboard-tests
    as a downstream job, we need to find the parent build for deployment/install failures.
    
    Args:
        jenkins_cli: Jenkins client instance
        dashboard_build_num: The dashboard-tests build number
        dashboard_build_time: When the dashboard-tests build started
        
    Returns:
        dict with parent build info or None if not found
    """
    parent_job_path = Config.RHOAI_TEST_FLOW_JOB_PATH
    
    try:
        # Get recent builds from rhoai-test-flow
        async with httpx.AsyncClient(verify=Config.SSL_VERIFY, timeout=120.0) as client:
            url = f"{jenkins_cli.jenkins_url}/job/{parent_job_path.replace('/', '/job/')}/api/json?tree=builds[number,timestamp,result,description]{{0,20}}"
            
            if ':' in jenkins_cli.jenkins_token:
                username, token = jenkins_cli.jenkins_token.split(':', 1)
                auth = (username, token)
                response = await client.get(url, auth=auth)
            else:
                headers = {"Authorization": f"Bearer {jenkins_cli.jenkins_token}"}
                response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            builds = data.get('builds', [])
            
            # Find the parent build that started shortly before the dashboard-tests build
            # The parent build should have started 0-60 minutes before the dashboard build
            for build in builds:
                build_time = datetime.fromtimestamp(build['timestamp'] / 1000)
                time_diff = (dashboard_build_time - build_time).total_seconds()
                
                # Parent build should have started before (positive time_diff)
                # and within a reasonable window (less than 2 hours before)
                if 0 < time_diff < 7200:  # Within 2 hours
                    # Get console output to verify it triggered the dashboard build
                    console_url = f"{jenkins_cli.jenkins_url}/job/{parent_job_path.replace('/', '/job/')}/{build['number']}/consoleText"
                    
                    if ':' in jenkins_cli.jenkins_token:
                        console_response = await client.get(console_url, auth=auth)
                    else:
                        console_response = await client.get(console_url, headers=headers)
                    
                    if console_response.status_code == 200:
                        console = console_response.text
                        # Check if this parent build triggered our dashboard build
                        if f'dashboard-tests#{dashboard_build_num}' in console or \
                           f'dashboard-tests/{dashboard_build_num}' in console:
                            return {
                                'number': build['number'],
                                'timestamp': build['timestamp'],
                                'result': build.get('result'),
                                'description': build.get('description', ''),
                                'url': f"{jenkins_cli.jenkins_url}/job/{parent_job_path.replace('/', '/job/')}/{build['number']}/",
                                'console_output': console
                            }
            
            return None
            
    except Exception as e:
        print(f"   ⚠ Could not find parent rhoai-test-flow build: {e}")
        return None


def analyze_parent_pipeline_failure(parent_console: str, parent_result: str) -> dict:
    """
    Analyze pipeline failures in the parent rhoai-test-flow job.
    
    This handles failures that occur BEFORE the dashboard tests stage:
    - Cluster setup/configuration
    - Operator installation
    - Dashboard deployment verification
    
    Args:
        parent_console: Console output from the parent rhoai-test-flow build
        parent_result: Build result (SUCCESS, FAILURE, etc.)
        
    Returns:
        dict with failure analysis specific to the parent job
    """
    failure_info = {
        'is_parent_failure': False,
        'failed_step': None,
        'error_details': None,
        'failed_before_tests': False,
        'stages_completed': [],
        'stages_failed': []
    }
    
    if parent_result == 'SUCCESS':
        return failure_info
    
    if not parent_console:
        return failure_info
    
    # Track stage completions in rhoai-test-flow
    stages_to_track = [
        'Configure Cluster',
        'Deploy External DNS',
        'Create IDP',
        'Deploy RHOAI Operator',
        'Deploy ODH Operator',
        'Install Operator',
        'Verify Dashboard is Ready',
        'Trigger Dashboard Cypress Tests'
    ]
    
    for stage in stages_to_track:
        if f'[{stage}]' in parent_console and 'SUCCESS' in parent_console:
            failure_info['stages_completed'].append(stage)
    
    # Check for failures using the general analyzer
    pipeline_failure = analyze_pipeline_failure_general(parent_console, parent_result)
    
    if pipeline_failure['is_deployment_failure']:
        failure_info['is_parent_failure'] = True
        failure_info['failed_step'] = pipeline_failure['failed_step']
        failure_info['error_details'] = pipeline_failure['error_details']
        failure_info['stages_failed'] = pipeline_failure.get('all_failed_stages', [])
        
        # Check if failure happened before tests could run
        test_trigger_stages = ['Trigger Dashboard Cypress Tests', 'Dashboard Cypress Tests']
        failure_info['failed_before_tests'] = not any(
            stage in failure_info['stages_completed'] 
            for stage in test_trigger_stages
        )
    
    return failure_info


async def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python comprehensive_analysis.py <build_number|latest> [odh|rhoai] [--enable-trend]")
        print("\nExamples:")
        print("  python comprehensive_analysis.py 3565 odh")
        print("  python comprehensive_analysis.py latest rhoai          # Auto-finds latest build")
        print("  python comprehensive_analysis.py 3565 odh --enable-trend (for nightly automation)")
        return

    build_arg = sys.argv[1]
    variant = sys.argv[2].upper() if len(sys.argv) > 2 else "ODH"
    enable_trend_analysis = '--enable-trend' in sys.argv
    
    # Create jenkins client for build lookup
    jenkins_cli = jenkins_client.JenkinsClient(
        jenkins_url=os.getenv("JENKINS_URL", "https://your-jenkins-url.example.com"),
        jenkins_token=os.getenv("JENKINS_TOKEN", ""),
        jenkins_username=os.getenv("JENKINS_USER", ""),
        jenkins_password=os.getenv("JENKINS_TOKEN", "")
    )
    
    # Auto-detect latest build if requested
    if build_arg.lower() == "latest":
        print(f"🔍 Finding latest build for {variant}...")
        
        # Use dashboard-tests job - this is where the Cypress test results are
        # (rhoai-test-flow triggers dashboard-tests as a downstream job)
        job_path = Config.DASHBOARD_TESTS_JOB_PATH
        
        # Get recent builds and find the latest for this variant
        async with httpx.AsyncClient(verify=Config.SSL_VERIFY, timeout=120.0) as client:
            url = f"{jenkins_cli.jenkins_url}/job/{job_path.replace('/', '/job/')}/api/json?tree=builds[number,timestamp,result,description]{{0,30}}"
            if ':' in jenkins_cli.jenkins_token:
                username, token = jenkins_cli.jenkins_token.split(':', 1)
                auth = (username, token)
                response = await client.get(url, auth=auth)
            else:
                headers = {"Authorization": f"Bearer {jenkins_cli.jenkins_token}"}
                response = await client.get(url, headers=headers)
            
            response.raise_for_status()
            data = response.json()
            
            # Find the most recent build for this variant
            target_description = f'dash-e2e-{variant.lower()}'
            latest_build = None
            
            for build in data.get('builds', []):
                description = build.get('description', '').lower()
                if target_description in description:
                    latest_build = build
                    break
            
            if not latest_build:
                print(f"❌ Could not find any {variant} builds in recent history")
                sys.exit(1)
            
            build_num = latest_build['number']
            build_time = datetime.fromtimestamp(latest_build['timestamp'] / 1000)
            hours_ago = (datetime.now() - build_time).total_seconds() / 3600
            
            print(f"✅ Found latest {variant} build: #{build_num}")
            print(f"   Build time: {build_time.strftime('%Y-%m-%d %H:%M:%S')} ({hours_ago:.1f} hours ago)")
            print()
    else:
        # Input validation: ensure build_arg is a valid positive integer
        if not build_arg.isdigit():
            print(f"❌ Error: Invalid build number '{build_arg}'")
            print("   Build number must be a positive integer or 'latest'")
            sys.exit(1)
        
        build_num = int(build_arg)
        
        if build_num <= 0:
            print(f"❌ Error: Build number must be a positive integer, got {build_num}")
            sys.exit(1)
        
        # SMART CHECK: Warn if build is old
        print(f"⚠️  Checking if build #{build_num} is recent...")
        
        try:
            build_data = await jenkins_cli.get_build(Config.DASHBOARD_TESTS_JOB_PATH, build_num)
            build_time = datetime.fromtimestamp(build_data['timestamp'] / 1000)
            hours_ago = (datetime.now() - build_time).total_seconds() / 3600
            description = build_data.get('description', '').lower()
            target_description = f'dash-e2e-{variant.lower()}'
            
            # Check if build is more than 48 hours old
            if hours_ago > 48:
                print(f"⚠️  WARNING: Build #{build_num} is {hours_ago:.1f} hours old ({build_time.strftime('%Y-%m-%d %H:%M')})")
                print(f"⚠️  This may not be 'last night's build'!")
                print()
                
                # Find the actual latest build
                async with httpx.AsyncClient(verify=Config.SSL_VERIFY, timeout=120.0) as client:
                    url = f"{jenkins_cli.jenkins_url}/job/{Config.DASHBOARD_TESTS_JOB_PATH.replace('/', '/job/')}/api/json?tree=builds[number,timestamp,description]{{0,20}}"
                    if ':' in jenkins_cli.jenkins_token:
                        username, token = jenkins_cli.jenkins_token.split(':', 1)
                        auth = (username, token)
                        response = await client.get(url, auth=auth)
                    else:
                        headers = {"Authorization": f"Bearer {jenkins_cli.jenkins_token}"}
                        response = await client.get(url, headers=headers)
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    # Find the most recent build for this variant
                    for build in data.get('builds', []):
                        desc = build.get('description', '').lower()
                        if target_description in desc:
                            latest_num = build['number']
                            latest_time = datetime.fromtimestamp(build['timestamp'] / 1000)
                            latest_hours_ago = (datetime.now() - latest_time).total_seconds() / 3600
                            
                            print(f"💡 The actual latest {variant} build is #{latest_num}")
                            print(f"   Build time: {latest_time.strftime('%Y-%m-%d %H:%M')} ({latest_hours_ago:.1f} hours ago)")
                            print()
                            print(f"💡 TIP: Use 'latest' to auto-find the newest build:")
                            print(f"   python comprehensive_analysis.py latest {variant.lower()}")
                            print()
                            break
                
                response = input("Continue with the old build anyway? [y/N]: ")
                if response.lower() != 'y':
                    print("Cancelled. Run with 'latest' to auto-find the newest build.")
                    sys.exit(0)
            
            # Check if build matches the requested variant
            if target_description not in description:
                print(f"⚠️  WARNING: Build #{build_num} does not appear to be a {variant} build")
                print(f"   Description: {description}")
                print(f"   Expected to contain: {target_description}")
                print()
                
                response = input("Continue anyway? [y/N]: ")
                if response.lower() != 'y':
                    print("Cancelled.")
                    sys.exit(0)
            else:
                print(f"✅ Build #{build_num} is a {variant} build from {hours_ago:.1f} hours ago")
                print()
        except Exception as e:
            print(f"⚠️  Could not verify build age: {e}")
            print("Continuing anyway...")
            print()

    jira = jira_client.JiraClient(
        base_url=os.getenv("JIRA_URL", "https://issues.redhat.com"),
        api_token=os.getenv("JIRA_TOKEN", "")
    )

    frontend_repo = os.getenv("FRONTEND_REPO_PATH", "/path/to/odh-dashboard")
    jenkins_repo = os.getenv("JENKINS_REPO_PATH", "/path/to/jenkins")

    # Both ODH and RHOAI builds are in the same dashboard-tests job
    # They are differentiated by build parameters (CLUSTER_NAME), not separate job paths
    # Build numbers are unique per execution in the job
    # Note: Nightly crons now start from rhoai-test-flow which triggers dashboard-tests as downstream
    job_path = Config.DASHBOARD_TESTS_JOB_PATH

    if variant == "ODH":
        name = "ODH"
        github_repo = "opendatahub-io/odh-dashboard"
        cluster_config = cluster_inspector.ClusterInspector.ODH_CONFIG
    else:  # RHOAI
        name = "RHOAI"
        github_repo = "opendatahub-io/odh-dashboard"
        cluster_config = cluster_inspector.ClusterInspector.RHOAI_CONFIG

    print("=" * 100)
    print(f"🚀 COMPREHENSIVE {name} ANALYSIS V3 - Build #{build_num}")
    print("=" * 100)
    print()

    # Step 1: Get build data and console
    print(f"[1/12] 📥 Fetching build data and console output...")
    build_data = await jenkins_cli.get_build(job_path, build_num)
    console_output = await jenkins_cli.get_console_output(job_path, build_num)
    print(f"   ✓ Console output: {len(console_output)} characters")

    # Step 1b: Check if this is a nightly cron build (via rhoai-test-flow)
    nightly_info = is_nightly_cron_build(console_output)
    parent_build = None
    parent_failure = None
    
    if nightly_info['is_nightly']:
        print(f"   📅 Nightly cron build detected: {nightly_info['cluster_name']}")
        
        # Try to find the parent rhoai-test-flow build
        build_timestamp = build_data.get('timestamp', 0) / 1000
        build_time = datetime.fromtimestamp(build_timestamp) if build_timestamp else datetime.now()
        
        print(f"   🔍 Looking for parent rhoai-test-flow build...")
        parent_build = await find_parent_test_flow_build(jenkins_cli, build_num, build_time)
        
        if parent_build:
            print(f"   ✓ Found parent build: #{parent_build['number']} ({parent_build['result']})")
            print(f"   🔗 Parent URL: {parent_build['url']}")
            
            # Analyze parent build for deployment failures
            if parent_build['result'] != 'SUCCESS':
                parent_failure = analyze_parent_pipeline_failure(
                    parent_build.get('console_output', ''),
                    parent_build['result']
                )
                if parent_failure['is_parent_failure']:
                    print(f"   ❌ Parent build failed: {parent_failure['failed_step']}")
                    if parent_failure['failed_before_tests']:
                        print(f"   ⚠️  Failure occurred BEFORE tests could run!")
        else:
            print(f"   ⚠ Could not find parent rhoai-test-flow build")
    else:
        print(f"   ℹ️  Manual/ad-hoc build (not from nightly cron)")

    # Step 2: Extract ALL deployed images
    print(f"\n[2/12] 🔍 Extracting deployed images...")
    deployed_images = extract_all_deployed_images(console_output)
    for img_type, img_uri in deployed_images.items():
        if img_uri:
            print(f"   • {img_type}: {img_uri[:80]}...")

    # Step 3: Use tracer to get image metadata
    print(f"\n[3/12] 🔬 Running tracer on images...")
    image_metadata = {}
    for img_type, img_uri in deployed_images.items():
        if img_uri:
            print(f"   Tracing {img_type}...")
            metadata = get_image_metadata_with_tracer(img_uri)
            image_metadata[img_type] = metadata

            if metadata.get('error'):
                print(f"      ⚠ {metadata['error']}")
            else:
                if metadata.get('build_date'):
                    print(f"      Build date: {metadata['build_date']}")
                if metadata.get('commit_sha_full'):
                    print(f"      Commit: {metadata['commit_sha_full'][:12]}")

    # Fallback: extract dashboard commit from console
    dashboard_commit = extract_dashboard_commit(console_output)

    # Step 3b: Detect dashboard commit sync issues (CRITICAL!)
    print(f"\n[3b/12] 🔄 Checking test/code synchronization...")
    sync_issues = detect_commit_sync_issues(console_output)

    if sync_issues['severity'] == 'critical':
        print(f"   🚨 CRITICAL SYNC ISSUE DETECTED!")
        print(f"      {sync_issues['warning_message']}")
        if sync_issues['deployed_image_registry']:
            print(f"      Image: {sync_issues['deployed_image_registry'][:80]}...")
        if sync_issues['branch_used_for_tests']:
            print(f"      Test branch: {sync_issues['branch_used_for_tests']}")
    elif sync_issues['fell_back_to_main']:
        print(f"   ⚠️  Tests fell back to main branch")
    else:
        print(f"   ✅ No sync issues detected")

    # Step 3c: Analyze image registry types
    print(f"\n[3c/12] 🏷️  Analyzing image registry types...")
    registry_analyses = {}
    for img_type, img_uri in deployed_images.items():
        if img_uri:
            registry_info = analyze_image_registry_type(img_uri)
            registry_analyses[img_type] = registry_info
            if registry_info['registry_type'] != 'unknown':
                print(f"   • {img_type}: {registry_info['registry_type']} ({registry_info['notes']})")

    # Step 4: Analyze pipeline failures (GENERAL)
    print(f"\n[4/12] 🔧 Analyzing pipeline status...")
    build_result = build_data.get('result', 'UNKNOWN')
    pipeline_failure = analyze_pipeline_failure_general(console_output, build_result)

    # Step 4b: Search Jira for pipeline failure issues
    pipeline_jira_issues = []
    if pipeline_failure['is_deployment_failure']:
        print(f"   ❌ Pipeline failure detected!")
        print(f"      Failed step: {pipeline_failure['failed_step']}")
        print(f"      Details: {pipeline_failure['error_details']}")

        # Smart Jira search for this pipeline failure
        print(f"   🔍 Searching Jira for '{pipeline_failure['failed_step']}' issues...")
        try:
            search_terms = []
            failed_step = pipeline_failure['failed_step']

            # Build smart search query based on failed step
            if 'Dashboard' in failed_step and 'Ready' in failed_step:
                search_terms = ['dashboard', 'ready', 'timeout', 'deployment']
            elif 'Cluster' in failed_step and 'Ready' in failed_step:
                search_terms = ['cluster', 'ready', 'timeout', 'openshift']
            elif 'Operator' in failed_step:
                search_terms = ['operator', 'install', 'deployment']
            else:
                # Generic search based on stage name words
                search_terms = failed_step.lower().split()

            # Search Jira using test_name parameter
            search_query = ' '.join(search_terms[:3])  # Use top 3 terms
            jira_results = await jira.search_issues(
                test_name=search_query,
                max_results=10
            )

            # Filter and rank results
            for issue in jira_results:
                # Skip CVEs
                if 'CVE' in issue.get('key', '') or 'CVE' in issue.get('summary', ''):
                    continue

                # Check relevance
                summary_lower = issue.get('summary', '').lower()
                relevance_score = sum(1 for term in search_terms if term.lower() in summary_lower)

                if relevance_score > 0:
                    pipeline_jira_issues.append({
                        'key': issue.get('key'),
                        'summary': issue.get('summary'),
                        'status': issue.get('status'),
                        'url': f"https://issues.redhat.com/browse/{issue.get('key')}",
                        'relevance': relevance_score
                    })

            # Sort by relevance
            pipeline_jira_issues.sort(key=lambda x: x['relevance'], reverse=True)
            pipeline_jira_issues = pipeline_jira_issues[:5]  # Top 5

            if pipeline_jira_issues:
                print(f"      Found {len(pipeline_jira_issues)} related Jira issue(s)")

        except Exception as e:
            print(f"      ⚠ Jira search failed: {e}")

        if pipeline_failure['known_issue']:
            print(f"      Known issue: {pipeline_failure['known_issue']}")
        if len(pipeline_failure['all_failed_stages']) > 1:
            print(f"      Total failed stages: {len(pipeline_failure['all_failed_stages'])}")

        # Step 4c: Check recent GitLab commits if pipeline failed (Dashboard AND Jenkins repos)
        # Calculate hours from build time to now (not just last 24 hours)
        build_timestamp = build_data.get('timestamp', 0) / 1000  # Convert from ms
        build_time = datetime.fromtimestamp(build_timestamp) if build_timestamp else datetime.now()
        hours_since_build = (datetime.now() - build_time).total_seconds() / 3600
        # Look for commits from 48 hours before build to now
        hours_to_check = int(hours_since_build + 48)
        
        print(f"   📋 Checking recent commits (GitHub Dashboard + GitLab Jenkins repos)...")
        print(f"      Build time: {build_time.strftime('%Y-%m-%d %H:%M')}, checking last {hours_to_check}h of commits...")
        recent_merges = check_recent_gitlab_merges(frontend_repo, jenkins_repo, hours_back=hours_to_check)
        
        # Separate Jenkins (can break pipeline) from Dashboard (can only break tests)
        jenkins_commits = [m for m in recent_merges if m['repository'] == 'Jenkins']
        dashboard_commits = [m for m in recent_merges if m['repository'] == 'Dashboard']

        if jenkins_commits:
            print(f"      Found {len(jenkins_commits)} Jenkins config change(s) (can break pipeline)")
            for commit in jenkins_commits[:3]:  # Show top 3
                mr_display = f"!{commit['mr_number']}" if commit['mr_number'] else commit['sha']
                print(f"         🚨 {mr_display}: {commit['subject'][:60]}...")
        
        if dashboard_commits:
            print(f"      Found {len(dashboard_commits)} Dashboard change(s) (can break E2E tests only)")
            for commit in dashboard_commits[:2]:  # Show top 2
                mr_display = f"#{commit['mr_number']}" if commit['mr_number'] else commit['sha']
                print(f"         📊 {mr_display}: {commit['subject'][:60]}...")
        else:
            print(f"      No merges in last 24 hours")
    else:
        print(f"   ✅ Pipeline completed successfully")
        recent_merges = []

    # Step 5: Get test results
    print(f"\n[5/12] 📊 Fetching test results...")
    artifacts = await jenkins_cli.list_artifacts(job_path, build_num)

    test_results_artifact = None
    for artifact in artifacts:
        rel_path = artifact.get('relativePath', '')
        if f'test-output/cypress-{build_num}-results.xml' in rel_path:
            test_results_artifact = rel_path
            break

    if not test_results_artifact:
        print(f"   ⚠ No test results found")
        parsed_results = {'total_tests': 0, 'passed_tests': 0, 'failed_tests': 0, 'failures': []}
    else:
        xml_content = await jenkins_cli.get_artifact_content(job_path, build_num, test_results_artifact)
        parser = artifact_parser.ArtifactParser()
        parsed_results = parser.parse_junit_xml(xml_content)

        print(f"   Total: {parsed_results.get('total_tests', 0)}, "
              f"Passed: {parsed_results.get('passed_tests', 0)}, "
              f"Failed: {parsed_results.get('failed_tests', 0)}")

    # Step 6: Connect to cluster
    print(f"\n[6/12] 🌐 Connecting to {name} cluster...")
    inspector = cluster_inspector.ClusterInspector(cluster_config)

    if not await inspector.login():
        print(f"   ❌ Failed to login")
        cluster_analysis = None
        all_namespaces = []
    else:
        print(f"   ✓ Connected")
        namespace = "opendatahub" if name == "ODH" else "redhat-ods-applications"
        cluster_analysis = await inspector.analyze_test_environment(namespace)
        print(f"   Pods in {namespace}: {cluster_analysis['pod_health']['total']} total")

        # Check ALL namespaces
        all_namespaces = await check_all_namespaces(inspector)

    # Step 7: Process failures and check git diff
    print(f"\n[7/12] 📝 Processing test failures...")
    failures = []
    git_analysis = {}

    for failure_data in parsed_results.get('failures', []):
        test_name_from_xml = failure_data.get('fullTitle', failure_data.get('test', ''))
        suite_name = failure_data.get('suite', '')
        test_file = improved_file_extraction(test_name_from_xml, suite_name)

        # Extract clean test name - PRIORITY ORDER:
        # 1. From filename (e.g., testRegisterModel.cy.ts -> testRegisterModel)
        # 2. From it() block in file
        # 3. Last resort: first part of XML name (before first space)
        
        # Try filename first
        filename = os.path.basename(test_file)
        if filename.startswith('test') and filename.endswith('.cy.ts'):
            clean_test_name = filename.replace('.cy.ts', '')
        else:
            # Try reading from file
            full_test_path = os.path.join(frontend_repo, 'frontend/src/__tests__/cypress', test_file)
            clean_test_name = extract_test_name_from_it_block(full_test_path)
            
            # Last resort: simplify XML name (take first meaningful part)
            if not clean_test_name:
                # Take first part before repeated text or very long name
                parts = test_name_from_xml.split(' ')
                if len(parts) > 3 and len(test_name_from_xml) > 80:
                    # It's a long describe/it chain, just use suite name if available
                    clean_test_name = suite_name.split(' ')[0] if suite_name else 'Unknown Test'
                else:
                    clean_test_name = test_name_from_xml

        failure = artifact_parser.TestFailure(
            test_name=clean_test_name,
            test_file=test_file,
            error_message=failure_data.get('error', 'No error message'),
            stack_trace=failure_data.get('stack', ''),
            suite=suite_name,
            duration=failure_data.get('duration')
        )
        failures.append(failure)

        # Git analysis
        commit_hash = dashboard_commit['commit_hash']
        if not commit_hash and image_metadata.get('dashboard', {}).get('commit_sha_full'):
            commit_hash = image_metadata['dashboard']['commit_sha_full'][:8]

        git_info = check_git_diff_for_test(test_file, commit_hash, frontend_repo)
        git_analysis[test_file] = git_info

    test_result = artifact_parser.TestResult(
        job_name=f"dash-e2e-{name.lower()}",
        build_number=build_num,
        build_url=f"{jenkins_cli.jenkins_url}/job/{job_path.replace('/', '/job/')}/{build_num}/",
        timestamp=build_data.get('timestamp', 0),
        status=build_data.get('result', 'UNKNOWN'),
        total_tests=parsed_results.get('total_tests', 0),
        passed_tests=parsed_results.get('passed_tests', 0),
        failed_tests=parsed_results.get('failed_tests', 0),
        skipped_tests=parsed_results.get('skipped_tests', 0),
        duration=parsed_results.get('duration', 0),
        failures=failures
    )

    # Step 8: Analyze with Jira
    print(f"\n[8/12] 🐛 Searching Jira for related bugs...")
    analyzer = failure_analyzer.FailureAnalyzer(
        jira_client=jira,
        enable_test_rerun=False,
        frontend_repo_path=frontend_repo
    )

    analysis = await analyzer.analyze_test_result(test_result, cluster_analysis, cluster_name=name.lower())

    # Step 9: Decide on test reruns with selective/grouped approach
    should_rerun = False
    skip_reason = None
    failures_to_rerun = []

    # Define stages that happen BEFORE tests run (true deployment failures)
    pre_test_stages = [
        'Setup OpenShift Local Cluster',
        'Verify Cluster is Ready',
        'Prepare Users and Registry',
        'Install ODH Operator',
        'Install RHOAI Operator',
        'Verify Dashboard is Ready',
        'Update Dashboard Image in DSC',
        'Match Dashboard Testing Branch',
        'Update Dashboard Packages',
        'Cluster Configuration'
    ]
    
    # Only skip test reruns if it's a TRUE deployment failure (before tests run)
    is_pre_test_failure = (
        pipeline_failure['is_deployment_failure'] and 
        pipeline_failure['failed_step'] in pre_test_stages
    )
    
    # Check if this is a post-test failure (like Post Actions)
    is_post_test_failure = pipeline_failure.get('is_post_test_failure', False)
    
    if is_pre_test_failure:
        skip_reason = f"Pipeline deployment failure: {pipeline_failure['failed_step']}"
    elif len(failures) == 0:
        skip_reason = "No failures to rerun"
    elif len(failures) < 5:
        # Rerun all failures when < 5
        should_rerun = True
        failures_to_rerun = failures
        print(f"\n[9/12] 🔄 Rerunning all {len(failures)} failing test(s)...")
    else:
        # When >= 5 failures, group by exception and rerun one per group
        should_rerun = True
        exception_groups = group_failures_by_exception(failures)

        print(f"\n[9/12] 🔄 {len(failures)} failures detected - grouping by exception type...")
        print(f"   Found {len(exception_groups)} exception type(s):")

        for exc_type, group_failures in exception_groups.items():
            print(f"      • {exc_type}: {len(group_failures)} failure(s)")
            # Pick the first failure from each group to rerun
            failures_to_rerun.append(group_failures[0])

        print(f"   Rerunning {len(failures_to_rerun)} representative test(s) (one per exception type)...")

    if should_rerun and len(failures_to_rerun) > 0:
        # Create a modified test result with only the failures we want to rerun
        test_result_for_rerun = artifact_parser.TestResult(
            job_name=test_result.job_name,
            build_number=test_result.build_number,
            build_url=test_result.build_url,
            timestamp=test_result.timestamp,
            status=test_result.status,
            total_tests=test_result.total_tests,
            passed_tests=test_result.passed_tests,
            failed_tests=len(failures_to_rerun),
            skipped_tests=test_result.skipped_tests,
            duration=test_result.duration,
            failures=failures_to_rerun
        )

        # Create a fresh analyzer with reruns enabled
        analyzer_with_reruns = failure_analyzer.FailureAnalyzer(
            jira_client=jira,
            enable_test_rerun=True,
            frontend_repo_path=frontend_repo
        )
        
        # Analyze only the failures we want to rerun
        analysis_with_reruns = await analyzer_with_reruns.analyze_test_result(
            test_result_for_rerun,
            cluster_analysis,
            cluster_name=name.lower()
        )
        
        # For the non-rerun failures, analyze them without rerunning
        if len(failures_to_rerun) < len(failures):
            analyzer_no_rerun = failure_analyzer.FailureAnalyzer(
                jira_client=jira,
                enable_test_rerun=False,
                frontend_repo_path=frontend_repo
            )
            
            non_rerun_failures = [f for f in failures if f not in failures_to_rerun]
            test_result_no_rerun = artifact_parser.TestResult(
                job_name=test_result.job_name,
                build_number=test_result.build_number,
                build_url=test_result.build_url,
                timestamp=test_result.timestamp,
                status=test_result.status,
                total_tests=test_result.total_tests,
                passed_tests=test_result.passed_tests,
                failed_tests=len(non_rerun_failures),
                skipped_tests=test_result.skipped_tests,
                duration=test_result.duration,
                failures=non_rerun_failures
            )
            
            analysis_no_rerun = await analyzer_no_rerun.analyze_test_result(
                test_result_no_rerun,
                cluster_analysis,
                cluster_name=name.lower()
            )
            
            # Merge the analyses
            analysis_with_reruns['failure_analyses'].extend(analysis_no_rerun['failure_analyses'])
    else:
        print(f"\n[9/12] ⏭ Skipping test reruns - {skip_reason}")
        analysis_with_reruns = analysis

    # Step 10: Get screenshots for each failure
    print(f"\n[10/12] 📸 Fetching failure screenshots...")
    failure_screenshots = {}
    
    for failure in failures:
        # Pass test_file for stricter screenshot matching
        screenshots = await get_test_failure_screenshots(jenkins_cli, job_path, build_num, failure.test_name, failure.test_file)
        if screenshots:
            failure_screenshots[failure.test_name] = screenshots
            print(f"   • {Path(failure.test_file).name}: {len(screenshots)} screenshot(s)")

    # Generate comprehensive V2 report (modern and exciting!)
    print(f"\n📄 Generating comprehensive V2 report...")

    lines = []

    # Header with emoji
    lines.append(f"# 🚀 {name} Nightly Analysis - Build #{build_num}")
    lines.append("")
    lines.append(f"**📅 Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**🔗 Build URL:** [{build_num}]({test_result.build_url})")
    
    # Add parent build link if this is a nightly cron build
    if nightly_info['is_nightly'] and parent_build:
        lines.append(f"**🔗 Parent Job:** [rhoai-test-flow #{parent_build['number']}]({parent_build['url']}) ({parent_build['result']})")
    elif nightly_info['is_nightly']:
        lines.append(f"**📅 Nightly Cron:** `{nightly_info['cluster_name']}`")
    
    lines.append("")
    lines.append("---")
    lines.append("")

    # Quick Status Overview
    lines.append("## 📊 Quick Status Overview")
    lines.append("")
    total_tests = parsed_results.get('total_tests', 0)
    num_failures = len(analysis_with_reruns['failure_analyses'])

    # CRITICAL FIX: Distinguish "tests not executed" from "tests passed"
    # Check both parent and dashboard-tests job for deployment failures
    has_parent_failure = parent_failure and parent_failure['is_parent_failure'] and parent_failure['failed_before_tests']
    has_pipeline_failure = pipeline_failure['is_deployment_failure']
    
    if (has_parent_failure or has_pipeline_failure) and total_tests == 0:
        lines.append("### ⚠️ **TESTS NOT EXECUTED**")
        lines.append("")
        if has_parent_failure:
            lines.append(f"Tests did not run due to a failure in the **rhoai-test-flow** parent job.")
            lines.append(f"The parent job handles cluster setup and operator installation.")
            lines.append("")
            lines.append(f"See **Parent Pipeline Failure** section below for details.")
        else:
            lines.append(f"Tests did not run due to a deployment failure during the pipeline.")
            lines.append("")
            lines.append(f"See **Pipeline Failure Details** section below for complete error information.")
    elif num_failures == 0 and total_tests > 0:
        lines.append("### ✅ **ALL TESTS PASSED**")
        lines.append("")
        lines.append(f"- **Total Tests:** {total_tests}")
        lines.append(f"- **Passed:** {parsed_results.get('passed_tests', 0)}")
        lines.append(f"- **Failed:** 0")
    elif num_failures > 0:
        lines.append(f"### ❌ **{num_failures} TEST(S) FAILED**")
        lines.append("")
        lines.append(f"- **Total Tests:** {total_tests}")
        lines.append(f"- **Passed:** {parsed_results.get('passed_tests', 0)}")
        lines.append(f"- **Failed:** {num_failures}")
        lines.append("")
        lines.append("**Failed Tests:**")
        for i, fa in enumerate(analysis_with_reruns['failure_analyses'], 1):
            # Show the test file name (e.g., testConnectionCreation.cy.ts) not the JUnit test name
            test_file_name = Path(fa.failure.test_file).name if fa.failure.test_file else fa.failure.test_name
            lines.append(f"{i}. `{test_file_name}`")
    else:
        lines.append("### ⚠️ **NO TEST DATA AVAILABLE**")
        lines.append("")
        lines.append("Could not retrieve test execution results.")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Test/Code Synchronization Status (NEW!)
    if sync_issues['severity'] in ['critical', 'warning'] or sync_issues['fell_back_to_main']:
        lines.append("## 🔄 Test/Code Synchronization Status")
        lines.append("")

        if sync_issues['severity'] == 'critical':
            lines.append("### 🚨 **CRITICAL SYNC ISSUE DETECTED**")
            lines.append("")
            lines.append(f"**Problem:** {sync_issues['warning_message']}")
            lines.append("")

            if sync_issues['deployed_image_registry']:
                lines.append("**Deployed Image:**")
                lines.append("```")
                lines.append(f"{sync_issues['deployed_image_registry']}")
                lines.append("```")
                lines.append("")

            if sync_issues['branch_used_for_tests']:
                lines.append(f"- **Tests Executed From:** `{sync_issues['branch_used_for_tests']}` branch")
                lines.append(f"- **Image Commit:** Could not be determined")
                lines.append("")

            lines.append("**⚠️ Impact:**")
            lines.append("- Test failures may be FALSE POSITIVES due to test/code mismatch")
            lines.append("- Tests run against NEWER code than deployed in cluster")
            lines.append("- Do not treat failures as confirmed product bugs without verification")
            lines.append("")

            lines.append("**🔧 Recommended Actions:**")
            lines.append("1. Investigate why commit metadata is missing from deployed image")
            lines.append("2. Verify image registry type (production vs development)")
            lines.append("3. Consider retesting with correctly synchronized branches")
            lines.append("4. Review individual test failures with extra caution")
            lines.append("")

        elif sync_issues['fell_back_to_main']:
            lines.append("### ⚠️ **Tests Fell Back to Main Branch**")
            lines.append("")
            lines.append(f"- **Tests Executed From:** `main` branch (fallback)")
            lines.append(f"- **Reason:** Dashboard commit could not be determined from deployed image")
            lines.append("")
            if sync_issues['warning_message']:
                lines.append(f"**Note:** {sync_issues['warning_message']}")
                lines.append("")

        # Show registry analysis for deployed images
        if registry_analyses:
            lines.append("### 📋 Image Registry Analysis")
            lines.append("")
            for img_type, reg_info in registry_analyses.items():
                if reg_info and reg_info['registry_type'] != 'unknown':
                    tracer_status = "✅ Compatible" if reg_info['tracer_compatible'] else "❌ Not compatible"
                    lines.append(f"**{img_type.replace('_', ' ').title()}:**")
                    lines.append(f"- Registry Type: `{reg_info['registry_type']}`")
                    lines.append(f"- Tracer Tool: {tracer_status}")
                    if reg_info['notes']:
                        lines.append(f"- Note: {reg_info['notes']}")
                    lines.append("")

        lines.append("---")
        lines.append("")

    # Deployment Information with Tracer Data
    lines.append("## 🐳 Deployment & Image Information")
    lines.append("")

    # Show ALL images (FBC, IIB, Dashboard) - even if tracer failed
    if deployed_images:
        for img_type, img_uri in deployed_images.items():
            if img_uri:
                lines.append(f"### {img_type.replace('_', ' ').title()}")
                lines.append("")

                # Always show the image URI
                lines.append(f"**Image URI:**")
                lines.append(f"```")
                lines.append(f"{img_uri}")
                lines.append(f"```")
                lines.append("")

                # If we have metadata from tracer, include it
                metadata = image_metadata.get(img_type, {})
                if metadata and not metadata.get('error'):
                    if metadata.get('build_date'):
                        lines.append(f"- 📅 **Build Date:** `{metadata['build_date']}`")

                    if metadata.get('rhoai_version'):
                        lines.append(f"- 🏷️ **RHOAI Version:** `{metadata['rhoai_version']}`")

                    if metadata.get('commit_sha_full'):
                        commit_short = metadata['commit_sha_full'][:8]
                        if metadata.get('commit_url'):
                            lines.append(f"- 🔗 **Commit:** [`{commit_short}`]({metadata['commit_url']})")
                            lines.append(f"  - Full SHA: `{metadata['commit_sha_full']}`")
                        else:
                            lines.append(f"- 🔗 **Commit:** `{metadata['commit_sha_full']}`")
                elif metadata and metadata.get('error'):
                    lines.append(f"- ⚠️ **Tracer Error:** {metadata['error']}")

                lines.append("")

    # Git comparison
    main_commit = None
    commits_behind = 0
    for git_info in git_analysis.values():
        if git_info.get('main_commit'):
            main_commit = git_info['main_commit']
            commits_behind = git_info.get('commits_behind', 0)
            break

    if main_commit:
        main_github_url = f"https://github.com/{github_repo}/commit/{main_commit}"
        lines.append(f"### Main Branch Comparison")
        lines.append("")
        lines.append(f"- **Main Branch HEAD:** [`{main_commit}`]({main_github_url})")

        # CRITICAL FIX: Check if we have a valid image commit before comparing
        # If there's a sync issue, we don't have a valid commit to compare against
        if sync_issues['severity'] == 'critical' or (not dashboard_commit['commit_hash'] and not image_metadata.get('fbc_fragment', {}).get('commit_sha_full')):
            lines.append(f"- ❌ **Cannot compare - image commit unknown due to sync issue**")
            lines.append(f"- ⚠️ **Tests may be running against newer code than deployed**")
        elif commits_behind > 0:
            lines.append(f"- ⚠️ **Image is {commits_behind} commits behind main branch**")
        else:
            lines.append(f"- ✅ Image commit matches current main branch")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Trend Analysis (compare with previous build) - ONLY for automated nightly runs
    if enable_trend_analysis and pipeline_failure['is_deployment_failure'] and build_num > 1:
        try:
            # Fetch previous build for same cluster type
            prev_build_num = build_num - 1
            while prev_build_num > 0:
                try:
                    prev_build = await jenkins_cli.get_build(job_path, prev_build_num)
                    prev_description = prev_build.get('description', '').lower()
                    
                    # Check if this is the same cluster type
                    current_is_rhoai = variant.upper() == "RHOAI"
                    prev_is_rhoai = 'dash-e2e-rhoai' in prev_description
                    
                    if current_is_rhoai == prev_is_rhoai:
                        # Found matching cluster type
                        prev_result = prev_build.get('result', '')
                        
                        if prev_result == 'FAILURE':
                            # Get previous console to compare errors
                            prev_console = await jenkins_cli.get_console_output(job_path, prev_build_num)
                            prev_failure = analyze_pipeline_failure_general(prev_console, prev_result)
                            
                            if prev_failure['is_deployment_failure']:
                                lines.append("## 📈 Trend Analysis")
                                lines.append("")
                                lines.append(f"**Comparing with previous {variant} build #{prev_build_num}:**")
                                lines.append("")
                                
                                current_error = pipeline_failure['exception_message'] or pipeline_failure['error_details']
                                prev_error = prev_failure['exception_message'] or prev_failure['error_details']
                                
                                if current_error != prev_error:
                                    lines.append(f"⚠️ **Error message has CHANGED:**")
                                    lines.append("")
                                    lines.append(f"**Previous build #{prev_build_num}:**")
                                    lines.append(f"```")
                                    lines.append(prev_error[:200])
                                    lines.append(f"```")
                                    lines.append("")
                                    lines.append(f"**Current build #{build_num}:**")
                                    lines.append(f"```")
                                    lines.append(current_error[:200])
                                    lines.append(f"```")
                                    lines.append("")
                                    
                                    # Highlight key differences
                                    if "''" in prev_error and "''" not in current_error:
                                        lines.append(f"💡 **Key change:** Previous build had empty string `''`, current build has actual cluster name. This suggests partial fix!")
                                        lines.append("")
                                elif prev_failure['failed_step'] == pipeline_failure['failed_step']:
                                    lines.append(f"🔁 **Same failure as build #{prev_build_num}:** `{pipeline_failure['failed_step']}`")
                                    lines.append("")
                                
                                lines.append("---")
                                lines.append("")
                        
                        break  # Found matching cluster, stop searching
                    
                    prev_build_num -= 1
                    if build_num - prev_build_num > 10:  # Don't search too far back
                        break
                        
                except Exception:
                    prev_build_num -= 1
                    if build_num - prev_build_num > 10:
                        break
        except Exception as e:
            # Silently skip if trend analysis fails
            pass

    # Parent Pipeline Failure (rhoai-test-flow)
    if parent_failure and parent_failure['is_parent_failure']:
        lines.append("## 🔴 Parent Pipeline Failure (rhoai-test-flow)")
        lines.append("")
        lines.append(f"**⚠️ The parent orchestrator job failed before tests could run!**")
        lines.append("")
        lines.append(f"**Parent Job:** [rhoai-test-flow #{parent_build['number']}]({parent_build['url']})")
        lines.append(f"**Failed Step:** `{parent_failure['failed_step']}`")
        lines.append(f"**Error:** {parent_failure['error_details']}")
        lines.append("")
        
        if parent_failure['failed_before_tests']:
            lines.append("### ⚠️ Failure Occurred BEFORE Tests Could Run")
            lines.append("")
            lines.append("The rhoai-test-flow job handles:")
            lines.append("- Cluster configuration and setup")
            lines.append("- RHOAI/ODH operator installation")
            lines.append("- Dashboard deployment and verification")
            lines.append("")
            lines.append("After completing these steps, it triggers `dashboard-tests` to run Cypress E2E tests.")
            lines.append("")
            lines.append("**Since the failure occurred in the parent job, no tests were executed.**")
            lines.append("")
        
        if parent_failure['stages_completed']:
            lines.append(f"**Stages Completed ({len(parent_failure['stages_completed'])}):**")
            for stage in parent_failure['stages_completed']:
                lines.append(f"- ✅ `{stage}`")
            lines.append("")
        
        if parent_failure['stages_failed']:
            lines.append(f"**Stages Failed ({len(parent_failure['stages_failed'])}):**")
            for stage_info in parent_failure['stages_failed']:
                lines.append(f"- ❌ `{stage_info['stage']}` (exit code: {stage_info['exit_code']})")
            lines.append("")
        
        lines.append("**💡 To investigate:**")
        lines.append(f"1. Check the [parent build console]({parent_build['url']}console)")
        lines.append("2. Look for cluster configuration issues")
        lines.append("3. Check operator installation logs")
        lines.append("4. Verify cluster health and resources")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Pipeline Status (dashboard-tests job)
    if pipeline_failure['is_deployment_failure']:
        lines.append("## 🚨 Pipeline Failure Details")
        lines.append("")
        lines.append(f"**Failed Step:** `{pipeline_failure['failed_step']}`")
        lines.append("")
        lines.append(f"**Error:** {pipeline_failure['error_details']}")
        lines.append("")

        # Add Java/Groovy exception details if available
        if pipeline_failure.get('exception_type'):
            lines.append(f"**Exception Type:** `{pipeline_failure['exception_type']}`")
            lines.append("")

            if pipeline_failure.get('exception_message'):
                lines.append(f"**Exception Message:**")
                lines.append("```")
                lines.append(pipeline_failure['exception_message'])
                lines.append("```")
                lines.append("")

            if pipeline_failure.get('exception_location'):
                lines.append("**Stack Trace (Top 3 calls):**")
                for method, file_info in pipeline_failure['exception_location']:
                    lines.append(f"- `{method}.call({file_info})`")
                lines.append("")

        if pipeline_failure['known_issue']:
            lines.append(f"🐛 **Known Issue:** [{pipeline_failure['known_issue']}](https://issues.redhat.com/browse/{pipeline_failure['known_issue']})")
            lines.append("")

        if len(pipeline_failure['all_failed_stages']) > 1:
            lines.append(f"**All Failed Stages ({len(pipeline_failure['all_failed_stages'])}):**")
            for stage_info in pipeline_failure['all_failed_stages']:
                lines.append(f"- `{stage_info['stage']}` (exit code: {stage_info['exit_code']})")
            lines.append("")

        # Add related Jira issues for pipeline failure
        if pipeline_jira_issues:
            lines.append(f"### 🔍 Related Jira Issues for This Pipeline Failure")
            lines.append("")
            lines.append(f"Found **{len(pipeline_jira_issues)}** potentially related issue(s):")
            lines.append("")

            for idx, issue in enumerate(pipeline_jira_issues, 1):
                lines.append(f"{idx}. [{issue['key']}]({issue['url']}) - `{issue['status']}`")
                lines.append(f"   - {issue['summary']}")
                lines.append(f"   - Relevance: {issue['relevance']} matching term(s)")
                lines.append("")
        else:
            lines.append("### 🔍 Related Jira Issues")
            lines.append("")
            lines.append("No related Jira issues found for this pipeline failure.")
            lines.append("")

        # Add recent commits section (GitHub Dashboard + GitLab Jenkins)
        if recent_merges:
            lines.append("### 📋 Recent Commits (GitHub + GitLab)")
            lines.append("")

            # Separate GitLab (pipeline) from Dashboard (test/app) commits
            jenkins_commits = [m for m in recent_merges if m['repository'] == 'Jenkins']
            dashboard_commits = [m for m in recent_merges if m['repository'] == 'Dashboard']

            if jenkins_commits:
                lines.append(f"**🚨 GitLab Jenkins Changes ({len(jenkins_commits)}) - Can Break Pipeline:**")
                lines.append("")
                lines.append("These Jenkins configuration changes may have caused the pipeline failure:")
                lines.append("")
                for commit in jenkins_commits:
                    if commit['mr_number']:
                        mr_link = f"[!{commit['mr_number']}](https://gitlab.cee.redhat.com/ods/jenkins/-/merge_requests/{commit['mr_number']})"
                    else:
                        mr_link = f"[{commit['sha']}](https://gitlab.cee.redhat.com/ods/jenkins/-/commit/{commit['full_sha']})"
                    
                    lines.append(f"- **{mr_link}** by {commit['author']}")
                    lines.append(f"  - {commit['subject']}")
                    lines.append(f"  - Committed: {commit['timestamp']}")
                    if commit['body']:
                        lines.append(f"  - Details: {commit['body'][:100]}...")
                    lines.append("")

            if dashboard_commits:
                lines.append(f"**📊 GitHub Dashboard Changes ({len(dashboard_commits)}) - Can Break E2E Tests Only:**")
                lines.append("")
                lines.append("These Dashboard changes do NOT cause pipeline failures, only E2E test failures:")
                lines.append("")
                
                for commit in dashboard_commits[:5]:  # Limit to 5 for brevity
                    if commit['mr_number']:
                        pr_link = f"[#{commit['mr_number']}](https://github.com/opendatahub-io/odh-dashboard/pull/{commit['mr_number']})"
                    else:
                        pr_link = f"[{commit['sha']}](https://github.com/opendatahub-io/odh-dashboard/commit/{commit['full_sha']})"
                    
                    lines.append(f"- **{pr_link}** by {commit['author']}: {commit['subject'][:80]}")
                
                if len(dashboard_commits) > 5:
                    lines.append(f"- ... and {len(dashboard_commits) - 5} more Dashboard commit(s)")
                lines.append("")
            if not jenkins_commits and not dashboard_commits:
                lines.append("No recent commits found before this build.")
                lines.append("")
        else:
            lines.append("### 📋 Recent Commits (GitHub + GitLab)")
            lines.append("")
            lines.append("No recent commits found before this build.")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Cluster Health - ALWAYS show this section
    has_pod_issues = False
    if cluster_analysis and cluster_analysis['pod_health'].get('problems'):
        has_pod_issues = True
    cypress_ns = [ns for ns in all_namespaces if ns['is_cypress_related']]
    problem_ns = [ns for ns in all_namespaces if ns['problems']]

    lines.append("## 🏥 Cluster Health")
    lines.append("")

    # Show explanation if cluster analysis is not available
    if not cluster_analysis and not cypress_ns and not problem_ns:
        lines.append("⚠️ **Cluster health data not available**")
        lines.append("")
        lines.append("Cluster analysis requires OpenShift login credentials. Configure the following in your `.env` file:")
        lines.append("")
        lines.append(f"```")
        lines.append(f"{name}_API_SERVER=https://api.your-{name.lower()}-cluster.example.com:6443")
        lines.append(f"{name}_USERNAME=cluster-admin")
        lines.append(f"{name}_PASSWORD=your-password")
        lines.append(f"```")
        lines.append("")
        lines.append("---")
        lines.append("")

    if cluster_analysis:
        pod_health = cluster_analysis['pod_health']
        lines.append(f"### Primary Namespace: `{cluster_analysis['namespace']}`")
        lines.append(f"- **Total Pods:** {pod_health['total']}")
        lines.append(f"- **Running:** {pod_health['running']} ✅")
        lines.append(f"- **Failed:** {pod_health['failed']} ❌")
        lines.append("")

        if pod_health.get('problems'):
            lines.append("**Pod Issues:**")
            for problem in pod_health['problems']:
                lines.append(f"- 🔴 **{problem['pod']}**: {problem['issue']}")
            lines.append("")

    if cypress_ns or problem_ns:
        lines.append(f"### Namespace Issues")
        lines.append("")

        if cypress_ns:
            lines.append(f"**⚠️ Cypress-Related Namespaces (cleanup recommended):**")
            for ns in cypress_ns:
                lines.append(f"- `{ns['namespace']}`: {ns['total_pods']} pods ({ns['running_pods']} running, {ns['failed_pods']} failed)")
            lines.append("")

        if problem_ns:
            lines.append(f"**🔴 Namespaces with Pod Issues:**")
            for ns in problem_ns:
                lines.append(f"- `{ns['namespace']}`: {len(ns['problems'])} issue(s)")
                for problem in ns['problems'][:3]:
                    lines.append(f"  - {problem['pod']}: {problem['issue']}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Detailed Test Failures
    if num_failures > 0:
        lines.append("## 🔍 Detailed Test Failure Analysis")
        lines.append("")

        for i, fa in enumerate(analysis_with_reruns['failure_analyses'], 1):
            # Use the test file name as the heading (e.g., testConnectionCreation.cy.ts)
            test_file_name = Path(fa.failure.test_file).name if fa.failure.test_file else fa.failure.test_name
            lines.append(f"### {i}. {test_file_name}")
            lines.append("")
            lines.append(f"**📁 File:** `{fa.failure.test_file}`")
            lines.append("")

            # Git analysis
            git_info = git_analysis.get(fa.failure.test_file, {})

            if git_info:
                lines.append("**📝 Code Analysis:**")
                if git_info.get('quarantined'):
                    lines.append(f"- ⚠️ **Test is QUARANTINED in main** (`@Bug` tag)")
                    if git_info.get('bug_references'):
                        for bug in git_info['bug_references']:
                            lines.append(f"  - 🐛 Product Bug: [{bug}](https://issues.redhat.com/browse/{bug})")

                if git_info.get('needs_maintenance'):
                    lines.append(f"- 🔧 **Test NEEDS MAINTENANCE** (`@Maintain` tag)")

                if git_info.get('file_changed'):
                    lines.append(f"- 📝 **Test file changed** between image commit and main")
                elif commits_behind > 0:
                    lines.append(f"- ✅ Test file unchanged (image {commits_behind} commits behind)")

                lines.append("")

            # Original error
            lines.append("**❌ Original Error:**")
            lines.append("```")
            lines.append(fa.failure.error_message[:600])
            lines.append("```")
            lines.append("")

            # Screenshots (NEW!)
            if fa.failure.test_name in failure_screenshots:
                screenshots = failure_screenshots[fa.failure.test_name]
                lines.append("**📸 Failure Screenshots:**")
                lines.append("")

                # If we extracted a test file from screenshot path, update the file path
                if screenshots and screenshots[0].get('test_file'):
                    test_file_from_screenshot = screenshots[0]['test_file']
                    # Update the test file in the report header
                    for i, line in enumerate(lines):
                        if f"**📁 File:** `{fa.failure.test_file}`" in line:
                            lines[i] = f"**📁 File:** `{test_file_from_screenshot}`"
                            break

                from urllib.parse import quote
                for screenshot in screenshots[:3]:  # Limit to 3 screenshots per test
                    retry_tag = " (Retry)" if screenshot['is_retry'] else ""
                    # URL-encode the screenshot URL (spaces break markdown links)
                    encoded_url = screenshot['url'].replace(' ', '%20')
                    lines.append(f"- [{screenshot['name']}{retry_tag}]({encoded_url})")
                lines.append("")

            # Test rerun results
            if hasattr(fa, 'rerun_result') and fa.rerun_result and fa.rerun_result.get('attempted'):
                rerun = fa.rerun_result
                lines.append("**🔄 Test Rerun on Main Branch:**")
                if rerun.get('success'):
                    lines.append(f"- ✅ **PASSED** on main (took {rerun.get('duration', 0):.1f}s)")

                    if git_info.get('quarantined'):
                        lines.append(f"- **💡 Conclusion:** Known issue - quarantined in main")
                    elif git_info.get('file_changed'):
                        lines.append(f"- **💡 Conclusion:** Fixed in main - image needs update")
                    else:
                        lines.append(f"- **💡 Conclusion:** Flaky/intermittent test")
                else:
                    lines.append(f"- ❌ **FAILED** on main (exit code: {rerun.get('exit_code', 'N/A')})")

                    rerun_error = rerun.get('error_output', '')
                    comparison = compare_errors(fa.failure.error_message, rerun_error)
                    if comparison['same_error']:
                        lines.append(f"- **Error comparison:** ✅ Same error (consistent failure)")
                    else:
                        lines.append(f"- **Error comparison:** ⚠️ Different error")
                        lines.append(f"- **Rerun error (first 300 chars):**")
                        lines.append("  ```")
                        lines.append(f"  {rerun_error[:300]}")
                        lines.append("  ```")

                    if git_info.get('quarantined'):
                        lines.append(f"- **💡 Conclusion:** Known issue - quarantined in main")
                    elif git_info.get('needs_maintenance'):
                        lines.append(f"- **💡 Conclusion:** Test needs maintenance")
                    else:
                        lines.append(f"- **💡 Conclusion:** Consistent failure - needs investigation")
                lines.append("")

            # Jira
            if hasattr(fa, 'jira_issues') and fa.jira_issues:
                lines.append("**🐛 Potential Related Jira Issues:**")
                lines.append("")
                shown = 0
                for issue in fa.jira_issues:
                    if 'CVE' in issue['key'] or 'CVE' in issue['summary']:
                        continue
                    if shown >= 3:
                        break
                    lines.append(f"- [{issue['key']}]({issue['url']}) - `{issue['status']}`")
                    lines.append(f"  {issue['summary']}")
                    shown += 1
                lines.append("")
            else:
                lines.append("**🐛 Jira:** No related issues found")
                lines.append("")

            lines.append("---")
            lines.append("")

    report_content = "\n".join(lines)

    # Save to NEW directory structure
    os.makedirs(f"reports/current/{name}", exist_ok=True)
    os.makedirs("reports/historical", exist_ok=True)

    # Current report
    current_report_path = f"reports/current/{name}/latest-build-{build_num}.md"
    with open(current_report_path, 'w') as f:
        f.write(report_content)

    # Historical copy
    date_str = datetime.now().strftime('%Y-%m-%d')
    historical_report_path = f"reports/historical/{date_str}-{name}-build-{build_num}-v2.md"
    with open(historical_report_path, 'w') as f:
        f.write(report_content)

    # Final summary
    print()
    print("=" * 100)
    print(f"✅ COMPREHENSIVE ANALYSIS V2 COMPLETE")
    print("=" * 100)
    print()
    print(f"📄 Current Report: {current_report_path}")
    print(f"📄 Historical Copy: {historical_report_path}")
    print()
    print(f"🐳 Images analyzed: {len([m for m in image_metadata.values() if m and not m.get('error')])}")
    print(f"🧪 Tests executed: {total_tests}")
    print(f"❌ Tests failed: {num_failures}")
    if pipeline_failure['is_deployment_failure']:
        print(f"🚨 Pipeline failure: {pipeline_failure['failed_step']}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
