# Jenkins Job Analysis: cypress/dashboard-tests

**Build:** [3750](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3750/)
**Date:** 2025-12-16 09:27:54

## Test Results

- Total: 48
- Passed: 44
- Failed: 4
- Skipped: 0

## Failed Tests

### 1. An admin user can import and run a pipeline An admin user can import and run a pipeline An admin User can Import and Run a Pipeline

**File:** `cypress/tests/e2e//cypress/tests/e2e/dataSciencePipelines/pipelines.cy.ts`

**Category:** timeout

**Error:**
```
Test steps were:  1. Navigate to DSP ${projectName} 2. Navigate to: https://rhods-dashboard-redhat-ods-applications.apps.sjagtap1.osp.rh-ods.com/ 3. Import a pipeline by URL  Timed out retrying after 60000ms: expected '<h1.pf-v6-c-content--h1>' to have text 'test-pipelines-pipeline', but the text was 'test-pipelines-prj-973043'
AssertionError: Timed out retrying after 60000ms: expected '<h1.pf-v6-c-content--h1>' to have text 'test-pipelines-pipeline', but the text was 'test-pipelines-prj-973043'
```

**✗ Rerun Result:** FAILED on rerun (exit code: 1)

> **Note:** Test consistently fails - not intermittent

### 2. Verify that a pipeline can be scheduled to run Verify that a pipeline can be scheduled to run Admin imports a pipeline and schedules it to run

**File:** `cypress/tests/e2e//cypress/tests/e2e/dataSciencePipelines/testSchedulePipeline.cy.ts`

**Category:** timeout

**Error:**
```
Test steps were:  1. Navigate to DSP test-dsp-schedule-prj-27388 2. Navigate to: https://rhods-dashboard-redhat-ods-applications.apps.sjagtap1.osp.rh-ods.com/ 3. Import a pipeline by URL 4. Verify pipeline detail is loaded  Timed out retrying after 60000ms: expected '<h1.pf-v6-c-content--h1>' to have text 'test-scheduled-pipeline', but the text was 'test-dsp-schedule-prj-27388'
AssertionError: Timed out retrying after 60000ms: expected '<h1.pf-v6-c-content--h1>' to have text 'test-scheduled-pipe
```

**✗ Rerun Result:** FAILED on rerun (exit code: 1)

> **Note:** Test consistently fails - not intermittent

### 3. A model can be deployed with token auth A model can be deployed with token auth "before each" hook: retryableBeforeEach for "Verify that a model can be deployed with token auth"

**File:** `cypress/tests/e2e/modelRegistry/testArchiveModels.cy.ts`

**Category:** timeout

**Error:**
```
`cy.exec('oc delete project test-model-token-auth-638672')` timed out after waiting `60000ms`.  https://on.cypress.io/exec  Because this error occurred during a `before each` hook we are skipping the remaining tests in the current suite: `A model can be deployed wit...`
CypressError: `cy.exec('oc delete project test-model-token-auth-638672')` timed out after waiting `60000ms`.

https://on.cypress.io/exec

Because this error occurred during a `before each` hook we are skipping the remaining tests
```

**✗ Rerun Result:** FAILED on rerun (exit code: 1)

> **Note:** Test consistently fails - not intermittent

### 4. Verify Admin Single Model Creation and Validation using the UI Verify Admin Single Model Creation and Validation using the UI "before each" hook: retryableBeforeEach for "Verify that an Admin can Serve, Query a Single Model using both the UI and External links"

**File:** `cypress/tests/e2e/modelRegistry/testArchiveModels.cy.ts`

**Category:** timeout

**Error:**
```
`cy.exec('oc delete project cy-single-model-admin-test-812037')` timed out after waiting `60000ms`.  https://on.cypress.io/exec  Because this error occurred during a `before each` hook we are skipping the remaining tests in the current suite: `Verify Admin Single Model C...`
CypressError: `cy.exec('oc delete project cy-single-model-admin-test-812037')` timed out after waiting `60000ms`.

https://on.cypress.io/exec

Because this error occurred during a `before each` hook we are skipping the remai
```

**✗ Rerun Result:** FAILED on rerun (exit code: 1)

> **Note:** Test consistently fails - not intermittent