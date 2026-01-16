# 🚀 ODH Nightly Analysis - Build #3760

**📅 Date:** 2025-12-17 09:59:23
**🔗 Build URL:** [3760](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3760/)
**📅 Nightly Cron:** `dash-e2e-odh`

---

## 📊 Quick Status Overview

### ❌ **1 TEST(S) FAILED**

- **Total Tests:** 93
- **Passed:** 92
- **Failed:** 1

**Failed Tests:**
1. `testNotebookTolerations.cy.ts`

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
brew.registry.redhat.io/rh-osbs/iib:1083915
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

### 1. testNotebookTolerations.cy.ts

**📁 File:** `cypress/tests/e2e/settings/hardwareProfiles/testNotebookTolerations.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Log into the application 2. Navigate to: https://data-science-gateway.apps.dash-e2e-odh.osp.rh-ods.com/ 3. Launch Standalone notebook server 4. Choose Code Server Image 5. Select the hardware profile 6. Check Start server button is enabled 7. Launch a notebook server 8. Verify the Jupyter Notebook pod is ready 9. Expand the Event log 10. Waits for the Success alert  Timed out retrying after 120000ms: Unable to find an element with the text: Running. This could be because the text is broken up by multiple elements. In this case, you can provide a function for your text matc
```

**📸 Failure Screenshots:**

- [Notebooks - tolerations tests -- Verify Juypter Notebook Creation using Hardware Profiles and applying Tolerations (failed).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3760/artifact/test-output/SmokeSet2/e2e/screenshots/settings/hardwareProfiles/testNotebookTolerations.cy.ts/Notebooks%20-%20tolerations%20tests%20--%20Verify%20Juypter%20Notebook%20Creation%20using%20Hardware%20Profiles%20and%20applying%20Tolerations%20(failed).png)
- [Notebooks - tolerations tests -- Verify Juypter Notebook Creation using Hardware Profiles and applying Tolerations (failed) (attempt 2).png (Retry)](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3760/artifact/test-output/SmokeSet2/e2e/screenshots/settings/hardwareProfiles/testNotebookTolerations.cy.ts/Notebooks%20-%20tolerations%20tests%20--%20Verify%20Juypter%20Notebook%20Creation%20using%20Hardware%20Profiles%20and%20applying%20Tolerations%20(failed)%20(attempt%202).png)

**🔄 Test Rerun on Main Branch:**
- ❌ **FAILED** on main (exit code: 1)
- **Error comparison:** ⚠️ Different error
- **Rerun error (first 300 chars):**
  ```
  
  ```
- **💡 Conclusion:** Consistent failure - needs investigation

**🐛 Jira:** No related issues found

---
