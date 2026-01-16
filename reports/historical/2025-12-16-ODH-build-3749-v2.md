# 🚀 ODH Nightly Analysis - Build #3749

**📅 Date:** 2025-12-16 10:26:02
**🔗 Build URL:** [3749](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3749/)
**📅 Nightly Cron:** `dash-e2e-odh`

---

## 📊 Quick Status Overview

### ❌ **3 TEST(S) FAILED**

- **Total Tests:** 93
- **Passed:** 90
- **Failed:** 3

**Failed Tests:**
1. `testProjectEditing.cy.ts`
2. `testNotebookTolerations.cy.ts`
3. `testConnectionCreation.cy.ts`

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
brew.registry.redhat.io/rh-osbs/iib:1083355
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

### 1. testProjectEditing.cy.ts

**📁 File:** `cypress/tests/e2e/dataScienceProjects/testProjectEditing.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Log into the application 2. Navigate to: https://data-science-gateway.apps.dash-e2e-odh.osp.rh-ods.com/ 3. Launch Standalone notebook server 4. Choose Code Server Image 5. Check Start server button is enabled 6. Launch a notebook server 7. Verify the Jupyter Notebook pod is ready  The following error originated from your test code, not from Cypress.    > Test exceeded 480s  When Cypress detects uncaught errors originating from your test code it will automatically fail the current test.
Error: The following error originated from your test code, not from Cypress.

  > Test e
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

### 2. testNotebookTolerations.cy.ts

**📁 File:** `cypress/tests/e2e/settings/hardwareProfiles/testNotebookTolerations.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Log into the application 2. Navigate to: https://data-science-gateway.apps.dash-e2e-odh.osp.rh-ods.com/ 3. Launch Standalone notebook server 4. Choose Code Server Image 5. Select the hardware profile 6. Check Start server button is enabled 7. Launch a notebook server 8. Verify the Jupyter Notebook pod is ready  The following error originated from your test code, not from Cypress.    > Test exceeded 480s  When Cypress detects uncaught errors originating from your test code it will automatically fail the current test.
Error: The following error originated from your test code
```

**📸 Failure Screenshots:**

- [Notebooks - tolerations tests -- Verify Juypter Notebook Creation using Hardware Profiles and applying Tolerations (failed).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3749/artifact/test-output/SmokeSet1/e2e/screenshots/settings/hardwareProfiles/testNotebookTolerations.cy.ts/Notebooks%20-%20tolerations%20tests%20--%20Verify%20Juypter%20Notebook%20Creation%20using%20Hardware%20Profiles%20and%20applying%20Tolerations%20(failed).png)
- [Notebooks - tolerations tests -- Verify Juypter Notebook Creation using Hardware Profiles and applying Tolerations (failed) (attempt 2).png (Retry)](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3749/artifact/test-output/SmokeSet1/e2e/screenshots/settings/hardwareProfiles/testNotebookTolerations.cy.ts/Notebooks%20-%20tolerations%20tests%20--%20Verify%20Juypter%20Notebook%20Creation%20using%20Hardware%20Profiles%20and%20applying%20Tolerations%20(failed)%20(attempt%202).png)

**🔄 Test Rerun on Main Branch:**
- ❌ **FAILED** on main (exit code: 1)
- **Error comparison:** ⚠️ Different error
- **Rerun error (first 300 chars):**
  ```
  
  ```
- **💡 Conclusion:** Consistent failure - needs investigation

**🐛 Jira:** No related issues found

---

### 3. testConnectionCreation.cy.ts

**📁 File:** `cypress/tests/e2e/dataScienceProjects/connections/testConnectionCreation.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Navigate to DS Project test-oci-deployment-680619 2. Navigate to: https://data-science-gateway.apps.dash-e2e-odh.osp.rh-ods.com/ 3. Create an OCI Connection 4. Deploy OCI Connection with KServe  Timed out retrying after 10000ms: Unable to find an element by: [data-testid="deploy-button"]  Ignored nodes: comments, script, style <html   lang="en-US" >   <head>           <meta       charset="utf-8"     />     <meta       content="width=device-width,initial-scale=1"       name="viewport"     />     <meta       content="#ffffff"       name="theme-color"     />     <title>      
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
