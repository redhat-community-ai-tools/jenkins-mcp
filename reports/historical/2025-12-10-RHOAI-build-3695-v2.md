# 🚀 RHOAI Nightly Analysis - Build #3695

**📅 Date:** 2025-12-10 11:42:27
**🔗 Build URL:** [3695](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3695/)

---

## 📊 Quick Status Overview

### ❌ **6 TEST(S) FAILED**

- **Total Tests:** 91
- **Passed:** 85
- **Failed:** 6

**Failed Tests:**
1. `testGenAi.cy.ts`
2. `testWorkbenchStorageClasses.cy.ts`
3. `testEnabledISVs.cy.ts`
4. `testWorkbenchTolerations.cy.ts`
5. `testWorkbenchTolerations.cy.ts`
6. `testModelStopStart.cy.ts`

---

## 🐳 Deployment & Image Information

### Fbc Fragment

**Image URI:**
```
quay.io/rhoai/rhoai-fbc-fragment@sha256:87520f91cf3b482e8d576219c5b2d97c712a3d85a0fd32a22201b9a53d63d988
```

- 📅 **Build Date:** `2025-12-10T01:51:37Z`
- 🏷️ **RHOAI Version:** `v3.2.0`
- 🔗 **Commit:** [`6b92f3fd`](https://github.com/red-hat-data-services/odh-dashboard/tree/6b92f3fd471805eb5424f6b379310fe2d8e778c2)
  - Full SHA: `6b92f3fd471805eb5424f6b379310fe2d8e778c2`

### Dashboard

**Image URI:**
```
quay.io/rhoai/odh-dashboard-rhel9@sha256:e9b319e962f4de5aa58c410129f31d81c0c7c2d34ec28031440a5239c4e2b89d
```

- 📅 **Build Date:** `2025-12-10T00:53:43Z`
- 🏷️ **RHOAI Version:** `v3.2.0`
- 🔗 **Commit:** [`6b92f3fd`](https://github.com/red-hat-data-services/odh-dashboard/tree/6b92f3fd471805eb5424f6b379310fe2d8e778c2)
  - Full SHA: `6b92f3fd471805eb5424f6b379310fe2d8e778c2`

### Main Branch Comparison

- **Main Branch HEAD:** [`951efd8c`](https://github.com/opendatahub-io/odh-dashboard/commit/951efd8c)
- ✅ Image commit matches current main branch

---

## 🚨 Pipeline Failure Details

**Failed Step:** `Post Actions`

**Error:** Post Actions stage failed (occurs after test execution)

### 🔍 Related Jira Issues

No related Jira issues found for this pipeline failure.

### 📋 Recent Commits (GitHub + GitLab)

**📊 GitHub Dashboard Changes (5) - Can Break E2E Tests Only:**

These Dashboard changes do NOT cause pipeline failures, only E2E test failures:

- **[2076a1991](https://github.com/opendatahub-io/odh-dashboard/commit/2076a1991b46bd16a7fe529f9ca6ea64cfa075d8)** by Matias Schimuneck: docs: Add Gen AI BFF overview and introduction guide (#5701)
- **[d02fc767a](https://github.com/opendatahub-io/odh-dashboard/commit/d02fc767a61cb3cfcd0912a897c148bbd6d2d96b)** by Emmanuel Ikeola: removed doc and docx and added txt to allowed file types (#5700)
- **[951efd8c6](https://github.com/opendatahub-io/odh-dashboard/commit/951efd8c63cf3dfd7c949e2488d1fa2acdfd55fd)** by Griffin Sullivan: Update module-federation/enhanced for react2shell vulnerability (#5703)
- **[869fe32af](https://github.com/opendatahub-io/odh-dashboard/commit/869fe32afa7add5cb1bc196c40f875caa36242cf)** by Ashley McEntee: Hide token secret behind toggle (#5591)
- **[f7a5c5353](https://github.com/opendatahub-io/odh-dashboard/commit/f7a5c5353ea25384cdc086bcd257580b73c5d330)** by Griffin Sullivan: Create page shells and navigation for MaaS Tiers (#5589)

---

## 🏥 Cluster Health

### Primary Namespace: `redhat-ods-applications`
- **Total Pods:** 12
- **Running:** 12 ✅
- **Failed:** 0 ❌

### Namespace Issues

**🔴 Namespaces with Pod Issues:**
- `openshift-insights`: 1 issue(s)
  - insights-runtime-extractor-x2j44: Phase: Failed
- `openshift-multus`: 1 issue(s)
  - network-metrics-daemon-w7vqn: Phase: Failed
- `openshift-network-diagnostics`: 1 issue(s)
  - network-check-target-wpdlk: Phase: Failed
- `openshift-network-operator`: 1 issue(s)
  - iptables-alerter-wj4nw: Phase: Failed

---

## 🔍 Detailed Test Failure Analysis

### 1. testGenAi.cy.ts

**📁 File:** `cypress/tests/e2e/gen-ai/testGenAi.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Check if the operator is RHOAI 2. Set LlamaStack to Managed 3. Wait for LlamaStack operator to be ready 4. Polling for LlamaStackOperatorReady condition (max 300s) 5. Wait for namespace redhat-ods-applications to be created 6. Enable Gen AI Studio 7. Wait for genAiStudio feature flag to be set 8. Wait for Gen AI Studio to appear in sidebar 9. Attempt 1/15 - Checking for Gen AI studio in sidebar... 10. Navigate to: https://data-science-gateway.apps.dash-e2e-rhoai.osp.rh-ods.com/ 11. Log into the application 12. Navigate to: https://data-science-gateway.apps.dash-e2e-rhoai.o
```

**📸 Failure Screenshots:**

- [Verify Gen AI Namespace - Creation and Connection -- Create and verify Gen AI Playground functionality (failed).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3695/artifact/test-output/SanitySet1/e2e/screenshots/gen-ai/testGenAi.cy.ts/Verify%20Gen%20AI%20Namespace%20-%20Creation%20and%20Connection%20--%20Create%20and%20verify%20Gen%20AI%20Playground%20functionality%20(failed).png)
- [Verify Gen AI Namespace - Creation and Connection -- Create and verify Gen AI Playground functionality (failed) (attempt 2).png (Retry)](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3695/artifact/test-output/SanitySet1/e2e/screenshots/gen-ai/testGenAi.cy.ts/Verify%20Gen%20AI%20Namespace%20-%20Creation%20and%20Connection%20--%20Create%20and%20verify%20Gen%20AI%20Playground%20functionality%20(failed)%20(attempt%202).png)

**🔄 Test Rerun on Main Branch:**
- ❌ **FAILED** on main (exit code: 1)
- **Error comparison:** ⚠️ Different error
- **Rerun error (first 300 chars):**
  ```
  
  ```
- **💡 Conclusion:** Consistent failure - needs investigation

**🐛 Jira:** No related issues found

---

### 2. testWorkbenchStorageClasses.cy.ts

**📁 File:** `cypress/tests/e2e/dataScienceProjects/workbenches/testWorkbenchStorageClasses.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Provisioning storage class 2. Provisioning project 3. Log into the application 4. Navigate to: https://data-science-gateway.apps.dash-e2e-rhoai.osp.rh-ods.com/projects 5. Navigate to the Project list tab and search for test-workbench-storage-preset-519309 6. Create storages with different access modes 7. Open workbench creation form 8. Open attach storage modal 9. Select RWO storage and verify ReadWriteOnce is displayed 10. Select RWX storage and verify ReadWriteMany is displayed 11. Select ROX storage and verify ReadOnlyMany is displayed  Timed out retrying after 10050ms:
```

**📸 Failure Screenshots:**

- [Workbench Storage Classes Tests -- Display access mode information when selecting storage to attach to workbench (failed).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3695/artifact/test-output/SmokeSet1/e2e/screenshots/dataScienceProjects/workbenches/testWorkbenchStorageClasses.cy.ts/Workbench%20Storage%20Classes%20Tests%20--%20Display%20access%20mode%20information%20when%20selecting%20storage%20to%20attach%20to%20workbench%20(failed).png)
- [Workbench Storage Classes Tests -- Display access mode information when selecting storage to attach to workbench (failed) (attempt 2).png (Retry)](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3695/artifact/test-output/SmokeSet1/e2e/screenshots/dataScienceProjects/workbenches/testWorkbenchStorageClasses.cy.ts/Workbench%20Storage%20Classes%20Tests%20--%20Display%20access%20mode%20information%20when%20selecting%20storage%20to%20attach%20to%20workbench%20(failed)%20(attempt%202).png)

**🔄 Test Rerun on Main Branch:**
- ❌ **FAILED** on main (exit code: 1)
- **Error comparison:** ⚠️ Different error
- **Rerun error (first 300 chars):**
  ```
  
  ```
- **💡 Conclusion:** Consistent failure - needs investigation

**🐛 Jira:** No related issues found

---

### 3. testEnabledISVs.cy.ts

**📁 File:** `cypress/tests/e2e/applications/explore/testEnabledISVs.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Login to the application 2. Navigate to: https://data-science-gateway.apps.dash-e2e-rhoai.osp.rh-ods.com/ 3. Navigate to the Explore page 4. Navigate to: https://data-science-gateway.apps.dash-e2e-rhoai.osp.rh-ods.com/applications/explore 5. Searching for each ISV based on the oc command output and rhoai-app manifest flag  Timed out retrying after 10000ms: Expected to find element: `[data-testid="card custom-odsci-app"] label`, but never found it.
AssertionError: Timed out retrying after 10000ms: Expected to find element: `[data-testid="card custom-odsci-app"] label`, but 
```

**📸 Failure Screenshots:**

- [Verify RHODS Explore Section Contains Only Expected ISVs -- Validate that configured ISVs display in the Explore Section (failed).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3695/artifact/test-output/SmokeSet1/e2e/screenshots/applications/explore/testEnabledISVs.cy.ts/Verify%20RHODS%20Explore%20Section%20Contains%20Only%20Expected%20ISVs%20--%20Validate%20that%20configured%20ISVs%20display%20in%20the%20Explore%20Section%20(failed).png)
- [Verify RHODS Explore Section Contains Only Expected ISVs -- Validate that configured ISVs display in the Explore Section (failed) (attempt 2).png (Retry)](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3695/artifact/test-output/SmokeSet1/e2e/screenshots/applications/explore/testEnabledISVs.cy.ts/Verify%20RHODS%20Explore%20Section%20Contains%20Only%20Expected%20ISVs%20--%20Validate%20that%20configured%20ISVs%20display%20in%20the%20Explore%20Section%20(failed)%20(attempt%202).png)

**🐛 Jira:** No related issues found

---

### 4. testWorkbenchTolerations.cy.ts

**📁 File:** `cypress/tests/e2e/settings/hardwareProfiles/testWorkbenchTolerations.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Log into the application 2. Navigate to: https://data-science-gateway.apps.dash-e2e-rhoai.osp.rh-ods.com/ 3. Navigate to workbenches tab of Project dsp-wb-tolerations-test-13607 4. Stop workbench dsp-test-wb  Timed out retrying after 10000ms: Unable to find an element by: [data-testid="notebook-table"]  Ignored nodes: comments, script, style <html   lang="en-US" >   <head>           <meta       charset="utf-8"     />     <meta       content="width=device-width,initial-scale=1"       name="viewport"     />     <meta       content="#ffffff"       name="theme-color"     />   
```

**📸 Failure Screenshots:**

- [Workbenches - tolerations tests -- Validate pod tolerations for a stopped workbench (failed).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3695/artifact/test-output/SanitySet2/e2e/screenshots/settings/hardwareProfiles/testWorkbenchTolerations.cy.ts/Workbenches%20-%20tolerations%20tests%20--%20Validate%20pod%20tolerations%20for%20a%20stopped%20workbench%20(failed).png)
- [Workbenches - tolerations tests -- Validate pod tolerations when a workbench is restarted with tolerations and tolerations are disabled (failed).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3695/artifact/test-output/SanitySet2/e2e/screenshots/settings/hardwareProfiles/testWorkbenchTolerations.cy.ts/Workbenches%20-%20tolerations%20tests%20--%20Validate%20pod%20tolerations%20when%20a%20workbench%20is%20restarted%20with%20tolerations%20and%20tolerations%20are%20disabled%20(failed).png)
- [Workbenches - tolerations tests -- Validate pod tolerations for a stopped workbench (failed) (attempt 2).png (Retry)](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3695/artifact/test-output/SanitySet2/e2e/screenshots/settings/hardwareProfiles/testWorkbenchTolerations.cy.ts/Workbenches%20-%20tolerations%20tests%20--%20Validate%20pod%20tolerations%20for%20a%20stopped%20workbench%20(failed)%20(attempt%202).png)

**🐛 Jira:** No related issues found

---

### 5. testWorkbenchTolerations.cy.ts

**📁 File:** `cypress/tests/e2e/settings/hardwareProfiles/testWorkbenchTolerations.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Log into the application 2. Navigate to: https://data-science-gateway.apps.dash-e2e-rhoai.osp.rh-ods.com/ 3. Navigate to Cluster Settings and disable Pod Tolerations 4. Navigate to workbenches tab of Project dsp-wb-tolerations-test-13607 5. Restart workbench dsp-test-wb and validate it has been started  Timed out retrying after 10000ms: Unable to find an element by: [data-testid="notebook-table"]  Ignored nodes: comments, script, style <html   lang="en-US" >   <head>           <meta       charset="utf-8"     />     <meta       content="width=device-width,initial-scale=1"  
```

**📸 Failure Screenshots:**

- [Workbenches - tolerations tests -- Validate pod tolerations for a stopped workbench (failed).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3695/artifact/test-output/SanitySet2/e2e/screenshots/settings/hardwareProfiles/testWorkbenchTolerations.cy.ts/Workbenches%20-%20tolerations%20tests%20--%20Validate%20pod%20tolerations%20for%20a%20stopped%20workbench%20(failed).png)
- [Workbenches - tolerations tests -- Validate pod tolerations when a workbench is restarted with tolerations and tolerations are disabled (failed).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3695/artifact/test-output/SanitySet2/e2e/screenshots/settings/hardwareProfiles/testWorkbenchTolerations.cy.ts/Workbenches%20-%20tolerations%20tests%20--%20Validate%20pod%20tolerations%20when%20a%20workbench%20is%20restarted%20with%20tolerations%20and%20tolerations%20are%20disabled%20(failed).png)
- [Workbenches - tolerations tests -- Validate pod tolerations for a stopped workbench (failed) (attempt 2).png (Retry)](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3695/artifact/test-output/SanitySet2/e2e/screenshots/settings/hardwareProfiles/testWorkbenchTolerations.cy.ts/Workbenches%20-%20tolerations%20tests%20--%20Validate%20pod%20tolerations%20for%20a%20stopped%20workbench%20(failed)%20(attempt%202).png)

**🐛 Jira:** No related issues found

---

### 6. testModelStopStart.cy.ts

**📁 File:** `cypress/tests/e2e/dataScienceProjects/models/testModelStopStart.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Log into the application with htpasswd-cluster-admin-user 2. Navigate to: https://data-science-gateway.apps.dash-e2e-rhoai.osp.rh-ods.com/ 3. Navigate to the Project list tab and search for test-model-stop-start-355203 4. Navigate to Model Serving and deploy a Model 5. Deploy a Model 6. Step 1: Model details 7. Step 2: Model deployment 8. Step 3: Advanced settings 9. Step 4: Review  Timed out retrying after 10000ms: Unable to find an element by: [data-testid="deployed-model-name"]  Ignored nodes: comments, script, style <div   class="pf-v6-l-stack pf-m-gutter"   data-testi
```

**📸 Failure Screenshots:**

- [A model can be stopped and started -- Verify that a model can be stopped and started (failed).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3695/artifact/test-output/SmokeSet3/e2e/screenshots/dataScienceProjects/models/testModelStopStart.cy.ts/A%20model%20can%20be%20stopped%20and%20started%20--%20Verify%20that%20a%20model%20can%20be%20stopped%20and%20started%20(failed).png)
- [A model can be stopped and started -- Verify that a model can be stopped and started (failed) (attempt 2).png (Retry)](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3695/artifact/test-output/SmokeSet3/e2e/screenshots/dataScienceProjects/models/testModelStopStart.cy.ts/A%20model%20can%20be%20stopped%20and%20started%20--%20Verify%20that%20a%20model%20can%20be%20stopped%20and%20started%20(failed)%20(attempt%202).png)

**🐛 Jira:** No related issues found

---
