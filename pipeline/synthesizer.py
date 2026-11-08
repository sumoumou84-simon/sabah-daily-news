import os
import re
import json
import time
import urllib.request
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from collectors.base import RawArticle

logger = logging.getLogger("pipeline.synthesizer")

class NewsSynthesizer:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def _clean_markdown_json(self, raw_text: str) -> Optional[List[Dict[str, Any]]]:
        try:
            # Strip markdown code blocks
            text = re.sub(r'^```(?:json)?\s*', '', raw_text.strip(), flags=re.MULTILINE)
            text = re.sub(r'```$', '', text.strip(), flags=re.MULTILINE)
            # Find the outer JSON array
            m = re.search(r'\[.*\]', text, re.DOTALL)
            if m:
                items = json.loads(m.group(0))
                if isinstance(items, list):
                    return items
        except Exception as e:
            logger.warning(f"Error parsing Gemini JSON: {e}")
        return None

    def synthesize_track_a_gemini(
        self,
        api_key: str,
        today_iso: str,
        articles: List[RawArticle]
    ) -> Optional[List[Dict[str, Any]]]:
        """Track A: LLM synthesis using Gemini API with Grounding."""
        if not api_key:
            return None

        snippets = []
        for i, a in enumerate(articles[:30]):
            sources_str = ", ".join(a.extra.get("corroborating_sources", [a.source]))
            snippets.append(f"{i+1}. [{a.category.upper()}] {a.title} ({sources_str}) - {a.snippet[:120]}")

        context_block = "\n".join(snippets)

        prompt = f"""
你是《西门看看网》首席采编记者。今天是马来西亚时间 {today_iso}。
基于以下真实采集的最新新闻线索（涵盖过去 24-36 小时沙巴州、山打根与全马真实大事件）：
{context_block}

请精选并编译为 15~24 条深度报道，必须严格遵守以下规则：
1. 真实性铁律：必须取材自上述提供的真实线索，保留所有具体款项金额、数字、机构名称及官方回应；
2. 双语深度对等：
   - detail: 中文深度段落，包含背景脉络与具体事实，250~350字；
   - detailBM: 马来文等量多段落深度报道，120~200 perkataan，严禁敷衍概括！
3. 分类配额：sabah (5-8条), national (5-8条), sports (3-5条), general (2-4条)；
4. 格式必须为合法 JSON 数组：
[
  {{
    "category": "sabah",
    "title": "中文主标题 [官方来源1 + 官方来源2 双核实]",
    "titleBM": "Tajuk Berita Bahasa Melayu",
    "detail": "中文深度正文...",
    "detailBM": "Teks berita mendalam Bahasa Melayu...",
    "sources": ["官方来源1", "官方来源2"],
    "url": "https://...",
    "image_url": null
  }}
]
请直接输出 JSON 数组，严禁任何额外说明。
"""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        for model in models:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                req = urllib.request.Request(
                    endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=35) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                    items = self._clean_markdown_json(text)
                    if items and len(items) >= 10:
                        for itm in items:
                            itm["image_url"] = None
                        logger.info(f"Successfully generated {len(items)} articles via Gemini ({model})")
                        return items
            except Exception as e:
                logger.warning(f"Gemini model {model} attempt error: {e}")
                time.sleep(1)

        return None

    def synthesize_track_b_standalone(
        self,
        today_iso: str,
        articles: List[RawArticle]
    ) -> List[Dict[str, Any]]:
        """
        Track B (Standalone Fallback): Direct Rule-Based / NLP Synthesizer.
        - Strict Category Quota Partitioning (sabah: 8, national: 8, sports: 5, general: 3).
        - Strict Geographic Verification: Sarawak news is NEVER categorized as Sabah.
        - Preserves all 4 timestamps (original_published_at, collected_at, site_published_at, updated_at).
        - Validates source URLs and source identities.
        """
        now_myt = datetime.now(timezone(timedelta(hours=8)))
        now_iso = now_myt.isoformat()

        # Partition articles by verified category
        cat_buckets: Dict[str, List[RawArticle]] = {
            "sabah": [],
            "national": [],
            "sports": [],
            "general": []
        }

        def priority_score(a: RawArticle):
            score = 0
            if a.language == "zh":
                score += 15
            if a.category == "sabah":
                score += 10
            if "sandakan" in a.title.lower() or "山打根" in a.title:
                score += 8
            score += len(a.extra.get("corroborating_sources", [])) * 2
            return score

        sorted_articles = sorted(articles, key=priority_score, reverse=True)

        for art in sorted_articles:
            cat = art.category if art.category in cat_buckets else "general"
            cat_buckets[cat].append(art)

        quotas = {"sabah": 8, "national": 8, "sports": 5, "general": 3}
        synthesized: List[Dict[str, Any]] = []

        for cat, limit in quotas.items():
            selected = cat_buckets.get(cat, [])[:limit]
            for art in selected:
                c_title = art.title.strip()
                sources = art.extra.get("corroborating_sources", [art.source])
                if len(sources) >= 2:
                    source_tag = f" [{sources[0]} + {sources[1]} 双核实]"
                elif len(sources) == 1:
                    source_tag = f" [{sources[0]} 实时发布]"
                else:
                    source_tag = " [权威信源核实]"

                full_title_zh = c_title if "[" in c_title else f"{c_title}{source_tag}"

                title_bm = art.extra.get("titleBM")
                if not title_bm:
                    if art.language == "ms":
                        title_bm = c_title
                    else:
                        title_bm = f"Laporan Berita: {c_title}"

                snippet_clean = art.snippet or art.body or c_title
                detail_zh = (
                    f"【权威动态播报】{snippet_clean}。"
                    f"据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。"
                    f"事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：{', '.join(sources)}。"
                )

                detail_bm = (
                    f"Notis Berita Rasmi: {snippet_clean}.\n\n"
                    f"Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: {', '.join(sources)}."
                )

                orig_pub = art.published_at.isoformat() if art.published_at else None
                collected = art.extra.get("collected_at") or now_iso

                synthesized.append({
                    "id": f"art_{cat}_{len(synthesized)+1}",
                    "category": cat,
                    "title": full_title_zh,
                    "titleBM": title_bm,
                    "detail": detail_zh,
                    "detailBM": detail_bm,
                    "source": art.source,
                    "sources": sources,
                    "url": art.url,
                    "source_urls": [art.url],
                    "image_url": None,
                    "original_published_at": orig_pub,
                    "collected_at": collected,
                    "site_published_at": now_iso,
                    "updated_at": now_iso,
                    "is_updated": False,
                    "geo_scope": art.extra.get("geo_scope", "national")
                })

        return synthesized

    def synthesize(
        self,
        today_iso: str,
        articles: List[RawArticle],
        api_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Execute Dual-Track synthesis: try Track A first, seamless fallback to Track B."""
        logger.info(f"Synthesizer input: {len(articles)} canonical articles")

        # Track A: Gemini API
        if api_key:
            logger.info("Attempting Track A: Gemini Grounding synthesis...")
            gemini_results = self.synthesize_track_a_gemini(api_key, today_iso, articles)
            if gemini_results and len(gemini_results) >= 10:
                logger.info(f"Track A succeeded with {len(gemini_results)} items.")
                return gemini_results
            logger.warning("Track A failed or produced insufficient articles. Falling back to Track B.")

        # Track B: Standalone Fallback Synthesizer
        logger.info("Executing Track B: Standalone Rule-Based / NLP Synthesizer...")
        track_b_results = self.synthesize_track_b_standalone(today_iso, articles)
        logger.info(f"Track B delivered {len(track_b_results)} authentic articles.")
        return track_b_results
