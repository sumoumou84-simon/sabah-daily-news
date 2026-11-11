#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sabah Daily News — Phase D-11.5: Full Article Content Retrieval & Source Corroboration
Execution Mode: LOCAL IMPLEMENTATION + LIVE NEWS RETRIEVAL + OFFLINE VERIFICATION
Gemini API Calls: 0
Gemini Quota Reservations: 0
Production Publishing: PROHIBITED
"""

import os
import sys
import re
import json
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("scripts.run_phase_d11_5_live_retrieval")

MYT = timezone(timedelta(hours=8))


def compute_sha256(filepath: str) -> str:
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def run_phase_d11_5():
    logger.info("=== Starting Phase D-11.5: Full Article Content Retrieval & Corroboration ===")
    now_myt = datetime.now(MYT)
    today_iso = "2026-11-09"

    # 1. Baseline Production Hashes
    prod_news_data = os.path.join(BASE_DIR, "news_data.json")
    prod_index_html = os.path.join(BASE_DIR, "index.html")
    baseline_news_data_hash = compute_sha256(prod_news_data)
    baseline_index_html_hash = compute_sha256(prod_index_html)
    logger.info(f"Baseline news_data.json SHA-256: {baseline_news_data_hash}")
    logger.info(f"Baseline index.html SHA-256:     {baseline_index_html_hash}")

    # 2. Config & Quota Safety
    config_path = os.path.join(BASE_DIR, "config", "news_config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    from pipeline.synthesizer import QuotaManager
    quota_mgr = QuotaManager(config)
    assert quota_mgr.daily_request_limit == 5
    local_state = quota_mgr.load_and_validate_local_state()
    logger.info(f"Quota state read-only inspection: reserved={local_state.get('reserved_count')}, limit={quota_mgr.daily_request_limit}")

    # 3. Live News Discovery
    from collectors.rss_collector import RSSCollector
    from collectors.portal_collector import PortalCollector
    from collectors.agency_collector import AgencyCollector
    from collectors.base import RawArticle, fetch_url_with_retry

    rss_collector = RSSCollector(config)
    portal_collector = PortalCollector(config)
    agency_collector = AgencyCollector(config)

    raw_articles: List[RawArticle] = []
    source_stats: Dict[str, Any] = {}

    rss_feeds = config.get("rss_feeds", [])
    for feed in rss_feeds:
        name = feed.get("name", "Unknown")
        url = feed.get("url", "")
        try:
            doc = fetch_url_with_retry(url, timeout=12, max_retries=2)
            if doc:
                count = len(re.findall(r'<item[\s>]', doc, re.IGNORECASE))
                source_stats[name] = {"type": "rss", "status": "SUCCESS", "items": count}
            else:
                source_stats[name] = {"type": "rss", "status": "EMPTY_OR_BLOCKED", "items": 0}
        except Exception as e:
            source_stats[name] = {"type": "rss", "status": f"ERROR: {e}", "items": 0}

    try:
        c_rss = rss_collector.collect()
        raw_articles.extend(c_rss)
        logger.info(f"RSSCollector gathered {len(c_rss)} raw items")
    except Exception as e:
        logger.warning(f"RSS error: {e}")

    portals = config.get("web_portals", [])
    for p in portals:
        name = p.get("name", "Unknown")
        url = p.get("url", "")
        try:
            doc = fetch_url_with_retry(url, timeout=12, max_retries=2)
            source_stats[name] = {"type": "portal", "status": "SUCCESS" if doc else "EMPTY_OR_BLOCKED", "bytes": len(doc) if doc else 0}
        except Exception as e:
            source_stats[name] = {"type": "portal", "status": f"ERROR: {e}", "bytes": 0}

    try:
        c_portals = portal_collector.collect()
        raw_articles.extend(c_portals)
        logger.info(f"PortalCollector gathered {len(c_portals)} raw items")
    except Exception as e:
        logger.warning(f"Portal error: {e}")

    agencies = config.get("agencies", [])
    for ag in agencies:
        name = ag.get("name", "Unknown")
        url = ag.get("warning_url") or ag.get("notice_url", "")
        try:
            doc = fetch_url_with_retry(url, timeout=12, max_retries=2) if url else None
            source_stats[name] = {"type": "agency", "status": "SUCCESS" if doc else "FAILED_OR_UNAVAILABLE"}
        except Exception as e:
            source_stats[name] = {"type": "agency", "status": f"ERROR: {e}"}

    try:
        c_agency = agency_collector.collect()
        raw_articles.extend(c_agency)
        logger.info(f"AgencyCollector gathered {len(c_agency)} raw items")
    except Exception as e:
        logger.warning(f"Agency error: {e}")

    logger.info(f"Total raw candidates collected: {len(raw_articles)}")

    # 4. Normalization
    from pipeline.normalizer import ArticleNormalizer
    sliding_hours = config.get("system", {}).get("sliding_window_hours", 36)
    if isinstance(sliding_hours, dict):
        sliding_hours = 36
    normalizer = ArticleNormalizer(sliding_window_hours=sliding_hours)
    normalized = normalizer.normalize(raw_articles)
    logger.info(f"Normalized candidates within sliding window: {len(normalized)}")

    # 5. Deduplication with Anti-Chaining Protection
    from pipeline.deduplicator import ArticleDeduplicator
    deduplicator = ArticleDeduplicator(sim_threshold=0.65)
    canonical = deduplicator.cluster_and_deduplicate(normalized)
    logger.info(f"Canonical stories after deduplication: {len(canonical)}")

    # Corroboration breakdown
    corroborated_stories = [c for c in canonical if len(c.extra.get("corroborating_sources", [])) >= 2]
    single_source_stories = [c for c in canonical if len(c.extra.get("corroborating_sources", [])) <= 1]
    logger.info(f"Corroborated stories (>= 2 sources): {len(corroborated_stories)}")
    logger.info(f"Single source stories: {len(single_source_stories)}")

    # 6. Focused Live Content Retrieval
    from pipeline.source_scraper import SourceScraper
    scraper = SourceScraper(config)

    scraping_stats = {
        "attempted": 0,
        "full_body_extracted": 0,
        "partial_body_extracted": 0,
        "access_blocked_or_challenge": 0,
        "paywall": 0,
        "redirect_resolution_failed": 0,
        "no_article_body_found": 0,
        "http_error": 0,
        "other": 0,
        "sample_retrievals": []
    }

    # Enrich canonical candidates
    for i, art in enumerate(canonical):
        scraping_stats["attempted"] += 1
        scraper.retrieve_article_body(art)
        status = art.extra.get("retrieval_status", "UNKNOWN")

        if status == "FULL_BODY_EXTRACTED":
            scraping_stats["full_body_extracted"] += 1
        elif status == "PARTIAL_BODY_EXTRACTED":
            scraping_stats["partial_body_extracted"] += 1
        elif status == "ACCESS_BLOCKED_OR_CHALLENGE":
            scraping_stats["access_blocked_or_challenge"] += 1
        elif status == "PAYWALL_DETECTED":
            scraping_stats["paywall"] += 1
        elif status == "REDIRECT_RESOLUTION_FAILED":
            scraping_stats["redirect_resolution_failed"] += 1
        elif status == "NO_ARTICLE_BODY_FOUND":
            scraping_stats["no_article_body_found"] += 1
        elif status == "HTTP_ERROR":
            scraping_stats["http_error"] += 1
        else:
            scraping_stats["other"] += 1

        # Keep representative sample of retrievals
        paragraphs = art.body.split("\n\n") if art.body else []
        if len(scraping_stats["sample_retrievals"]) < 20 or status == "FULL_BODY_EXTRACTED":
            if len(scraping_stats["sample_retrievals"]) < 30:
                scraping_stats["sample_retrievals"].append({
                    "title": art.title,
                    "source": art.source,
                    "original_url": art.extra.get("original_url", art.url),
                    "final_url": art.extra.get("final_url", art.url),
                    "extraction_status": status,
                    "body_is_snippet_fallback": art.extra.get("body_is_snippet_fallback", False),
                    "body_char_length": len(art.body) if art.body else 0,
                    "paragraph_count": len(paragraphs),
                    "body_preview": (art.body or "")[:200]
                })

    logger.info(
        f"Live retrieval results: {scraping_stats['full_body_extracted']} full, "
        f"{scraping_stats['partial_body_extracted']} partial, "
        f"{scraping_stats['access_blocked_or_challenge']} blocked, "
        f"{scraping_stats['no_article_body_found']} no body, "
        f"{scraping_stats['redirect_resolution_failed']} redirect failed, "
        f"{scraping_stats['http_error']} http error"
    )

    # 7. Editorial Selection of Top-10
    from pipeline.editorial_ranker import EditorialRanker
    ranker = EditorialRanker(config)
    top_10 = ranker.rank_and_select_top_10(canonical)
    logger.info(f"Selected Top 10 stories count: {len(top_10)}")

    top_10_details = []
    for rank, art in enumerate(top_10, 1):
        score, status = ranker.score_article(art)
        corrob_sources = art.extra.get("corroborating_sources", [art.source])
        top_10_details.append({
            "rank": rank,
            "title": art.title,
            "category": art.category,
            "score": score,
            "status": status,
            "corroboration_type": "multi_source" if len(corrob_sources) >= 2 else "single_source",
            "cluster_size": art.extra.get("cluster_size", 1),
            "corroborating_sources": corrob_sources,
            "original_url": art.extra.get("original_url", art.url),
            "final_url": art.extra.get("final_url", art.url),
            "retrieval_status": art.extra.get("retrieval_status"),
            "body_length_chars": len(art.body) if art.body else 0,
            "paragraph_count": len(art.body.split("\n\n")) if art.body else 0,
            "body_excerpt": (art.body or "")[:250]
        })

    # 8. Verify Production Safety Invariant
    post_news_data_hash = compute_sha256(prod_news_data)
    post_index_html_hash = compute_sha256(prod_index_html)
    assert baseline_news_data_hash == post_news_data_hash, "CRITICAL: news_data.json modified!"
    assert baseline_index_html_hash == post_index_html_hash, "CRITICAL: index.html modified!"
    logger.info("Production safety verified: news_data.json and index.html bit-for-bit unchanged.")

    # 9. Build Complete D-11.5 Report
    report = {
        "metadata": {
            "execution_mode": "LOCAL_IMPLEMENTATION_AND_AUTHORIZED_LIVE_RETRIEVAL",
            "target_news_date": today_iso,
            "timestamp_myt": now_myt.isoformat(),
            "gemini_api_calls": 0,
            "gemini_quota_reservations": 0,
            "gemini_api_key_access": "PROHIBITED_ZERO_ACCESS",
            "git_operations": "PROHIBITED_ZERO_OPERATIONS",
            "production_publishing": "PROHIBITED_ZERO_PUBLISHING",
            "production_hashes": {
                "news_data_json_sha256": post_news_data_hash,
                "index_html_sha256": post_index_html_hash,
                "unchanged_bit_for_bit": True
            }
        },
        "investigation_root_causes": {
            "scraper_failure_root_cause": (
                "In D-11.4, SourceScraper incorrectly checked 'cloudflare in lower_html'. "
                "Legitimate news websites such as See Hua Daily and Sin Chew Daily load legitimate CDN scripts "
                "from cdnjs.cloudflare.com and cloudflare-static plugins, causing genuine HTTP 200 pages "
                "with full article text to be falsely rejected as ACCESS_BLOCKED_OR_CHALLENGE (42 out of 45). "
                "Furthermore, Google News redirect URLs were fetched directly without unwrapping the batchexecute RPC."
            ),
            "corroboration_failure_root_cause": (
                "In D-11.4, ArticleDeduplicator matched generic numbers > 5 ('NUM:10', 'NUM:15') and generic words "
                "('air' = water in Malay, which appeared in 'tanah air' for homeland). Any article with LOC:SABAH "
                "and NUM:10 or 'air' was merged. Transitive single-linkage chaining (any(is_same_event)) chained "
                "247 articles into a single mega-cluster led by an unrelated international story ('No water to cook or bathe...'). "
                "When that cluster was penalized (-300) and discarded, all 54 corroborating sources were wiped out, "
                "leaving only isolated single-source items in the Top-10."
            )
        },
        "discovery_and_deduplication_summary": {
            "raw_candidates_collected": len(raw_articles),
            "normalized_candidates_in_window": len(normalized),
            "canonical_stories_after_dedup": len(canonical),
            "multi_source_corroborated_stories": len(corroborated_stories),
            "single_source_stories": len(single_source_stories),
            "anti_chaining_applied": "STAR_CLUSTERING_AGAINST_PRIMARY_LEADER",
            "entity_map_sanitized": "REMOVED_GENERIC_AIR_STOPWORD_AND_BODY_NUM_EXTRACTION"
        },
        "live_scraping_results": scraping_stats,
        "editorial_top_10": top_10_details
    }

    report_path_1 = os.path.join(BASE_DIR, "reports", "live_news_retrieval_d11_5.json")
    report_path_2 = os.path.join(BASE_DIR, "reports", "live_news_discovery_d11_5.json")
    with open(report_path_1, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    with open(report_path_2, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info(f"Report saved to {report_path_1} and {report_path_2}")

    return report


if __name__ == "__main__":
    run_phase_d11_5()
