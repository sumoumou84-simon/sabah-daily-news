# Sandakan 14-Day Event Engine — Test Plan & Quality Assurance Suite
**Project:** Sabah Daily News / 西门看看网  
**Component:** Independent Sandakan Event Engine (`scripts/sandakan_event_engine.py`)  
**Test Suite Specification:** Version 1.0.0-PROD-TEST  
**Target Environment:** Local Python 3.10+ / GitHub Actions CI  
**Deterministic Mandate:** 100% Mocked Network / ZERO Gemini API Calls / 0 Flakiness  

---

## 1. Test Architecture & Objectives

The Event Engine quality assurance suite validates that no unverified, misplaced, or chronologically inaccurate event ever reaches production. Tests are executed deterministically using fixture-based inputs with strict assertion barriers.

### Core Testing Pillars:
- **Zero Generative Reliance:** All tests verify deterministic rules (regex, datetime offsets, bounding boxes, fuzzy deduplication). No dynamic AI inference is used in unit tests.
- **Hermetic Isolation:** External HTTP requests (Sabah Tourism Board, Ticket2U, Daily Express, MPS) are completely mocked via synthetic response fixtures. Tests run safely offline.
- **Fail-Closed Safety:** Incomplete, contradictory, or unverified events must fail closed (i.e., blocked from publication) by default.

---

## 2. Test Matrix — 15 Deterministic Scenarios

| Test ID | Test Case Name | Objective / Trigger | Expected Outcome |
|---|---|---|---|
| **TEST-01** | `test_tier1_statutory_ingest` | Feed valid Sabah Tourism Board (STB) event fixture with Sandakan venue and dates | Parsed successfully; assigned `TIER_1_OFFICIAL`; `OFFICIAL_CONFIRMED`; approved for publication |
| **TEST-02** | `test_tier2_ticketing_ingest` | Feed Ticket2U event payload with valid ticket link and pricing for Sandakan | Parsed successfully; assigned `TIER_2_ESTABLISHED_ORGANISER`; `OFFICIAL_CONFIRMED` |
| **TEST-03** | `test_tier3_media_corroboration` | Feed 2 independent media articles (Daily Express + Sin Chew) reporting same tournament | Merged into single entity; `MULTI_SOURCE_CONFIRMED`; approved for publication |
| **TEST-04** | `test_tier4_social_rumor_rejection` | Feed unverified community/social media notice without official circular | Assigned `TIER_4_SOCIAL_DISCOVERY`; `DISCOVERED`; `is_approved_for_publication = False` |
| **TEST-05** | `test_geo_within_sandakan_boundary` | Feed venue coordinates (`5.8752° N, 117.9458° E` - Sepilok) | Passes geographic verification; district validated as `Sandakan` |
| **TEST-06** | `test_geo_rejection_out_of_district` | Feed venue with Likas Sports Complex (`Kota Kinabalu`) or Tawau address | Rejected with status `GEO_REJECT_OUT_OF_DISTRICT`; excluded from Sandakan feed |
| **TEST-07** | `test_chronological_completed_event` | Feed event with end time earlier than execution timestamp ($T_{\text{end}} < T_{\text{now}}$) | State set to `COMPLETED`; excluded from upcoming 14-day carousel; archived |
| **TEST-08** | `test_chronological_staging_beyond_14d` | Feed confirmed event scheduled 25 days in future ($T_{\text{start}} > T_{\text{now}} + 14\text{d}$) | Stored in database staging; suppressed from current 14-day user-facing feed |
| **TEST-09** | `test_state_machine_live_now` | Execution time falls between start and end datetime ($T_{\text{start}} \le T_{\text{now}} \le T_{\text{end}}$) | Event assigned `LIVE_NOW`; renders with live pulsing UI badge |
| **TEST-10** | `test_state_machine_today` | Event scheduled for today's calendar date but start time is in afternoon | Event assigned `TODAY`; featured prominently on top carousel |
| **TEST-11** | `test_state_machine_upcoming` | Event start time is 12 days in the future within the 14-day window | Event assigned `UPCOMING`; displayed in upcoming chronological order |
| **TEST-12** | `test_entity_deduplication_fuzzy` | Feed two listings: `"Elopura Marathon 2026"` and `"Sandakan Elopura Marathon"` with same venue/date | Deduplication engine unifies into 1 record; combines sources into `secondary_source_urls` |
| **TEST-13** | `test_conflicting_date_quarantine` | Feed conflicting event announcements (e.g. 15 Nov vs 22 Nov for same blood drive) | Assigned `CONFLICTED`; `is_approved_for_publication = False`; quarantined |
| **TEST-14** | `test_network_timeout_cache_fallback` | Simulate 100% network timeout across all upstream scrapers | Engine loads cached `data/sandakan_events.json`; updates time states; zero crash |
| **TEST-15** | `test_zero_llm_execution_independence` | Run complete pipeline with environment variable `GEMINI_API_KEY=""` | Pipeline completes in 100% deterministic rule-based mode; 0 API calls recorded |

