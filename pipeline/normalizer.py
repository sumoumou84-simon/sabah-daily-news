import re
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
from collectors.base import RawArticle

# Asia/Kuala_Lumpur is fixed UTC+8 (no DST)
MYT = timezone(timedelta(hours=8))

class ArticleNormalizer:
    def __init__(self, sliding_window_hours: int = 36):
        self.sliding_window_hours = sliding_window_hours

    def get_myt_now(self) -> datetime:
        return datetime.now(MYT)

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
        # Remove trailing " - Portal Name" or " | Portal Name"
        title = re.sub(r'\s+[-|–—]\s+[^-|–—]{2,30}$', '', raw_title)
        # Remove editorial brackets e.g. [视频], [更新], [及时]
        title = re.sub(r'\[(?:视频|更新|即时|独家|图辑|快讯|历史归档复核)\]', '', title)
        title = re.sub(r'\s+', ' ', title)
        return title.strip()

    def is_within_window(self, dt: Optional[datetime], now_myt: datetime) -> bool:
        """Check if article date falls within sliding window (default 36 hours)."""
        if dt is None:
            # Undated articles from live portal homepages are assumed fresh
            return True

        # Convert dt to MYT if aware, or assume MYT if naive
        if dt.tzinfo is None:
            dt_myt = dt.replace(tzinfo=MYT)
        else:
            dt_myt = dt.astimezone(MYT)

        cutoff = now_myt - timedelta(hours=self.sliding_window_hours)
        # Also ensure not in the future by more than 2 hours (clock skew tolerance)
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

            if not clean_t or len(clean_t) < 6:
                continue

            # Strip markdown links in title e.g. [Link Text](http...)
            if re.search(r'\[.*?\]\(https?://', clean_t):
                continue

            lower_t = clean_t.lower()
            if any(term in lower_t for term in junk_indicators):
                continue

            # Apply 36h sliding window
            if not self.is_within_window(art.published_at, now_myt):
                continue

            art.url = clean_url
            art.title = clean_t
            normalized_list.append(art)

        return normalized_list
