# Intelligent Jira Search Patterns

## Overview

The nightly analyzer includes an intelligent Jira search system that automatically generates targeted search queries based on test failures. Instead of generic searches, it uses pattern matching to identify the type of test failure and generates specific, relevant Jira queries.

## How It Works

### 1. Pattern Matching

When a test fails, the system analyzes three aspects:

- **Test File Path**: `modelRegistry/testArchiveModels.cy.ts`
- **Test Name**: "Verify that models can be archived"
- **Error Message**: "Timeout retrying... ContextProperty doesn't exist"

### 2. Pattern Categories

The system has predefined patterns for different test categories:

| Category | Example Tests | Search Focus |
|----------|--------------|--------------|
| **Model Registry** | testArchiveModels, testRegisterModel | database, archive, restore, registration |
| **Pipelines** | testSchedulePipeline, createPipeline | schedule, execution, trigger, cron |
| **Workbenches** | testWorkbenchCreation, workbenchImages | creation, images, notebook |
| **Storage** | clusterStorage, storageClasses | PVC, volume, storage class |
| **Authentication** | testUserLogin, authentication | OAuth, LDAP, login |
| **Dashboard** | dashboardNavigation, navigation | UI elements, navigation |
| **Model Serving** | testDeployModel, modelServing | deployment, KServe |
| **Operator** | installation failures | namespace terminating, cleanup |

### 3. Query Generation

For each failure, the system:

1. **Matches Patterns**: Scores each pattern based on file, test name, and error matches
2. **Prioritizes**: Ranks matches (Priority 1 = most specific, Priority 3 = generic)
3. **Generates JQL**: Creates Jira Query Language searches with appropriate components
4. **Provides URLs**: Gives direct links to search results

## Example: Model Registry Test Failure

### Input
```
Test File: cypress/tests/e2e/modelRegistry/testArchiveModels.cy.ts
Test Name: Verify that models can be archived and restored
Error: Timeout... Table 'ContextProperty' doesn't exist
```

### Generated Queries (Priority Order)

#### Query 1: Model Registry - Archive/Restore (Priority 1)
```jql
project = RHOAIENG AND
text ~ "model registry archive" AND
component in ("Model Registry")
ORDER BY priority DESC, updated DESC
```
**Why**: Exact match on file path + test name + component

#### Query 2: Model Registry - Database (Priority 1)
```jql
project = RHOAIENG AND
text ~ "model registry database" AND
component in ("Model Registry")
ORDER BY priority DESC, updated DESC
```
**Why**: Error mentions database table missing

#### Query 3: Generic - Timeout (Priority 3)
```jql
project = RHOAIENG AND
text ~ "timeout" AND
component in ("Dashboard", "UI")
ORDER BY priority DESC, updated DESC
```
**Why**: Fallback for timeout errors

## Example: Pipeline Test Failure

### Input
```
Test File: Pipelines/testSchedulePipeline.cy.ts
Test Name: Schedule a pipeline to run daily
Error: Pipeline schedule failed: cron expression invalid
```

### Generated Queries

#### Query 1: Pipelines - Scheduling (Priority 1)
```jql
project = RHOAIENG AND
text ~ "pipeline schedule" AND
component in ("Pipelines")
ORDER BY priority DESC
```

#### Query 2: Pipelines - Creation/Execution (Priority 1)
```jql
project = RHOAIENG AND
text ~ "pipeline execution" AND
component in ("Pipelines", "Data Science Pipelines")
```

## Pattern Definition Structure

Each pattern includes:

```python
JiraSearchPattern(
    name="Model Registry - Archive/Restore",
    file_patterns=[
        r"modelRegistry.*archive",  # Regex for file paths
        r"testArchiveModels",
    ],
    test_name_patterns=[
        r"archive.*model",  # Regex for test names
        r"restore.*model",
    ],
    error_patterns=[
        r"timeout.*model.*registry",  # Regex for errors
        r"ContextProperty",
    ],
    jira_keywords=[
        "model registry archive",  # Keywords to search
        "model registry restore",
    ],
    jira_components=["Model Registry"],  # Jira components
    priority=1  # 1=highest, 3=generic
)
```

## Adding New Patterns

To add support for new test types:

1. Open `analyzer/jira_search_patterns.py`
2. Add a new `JiraSearchPattern` to the `SEARCH_PATTERNS` list
3. Define appropriate regexes for file, test name, and error patterns
4. Specify relevant Jira keywords and components
5. Set priority (1 for specific, 2 for moderate, 3 for generic)

### Example: Adding Support for Serving Runtime Tests

```python
JiraSearchPattern(
    name="Serving Runtimes",
    file_patterns=[
        r"servingRuntime",
        r"testServingRuntime",
    ],
    test_name_patterns=[
        r"serving.*runtime",
        r"runtime.*template",
    ],
    error_patterns=[
        r"runtime.*not.*found",
        r"template.*invalid",
    ],
    jira_keywords=[
        "serving runtime",
        "runtime template",
    ],
    jira_components=["Model Serving", "Serving Runtimes"],
    priority=1
)
```

## Usage in Analysis

The analyzer automatically uses these patterns when analyzing failures:

```python
from analyzer.failure_analyzer import FailureAnalyzer
from analyzer.jira_client import JiraClient

analyzer = FailureAnalyzer(jira_client=JiraClient())

# Analyze will automatically:
# 1. Generate intelligent queries based on failure
# 2. Search Jira using those queries
# 3. Include results in the analysis
analysis = await analyzer.analyze_failure(test_failure)

# Access generated queries
for query in analysis.jira_queries:
    print(f"Search: {query['name']}")
    print(f"JQL: {query['jql']}")

# Access found issues
for issue in analysis.jira_issues:
    print(f"{issue['key']}: {issue['summary']}")
    print(f"Matched via: {issue['matched_query']}")
```

## Benefits

1. **Specificity**: Searches are targeted to the exact component and issue type
2. **Efficiency**: Fewer irrelevant results, faster triage
3. **Context**: Each search explains why it was generated
4. **Extensibility**: Easy to add new patterns for new test types
5. **Fallback**: Generic searches ensure something is always found
6. **Prioritization**: Most relevant searches tried first

## Integration with Reports

The generated queries are included in analysis reports:

```markdown
### Jira Search Queries Generated

1. **Model Registry - Archive/Restore** (Priority 1)
   - Search for: "model registry archive"
   - Component: Model Registry
   - JQL: `project = RHOAIENG AND text ~ "model registry archive"...`
   - [Search Now](https://issues.redhat.com/issues/?jql=...)

2. **Model Registry - Database** (Priority 1)
   - Search for: "model registry database"
   - Component: Model Registry
   - Found 3 matching issues:
     - RHOAIENG-1234: Model Registry database initialization fails
     - RHOAIENG-5678: ContextProperty table missing from schema
```

## Future Enhancements

Potential improvements:

1. **Machine Learning**: Learn from past searches which patterns are most effective
2. **Issue Deduplication**: Detect when multiple queries find the same issue
3. **Automatic Filing**: Generate pre-filled Jira issue if no match found
4. **Historical Analysis**: Track which issues are most common per test type
5. **Slack Integration**: Post search results to relevant channels
6. **Custom Filters**: User-defined patterns for specific teams/components
