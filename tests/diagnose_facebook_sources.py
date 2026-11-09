import os
import sys
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from collectors.base import fetch_url_with_retry, get_ssl_context
from collectors.facebook_collector import FacebookCollector
from pipeline.facebook_verifier import FacebookVerificationMatrix

logger = logging.getLogger("diagnose_facebook_sources")

def diagnose_page(source_entry: Dict[str, Any]) -> Dict[str, Any]:
    handle = source_entry.get("facebook_handle")
    fb_url = source_entry.get("facebook_url")
    page_name = source_entry.get("page_name")
    trust_level = source_entry.get("trust_level")
    identity_status = source_entry.get("identity_status")

    res: Dict[str, Any] = {
        "handle": handle,
        "page_name": page_name,
        "trust_level": trust_level,
        "identity_status": identity_status,
        "http_result": "UNKNOWN",
        "redirect_destination": None,
        "page_identity_evidence": source_entry.get("verification_notes", ""),
        "individual_post_retrieved": False,
        "unique_post_url_obtained": False,
        "original_text_extracted": False,
        "original_timestamp_available": False,
        "genuine_posts_count": 0,
        "search_discovery_leads": 0,
        "failure_reason": None,
        "sample_post_url": None
    }

    # 1. Connectivity & Redirect Check (head/get request with short timeout)
    ctx = get_ssl_context()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    try:
        req = urllib.request.Request(fb_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
            res["http_result"] = f"HTTP {response.status}"
            res["redirect_destination"] = response.geturl()
    except urllib.error.HTTPError as e:
        res["http_result"] = f"HTTP {e.code}"
        res["redirect_destination"] = e.geturl() if hasattr(e, "geturl") else None
        res["failure_reason"] = f"HTTP Error {e.code}: {e.reason}"
    except Exception as e:
        res["http_result"] = "CONNECTION_FAILED"
        res["failure_reason"] = str(e)

    # 2. Test Real Post Extraction via Collector
    collector = FacebookCollector({
        "facebook_pages": [{
            "handle": handle,
            "name": page_name,
            "keywords": source_entry.get("keywords", [])
        }]
    })

    articles = collector.collect()
    for art in articles:
        is_search = art.extra.get("is_discovery_lead", False)
        if is_search:
            res["search_discovery_leads"] += 1
        else:
            res["genuine_posts_count"] += 1
            res["individual_post_retrieved"] = True
            if FacebookVerificationMatrix.is_genuine_post_url(art.url):
                res["unique_post_url_obtained"] = True
                res["sample_post_url"] = art.url

        if art.title or art.snippet:
            res["original_text_extracted"] = True
        if art.published_at is not None:
            res["original_timestamp_available"] = True

    if not articles and not res["failure_reason"]:
        res["failure_reason"] = (
            "No public items extracted (Facebook login wall, anti-scraping block, or empty feed)"
        )

    return res

def run_diagnostics(output_file: Optional[str] = None) -> List[Dict[str, Any]]:
    matrix_file = os.path.join(BASE_DIR, "config", "facebook_verification_matrix.json")
    if not os.path.exists(matrix_file):
        print(f"Error: Matrix config not found at {matrix_file}")
        return []

    with open(matrix_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    sources = data.get("sources", [])
    print("=" * 80)
    print("🔍 FACEBOOK VERIFICATION MATRIX v1.0 — SOURCE CONNECTIVITY & EXTRACTION AUDIT")
    print(f"Total Sources in Registry: {len(sources)}")
    print("=" * 80)

    results = []
    for s in sources:
        handle = s.get("facebook_handle")
        level = s.get("trust_level")
        name = s.get("page_name")
        print(f"\n[Testing {level}] {name} (@{handle})...")
        diag = diagnose_page(s)
        results.append(diag)

        status_flag = "PASS" if (diag["genuine_posts_count"] > 0 or diag["search_discovery_leads"] > 0) else "BLOCKED/NO_DATA"
        print(f"  - HTTP Result: {diag['http_result']}")
        print(f"  - Identity Status: {diag['identity_status']}")
        print(f"  - Genuine Posts: {diag['genuine_posts_count']} | Search Leads: {diag['search_discovery_leads']}")
        print(f"  - Unique Post URL: {diag['unique_post_url_obtained']} | Sample: {diag['sample_post_url']}")
        print(f"  - Original Timestamp Available: {diag['original_timestamp_available']}")
        if diag["failure_reason"]:
            print(f"  - Notice/Reason: {diag['failure_reason']}")

    print("\n" + "=" * 80)
    print(f"DIAGNOSTIC SUMMARY: {len(results)} sources audited.")
    print("=" * 80)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Diagnostics written to: {output_file}")

    return results

if __name__ == "__main__":
    out_path = os.path.join(BASE_DIR, "config", "facebook_sources_diagnostic_report.json")
    run_diagnostics(out_path)
