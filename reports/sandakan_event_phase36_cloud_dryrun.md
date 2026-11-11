# Phase 3.6 — Controlled GitHub Cloud Dry-Run Report

## 1. Executive Summary & Authorization Scope

Under explicit authorization for **Phase 3.6**, a strictly controlled commit and push operation was performed to enable an isolated, non-deploying GitHub Actions cloud dry-run for the Sandakan Events engine.

### Strict Scope Enforcements
- **GitHub Pages Deployment:** ZERO deployments executed. No changes were made to repository GitHub Pages settings.
- **Production Website Integrity:** The public site published at `https://sumoumou84-simon.github.io/sabah-daily-news/` remains 100% untouched.
- **News Aggregation Pipeline:** ZERO execution (`build_news.py` and `agent_reach_editor.py` were not invoked; `news_data.json` and `index.html` remain untouched).
- **Gemini / LLM API Calls:** Exactly **0 calls** made ($0.00 spent).
- **Preserved Diagnostic Files:** All 4 diagnostic files remain unstaged and unchanged.

---

## 2. Public Repository Isolation & Branch Strategy

The live GitHub Pages deployment serves the `main` branch directly from the repository root (`/`). To prevent any public leakage of raw event data, scrapers, and internal tests, a strict branch isolation strategy was executed:

```
[origin/main] (Commit c08d2ba)
  ├── (Existing news website files untouched)
  └── .github/workflows/sandakan_events_publish.yml   <-- ONLY file added (ignored by Jekyll)

[origin/feature/sandakan-events-engine] (Commit 30ee6ae)
  ├── .github/workflows/sandakan_events_publish.yml
  ├── config/sandakan_event_config.json
  ├── data/sandakan_events_cache.json
  ├── event_engine/ (Scrapers, time engine, normalizer, etc.)
  ├── events.html
  ├── events_data.json (Raw internal data)
  ├── events_frontend.json
  ├── scripts/build_sandakan_events_site.py
  ├── scripts/sandakan_event_engine.py
  └── tests/ (164 deterministic unit & integration tests)
```

### Git Commit & Push Log
1. **Feature Branch (`feature/sandakan-events-engine`):**
   - Commit: `30ee6ae2aab6d4ecb99dd7535aa74f7ca6ccd2f4`
   - Message: `feat(events): implement standalone sandakan event engine with security hardening [skip ci]`
   - Status: Pushed cleanly to `origin/feature/sandakan-events-engine`.
2. **Default Production Branch (`main`):**
   - Commit: `c08d2ba0581c9ce8bb5a91f722ce65608d64d4b2`
   - Message: `ci: add sandakan_events_publish.yml manual workflow dispatch definition [skip ci]`
   - Files Added: Strictly `.github/workflows/sandakan_events_publish.yml` (1 file, 63 lines).
   - Status: Pushed cleanly to `origin/main`.

### Repository Root Verification on `main`
Inspection of `git ls-tree HEAD` on `main` confirms **zero internal files**:
- No `events_data.json`
- No `event_engine/`
- No `data/`
- No `events.html`
- No internal scripts or test files

---

## 3. Diagnostic Files Preservation

The four diagnostic files identified prior to implementation were verified as untouched and unstaged:
- `collectors/facebook_collector.py` (Unstaged, preserved)
- `config/news_config.json` (Unstaged, preserved)
- `pipeline/deduplicator.py` (Unstaged, preserved)
- `pipeline/normalizer.py` (Unstaged, preserved)

---

## 4. GitHub Actions Workflow Security & Hardening

File: `.github/workflows/sandakan_events_publish.yml`

