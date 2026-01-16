# 🚀 RHOAI Nightly Analysis - Build #3666

**📅 Date:** 2025-12-08 15:36:44
**🔗 Build URL:** [3666](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3666/)

---

## 📊 Quick Status Overview

### ❌ **2 TEST(S) FAILED**

- **Total Tests:** 80
- **Passed:** 78
- **Failed:** 2

**Failed Tests:**
1. `Create workbench with RWO storage and verify storage attachment`
2. `Should display storage classes with different access modes in cluster storage dropdown`

---

## 🐳 Deployment & Image Information

### Main Branch Comparison

- **Main Branch HEAD:** [`7486e0ea`](https://github.com/opendatahub-io/odh-dashboard/commit/7486e0ea)
- ✅ Image commit matches current main branch

---

## 🚨 Pipeline Failure Details

**Failed Step:** `Unknown pipeline step`

**Error:** Build failed but specific step not identified

### 🔍 Related Jira Issues

No related Jira issues found for this pipeline failure.

### 📋 Recent GitLab Commits

No recent commits found before this build.

---

## 🏥 Cluster Health

---

## 🔍 Detailed Test Failure Analysis

### 1. Create workbench with RWO storage and verify storage attachment

**📁 File:** `cypress/tests/e2e/dataScienceProjects/workbenches/testWorkbenchStorageClasses.cy.ts`

**📝 Code Analysis:**

**❌ Original Error:**
```
Test steps were:  1. Provisioning storage class 2. Provisioning project 3. Log into the application 4. Navigate to: https://data-science-gateway.apps.dash-e2e-rhoai.osp.rh-ods.com/projects 5. Navigate to the Project list tab and search for test-workbench-storage-preset 6. Create storages with different access modes 7. Open workbench creation form 8. Open attach storage modal 9. Select RWO storage and verify ReadWriteOnce is displayed 10. Select RWX storage and verify ReadWriteMany is displayed 11. Select ROX storage and verify ReadOnlyMany is displayed  Timed out retrying after 10050ms: `cy.cl
```

**📸 Failure Screenshots:**

**Cluster Storage Access Modes Tests -- Should display storage classes with different access modes in cluster storage dropdown (failed).png:**
![Cluster Storage Access Modes Tests -- Should display storage classes with different access modes in cluster storage dropdown (failed).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3666/artifact/test-output/SmokeSet2/e2e/screenshots/dataScienceProjects/clusterStorage/testClusterStorageAccessModes.cy.ts/Cluster Storage Access Modes Tests -- Should display storage classes with different access modes in cluster storage dropdown (failed).png)
[📥 Download](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3666/artifact/test-output/SmokeSet2/e2e/screenshots/dataScienceProjects/clusterStorage/testClusterStorageAccessModes.cy.ts/Cluster Storage Access Modes Tests -- Should display storage classes with different access modes in cluster storage dropdown (failed).png)

**Workbench Storage Classes Tests -- Display access mode information when selecting storage to attach to workbench (failed).png:**
![Workbench Storage Classes Tests -- Display access mode information when selecting storage to attach to workbench (failed).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3666/artifact/test-output/SmokeSet1/e2e/screenshots/dataScienceProjects/workbenches/testWorkbenchStorageClasses.cy.ts/Workbench Storage Classes Tests -- Display access mode information when selecting storage to attach to workbench (failed).png)
[📥 Download](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3666/artifact/test-output/SmokeSet1/e2e/screenshots/dataScienceProjects/workbenches/testWorkbenchStorageClasses.cy.ts/Workbench Storage Classes Tests -- Display access mode information when selecting storage to attach to workbench (failed).png)

**Workbenches - variable tests -- Verify user can set environment variables in their workbenches by uploading a yaml Secret and Config Map file (failed).png:**
![Workbenches - variable tests -- Verify user can set environment variables in their workbenches by uploading a yaml Secret and Config Map file (failed).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3666/artifact/test-output/SanitySet3/e2e/screenshots/dataScienceProjects/workbenches/testWorkbenchVariables.cy.ts/Workbenches - variable tests -- Verify user can set environment variables in their workbenches by uploading a yaml Secret and Config Map file (failed).png)
[📥 Download](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3666/artifact/test-output/SanitySet3/e2e/screenshots/dataScienceProjects/workbenches/testWorkbenchVariables.cy.ts/Workbenches - variable tests -- Verify user can set environment variables in their workbenches by uploading a yaml Secret and Config Map file (failed).png)

**Cluster Storage Access Modes Tests -- Should display storage classes with different access modes in cluster storage dropdown (failed) (attempt 2).png (Retry):**
![Cluster Storage Access Modes Tests -- Should display storage classes with different access modes in cluster storage dropdown (failed) (attempt 2).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3666/artifact/test-output/SmokeSet2/e2e/screenshots/dataScienceProjects/clusterStorage/testClusterStorageAccessModes.cy.ts/Cluster Storage Access Modes Tests -- Should display storage classes with different access modes in cluster storage dropdown (failed) (attempt 2).png)
[📥 Download](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3666/artifact/test-output/SmokeSet2/e2e/screenshots/dataScienceProjects/clusterStorage/testClusterStorageAccessModes.cy.ts/Cluster Storage Access Modes Tests -- Should display storage classes with different access modes in cluster storage dropdown (failed) (attempt 2).png)

**Workbench Storage Classes Tests -- Display access mode information when selecting storage to attach to workbench (failed) (attempt 2).png (Retry):**
![Workbench Storage Classes Tests -- Display access mode information when selecting storage to attach to workbench (failed) (attempt 2).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3666/artifact/test-output/SmokeSet1/e2e/screenshots/dataScienceProjects/workbenches/testWorkbenchStorageClasses.cy.ts/Workbench Storage Classes Tests -- Display access mode information when selecting storage to attach to workbench (failed) (attempt 2).png)
[📥 Download](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3666/artifact/test-output/SmokeSet1/e2e/screenshots/dataScienceProjects/workbenches/testWorkbenchStorageClasses.cy.ts/Workbench Storage Classes Tests -- Display access mode information when selecting storage to attach to workbench (failed) (attempt 2).png)

**🐛 Jira:** No related issues found

---

### 2. Should display storage classes with different access modes in cluster storage dropdown

**📁 File:** `cypress/tests/e2e/dataScienceProjects/clusterStorage/testClusterStorageAccessModes.cy.ts`

**📝 Code Analysis:**
- 🔧 **Test NEEDS MAINTENANCE** (`@Maintain` tag)

**❌ Original Error:**
```
Test steps were:  1. Provisioning storage classes with different access modes 2. Provisioning project 3. Log into the application 4. Navigate to: https://data-science-gateway.apps.dash-e2e-rhoai.osp.rh-ods.com/projects 5. Navigate to the Project list tab and search for test-cluster-storage-access-modes 6. Navigate to the Cluster Storage tab 7. Open the Create cluster storage modal 8. Verify storage class dropdown is enabled and contains our storage classes 9. Click on the storage class dropdown to open it 10. Verify storage classes with different access modes are available  Timed out retrying 
```

**📸 Failure Screenshots:**

**Cluster Storage Access Modes Tests -- Should display storage classes with different access modes in cluster storage dropdown (failed).png:**
![Cluster Storage Access Modes Tests -- Should display storage classes with different access modes in cluster storage dropdown (failed).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3666/artifact/test-output/SmokeSet2/e2e/screenshots/dataScienceProjects/clusterStorage/testClusterStorageAccessModes.cy.ts/Cluster Storage Access Modes Tests -- Should display storage classes with different access modes in cluster storage dropdown (failed).png)
[📥 Download](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3666/artifact/test-output/SmokeSet2/e2e/screenshots/dataScienceProjects/clusterStorage/testClusterStorageAccessModes.cy.ts/Cluster Storage Access Modes Tests -- Should display storage classes with different access modes in cluster storage dropdown (failed).png)

**Workbench Storage Classes Tests -- Display access mode information when selecting storage to attach to workbench (failed).png:**
![Workbench Storage Classes Tests -- Display access mode information when selecting storage to attach to workbench (failed).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3666/artifact/test-output/SmokeSet1/e2e/screenshots/dataScienceProjects/workbenches/testWorkbenchStorageClasses.cy.ts/Workbench Storage Classes Tests -- Display access mode information when selecting storage to attach to workbench (failed).png)
[📥 Download](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3666/artifact/test-output/SmokeSet1/e2e/screenshots/dataScienceProjects/workbenches/testWorkbenchStorageClasses.cy.ts/Workbench Storage Classes Tests -- Display access mode information when selecting storage to attach to workbench (failed).png)

**Cluster Storage Access Modes Tests -- Should display storage classes with different access modes in cluster storage dropdown (failed) (attempt 2).png (Retry):**
![Cluster Storage Access Modes Tests -- Should display storage classes with different access modes in cluster storage dropdown (failed) (attempt 2).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3666/artifact/test-output/SmokeSet2/e2e/screenshots/dataScienceProjects/clusterStorage/testClusterStorageAccessModes.cy.ts/Cluster Storage Access Modes Tests -- Should display storage classes with different access modes in cluster storage dropdown (failed) (attempt 2).png)
[📥 Download](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3666/artifact/test-output/SmokeSet2/e2e/screenshots/dataScienceProjects/clusterStorage/testClusterStorageAccessModes.cy.ts/Cluster Storage Access Modes Tests -- Should display storage classes with different access modes in cluster storage dropdown (failed) (attempt 2).png)

**Workbench Storage Classes Tests -- Display access mode information when selecting storage to attach to workbench (failed) (attempt 2).png (Retry):**
![Workbench Storage Classes Tests -- Display access mode information when selecting storage to attach to workbench (failed) (attempt 2).png](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3666/artifact/test-output/SmokeSet1/e2e/screenshots/dataScienceProjects/workbenches/testWorkbenchStorageClasses.cy.ts/Workbench Storage Classes Tests -- Display access mode information when selecting storage to attach to workbench (failed) (attempt 2).png)
[📥 Download](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3666/artifact/test-output/SmokeSet1/e2e/screenshots/dataScienceProjects/workbenches/testWorkbenchStorageClasses.cy.ts/Workbench Storage Classes Tests -- Display access mode information when selecting storage to attach to workbench (failed) (attempt 2).png)

**🐛 Jira:** No related issues found

---
