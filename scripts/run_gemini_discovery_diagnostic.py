#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sabah Daily News — Phase D-2: Isolated Gemini News Discovery Diagnostic Runner
- Exactly ONE HTTP request using gemini-3.5-flash-lite with Google Search Grounding.
- Quota protected via QuotaManager (write-ahead reservation to origin/main).
- Zero retries, zero fallback models.
- Read-only comparison with existing morning baseline (news_data.json).
- Never publishes to website, never touches index.html or news_data.json.
- Emits structured diagnostic artifact and GitHub Actions Step Summary.
"""

import os
import sys
import re
import json
import uuid
import logging
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from zoneinfo import ZoneInfo

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from pipeline.synthesizer import QuotaManager, MYT_TZ
from pipeline.normalizer import ArticleNormalizer
from pipeline.geo_verifier import GeographicVerifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("scripts.gemini_discovery_diagnostic")


def mask_secret(text: str) -> str:
    """Mask any potential API key tokens from output strings."""
    if not text:
        return ""
    return re.sub(r'(key=)[A-Za-z0-9_-]{10,}', r'\1[MASKED_SECRET]', text)


def build_grounded_payload(today_str: str) -> Dict[str, Any]:
    """Construct prompt asking for recent Sabah/Sandakan/National news with Search Grounding."""
    prompt = (
        f"Today is {today_str} in Malaysia (Asia/Kuala_Lumpur).\n"
        "You are an objective news discovery engine for Sabah Daily News (西门看看网).\n"
        "Using Google Search Grounding, discover authentic breaking news events from the past 24 hours regarding:\n"
        "1. Sabah state government, public policy, economic announcements, and political developments;\n"
        "2. Sandakan municipal affairs, utility advisories (water/electricity/weather), and community incidents;\n"
        "3. Other Sabah districts (Kota Kinabalu, Tawau, Lahad Datu, Kudat, Keningau);\n"
        "4. Major Malaysia national breaking news directly affecting Sabah.\n\n"
        "Strict Guidelines:\n"
        "- ONLY report real, verifiable news with authentic publisher sources.\n"
        "- DO NOT invent missing article details or fabricate URLs.\n"
        "- DO NOT confuse Sarawak news (Kuching, Miri, Sibu) with Sabah news.\n\n"
        "Output MUST be a valid JSON array of objects with these exact keys:\n"
        "[\n"
        "  {\n"
        "    \"headline\": \"Original headline\",\n"
        "    \"source\": \"Publisher or agency name\",\n"
        "    \"url\": \"https://direct-article-url...\",\n"
        "    \"published_at\": \"YYYY-MM-DDTHH:MM:SS+08:00 (or null if unavailable)\",\n"
        "    \"summary\": \"Concise factual description of what happened (2-3 sentences)\",\n"
        "    \"category\": \"sabah\" or \"national\",\n"
        "    \"sabah_relevance\": \"Why this story matters to Sabah or Sandakan readers\",\n"
        "    \"item_type\": \"news_article\" or \"official_announcement\"\n"
        "  }\n"
        "]\n"
        "Return ONLY the valid JSON array without any markdown formatting or commentary."
    )
    return {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "tools": [
            {
                "google_search": {}
            }
        ]
    }


def parse_gemini_json_array(text: str) -> Optional[List[Dict[str, Any]]]:
    """Safely extract and parse JSON array from Gemini response text."""
    if not text:
        return None
    try:
        clean = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.MULTILINE)
        clean = re.sub(r'```$', '', clean.strip(), flags=re.MULTILINE)
        m = re.search(r'\[.*\]', clean, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            if isinstance(data, list):
                return data
    except Exception as e:
        logger.warning(f"Failed to parse JSON array from Gemini: {e}")
    return None


def execute_single_discovery_request(
    api_key: str,
    model: str,
    payload: Dict[str, Any],
    timeout: int = 35
) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[int]]:
    """
    Execute exactly ONE HTTP request to Gemini API with no retry.
    Returns (response_json, error_message, http_status_code).
    """
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.getcode()
            raw_body = resp.read().decode("utf-8")
            data = json.loads(raw_body)
            return data, None, code
    except urllib.error.HTTPError as e:
        return None, f"HTTP_{e.code}: {e.reason}", e.code
    except urllib.error.URLError as e:
        return None, f"NETWORK_TIMEOUT_OR_URLERROR: {e.reason}", None
    except Exception as e:
        return None, f"UNEXPECTED_ERROR: {str(e)}", None


def load_morning_baseline() -> List[Dict[str, Any]]:
    """Load existing morning collector baseline from news_data.json in read-only mode."""
    path = os.path.join(BASE_DIR, "news_data.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
                return d.get("headlines", [])
        except Exception as e:
            logger.warning(f"Could not load morning baseline from {path}: {e}")
    return []


def run_discovery_diagnostic(
    api_key_override: Optional[str] = None,
    config_override: Optional[Dict[str, Any]] = None,
    execution_mode_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main diagnostic orchestration:
    1. Preflight & credential inspection
    2. Write-ahead reservation via QuotaManager
    3. Exactly 1 Grounded HTTP dispatch
    4. Slot finalization
    5. Grounding metadata extraction & validation
    6. Read-only comparison with morning baseline
    7. Artifact and Step Summary output
    """
    logger.info("=================================================================")
    logger.info("🔍 Sabah Daily News — Single Gemini News Discovery Live Test (Phase D-2)")
    logger.info("=================================================================")

    config_path = os.path.join(BASE_DIR, "config", "news_config.json")
    config = config_override or {}
    if not config and os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")

    api_key = (
        api_key_override
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or ""
    ).strip()

    if not api_key:
        logger.error("[PREFLIGHT ABORT] No GEMINI_API_KEY detected in environment. Emitting 0 HTTP requests.")
        return {
            "status": "ABORTED_NO_CREDENTIALS",
            "http_requests_sent": 0,
            "quota_reserved": False,
            "detail": "Secure Gemini credential unavailable in runner environment."
        }

    # 1. Quota Manager Initialization
    quota_mgr = QuotaManager(
        config=config,
        execution_mode_override=execution_mode_override
    )
    candidate_models = quota_mgr.candidate_models
    model = candidate_models[0] if candidate_models else "gemini-3.5-flash-lite"

    now_myt = datetime.now(MYT_TZ)
    today_str = now_myt.strftime("%Y-%m-%d")

    logger.info(f"Execution Mode:   {quota_mgr.execution_mode}")
    logger.info(f"Candidate Model:  {model}")
    logger.info(f"Target Date (MYT):{today_str}")

    # 2. Write-Ahead Quota Reservation
    logger.info("[QUOTA GATE] Attempting write-ahead reservation for Gemini Discovery...")
    reservation = quota_mgr.reserve_slot(model)
    if not reservation:
        logger.error("[QUOTA GATE REJECTED] Reservation denied, exhausted, or unpersisted. Immediate abort (0 HTTP calls).")
        return {
            "status": "ABORTED_RESERVATION_FAILED",
            "http_requests_sent": 0,
            "quota_reserved": False,
            "detail": "Quota reservation failed or was rejected."
        }

    res_id = reservation["reservation_id"]
    logger.info(f"[QUOTA GATE GRANTED] Reservation secured: {res_id}")

    # 3. Build Search Grounded Payload
    payload = build_grounded_payload(today_str)

    # 4. Execute EXACTLY ONE HTTP request
    logger.info(f"[HTTP DISPATCH] Sending exactly ONE grounded discovery request to {model} (timeout=35s)...")
    res_json, error_msg, http_code = execute_single_discovery_request(
        api_key=api_key,
        model=model,
        payload=payload,
        timeout=35
    )

    # 5. Finalize Quota Slot
    if error_msg:
        logger.warning(f"[HTTP FAILED] {error_msg}. Finalizing slot as failed (no refund).")
        slot_status = f"FAILED_{error_msg[:30]}"
        quota_mgr.finalize_slot(res_id, slot_status)
        return {
            "status": "FAILED_HTTP",
            "http_requests_sent": 1,
            "http_code": http_code,
            "error": error_msg,
            "quota_reserved": True,
            "reservation_id": res_id,
            "model": model
        }

    quota_mgr.finalize_slot(res_id, "COMPLETED")
    logger.info(f"[HTTP SUCCESS] Received HTTP {http_code}. Quota slot finalized as COMPLETED.")

    # 6. Extract Grounding Metadata & Candidates
    candidates_list: List[Dict[str, Any]] = []
    grounding_metadata: Dict[str, Any] = {}
    grounding_chunks: List[Dict[str, Any]] = []
    search_queries: List[str] = []

    try:
        cand0 = res_json.get("candidates", [])[0]
        grounding_metadata = cand0.get("groundingMetadata", {})
        search_queries = grounding_metadata.get("webSearchQueries", [])
        raw_chunks = grounding_metadata.get("groundingChunks", [])
        for chunk in raw_chunks:
            web_info = chunk.get("web", {})
            if web_info:
                grounding_chunks.append({
                    "title": web_info.get("title", ""),
                    "uri": web_info.get("uri", "")
                })

        resp_text = cand0.get("content", {}).get("parts", [])[0].get("text", "")
        parsed_items = parse_gemini_json_array(resp_text)
        if parsed_items:
            candidates_list = parsed_items
        else:
            logger.warning("Gemini response text did not contain a cleanly parseable JSON array.")
    except Exception as e:
        logger.error(f"Error parsing Gemini candidate content: {e}")

    logger.info(f"Google Search Queries Executed by Gemini: {len(search_queries)}")
    for q in search_queries:
        logger.info(f"  • Search Query: {q}")
    logger.info(f"Grounding Web Source Chunks: {len(grounding_chunks)}")
    logger.info(f"Structured Candidate Items Extracted: {len(candidates_list)}")

    # 7. Local Validation & Morning Baseline Comparison
    normalizer = ArticleNormalizer(sliding_window_hours=36)
    geo_verifier = GeographicVerifier()
    morning_baseline = load_morning_baseline()
    baseline_titles = {h.get("title", "").lower() for h in morning_baseline}
    baseline_urls = {h.get("url", "").strip().rstrip("/") for h in morning_baseline if h.get("url")}

    evaluated_candidates: List[Dict[str, Any]] = []
    category_counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    new_discoveries_count = 0
    covered_count = 0

    for cand in candidates_list:
        c_title = cand.get("headline", "") or cand.get("title", "")
        c_url = cand.get("url", "") or ""
        c_source = cand.get("source", "Unknown")
        c_dt_str = cand.get("published_at")
        c_summary = cand.get("summary", "")
        c_type = cand.get("item_type", "news_article")

        # Temporal validation
        is_fresh = True
        dt_parsed = None
        if c_dt_str:
            try:
                dt_parsed = datetime.fromisoformat(c_dt_str)
                is_fresh = normalizer.is_within_window(dt_parsed, now_myt)
            except Exception:
                is_fresh = False

        # Geographic validation using GeographicVerifier
        geo_res = geo_verifier.verify(
            title=c_title,
            snippet=c_summary,
            url=c_url,
            source=c_source,
            proposed_category=cand.get("category", "sabah")
        )
        is_sarawak = (geo_res.get("geo_scope") == "sarawak")
        is_sabah_rel = (geo_res.get("geo_scope") in ("sabah", "sandakan")) or (cand.get("category") == "sabah")

        # Baseline comparison
        is_in_baseline = False
        if c_url and c_url.rstrip("/") in baseline_urls:
            is_in_baseline = True
        elif any(c_title.lower() in bt or bt in c_title.lower() for bt in baseline_titles if len(bt) > 8):
            is_in_baseline = True

        # Classification
        # A: Relevant verifiable news article
        # B: Official announcement or agency update
        # C: Search reference without sufficient article evidence
        # D: Irrelevant, duplicate, out-of-window, or unverifiable
        if not c_url or not c_url.startswith("http") or is_sarawak or not is_fresh:
            cand_class = "D"
            class_reason = "URL invalid, Sarawak leakage, or outside 36h window"
        elif c_type == "official_announcement" or any(k in c_source.lower() for k in ["mps", "jans", "sesb", "metmalaysia", "polis", "jabatan"]):
            cand_class = "B"
            class_reason = "Official announcement or public agency advisory"
        elif len(c_summary) < 20:
            cand_class = "C"
            class_reason = "Search reference without sufficient article text"
        else:
            cand_class = "A"
            class_reason = "Relevant, verifiable news article"

        category_counts[cand_class] += 1

        if is_in_baseline:
            covered_count += 1
            comparison_status = "ALREADY_COVERED_IN_MORNING_BASELINE"
        else:
            if cand_class in ("A", "B") and is_sabah_rel:
                new_discoveries_count += 1
                comparison_status = "GENUINELY_NEW_DISCOVERY"
            else:
                comparison_status = "UNCOVERED_OR_MARGINAL"

        evaluated_candidates.append({
            "headline": c_title,
            "source": c_source,
            "url": c_url,
            "published_at": c_dt_str,
            "classification": cand_class,
            "classification_reason": class_reason,
            "comparison_status": comparison_status,
            "is_within_36h": is_fresh,
            "is_sabah_relevant": is_sabah_rel,
            "is_sarawak_leakage": is_sarawak,
            "summary": c_summary
        })

    # 8. Compile Final Diagnostic Report
    report = {
        "timestamp_myt": now_myt.isoformat(),
        "status": "SUCCESS",
        "model_used": model,
        "reservation_id": res_id,
        "http_requests_sent": 1,
        "http_status_code": http_code,
        "google_search_queries": search_queries,
        "google_search_chunks_count": len(grounding_chunks),
        "total_candidates_extracted": len(candidates_list),
        "classification_breakdown": category_counts,
        "already_covered_count": covered_count,
        "genuinely_new_discoveries_count": new_discoveries_count,
        "candidates": evaluated_candidates,
        "grounding_sources": grounding_chunks,
        "production_integrity_check": {
            "news_data_modified": False,
            "index_html_modified": False,
            "website_published": False
        }
    }

    # 9. Save Artifact to reports/
    reports_dir = os.path.join(BASE_DIR, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    report_filename = f"discovery_diagnostic_{now_myt.strftime('%Y%m%d_%H%M%S')}.json"
    report_file_path = os.path.join(reports_dir, report_filename)
    try:
        with open(report_file_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Diagnostic artifact saved to: {report_file_path}")
    except Exception as e:
        logger.error(f"Failed to save diagnostic report: {e}")

    # 10. Generate GitHub Step Summary if in CI
    step_summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if step_summary_path:
        try:
            with open(step_summary_path, "a", encoding="utf-8") as sf:
                sf.write(f"## 🔍 Gemini News Discovery Live Diagnostic Report\n\n")
                sf.write(f"- **Execution Time (MYT):** `{now_myt.strftime('%Y-%m-%d %H:%M:%S')}`\n")
                sf.write(f"- **Model Used:** `{model}` (Grounded with Google Search)\n")
                sf.write(f"- **Quota Reservation ID:** `{res_id}`\n")
                sf.write(f"- **Search Queries Executed:** `{len(search_queries)}`\n")
                sf.write(f"- **Candidates Extracted:** `{len(candidates_list)}`\n")
                sf.write(f"- **Genuinely New Discoveries (Missed by Baseline):** `{new_discoveries_count}`\n")
                sf.write(f"- **Already Covered by Morning Baseline:** `{covered_count}`\n\n")

                sf.write("### 📊 Classification Breakdown\n")
                sf.write(f"| Category | Description | Count |\n| :--- | :--- | :---: |\n")
                sf.write(f"| **A** | Relevant Verifiable News Article | `{category_counts['A']}` |\n")
                sf.write(f"| **B** | Official Announcement / Agency Update | `{category_counts['B']}` |\n")
                sf.write(f"| **C** | Search Reference without Sufficient Evidence | `{category_counts['C']}` |\n")
                sf.write(f"| **D** | Irrelevant, Duplicate, or Unverifiable | `{category_counts['D']}` |\n\n")

                sf.write("### 📰 Discovered Candidates & Baseline Cross-Reference\n\n")
                sf.write("| # | Headline | Source | Class | Status | URL |\n| :--- | :--- | :--- | :---: | :--- | :--- |\n")
                for i, c in enumerate(evaluated_candidates, 1):
                    url_display = f"[Link]({c['url']})" if c['url'] else "None"
                    sf.write(f"| {i} | {c['headline'][:60]} | {c['source']} | `{c['classification']}` | `{c['comparison_status']}` | {url_display} |\n")
        except Exception as e:
            logger.warning(f"Failed to append to GITHUB_STEP_SUMMARY: {e}")

    return report


if __name__ == "__main__":
    res = run_discovery_diagnostic()
    if res.get("status") not in ("SUCCESS", "DRY_RUN"):
        sys.exit(1)