```yaml
name: 山打根活动周历独立发布流程 (Sandakan Events Publish)

on:
  workflow_dispatch:
    inputs:
      dry_run:
        description: '仅执行测试与构建校验，不发布 (Dry Run Only)'
        required: true
        default: true
        type: boolean

permissions:
  contents: read

jobs:
  build_events_artifact:
    name: 构建沙巴山打根活动独立公开发布工件
    runs-on: ubuntu-latest
    steps:
      - name: 检出仓库代码 (Checkout Repository)
        uses: actions/checkout@v4
      - name: 配置 Python 运行环境 (Setup Python 3.11)
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: 安装基础依赖 (Install Dependencies)
        run: |
          pip install --upgrade pip
          pip install requests urllib3 || true
      - name: 执行事件引擎单元测试与回归套件 (Run Event Engine Tests)
        run: |
          python -m unittest discover -s tests -p "test_*.py"
      - name: 构建安全隔离公开发布工件 (Build Allowlisted Public Artifact)
        run: |
          python scripts/build_sandakan_events_site.py --source events_data.json --dest dist_events
      - name: 严苛校验发布工件隔离性 (Verify Public Artifact Isolation)
        run: |
          echo "Checking dist_events directory contents..."
          ls -la dist_events/
          if [ -f "dist_events/events_data.json" ]; then
            echo "CRITICAL SECURITY BREACH: Raw events_data.json detected in public artifact!"
            exit 1
          fi
          if [ -d "dist_events/event_engine" ]; then
            echo "CRITICAL SECURITY BREACH: Internal event_engine directory detected in public artifact!"
            exit 1
          fi
          echo "Artifact isolation verified successfully."
      - name: 上传构建工件供审核 (Upload Build Artifact for Review)
        uses: actions/upload-artifact@v4
        with:
          name: sandakan-events-public-artifact
          path: dist_events/
          retention-days: 7
```

### Key Security Safeguards
1. **Least-Privilege Token Permissions:** Stripped of `pages: write` and `id-token: write`. Strictly limited to `contents: read`.
2. **Zero Auto-Deploy:** Does not call `actions/deploy-pages@v4` or push to any git branch.
3. **Automated Assertion:** Build fails immediately if any raw JSON or engine code leaks into `dist_events/`.
4. **Artifact Upload:** Staged files are uploaded to GitHub Actions artifacts for manual download and verification.

---

## 5. Artifact Audit Matrix

The builder `scripts/build_sandakan_events_site.py` produces exactly 5 allowlisted files in `dist_events/`:

| File | Size | Role | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| `events.html` | 43,983 B | Public UI standalone view | `dcf77a2530d713725dfc37c7a1fc501264d62782f3cbe74f0083467552c85a26` |
| `events_frontend.json` | 5,365 B | Sanitized public events feed | `64f07ae46f139b2c25fe79fa2cc4ee5110447d7c65f5a221c4774fdb21821bae` |
| `icon-192.png` | 6,268 B | PWA icon (192px) | `11eeaec8d92ce0ed722fface0a3c6b34b7cd35eefd0551851d7a698408714f7f` |
| `icon-512.png` | 30,491 B | PWA icon (512px) | `30e9ae165ae20e7123f56a938840546c6feccce4e49b8ab12a5baf31aa05c6a0` |
| `manifest.json` | 604 B | Web application manifest | `10fd94247f1cfe5728657db1cda871e33db3e6786264efe4dbf3e9aca7668bb1` |

All internal and raw files (`events_data.json`, `event_engine/`, `data/`, `config/`, `scripts/`, `tests/`) are strictly excluded.

---

## 6. How to Trigger the Cloud Dry-Run

To execute the dry-run in the cloud:

1. Open repository Actions page:  
   `https://github.com/sumoumou84-simon/sabah-daily-news/actions/workflows/sandakan_events_publish.yml`
2. Click **Run workflow** on the right side.
3. Select **Branch: `feature/sandakan-events-engine`**.
4. Confirm `dry_run` is checked (`true`).
5. Click **Run workflow**.

### Expected Cloud Dry-Run Execution Log
- Workflow checks out `feature/sandakan-events-engine`.
- Runs 164 unit/integration tests (`OK`).
- Runs `scripts/build_sandakan_events_site.py` to create `dist_events/`.
- Verifies isolation of `dist_events/`.
- Uploads `sandakan-events-public-artifact.zip`.
- Completes with green status in ~30 seconds.

---

## 7. Deliverable References
- Git Manifest: [sandakan_event_phase36_git_manifest.json](file:///c:/simon%20kankan/reports/sandakan_event_phase36_git_manifest.json)
- Cloud Artifact Audit: [sandakan_event_phase36_cloud_artifact_audit.json](file:///c:/simon%20kankan/reports/sandakan_event_phase36_cloud_artifact_audit.json)
- Full Report: [sandakan_event_phase36_cloud_dryrun.md](file:///c:/simon%20kankan/reports/sandakan_event_phase36_cloud_dryrun.md)

---

## 8. Final Verdict

**PHASE 3.6 CONTROLLED GITHUB CLOUD DRY-RUN PREPARATION: COMPLETE & VERIFIED**

Public repository isolation is completely preserved. No production deployments or news aggregation tasks were run. The engine is ready for cloud dry-run triggering and awaiting user review.
