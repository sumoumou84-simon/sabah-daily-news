import re
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from collectors.base import RawArticle
from .geo_verifier import GeographicVerifier

# Asia/Kuala_Lumpur is fixed UTC+8 (no DST)
MYT = timezone(timedelta(hours=8))

# Commercial advertisement indicators to separate ads from editorial content
AD_INDICATORS = [
    "saza rice", "jetour dashing", "买大米赢豪车", "抽奖", "岁末抽奖",
    "marco thien", "山打根租车", "优质租车", "car rental", "rent car",
    "peraduan beli & menang", "peraduan cabutan bertuah", "商业广告",
    "赞助商", "sponsored content", "iklan berbayar", "advertorial"
]

class ArticleNormalizer:
    def __init__(self, sliding_window_hours: int = 36):
        self.sliding_window_hours = sliding_window_hours
        self.geo_verifier = GeographicVerifier()
        self.ad_filter_count = 0
        self.geo_mismatch_count = 0

    def get_myt_now(self) -> datetime:
        return datetime.now(MYT)

    def is_advertisement(self, text: str) -> bool:
        """Strictly detect commercial advertisements to keep editorial news pure."""
        lower_t = text.lower()
        return any(term in lower_t for term in AD_INDICATORS)

    def normalize_url(self, raw_url: str) -> str:
        """Strip tracking query parameters (utm_*, fbclid, etc.) and fragments."""
        if not raw_url:
            return ""
        try:
            parsed = urllib.parse.urlparse(raw_url)
            query_pairs = urllib.parse.parse_qsl(parsed.query)
            clean_pairs = [
                (k, v) for k, v in query_pairs
                if not k.startswith("utm_") and k not in ("fbclid", "gclid", "ref", "spm")
            ]
            clean_query = urllib.parse.urlencode(clean_pairs)
            clean_parsed = parsed._replace(query=clean_query, fragment="")
            return urllib.parse.urlunparse(clean_parsed).rstrip("/")
        except Exception:
            return raw_url.strip()

    def normalize_title(self, raw_title: str) -> str:
        """Strip redundant brackets, HTML tags, and trailing source names."""
        if not raw_title:
            return ""
        title = re.sub(r'\s+[-|–—]\s+[^-|–—]{2,30}$', '', raw_title)
        title = re.sub(r'\[(?:视频|更新|即时|独家|图辑|快讯|历史归档复核)\]', '', title)
        title = re.sub(r'\s+', ' ', title)
        return title.strip()

    def is_within_window(self, dt: Optional[datetime], now_myt: datetime) -> bool:
        """Check if article date falls within sliding window (default 36 hours)."""
        if dt is None:
            # Undated articles from live portal homepages are assumed fresh
            return True

        if dt.tzinfo is None:
            dt_myt = dt.replace(tzinfo=MYT)
        else:
            dt_myt = dt.astimezone(MYT)

        cutoff = now_myt - timedelta(hours=self.sliding_window_hours)
        future_limit = now_myt + timedelta(hours=2)
        return cutoff <= dt_myt <= future_limit

    def normalize(self, articles: List[RawArticle]) -> List[RawArticle]:
        now_myt = self.get_myt_now()
        normalized_list = []

        junk_indicators = [
            "log in", "sign up", "device-based", "create new account", "forgot password",
            "facebook.com/login", "messenger", "l.facebook.com", "whatsapp"
        ]

        for art in articles:
            clean_url = self.normalize_url(art.url)
            clean_t = self.normalize_title(art.title)

            # Must have valid HTTP/HTTPS URL
            if not clean_url or not clean_url.startswith("http"):
                continue

            if not clean_t or len(clean_t) < 6:
                continue

            # Check markdown links in title e.g. [Link Text](http...)
            if re.search(r'\[.*?\]\(https?://', clean_t):
                continue

            lower_t = clean_t.lower()
            if any(term in lower_t for term in junk_indicators):
                continue

            # Facebook Specific Checks: Reject generic Facebook page URLs & uncorroborated rejected claims
            if "facebook.com" in clean_url and not art.extra.get("is_discovery_lead"):
                from pipeline.facebook_verifier import FacebookVerificationMatrix
                if FacebookVerificationMatrix.is_generic_page_url(clean_url):
                    continue

            if art.extra.get("content_verification_status") == "rejected":
                continue

            # AD CHECK: Exclude commercial advertisements from editorial news
            if self.is_advertisement(clean_t + " " + art.snippet + " " + art.body):
                self.ad_filter_count += 1
                continue

            # 36h Sliding Window Check
            if not self.is_within_window(art.published_at, now_myt):
                continue

            # Strict Geographic Verification
            geo_res = self.geo_verifier.verify(
                title=clean_t,
                snippet=art.snippet,
                body=art.body,
                url=clean_url,
                source=art.source,
                proposed_category=art.category
            )

            if geo_res.get("rejection_reason"):
                self.geo_mismatch_count += 1

            # Update article with verified attributes
            art.url = clean_url
            art.title = clean_t
            art.category = geo_res["verified_category"]
            art.source = geo_res["corrected_source"]
            art.extra["geo_scope"] = geo_res["geo_scope"]
            art.extra["is_sabah"] = geo_res["is_sabah"]
            art.extra["is_sarawak"] = geo_res["is_sarawak"]
            art.extra["collected_at"] = now_myt.isoformat()

            normalized_list.append(art)

        return normalized_list
