# 🚀 RHOAI Nightly Analysis - Build #3676

**📅 Date:** 2025-12-08 16:13:57
**🔗 Build URL:** [3676](https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com/job/cypress/job/dashboard-tests/3676/)

---

## 📊 Quick Status Overview

### ⚠️ **TESTS NOT EXECUTED**

Tests did not run due to a deployment failure during the pipeline.

See **Pipeline Failure Details** section below for complete error information.

---

## 🐳 Deployment & Image Information

---

## 🚨 Pipeline Failure Details

**Failed Step:** `Verify Dashboard is Ready`

**Error:** Stage "Verify Dashboard is Ready" failed with error signal

🐛 **Known Issue:** [RHOAIENG-38766](https://issues.redhat.com/browse/RHOAIENG-38766)

### 🔍 Related Jira Issues

No related Jira issues found for this pipeline failure.

### 📋 Recent Commits (GitHub + GitLab)

**🚨 GitLab Jenkins Changes (3) - Can Break Pipeline:**

These Jenkins configuration changes may have caused the pipeline failure:

- **[02c7cbeb](https://gitlab.cee.redhat.com/ods/jenkins/-/commit/02c7cbeb4cca325124ef5b8a9a7058c4e0ec3f7c)** by Radim Kubis
  - New(vars/doPostBuildActions): Add ReportPortal link to currentBuild description
  - Committed: 2025-12-05 15:40:16 +0000

- **[59085e41](https://gitlab.cee.redhat.com/ods/jenkins/-/commit/59085e4174ecaefd408e5cdaeee4243a1d9a4a4f)** by Berto D'Attoma
  - Add 1 git-crypt collaborator - Christopher Chase
  - Committed: 2025-12-05 10:40:11 +0000

- **[f253fd05](https://gitlab.cee.redhat.com/ods/jenkins/-/commit/f253fd0508fe0f9e043da50a8717d1eeddf0b425)** by Noam Manos
  - Dashboard-E2E: Fail build if dashboard route verification fails
  - Committed: 2025-12-05 06:07:25 +0000

**📊 GitHub Dashboard Changes (8) - Can Break E2E Tests Only:**

These Dashboard changes do NOT cause pipeline failures, only E2E test failures:

- **[2076a1991](https://github.com/opendatahub-io/odh-dashboard/commit/2076a1991b46bd16a7fe529f9ca6ea64cfa075d8)** by Matias Schimuneck: docs: Add Gen AI BFF overview and introduction guide (#5701)
- **[d02fc767a](https://github.com/opendatahub-io/odh-dashboard/commit/d02fc767a61cb3cfcd0912a897c148bbd6d2d96b)** by Emmanuel Ikeola: removed doc and docx and added txt to allowed file types (#5700)
- **[951efd8c6](https://github.com/opendatahub-io/odh-dashboard/commit/951efd8c63cf3dfd7c949e2488d1fa2acdfd55fd)** by Griffin Sullivan: Update module-federation/enhanced for react2shell vulnerability (#5703)
- **[869fe32af](https://github.com/opendatahub-io/odh-dashboard/commit/869fe32afa7add5cb1bc196c40f875caa36242cf)** by Ashley McEntee: Hide token secret behind toggle (#5591)
- **[f7a5c5353](https://github.com/opendatahub-io/odh-dashboard/commit/f7a5c5353ea25384cdc086bcd257580b73c5d330)** by Griffin Sullivan: Create page shells and navigation for MaaS Tiers (#5589)
- ... and 3 more Dashboard commit(s)

---

## 🏥 Cluster Health

---
