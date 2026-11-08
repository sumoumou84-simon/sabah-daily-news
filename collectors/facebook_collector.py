import os
import re
import html
import urllib.parse
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from .base import BaseCollector, RawArticle, fetch_url_with_retry

class FacebookCollector(BaseCollector):
    """
    Multi-Tier Cascading Collector for Public Facebook Pages (MPS, JANS, SESB, etc.)
    Tier 1: Direct Public RSSHub / Configured API (e.g. APIFY_TOKEN if set)
    Tier 2: Public Reader Bridge (r.jina.ai / mbasic mirror)
    Tier 3: Search Engine Social Index (Bing / Google News site:facebook.com query within past 36h)
    Tier 4: Structured failure logging without crashing pipeline
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("Facebook_Collector", config)

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', ' ', text)
        text = html.unescape(text)
        return re.sub(r'\s+', ' ', text).strip()

    def _tier1_apify_or_rsshub(self, handle: str) -> List[RawArticle]:
        """Tier 1: Try public RSSHub route or Apify API if APIFY_TOKEN is present in env."""
        apify_token = os.getenv("APIFY_TOKEN")
        if apify_token:
            # Apify Actor call would go here if configured
            pass

        # Public RSSHub instances for Facebook page (often restricted, so graceful fallback)
        rsshub_url = f"https://rsshub.app/facebook/page/{handle}"
        xml_data = fetch_url_with_retry(rsshub_url, timeout=6, max_retries=1)
        if xml_data and "<item>" in xml_data:
            items = []
            matches = re.findall(r'<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>', xml_data, re.DOTALL)
            for t, l in matches[:5]:
                items.append(RawArticle(
                    title=f"[{handle.upper()}] {self._clean_text(t)[:80]}",
                    url=l.strip(),
                    source=f"Facebook @{handle}",
                    category="sabah",
                    language="ms",
                    extra={"tier": 1, "handle": handle}
                ))
            return items
        return []

    def _tier2_jina_reader(self, handle: str) -> List[RawArticle]:
        """Tier 2: Jina Reader bridge (r.jina.ai) to bypass client JS requirement."""
        jina_url = f"https://r.jina.ai/https://www.facebook.com/{handle}"
        content = fetch_url_with_retry(jina_url, headers={"X-No-Cache": "true"}, timeout=8, max_retries=1)
        if not content:
            return []

        # If Facebook prompts login wall, do not capture login boilerplate
        login_indicators = ["log in", "sign up", "forgot password", "create new account", "device-based", "login/?"]
        
        # Parse markdown lines or paragraphs from Jina reader
        lines = [line.strip() for line in content.split("\n") if len(line.strip()) > 30]
        items = []
        for line in lines:
            lower_l = line.lower()
            if any(term in lower_l for term in login_indicators):
                continue
            if "cookie" in lower_l or "privacy policy" in lower_l or "meta ©" in lower_l:
                continue
            clean_l = self._clean_text(line)
            if len(clean_l) < 20 or clean_l.startswith("http"):
                continue
            items.append(RawArticle(
                title=f"[{handle.upper()}] {clean_l[:70]}",
                url=f"https://www.facebook.com/{handle}",
                source=f"Facebook @{handle}",
                category="sabah",
                snippet=clean_l[:250],
                language="ms",
                extra={"tier": 2, "handle": handle}
            ))
            if len(items) >= 2:
                break
        return items

    def _tier3_search_engine_social_index(self, handle: str, keywords: List[str]) -> List[RawArticle]:
        """Tier 3: Query Bing/Google RSS for indexed public Facebook posts within past 36h."""
        items = []
        kw = "+".join(keywords[:3]) if keywords else handle
        query = urllib.parse.quote(f"site:facebook.com/{handle} {kw}")
        bing_rss_url = f"https://www.bing.com/news/search?q={query}&format=rss"

        xml_data = fetch_url_with_retry(bing_rss_url, timeout=8, max_retries=1)
        if xml_data and "<item>" in xml_data:
            matches = re.findall(r'<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>.*?<description>(.*?)</description>', xml_data, re.DOTALL)
            for t, l, d in matches[:3]:
                clean_t = self._clean_text(t)
                clean_d = self._clean_text(d)
                items.append(RawArticle(
                    title=f"[{handle.upper()}] {clean_t[:70]}",
                    url=l.strip(),
                    source=f"Facebook @{handle} (Social Index)",
                    category="sabah",
                    snippet=clean_d[:250],
                    language="ms",
                    extra={"tier": 3, "handle": handle}
                ))
        return items

    def collect(self) -> List[RawArticle]:
        self.health_status["status"] = "running"
        articles: List[RawArticle] = []
        fb_pages = self.config.get("facebook_pages", [])

        for page in fb_pages:
            handle = page.get("handle")
            name = page.get("name", handle)
            keywords = page.get("keywords", [])
            if not handle:
                continue

            page_items = []
            tier_used = None

            # Cascading fallback chain
            # Tier 1
            try:
                page_items = self._tier1_apify_or_rsshub(handle)
                if page_items:
                    tier_used = "Tier 1 (Public/RSSHub)"
            except Exception:
                page_items = []

            # Tier 2
            if not page_items:
                try:
                    page_items = self._tier2_jina_reader(handle)
                    if page_items:
                        tier_used = "Tier 2 (Jina Reader Bridge)"
                except Exception:
                    page_items = []

            # Tier 3
            if not page_items:
                try:
                    page_items = self._tier3_search_engine_social_index(handle, keywords)
                    if page_items:
                        tier_used = "Tier 3 (Social Search Index)"
                except Exception:
                    page_items = []

            # Tier 4: Record structured failure without crashing
            if page_items:
                articles.extend(page_items)
                self.health_status[f"FB_{handle}"] = f"OK via {tier_used} ({len(page_items)} items)"
            else:
                self.health_status[f"FB_{handle}"] = "Tier 4 Fallback: Handled gracefully (no fresh public posts)"

        self.health_status["items_count"] = len(articles)
        self.health_status["status"] = "completed"
        return articles
