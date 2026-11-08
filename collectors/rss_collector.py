import re
import html
import email.utils
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from .base import BaseCollector, RawArticle, fetch_url_with_retry

class RSSCollector(BaseCollector):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("RSS_Collector", config)

    def _parse_pub_date(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            parsed = email.utils.parsedate_to_datetime(date_str)
            return parsed
        except Exception:
            return None

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Strip CDATA
        text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text, flags=re.DOTALL)
        # Strip HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Unescape HTML entities
        text = html.unescape(text)
        # Normalize whitespace
        return re.sub(r'\s+', ' ', text).strip()

    def _detect_language(self, text: str, default: str = "zh") -> str:
        # Check Chinese characters
        if re.search(r'[\u4e00-\u9fff]', text):
            return "zh"
        # Malay keywords
        ms_keywords = [
            r'\bberita\b', r'\bnegeri\b', r'\bpolis\b', r'\bdaerah\b',
            r'\bkeselamatan\b', r'\bpada\b', r'\bdan\b', r'\byang\b', r'\bdi\b'
        ]
        if any(re.search(kw, text, re.IGNORECASE) for kw in ms_keywords):
            return "ms"
        return "en"

    def collect(self) -> List[RawArticle]:
        self.health_status["status"] = "running"
        articles: List[RawArticle] = []
        feeds = self.config.get("rss_feeds", [])

        for feed in feeds:
            feed_name = feed.get("name", "Unknown RSS")
            feed_url = feed.get("url")
            feed_category = feed.get("category", "general")

            if not feed_url:
                continue

            try:
                xml_data = fetch_url_with_retry(feed_url, timeout=12, max_retries=2)
                if not xml_data:
                    self.health_status["errors"].append(f"{feed_name}: empty response")
                    continue

                items = re.findall(r'<item[\s>](.*?)</item>', xml_data, re.DOTALL | re.IGNORECASE)
                feed_count = 0

                for item_xml in items:
                    title_match = re.search(r'<title>(.*?)</title>', item_xml, re.DOTALL | re.IGNORECASE)
                    link_match = re.search(r'<link>(.*?)</link>', item_xml, re.DOTALL | re.IGNORECASE)
                    if not link_match:
                        # Try atom link or guid
                        link_match = re.search(r'<guid[^>]*>(https?://[^\s<]+)</guid>', item_xml, re.IGNORECASE)
                    pub_match = re.search(r'<pubDate>(.*?)</pubDate>', item_xml, re.DOTALL | re.IGNORECASE)
                    desc_match = re.search(r'<description>(.*?)</description>', item_xml, re.DOTALL | re.IGNORECASE)

                    raw_title = self._clean_text(title_match.group(1)) if title_match else ""
                    raw_link = link_match.group(1).strip() if link_match else ""
                    raw_date = pub_match.group(1).strip() if pub_match else ""
                    raw_desc = self._clean_text(desc_match.group(1)) if desc_match else ""

                    if not raw_title or not raw_link:
                        continue

                    # For Google News titles, e.g. "Headline - Source Name"
                    article_source = feed_name
                    if " - " in raw_title and "Google News" in feed_name:
                        parts = raw_title.rsplit(" - ", 1)
                        if len(parts) == 2 and len(parts[1]) < 30:
                            raw_title = parts[0].strip()
                            article_source = parts[1].strip()

                    dt = self._parse_pub_date(raw_date)
                    lang = self._detect_language(raw_title + " " + raw_desc)

                    articles.append(RawArticle(
                        title=raw_title,
                        url=raw_link,
                        source=article_source,
                        category=feed_category,
                        published_at=dt,
                        snippet=raw_desc,
                        language=lang,
                        extra={"raw_pubDate": raw_date, "feed_name": feed_name}
                    ))
                    feed_count += 1

                self.health_status[feed_name] = f"OK ({feed_count} items)"
            except Exception as e:
                self.health_status["errors"].append(f"{feed_name}: {str(e)}")

        self.health_status["items_count"] = len(articles)
        self.health_status["status"] = "completed" if articles else "warning"
        return articles
