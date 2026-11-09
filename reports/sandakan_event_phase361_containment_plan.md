# Phase 3.6.1 — Public Repository Containment & Remediation Plan

## 1. Executive Summary

Following the discovery that GitHub repository `sumoumou84-simon/sabah-daily-news` is public, internal Event Engine source files and operational test fixtures were verified as accessible on `origin/feature/sandakan-events-engine`.

Crucially, **no secrets, API keys, credentials, or personal data were exposed**.

This document outlines and compares four containment strategies, identifies the optimal remediation path, and provides deterministic execution steps awaiting user authorization for **Phase 3.6.2**.

---

## 2. Comprehensive Comparison of Containment Options

| Evaluation Dimension | Option A: Public Repo + Clean Feature Branch | Option B: Move All Dev to Private Repo | Option C: Switch Existing Repo to Private | Option D: Two-Tier Private Dev + Public Artifact (Recommended) |
| :--- | :--- | :--- | :--- | :--- |
| **Description** | Delete public remote feature branch; develop locally or in private branch. | Migrate engine and pipeline to a private repo; leave public repo stagnant. | Change repository visibility in GitHub Settings from Public to Private. | Maintain private repo for internal engine code; push only approved `dist_events/` artifacts to public repo. |
| **Security Benefits** | Immediately removes public branch and raw URL visibility of internal code. | Complete code privacy for all future developments and discussions. | Immediate global privacy for all branches and commits. | Maximum security: Scrapers, tests, and raw caches never touch public repo. |
| **Operational Risks** | Very Low. Local branch preserved; work is never lost. | Moderate. Requires managing repo sync and dual remotes. | **CRITICAL HIGH RISK:** Disables GitHub Pages on free accounts! | Low. Clean separation of concerns. |
| **Impact on News Website** | **Zero.** News pipeline and site unaffected. | **Zero.** | High risk of disruption. | **Zero.** News website remains 100% stable. |
| **Impact on GitHub Pages** | **Zero.** `https://sumoumou84-simon.github.io/sabah-daily-news/` continues running normally. | **Zero.** | **FATAL:** Free GitHub accounts disable Pages on private repos (site goes 404). | **Zero.** Pages continues to serve public files seamlessly. |
| **History Rewriting Needed?** | **No.** Deleting remote ref removes branch. `main` history remains clean. | **No.** | **No.** | **No.** |
| **Collaborator / Workflow Impact** | Workflow `sandakan_events_publish.yml` disabled until re-targeted. News workflow intact. | Team must be invited to private repo. | Public readers cannot access site. | Internal engine developers work in private repo; public repo receives only clean static releases. |

---

## 3. Critical Analysis of Option C (Visibility Change)

> [!CAUTION]
> **Why Option C Must Be Rejected:**
> On GitHub Free accounts, **GitHub Pages is exclusively supported on Public repositories**. Changing `sumoumou84-simon/sabah-daily-news` to Private will immediately unpublish the live news website, returning HTTP 404 to all readers, unless an active GitHub Pro, Team, or Enterprise subscription is attached to the account.

---

## 4. Recommended Remediation Strategy: Immediate Containment + Option D Architecture

We recommend a two-phase containment:

### Step 1: Immediate Containment (Phase 3.6.2)
1. **Delete Remote Feature Branch:**
   Execute `git push origin --delete feature/sandakan-events-engine`.  
   *Result:* The 28 internal files become immediately inaccessible via GitHub branch navigation and `raw.githubusercontent.com`.
2. **Revert Workflow on `main` (Optional/Cleanliness):**
   Remove `.github/workflows/sandakan_events_publish.yml` from `main` or retain it dormant with `skip ci`.
3. **Preserve Full Local Work:**
   The local branch `feature/sandakan-events-engine` remains completely intact on the local workstation with all code, tests, and documentation.

### Step 2: Long-Term Enterprise Architecture (Option D)
1. Initialize a private repository (e.g. `sumoumou84-simon/sandakan-event-engine-core`) for internal development, scrapers, and tests.
2. The public `sabah-daily-news` repository receives **strictly pre-built, allowlisted static web artifacts** (`dist_events/` containing `events.html`, `events_frontend.json`, and icons).

---

## 5. Exact Remediation Execution Steps (For Phase 3.6.2 Authorization)

When authorized, Phase 3.6.2 will execute strictly the following non-destructive commands:

```bash
# 1. Verify working directory cleanliness (maintaining the 4 diagnostic files unstaged)
git status --short

# 2. Delete the public remote feature branch containing internal engine code
git push origin --delete feature/sandakan-events-engine

# 3. Confirm remote branch deletion
git ls-remote --heads origin feature/sandakan-events-engine
# Expected output: (empty)

# 4. Remove dormant publish workflow from main (optional, keeps main completely clean)
git checkout main
git rm .github/workflows/sandakan_events_publish.yml
git commit -m "chore: remove dormant event workflow from public main branch [skip ci]"
git push origin main

# 5. Verify live public site and raw URL returns 404 for removed branch
python -c "import urllib.request; ..."
```

---

## 6. Rollback & Safety Considerations

1. **Local Work Safety:** Local branch `feature/sandakan-events-engine` is never deleted or modified during containment.
2. **News Website Isolation:** `news_data.json`, `index.html`, and `morning_publish.yml` are never touched.
3. **Zero Cost:** 0 Gemini API calls.

---

## 7. Status

**STOP CONDITION APPLIED:** All audit reports and containment plans are prepared. No deletion, rewriting, moving, committing, or pushing has been performed in Phase 3.6.1. Awaiting user authorization for Phase 3.6.2.
