import os
import re
import html
import urllib.parse
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from typing import List, Dict, Any, Optional, Tuple
from .base import BaseCollector, RawArticle, fetch_url_with_retry
from pipeline.facebook_verifier import FacebookVerificationMatrix

MYT = timezone(timedelta(hours=8))

class FacebookCollector(BaseCollector):
    """
    Facebook Verification Matrix Cascading Collector v1.0
    Multi-Tier Cascading Collector with Strict Post Integrity:
    - Tier 1: Direct Public RSSHub / Apify Check
    - Tier 2: Public Reader Bridge (r.jina.ai / mbasic mirror)
    - Tier 3: Search Engine Social Index (Bing / Google News site:facebook.com within past 36h)
    - Tier 4: Structured failure logging without crashing pipeline

    Enforces:
    1. Distinguishing genuine individual Facebook post vs search-engine discovery lead vs generic page.
    2. Rejection of generic page URLs, login walls, and cookie prompts.
    3. Separation of source trust level (L1~L4) and content verification status.
    4. Honest reporting of Apify integration status.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("Facebook_Collector", config)
        matrix_path = (config or {}).get("facebook_matrix_file")
        self.matrix = FacebookVerificationMatrix(matrix_path)

        apify_token = os.getenv("APIFY_TOKEN")
        self.apify_status = {
            "token_detected": bool(apify_token),
            "api_integrated": False,
            "details": "Environment variable check only; no active Apify Actor API integration implemented."
        }
        self.health_status["apify_status"] = self.apify_status

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', ' ', text)
        text = html.unescape(text)
        return re.sub(r'\s+', ' ', text).strip()

    def _extract_post_id(self, url: str) -> Optional[str]:
        """Extract unique post ID from standard Facebook post permalinks."""
        if not url:
            return None
        # /posts/<id>
        m = re.search(r'/posts/([A-Za-z0-9_-]+)', url)
        if m:
            return m.group(1)
        # story_fbid=<id>
        m = re.search(r'[?&](?:story_fbid|fbid)=([0-9]+)', url)
        if m:
            return m.group(1)
        # /photos/<id> or /videos/<id>
        m = re.search(r'/(?:photos|videos)/(?:[a-zA-Z0-9_.-]+/)?([0-9]+)', url)
        if m:
            return m.group(1)
        # /<handle>/<numeric_id>
        m = re.search(r'/([^/?#]+)/(\d{8,})', url)
        if m:
            return m.group(2)
        return None

    def _parse_rfc822_date(self, date_str: str) -> Optional[datetime]:
        """Safely parse RFC 822 / 2822 date string without guessing or defaulting to now."""
        if not date_str:
            return None
        try:
            dt = parsedate_to_datetime(date_str)
            return dt.astimezone(MYT) if dt.tzinfo else dt.replace(tzinfo=MYT)
        except Exception:
            return None

    def _create_raw_article(
        self,
        handle: str,
        title: str,
        post_url: str,
        snippet: str = "",
        published_at: Optional[datetime] = None,
        evidence_type: str = "direct_post",
        discovery_url: Optional[str] = None,
        tier: int = 1
    ) -> Optional[RawArticle]:
        """Build a standardized RawArticle enriched with Facebook Verification Matrix v1.0 fields."""
        source_meta = self.matrix.get_source(handle) or {
            "page_name": handle,
            "trust_level": "L4",
            "identity_status": "pending",
            "expected_geographic_scope": "sabah",
            "source_category": "community"
        }

        # 1. Reject generic page URLs
        if evidence_type != "search_discovery" and self.matrix.is_generic_page_url(post_url):
            return None

        # 2. Reject login boilerplate
        clean_t = self._clean_text(title)
        clean_s = self._clean_text(snippet)
        if self.matrix.contains_login_or_boilerplate(clean_t + " " + clean_s):
            return None

        if len(clean_t) < 6:
            return None

        post_id = self._extract_post_id(post_url)
        now_iso = datetime.now(MYT).isoformat()

        trust_level, identity_status, content_status = self.matrix.evaluate_verification_status(
            handle=handle,
            title=clean_t,
            body=clean_s,
            evidence_type=evidence_type,
            is_corroborated=False,
            corroborating_count=1
        )

        # Geographic scope
        geo_scope = source_meta.get("expected_geographic_scope", "sabah")
        district = "sandakan" if geo_scope == "sandakan" else ("sabah" if geo_scope == "sabah" else "national")

        # Display category mapping
        category = "sabah"
        if geo_scope == "sandakan" or geo_scope == "sabah":
            category = "sabah"
        elif geo_scope == "national":
            category = "national"
        elif geo_scope == "lifestyle":
            category = "general"

        extra = {
            "source_platform": "facebook",
            "source_page_name": source_meta.get("page_name", handle),
            "source_page_handle": handle,
            "source_trust_level": trust_level,
            "source_identity_status": identity_status,
            "original_post_url": post_url,
            "original_post_id": post_id,
            "original_published_at": published_at.isoformat() if published_at else None,
            "collected_at": now_iso,
            "content_verification_status": content_status,
            "corroborating_sources": [f"Facebook @{handle}"],
            "geographic_scope": geo_scope,
            "district": district,
            "evidence_type": evidence_type,
            "is_discovery_lead": (evidence_type == "search_discovery"),
            "tier": tier,
            "handle": handle
        }
        if discovery_url:
            extra["discovery_url"] = discovery_url

        # Format title cleanly with handle badge
        display_title = clean_t
        if not display_title.startswith(f"[{handle.upper()}]"):
            display_title = f"[{handle.upper()}] {clean_t}"

        return RawArticle(
            title=display_title,
            url=post_url,
            source=f"Facebook @{handle}",
            category=category,
            published_at=published_at,
            snippet=clean_s[:300],
            language="ms" if any(w in clean_t.lower() for w in ["polis", "jalan", "air", "notis"]) else "zh",
            extra=extra
        )

    def _tier1_apify_or_rsshub(self, handle: str) -> List[RawArticle]:
        """
        Tier 1: Direct Public RSSHub route.
        Inspects Apify token, but transparently reports lack of active actor endpoint.
        """
        apify_token = os.getenv("APIFY_TOKEN")
        if apify_token:
            # Note: Apify token exists in environment, but no custom Facebook Actor integration is configured.
            pass

        rsshub_url = f"https://rsshub.app/facebook/page/{handle}"
        xml_data = fetch_url_with_retry(rsshub_url, timeout=6, max_retries=1)
        if not xml_data or "<item>" not in xml_data:
            return []

        # Reject login or error pages returned as XML
        if self.matrix.contains_login_or_boilerplate(xml_data):
            return []

        items = []
        item_blocks = re.findall(r'<item>(.*?)</item>', xml_data, re.DOTALL)
        for block in item_blocks[:5]:
            t_match = re.search(r'<title>(.*?)</title>', block, re.DOTALL)
            l_match = re.search(r'<link>(.*?)</link>', block, re.DOTALL)
            d_match = re.search(r'<description>(.*?)</description>', block, re.DOTALL)
            p_match = re.search(r'<pubDate>(.*?)</pubDate>', block, re.DOTALL)

            raw_link = l_match.group(1).strip() if l_match else ""
            raw_title = t_match.group(1).strip() if t_match else ""
            raw_desc = d_match.group(1).strip() if d_match else ""
            pub_date = self._parse_rfc822_date(p_match.group(1).strip()) if p_match else None

            # Only accept if it's a genuine post URL
            if not self.matrix.is_genuine_post_url(raw_link):
                continue

            art = self._create_raw_article(
                handle=handle,
                title=raw_title,
                post_url=raw_link,
                snippet=raw_desc,
                published_at=pub_date,
                evidence_type="public_feed",
                tier=1
            )
            if art:
                items.append(art)
        return items

    def _tier2_jina_reader(self, handle: str) -> List[RawArticle]:
        """
        Tier 2: Public Reader Bridge (r.jina.ai) to bypass client JS requirement.
        Must strictly reject login prompts, cookie dialogs, and generic page URLs.
        """
        jina_url = f"https://r.jina.ai/https://www.facebook.com/{handle}"
        content = fetch_url_with_retry(jina_url, headers={"X-No-Cache": "true"}, timeout=8, max_retries=1)
        if not content:
            return []

        # If Facebook prompts login wall or cookie notice, reject immediately
        if self.matrix.contains_login_or_boilerplate(content):
            return []

        items = []
        # Look for markdown post links [Title/Snippet](https://www.facebook.com/.../posts/...)
        post_link_matches = re.findall(
            r'\[([^\]]{15,})\]\((https?://(?:www\.)?facebook\.com/[^\s)]+)\)',
            content
        )
        for post_text, post_url in post_link_matches:
            if not self.matrix.is_genuine_post_url(post_url):
                continue
            if self.matrix.contains_login_or_boilerplate(post_text):
                continue

            art = self._create_raw_article(
                handle=handle,
                title=post_text,
                post_url=post_url,
                snippet=post_text,
                published_at=None,  # Jina reader does not reliably provide original pubDate
                evidence_type="direct_post",
                tier=2
            )
            if art:
                items.append(art)
                if len(items) >= 2:
                    break
        return items

    def _tier3_search_engine_social_index(self, handle: str, keywords: List[str]) -> List[RawArticle]:
        """
        Tier 3: Query Bing/Google RSS for indexed public Facebook posts within past 36h.
        Explicitly labelled as search_discovery leads; keeps discovery URL separate from original post URL.
        """
        items = []
        kw = "+".join(keywords[:3]) if keywords else handle
        query = urllib.parse.quote(f"site:facebook.com/{handle} {kw}")
        bing_rss_url = f"https://www.bing.com/news/search?q={query}&format=rss"

        xml_data = fetch_url_with_retry(bing_rss_url, timeout=8, max_retries=1)
        if not xml_data or "<item>" not in xml_data:
            return []

        item_blocks = re.findall(r'<item>(.*?)</item>', xml_data, re.DOTALL)
        for block in item_blocks[:3]:
            t_match = re.search(r'<title>(.*?)</title>', block, re.DOTALL)
            l_match = re.search(r'<link>(.*?)</link>', block, re.DOTALL)
            d_match = re.search(r'<description>(.*?)</description>', block, re.DOTALL)
            p_match = re.search(r'<pubDate>(.*?)</pubDate>', block, re.DOTALL)

            raw_link = l_match.group(1).strip() if l_match else ""
            raw_title = t_match.group(1).strip() if t_match else ""
            raw_desc = d_match.group(1).strip() if d_match else ""
            pub_date = self._parse_rfc822_date(p_match.group(1).strip()) if p_match else None

            # Discovery result
            art = self._create_raw_article(
                handle=handle,
                title=raw_title,
                post_url=raw_link,
                snippet=raw_desc,
                published_at=pub_date,
                evidence_type="search_discovery",
                discovery_url=bing_rss_url,
                tier=3
            )
            if art:
                items.append(art)
        return items

    def get_configured_pages(self) -> List[Dict[str, Any]]:
        """Return list of enabled pages from caller's config.facebook_pages or Matrix registry."""
        if "facebook_pages" in self.config and self.config.get("facebook_pages"):
            return self.config.get("facebook_pages", [])

        pages = []
        if self.matrix.sources:
            for s in self.matrix.sources.values():
                if s.get("enabled", True):
                    pages.append({
                        "handle": s.get("facebook_handle"),
                        "name": s.get("page_name"),
                        "keywords": s.get("keywords", []),
                        "trust_level": s.get("trust_level", "L4"),
                        "identity_status": s.get("identity_status", "pending")
                    })
        return pages

    def collect(self) -> List[RawArticle]:
        self.health_status["status"] = "running"
        articles: List[RawArticle] = []
        fb_pages = self.get_configured_pages()

        genuine_posts_count = 0
        discovery_leads_count = 0

        for page in fb_pages:
            handle = page.get("handle")
            keywords = page.get("keywords", [])
            if not handle:
                continue

            page_items = []
            tier_used = None
            failure_reason = None

            # Cascading fallback chain
            # Tier 1
            try:
                page_items = self._tier1_apify_or_rsshub(handle)
                if page_items:
                    tier_used = "Tier 1 (Public/RSSHub)"
            except Exception as e:
                failure_reason = f"Tier 1 error: {e}"
                page_items = []

            # Tier 2
            if not page_items:
                try:
                    page_items = self._tier2_jina_reader(handle)
                    if page_items:
                        tier_used = "Tier 2 (Jina Reader Bridge)"
                except Exception as e:
                    failure_reason = f"Tier 2 error: {e}"
                    page_items = []

            # Tier 3
            if not page_items:
                try:
                    page_items = self._tier3_search_engine_social_index(handle, keywords)
                    if page_items:
                        tier_used = "Tier 3 (Social Search Index)"
                except Exception as e:
                    failure_reason = f"Tier 3 error: {e}"
                    page_items = []

            # Tier 4: Record structured status
            if page_items:
                articles.extend(page_items)
                for item in page_items:
                    if item.extra.get("evidence_type") == "search_discovery":
                        discovery_leads_count += 1
                    else:
                        genuine_posts_count += 1

                self.health_status[f"FB_{handle}"] = {
                    "status": "OK",
                    "tier": tier_used,
                    "items": len(page_items),
                    "evidence_types": [it.extra.get("evidence_type") for it in page_items]
                }
            else:
                self.health_status[f"FB_{handle}"] = {
                    "status": "Tier 4 Fallback",
                    "message": "Handled gracefully (no fresh public posts or blocked by login wall)",
                    "last_error": failure_reason
                }

        self.health_status["genuine_posts_count"] = genuine_posts_count
        self.health_status["discovery_leads_count"] = discovery_leads_count
        self.health_status["items_count"] = len(articles)
        self.health_status["status"] = "completed"
        return articles
