# 🚀 ODH Nightly Analysis - Build #3817

**📅 Date:** 2025-12-31 10:48:25
**🔗 Build URL:** [3817](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3817/)

---

## 📊 Quick Status Overview

### ❌ **5 TEST(S) FAILED**

- **Total Tests:** 95
- **Passed:** 90
- **Failed:** 5

**Failed Tests:**
1. `workbenches.cy.ts`
2. `testConnectionCreation.cy.ts`
3. `testWorkbenchCreation.cy.ts`
4. `testEnableNIM.cy.ts`
5. `connectionTypes.cy.ts`

---

## 🔄 Test/Code Synchronization Status

### 🚨 **CRITICAL SYNC ISSUE DETECTED**

**Problem:** Quay.io image should have metadata - investigate why tracer failed

**Deployed Image:**
```
quay.io/rhoai/odh-dashboard-rhel8@sha256:30aff2eae7072883084e0d54da8f450879965653182631103191ceade5465a47
```

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
brew.registry.redhat.io/rh-osbs/iib:1086070
```


### Dashboard

**Image URI:**
```
quay.io/rhoai/odh-dashboard-rhel8@sha256:30aff2eae7072883084e0d54da8f450879965653182631103191ceade5465a47
```


### Main Branch Comparison

- **Main Branch HEAD:** [`951efd8c`](https://github.com/opendatahub-io/odh-dashboard/commit/951efd8c)
- ❌ **Cannot compare - image commit unknown due to sync issue**
- ⚠️ **Tests may be running against newer code than deployed**

---

## 🏥 Cluster Health

### Primary Namespace: `opendatahub`
- **Total Pods:** 10
- **Running:** 10 ✅
- **Failed:** 0 ❌

## 🔍 Detailed Test Failure Analysis

### 1. workbenches.cy.ts

**📁 File:** `cypress/tests/e2e/dataScienceProjects/workbenches/workbenches.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Log into the application 2. Navigate to: https://data-science-gateway.apps.dash-e2e-odh.osp.rh-ods.com/ 3. Navigate to workbenches tab of Project dsp-wb-edit-test-483205 4. Create workbench dsp-wb-edit-test-483205 using storage pvc--edit-test-display-name 5. Wait for workbench wb-edit-test-483205 to display a "Running" status  Timed out retrying after 120000ms: expected '<span.pf-v6-c-label.pf-m-filled.pf-m-danger.pf-m-compact.pf-m-clickable>' to have text 'Running', but the text was 'Failed'
AssertionError: Timed out retrying after 120000ms: expected '<span.pf-v6-c-label.
```

**🔄 Test Rerun on Main Branch:**
- ❌ **FAILED** on main (exit code: -1)
- **Error comparison:** ⚠️ Different error
- **Rerun error (first 300 chars):**
  ```
  
  ```
- **💡 Conclusion:** Consistent failure - needs investigation

**🐛 Jira:** No related issues found

---

### 2. testConnectionCreation.cy.ts

**📁 File:** `cypress/tests/e2e/dataScienceProjects/connections/testConnectionCreation.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Log into the application 2. Navigate to: https://data-science-gateway.apps.dash-e2e-odh.osp.rh-ods.com/ 3. Navigate to workbenches tab of Project dsp-wb-edit-test-483205 4. Navigate to Connections and click to create Connection 5. Enter valid Connection details and verify creation 6. Delete the Connection and verify deletion 7. Navigate to Cluster Storage and click to create Cluster Storage 8. Delete the Cluster Storage and verify deletion  Timed out retrying after 10000ms: Expected to find element: `button[aria-label="Kebab toggle"]`, but never found it.
AssertionError: T
```

**🐛 Jira:** No related issues found

---

### 3. testWorkbenchCreation.cy.ts

**📁 File:** `cypress/tests/e2e/dataScienceProjects/workbenches/testWorkbenchCreation.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Log into the application 2. Navigate to: https://data-science-gateway.apps.dash-e2e-odh.osp.rh-ods.com/ 3. Navigate to workbenches tab of Project dsp-wb-status-test-634916 4. Create workbench wb-status-test-634916 5. Wait for workbench wb-status-test-634916 to display a "Running" status 6. Click on Running status, validate the Running status and navigate to the Progress tab 7. Navigate to Events Tab and verify successful event messages are displayed  Timed out retrying after 10000ms: Expected to find content: 'Created container' within the element: <span> but never did.
As
```

**📸 Failure Screenshots:**

- [Create, Delete and Edit - Workbench Tests -- Create Workbench from the launcher page and verify that it is created successfully (failed).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3817/artifact/test-output/SanitySet1/e2e/screenshots/dataScienceProjects/workbenches/testWorkbenchCreation.cy.ts/Create,%20Delete%20and%20Edit%20-%20Workbench%20Tests%20--%20Create%20Workbench%20from%20the%20launcher%20page%20and%20verify%20that%20it%20is%20created%20successfully%20(failed).png)
- [Create, Delete and Edit - Workbench Tests -- Verify user can delete PV storage, data connection and workbench in a shared DS project (failed).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3817/artifact/test-output/SanitySet1/e2e/screenshots/dataScienceProjects/workbenches/testWorkbenchCreation.cy.ts/Create,%20Delete%20and%20Edit%20-%20Workbench%20Tests%20--%20Verify%20user%20can%20delete%20PV%20storage,%20data%20connection%20and%20workbench%20in%20a%20shared%20DS%20project%20(failed).png)
- [Create, Delete and Edit - Workbench Tests -- Create Workbench from the launcher page and verify that it is created successfully (failed) (attempt 2).png (Retry)](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3817/artifact/test-output/SanitySet1/e2e/screenshots/dataScienceProjects/workbenches/testWorkbenchCreation.cy.ts/Create,%20Delete%20and%20Edit%20-%20Workbench%20Tests%20--%20Create%20Workbench%20from%20the%20launcher%20page%20and%20verify%20that%20it%20is%20created%20successfully%20(failed)%20(attempt%202).png)

**🐛 Jira:** No related issues found

---

### 4. testEnableNIM.cy.ts

**📁 File:** `cypress/tests/e2e/nim/testEnableNIM.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Login to the application 2. Navigate to: https://data-science-gateway.apps.dash-e2e-odh.osp.rh-ods.com/ 3. Navigate to the Explore page 4. Navigate to: https://data-science-gateway.apps.dash-e2e-odh.osp.rh-ods.com/applications/explore 5. Check if NIM application exists on cluster 6. NIM OdhApplication exists on cluster - checking UI 7. Check if NIM card is available in UI 8. NIM card is available - proceeding with enablement test 9. Validate NIM card contents 10. Click NIM card 11. Wait for drawer content to load 12. Validate drawer action list is visible 13. Wait for enab
```

**📸 Failure Screenshots:**

- [Verify NIM enable flow -- Enable and validate NIM flow (failed).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3817/artifact/test-output/SanitySet3/e2e/screenshots/nim/testEnableNIM.cy.ts/Verify%20NIM%20enable%20flow%20--%20Enable%20and%20validate%20NIM%20flow%20(failed).png)
- [Verify NIM enable flow -- Enable and validate NIM flow (failed) (attempt 2).png (Retry)](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3817/artifact/test-output/SanitySet3/e2e/screenshots/nim/testEnableNIM.cy.ts/Verify%20NIM%20enable%20flow%20--%20Enable%20and%20validate%20NIM%20flow%20(failed)%20(attempt%202).png)

**🐛 Jira:** No related issues found

---

### 5. connectionTypes.cy.ts

**📁 File:** `cypress/tests/e2e/settings/connectionTypes/connectionTypes.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Log into the application 2. Navigate to: https://data-science-gateway.apps.dash-e2e-odh.osp.rh-ods.com/ 3. Navigate to Connection Types page 4. Verify Create Connection Type page is displayed 5. Select category 6. Select model serving compatible type 7. Add new section heading  Timed out retrying after 10000ms: Unable to find an element by: [data-testid="add-section-heading-button"]  Ignored nodes: comments, script, style <html   lang="en-US" >   <head>           <meta       charset="utf-8"     />     <meta       content="width=device-width,initial-scale=1"       name="vie
```

**🐛 Jira:** No related issues found

---
