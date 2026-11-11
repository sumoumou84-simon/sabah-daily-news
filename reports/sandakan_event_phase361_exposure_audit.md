# Phase 3.6.1 — Public Repository Exposure Audit Report

## 1. Executive Security Assessment

**OVERALL AUDIT VERDICT:**
```
================================================================================
                      PUBLIC INTERNAL SOURCE EXPOSURE
================================================================================
```

### Critical Distinction: Source Code vs. Sensitive Secrets
- **No Sensitive Data Leaked:** A comprehensive regex and semantic scan of all 46 commits in the repository history confirmed **ZERO API keys, tokens, passwords, credentials, or Personal Identifiable Information (PII)** exist in the repository. No key revocation or credential rotation is required.
- **The Exposure Condition:** The GitHub repository `sumoumou84-simon/sabah-daily-news` is configured as a **Public** repository. When branch `feature/sandakan-events-engine` was pushed to remote in Phase 3.6, all 28 committed files became anonymously readable via GitHub's web interface and `raw.githubusercontent.com`.
- **Nature of Exposed Materials:** Internal application source code (`event_engine/`), scraper heuristics, collector configurations (`config/sandakan_event_config.json`), raw event fixtures (`events_data.json`), operational caches (`data/sandakan_events_cache.json`), and internal unit tests (`tests/`).

---

## 2. Public Exposure Verification Evidence

Live anonymous HTTP accessibility tests were conducted against GitHub's raw endpoints without authentication headers:

| Audited Target | Exists on `feature` | Raw HTTP Status | Exists on `main` | Production Pages Status | Information Classification |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `events_data.json` | **YES** | **200 (Public)** | NO | **404 (Not Deployed)** | Internal raw event schema & unverified draft records |
| `data/sandakan_events_cache.json` | **YES** | **200 (Public)** | NO | **404 (Not Deployed)** | Operational collector fallback cache & stale state |
| `config/sandakan_event_config.json` | **YES** | **200 (Public)** | NO | **404 (Not Deployed)** | System configuration, geo-boundaries, timeouts |
| `event_engine/` | **YES** | **200 (Public)** | NO | **404 (Not Deployed)** | Complete internal Python scrapers and normalization engine |
| `scripts/sandakan_event_engine.py` | **YES** | **200 (Public)** | NO | **404 (Not Deployed)** | Internal CLI execution script |
| `scripts/build_sandakan_events_site.py` | **YES** | **200 (Public)** | NO | **404 (Not Deployed)** | Public artifact isolation and build script |
| `events_frontend.json` | **YES** | **200 (Public)** | NO | **404 (Not Deployed)** | Sanitized public event feed (designed for public UI) |
| `events.html` | **YES** | **200 (Public)** | NO | **404 (Not Deployed)** | Public events frontend single-page application |
| `tests/` | **YES** | **200 (Public)** | NO | **404 (Not Deployed)** | Internal test suite and deterministic mocks |
| `.github/workflows/sandakan_events_publish.yml` | **YES** | **200 (Public)** | **YES** | N/A (Dot-directory ignored) | CI workflow dispatch definition |

### Live GitHub Pages Production Status
Tests against `https://sumoumou84-simon.github.io/sabah-daily-news/`:
- `GET /` -> **HTTP 200** (Original production Sabah Daily News frontpage intact)
- `GET /events.html` -> **HTTP 404** (Not deployed)
- `GET /events_frontend.json` -> **HTTP 404** (Not deployed)
- `GET /events_data.json` -> **HTTP 404** (Not deployed)

---

## 3. Affected Commit References & Historical Exposure Audit

### Commit Trace
1. **Commit `30ee6ae2aab6d4ecb99dd7535aa74f7ca6ccd2f4`**  
   - Branch: `feature/sandakan-events-engine` (Remote: `origin/feature/sandakan-events-engine`)
   - Introduced: 28 files (7,528 insertions) representing the internal Event Engine, config, cache, scripts, and tests.
   - Accessibility: Anonymously visible to anyone viewing the public repository branch dropdown or directly querying the branch ref.
