# Essential Commands for Dashboard Build Analyzer

## 🚀 Quick Analysis Commands

### Analyze Latest Build (Fastest - One Command)

```bash
cd /Users/acoughli/dashboard-build-analyzer && venv/bin/python scripts/analyze_job.py --job "cypress/dashboard-tests" --build latest
```

### Full RHOAI Analysis (Most Complete)

```bash
cd /Users/acoughli/dashboard-build-analyzer && venv/bin/python scripts/comprehensive_analysis.py 3695 rhoai
```

### Full ODH Analysis

```bash
cd /Users/acoughli/dashboard-build-analyzer && venv/bin/python scripts/comprehensive_analysis.py 3691 odh
```

## 📂 Report Locations

```bash
# RHOAI Reports
cat reports/current/RHOAI/latest-build-*.md

# ODH Reports
cat reports/current/ODH/latest-build-*.md

# Generic Job Reports
cat reports/analysis-*.md
```

## 🔍 Find Build Number

```bash
cd /Users/acoughli/dashboard-build-analyzer && venv/bin/python scripts/analyze_job.py --job "cypress/dashboard-tests" --build latest 2>&1 | grep "Build #"
```

## ✅ Key Facts

1. **Test reruns happen automatically** - no flags needed
2. **`--build latest` finds the newest build** automatically
3. **`comprehensive_analysis.py`** = full features (image tracking, sync detection, GitLab correlation)
4. **`analyze_job.py`** = quick analysis (any job, auto-finds latest)
5. All credentials loaded from `.env` file

## 📖 Full Documentation

- **Quick Guide:** `docs/CLAUDE_AGENT_GUIDE.md`
- **Full README:** `README.md`











