#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase D-14: Publish D-13.2 Full-Body Single-Batch News to Production
Loads the authentic D-13.2 Gemini output, maps to news_data.json schema,
validates D-7 parity, and compiles production index.html.
"""

import os
import sys
import json
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from pipeline.synthesizer import NewsSynthesizer
from pipeline.fact_schema import FactItem, FactCategory, FactStatus, SemanticLifecycleState, SourceEvidence
from scripts.run_phase_d12_single_batch import get_canonical_fact_anchors
import build_news

def publish_d14():
    print("==========================================================================")
    print("=== Phase D-14: Production Integration of Phase D-13.2 News Articles ===")
    print("==========================================================================")

    # 1. Load D-13.2 Real Output
    d13_2_path = os.path.join(BASE_DIR, "reports", "gemini_single_batch_preview_d13_2.json")
    if not os.path.exists(d13_2_path):
        raise FileNotFoundError(f"D-13.2 preview not found at {d13_2_path}")

    with open(d13_2_path, "r", encoding="utf-8") as f:
        d13_2 = json.load(f)

    gen_articles = d13_2.get("execution_summary", {}).get("generated_articles", [])
    if len(gen_articles) != 10:
        raise ValueError(f"CRITICAL: Expected exactly 10 articles from D-13.2, got {len(gen_articles)}")

    # 2. Load cached source bodies metadata
    cached_path = os.path.join(BASE_DIR, "reports", "cached_source_bodies_20261109.json")
    if not os.path.exists(cached_path):
        raise FileNotFoundError(f"Source bodies cache not found at {cached_path}")

    with open(cached_path, "r", encoding="utf-8") as f:
        cached_manifest = json.load(f)
    cached_stories = cached_manifest.get("stories", {})

    # 3. Validate D-7 Parity
    config_path = os.path.join(BASE_DIR, "config", "news_config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    synth = NewsSynthesizer(cfg)
    anchors_map = get_canonical_fact_anchors()

    production_headlines = []
    
    for art in gen_articles:
        idx = art["story_index"]
        cached = cached_stories.get(str(idx))
        if not cached:
            raise ValueError(f"Story #{idx} missing from cached bodies manifest")

        # Verify D-7 parity
        c_facts = anchors_map.get(idx, {})
        is_valid, errs = synth.validate_article_parity(art, canonical_facts=c_facts)
        if not is_valid:
            raise ValueError(f"CRITICAL: Story #{idx} failed D-7 parity validation: {errs}")

        publishers = cached.get("publishers", [art.get("publisher", "官方信源")])
        source_urls = cached.get("source_urls", [])
        primary_source = publishers[0] if publishers else "官方信源"
        primary_url = source_urls[0] if source_urls else "https://news.google.com"
        geo = cached.get("geographic_scope", "SABAH").lower()
        orig_published_at = cached.get("published_at", "2026-11-08T20:00:00+08:00")

        # Construct production article item
        item = {
            "id": f"art_sabah_{idx}",
            "category": art.get("category", "sabah"),
            "title": art["title"].strip(),
            "titleBM": art["titleBM"].strip(),
            "detail": art["detail"].strip(),
            "detailBM": art["detailBM"].strip(),
            "source": primary_source,
            "sources": publishers,
            "sourceBM": primary_source,
            "sourcesBM": publishers,
            "url": primary_url,
            "source_urls": source_urls,
            "image_url": None,
            "original_published_at": orig_published_at,
            "collected_at": "2026-11-09T17:13:46+08:00",
            "site_published_at": "2026-11-09T17:13:46+08:00",
            "updated_at": "2026-11-09T17:13:46+08:00",
            "is_updated": False,
            "geo_scope": geo
        }
        production_headlines.append(item)

    print(f"✅ Verified 10 production articles under D-7 fact parity.")

    # 4. Integrate into news_data.json
    news_data_path = os.path.join(BASE_DIR, "news_data.json")
    with open(news_data_path, "r", encoding="utf-8") as f:
        prod_data = json.load(f)

    # Preserve utilities, events, and historical archive
    prod_data["date"] = "2026-11-09"
    prod_data["updated_at"] = "2026-11-09 17:13:46"
    prod_data["headlines"] = production_headlines

    if "archive" not in prod_data:
        prod_data["archive"] = {}
    prod_data["archive"]["2026-11-09"] = production_headlines

    with open(news_data_path, "w", encoding="utf-8") as f:
        json.dump(prod_data, f, ensure_ascii=False, indent=2)
    print(f"✅ Successfully updated {news_data_path} with 10 real D-13.2 articles.")

    # Also synchronize archive_history.json
    archive_history_path = os.path.join(BASE_DIR, "archive_history.json")
    if os.path.exists(archive_history_path):
        try:
            with open(archive_history_path, "r", encoding="utf-8") as f:
                ah_data = json.load(f)
            ah_data["2026-11-09"] = production_headlines
            with open(archive_history_path, "w", encoding="utf-8") as f:
                json.dump(ah_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Successfully synchronized {archive_history_path} with 10 real D-13.2 articles.")
        except Exception as e:
            print(f"⚠️ Warning: could not update {archive_history_path}: {e}")

    # 5. Compile index.html
    build_news.generate_index_html()
    print("✅ Successfully generated production index.html.")

    # 6. Verify index.html content
    index_html_path = os.path.join(BASE_DIR, "index.html")
    with open(index_html_path, "r", encoding="utf-8") as f:
        html = f.read()

    for h in production_headlines:
        assert h["title"] in html, f"Chinese headline missing from index.html: {h['title']}"
        assert h["titleBM"] in html, f"Malay headline missing from index.html: {h['titleBM']}"

    print("✅ Verification passed: all 10 bilingual headlines are present in index.html.")
    return production_headlines

if __name__ == "__main__":
    publish_d14()
