# 🚀 ODH Nightly Analysis - Build #3784

**📅 Date:** 2025-12-19 09:43:58
**🔗 Build URL:** [3784](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3784/)
**📅 Nightly Cron:** `dash-e2e-odh`

---

## 📊 Quick Status Overview

### ❌ **1 TEST(S) FAILED**

- **Total Tests:** 93
- **Passed:** 92
- **Failed:** 1

**Failed Tests:**
1. `testWorkbenchCreation.cy.ts`

---

## 🔄 Test/Code Synchronization Status

### 🚨 **CRITICAL SYNC ISSUE DETECTED**

**Problem:** CRITICAL: Test/code mismatch - tests run from main but deployed image age unknown!

**Deployed Image:**
```
quay.io/rhoai/odh-dashboard-rhel8@sha256:0417e17f44adfdb7dada5e4cfafa9a7574500313edeb5cd83aa45779a5c7473d
```

- **Tests Executed From:** `main` branch
- **Image Commit:** Could not be determined

**⚠️ Impact:**
- Test failures may be FALSE POSITIVES due to test/code mismatch
- Tests run against NEWER code than deployed in cluster
- Do not treat failures as confirmed product bugs without verification

**🔧 Recommended Actions:**
1. Investigate why commit metadata is missing from deployed image
2. Verify image registry type (production vs development)
3. Consider retesting with correctly synchronized branches
4. Review individual test failures with extra caution

### 📋 Image Registry Analysis

**Iib:**
- Registry Type: `production`
- Tracer Tool: ❌ Not compatible
- Note: Production registry images lack commit metadata for tracer

**Dashboard:**
- Registry Type: `development`
- Tracer Tool: ✅ Compatible
- Note: Development registry with full metadata support

---

## 🐳 Deployment & Image Information

### Iib

**Image URI:**
```
brew.registry.redhat.io/rh-osbs/iib:1084425
```


### Dashboard

**Image URI:**
```
quay.io/rhoai/odh-dashboard-rhel8@sha256:0417e17f44adfdb7dada5e4cfafa9a7574500313edeb5cd83aa45779a5c7473d
```


### Main Branch Comparison

- **Main Branch HEAD:** [`951efd8c`](https://github.com/opendatahub-io/odh-dashboard/commit/951efd8c)
- ❌ **Cannot compare - image commit unknown due to sync issue**
- ⚠️ **Tests may be running against newer code than deployed**

---

## 🏥 Cluster Health

### Primary Namespace: `opendatahub`
- **Total Pods:** 11
- **Running:** 11 ✅
- **Failed:** 0 ❌

## 🔍 Detailed Test Failure Analysis

### 1. testWorkbenchCreation.cy.ts

**📁 File:** `cypress/tests/e2e/dataScienceProjects/workbenches/testWorkbenchCreation.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Log into the application 2. Navigate to: https://data-science-gateway.apps.dash-e2e-odh.osp.rh-ods.com/ 3. Navigate to workbenches tab of Project dsp-wb-status-test-624419 4. Create workbench wb-status-test-624419 5. Wait for workbench wb-status-test-624419 to display a "Running" status 6. Click on Running status, validate the Running status and navigate to the Progress tab 7. Navigate to Events Tab and verify successful event messages are displayed  Timed out retrying after 10000ms: Expected to find content: 'Created container' within the element: <span> but never did.
As
```

**🔄 Test Rerun on Main Branch:**
- ❌ **FAILED** on main (exit code: 1)
- **Error comparison:** ⚠️ Different error
- **Rerun error (first 300 chars):**
  ```
  
  ```
- **💡 Conclusion:** Consistent failure - needs investigation

**🐛 Jira:** No related issues found

---