---

## 3. Test Fixtures & Mock Implementation Details

### Directory Structure:
```
tests/
  ├── test_sandakan_event_engine.py      # Primary test suite (15 unit & integration tests)
  └── fixtures/
      ├── stb_sample_event.json          # Mock STB Borneo Bird Festival response
      ├── ticket2u_sample_event.json     # Mock Ticket2U Elopura Marathon payload
      ├── press_sample_articles.json     # Mock Daily Express & TVS Lion Dance coverage
      ├── out_of_district_event.json     # Kota Kinabalu Marathon mock (to test rejection)
      └── cached_events_sample.json      # Stale cache fallback mock
```

---

## 4. Test Scenario Specifications & Assertions

### Scenario 5 & 6: Geographic Boundary Enforcement
```python
def test_geo_boundary_filtering():
    verifier = SandakanGeoVerifier()
    
    # Valid Sandakan coordinate (Sepilok)
    assert verifier.is_valid_location(5.8752, 117.9458, "Rainforest Discovery Centre, Sandakan") is True
    
    # Valid Sandakan venue name (Sibuga)
    assert verifier.is_valid_location(5.8690, 118.0620, "Kompleks Sukan Sandakan") is True
    
    # Out of district coordinate (Likas, KK)
    assert verifier.is_valid_location(5.9872, 116.0982, "Kompleks Sukan Likas, Kota Kinabalu") is False
```

### Scenario 7 & 9: Deterministic State Machine Transitions
```python
def test_state_machine_transitions():
    now_ref = datetime.fromisoformat("2026-11-08T13:05:32+08:00")
    engine = EventStatusEngine(current_time=now_ref)
    
    # Case: Bird Run finished this morning (07:00 - 10:30)
    status_run = engine.evaluate(
        start="2026-11-08T07:00:00+08:00",
        end="2026-11-08T10:30:00+08:00"
    )
    assert status_run == "COMPLETED"
    
    # Case: Bird Festival active right now (Nov 7 07:00 - Nov 8 17:00)
    status_fest = engine.evaluate(
        start="2026-11-07T07:00:00+08:00",
        end="2026-11-08T17:00:00+08:00"
    )
    assert status_fest == "LIVE_NOW"
    
    # Case: Marathon in 14 days (Nov 22 00:30 - 08:00)
    status_marathon = engine.evaluate(
        start="2026-11-22T00:30:00+08:00",
        end="2026-11-22T08:00:00+08:00"
    )
    assert status_marathon == "UPCOMING"
```

### Scenario 13: Conflicting Date Quarantine Assertion
```python
def test_conflicted_date_quarantine():
    matcher = EventEvidenceMatcher()
    candidate = {
        "title": "Kempen Derma Darah HDOK",
        "sources": [
            {"date": "2026-11-15", "url": "https://facebook.com/blood_drive_banner_a"},
            {"date": "2026-11-22", "url": "https://facebook.com/blood_drive_banner_b"}
        ]
    }
    result = matcher.evaluate_candidate(candidate)
    assert result.verification_status == "CONFLICTED"
    assert result.is_approved_for_publication is False
```

### Scenario 15: Zero Gemini Call Enforcement
```python
def test_zero_gemini_calls_guarantee(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr("builtins.__import__", _forbid_google_generativeai)
    
    engine = SandakanEventEngine()
    result = engine.run_pipeline(use_cache=True)
    assert result["metadata"]["gemini_api_calls_used"] == 0
    assert len(result["events"]) > 0
```

---

## 5. Execution & CI Integration Commands

Once implementation is approved, run the suite via:
```bash
pytest tests/test_sandakan_event_engine.py -v --tb=short
```

**Quality Gate Criteria:**
- 15 passed, 0 failed, 0 warnings.
- Code coverage $\ge 95\%$ on `scripts/sandakan_event_engine.py`.
- Zero outgoing network traffic during test execution.

---
*Test Plan ready for automated execution upon user sign-off.*
