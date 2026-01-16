# 🚀 RHOAI Nightly Analysis - Build #3761

**📅 Date:** 2025-12-17 10:02:12
**🔗 Build URL:** [3761](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3761/)
**📅 Nightly Cron:** `dash-e2e-rhoai`

---

## 📊 Quick Status Overview

### ❌ **4 TEST(S) FAILED**

- **Total Tests:** 93
- **Passed:** 89
- **Failed:** 4

**Failed Tests:**
1. `workbenches.cy.ts`
2. `testArchiveModels.cy.ts`
3. `testArchiveModels.cy.ts`
4. `testArchiveModels.cy.ts`

---

## 🐳 Deployment & Image Information

### Dashboard

**Image URI:**
```
quay.io/rhoai/odh-dashboard-rhel9@sha256:9259a2bea563f1d06a8b4fefc04ae2659c52898593fe80df5681dd7325360394
```

- 📅 **Build Date:** `2025-12-17T00:52:13Z`
- 🏷️ **RHOAI Version:** `v3.2.0`
- 🔗 **Commit:** [`7156d667`](https://github.com/red-hat-data-services/odh-dashboard/tree/7156d667841314eb00c5b71dc718ca6eb75f9fbe)
  - Full SHA: `7156d667841314eb00c5b71dc718ca6eb75f9fbe`

### Main Branch Comparison

- **Main Branch HEAD:** [`951efd8c`](https://github.com/opendatahub-io/odh-dashboard/commit/951efd8c)
- ✅ Image commit matches current main branch

---

## 🏥 Cluster Health

### Primary Namespace: `redhat-ods-applications`
- **Total Pods:** 11
- **Running:** 11 ✅
- **Failed:** 0 ❌

## 🔍 Detailed Test Failure Analysis

### 1. workbenches.cy.ts

**📁 File:** `cypress/tests/e2e/dataScienceProjects/workbenches/workbenches.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Log into the application 2. Navigate to: https://data-science-gateway.apps.dash-e2e-rhoai.osp.rh-ods.com/ 3. Navigate to workbenches tab of Project dsp-wb-controls-test-553873 4. Create workbench dsp-wb-controls-test-553873 5. Wait for workbench wb-controls-test-553873 to display a "Running" status 6. Stop workbench and validate it has been stopped 7. Restart workbench and validate it starts successfully 8. Delete workbench and confirm deleteion  Timed out retrying after 10000ms: Unable to find an element by: [data-testid="empty-state-title"]  Ignored nodes: comments, scri
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

### 2. testArchiveModels.cy.ts

**📁 File:** `cypress/tests/e2e/modelRegistry/testArchiveModels.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Log into the application with ldap-user2 2. Navigate to: https://data-science-gateway.apps.dash-e2e-rhoai.osp.rh-ods.com/ 3. Navigate to the Project list tab and search for dsp-model-tolerations-test-335140 4. Navigate to Model Serving and click to Deploy a Single Model 5. Launch a Single Serving Model using OpenVINO Model Server and by selecting the Hardware Profile 6. Step 1: Model details 7. Step 2: Model deployment 8. Step 3: Advanced settings 9. Step 4: Review 10. Verify that the Model is created Successfully on the backend and frontend  The following error originated
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

### 3. testArchiveModels.cy.ts

**📁 File:** `cypress/tests/e2e/modelRegistry/testArchiveModels.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Log into the application with htpasswd-cluster-admin-user 2. Navigate to: https://data-science-gateway.apps.dash-e2e-rhoai.osp.rh-ods.com/ 3. Navigate to the Project list tab and search for cy-single-model-admin-test-278044 4. Navigate to Model Serving and click to Deploy a Single Model 5. Step 1: Model details 6. Step 2: Model deployment 7. Step 3: Advanced settings 8. Allow Model to be accessed from an External route without Authentication 9. Step 4: Review 10. Verify that the Model is created Successfully on the backend and frontend  The following error originated from 
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

### 4. testArchiveModels.cy.ts

**📁 File:** `cypress/tests/e2e/modelRegistry/testArchiveModels.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Log into the application with ldap-user2 2. Navigate to: https://data-science-gateway.apps.dash-e2e-rhoai.osp.rh-ods.com/ 3. Navigate to the Project list tab and search for cypress-single-model-test-project-13236 4. Navigate to Model Serving and click to Deploy a Single Model 5. Step 1: Model details 6. Step 2: Model deployment 7. Step 3: Advanced settings 8. Step 4: Review 9. Verify that the Model is created Successfully on the backend and frontend  The following error originated from your test code, not from Cypress.    > Test exceeded 480s  When Cypress detects uncaught
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