2. **Commit `c08d2ba0581c9ce8bb5a91f722ce65608d64d4b2`**  
   - Branch: `main` (Remote: `origin/main`)
   - Introduced: Strictly 1 file (`.github/workflows/sandakan_events_publish.yml`).
   - Accessibility: Visible in GitHub Actions and repository `.github` tree.

### Historical Audit Findings
- **Single Introduction Point:** Sandakan Event Engine files were introduced in exactly **one** commit (`30ee6ae`).
- **No Earlier Commits Affected:** Inspection of all 45 preceding commits in the Git history confirmed that internal event files were never committed previously.
- **No Dangling Tags or References:** `git show-ref` verified that only `main` and `feature/sandakan-events-engine` reference these commits; no tags or secondary branches preserve them.

---

## 4. Credential and Personal-Data Assessment

An automated scan covering all files in commit `30ee6ae` and all 46 historical repository commits checked for:
- GitHub Personal Access Tokens (`ghp_*`, `github_pat_*`): **0 matches**
- Google API Keys (`AIza*`): **0 matches**
- OpenAI API Keys (`sk-*`): **0 matches**
- Generic Secrets / Passwords / Auth Headers: **0 matches**
- Personal Email Addresses: **0 matches**
- Personal Phone Numbers: **0 matches**

All event organizers and venue contacts listed in `events_data.json` are publicly registered entities (Sabah Forestry Department, Borneo Bird Club, Ticket2U Malaysia, Persatuan Ortopedik Sandakan) with publicly published official URLs.

**Conclusion:** Zero secrets exist. No token revocation or credential rotation is required.

---

## 5. Production Branch Safety Assessment

1. **`main` Branch Integrity:**
   - `git diff 30b58ab..c08d2ba` shows strictly 1 file modified: `.github/workflows/sandakan_events_publish.yml`.
   - `news_data.json` is completely unchanged.
   - `index.html` is completely unchanged.
   - `.github/workflows/morning_publish.yml` is completely unchanged.
2. **Preserved Diagnostic Files:**
   The following 4 diagnostic files remain untouched in the working directory and completely unstaged:
   - `collectors/facebook_collector.py`
   - `config/news_config.json`
   - `pipeline/deduplicator.py`
   - `pipeline/normalizer.py`
3. **GitHub Pages Serving Integrity:**
   GitHub Pages continues to serve the live news site normally without regression or interruption.

---

## 6. Workflow Security Audit (`sandakan_events_publish.yml`)

1. **Triggers:** Strictly `on: workflow_dispatch`. No `push` triggers and no `schedule` (cron) triggers exist.
2. **Permissions:**
   ```yaml
   permissions:
     contents: read
   ```
   Least-privilege is enforced. The workflow token cannot push to any branch or write to GitHub Pages.
3. **Execution Steps:**
   - Checks out code, sets up Python 3.11, runs unit tests.
   - Builds public staging directory `dist_events/`.
   - Asserts zero internal files (`events_data.json`, `event_engine/`) exist in `dist_events/`.
   - Uploads artifact using `actions/upload-artifact@v4`.
4. **Audit of `dry_run` Parameter:**
   - Parameter `inputs.dry_run` is declared as a boolean with default `true`.
   - **Finding:** The step definitions do not evaluate `${{ inputs.dry_run }}`.
   - **Risk Evaluation:** This does **NOT** present a deployment risk because the workflow has **zero deployment actions** and lacks `pages: write` / `contents: write` permissions. The workflow is inherently a 100% dry-run build-and-test pipeline. Setting `dry_run: false` does not trigger deployment.

---

## 7. Deliverable References
- Exposure Manifest: [reports/sandakan_event_phase361_exposure_manifest.json](file:///c:/simon%20kankan/reports/sandakan_event_phase361_exposure_manifest.json)
- Containment Strategy Plan: [reports/sandakan_event_phase361_containment_plan.md](file:///c:/simon%20kankan/reports/sandakan_event_phase361_containment_plan.md)
