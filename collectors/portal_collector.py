import re
import html
from urllib.parse import urljoin
from typing import List, Dict, Any, Optional
from .base import BaseCollector, RawArticle, fetch_url_with_retry

class PortalCollector(BaseCollector):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("Portal_Collector", config)

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', ' ', text)
        text = html.unescape(text)
        return re.sub(r'\s+', ' ', text).strip()

    def _parse_seehua(self, portal_name: str, url: str, category: str) -> List[RawArticle]:
        articles = []
        html_doc = fetch_url_with_retry(url, timeout=12, max_retries=2)
        if not html_doc:
            return articles

        # Matches post links like href="https://news.seehua.com/post/123456" or href="/post/123456"
        matches = re.findall(
            r'<a\s+[^>]*href=[\'"]([^\'"]*(?:post/\d+|archives/\d+)[^\'"]*)[\'"][^>]*>([^<]{8,100})</a>',
            html_doc,
            re.IGNORECASE
        )
        seen_urls = set()
        for link, text in matches:
            clean_title = self._clean_text(text)
            full_url = urljoin(url, link)
            if not clean_title or full_url in seen_urls:
                continue
            if len(clean_title) < 8 or "更多" in clean_title or "上一页" in clean_title:
                continue
            seen_urls.add(full_url)
            articles.append(RawArticle(
                title=clean_title,
                url=full_url,
                source="诗华日报沙巴版",
                category=category,
                language="zh",
                extra={"portal": portal_name}
            ))
            if len(articles) >= 15:
                break
        return articles

    def _parse_sinchew(self, portal_name: str, url: str, category: str) -> List[RawArticle]:
        articles = []
        html_doc = fetch_url_with_retry(url, timeout=12, max_retries=2)
        if not html_doc:
            return articles

        matches = re.findall(
            r'<a\s+[^>]*href=[\'"](https?://sabah\.sinchew\.com\.my/[^\'"]+)[\'"][^>]*>([^<]{8,100})</a>',
            html_doc,
            re.IGNORECASE
        )
        seen_urls = set()
        for link, text in matches:
            clean_title = self._clean_text(text)
            if not clean_title or link in seen_urls:
                continue
            if len(clean_title) < 8 or "星洲" in clean_title and len(clean_title) < 12:
                continue
            seen_urls.add(link)
            articles.append(RawArticle(
                title=clean_title,
                url=link,
                source="沙巴星洲日报",
                category=category,
                language="zh",
                extra={"portal": portal_name}
            ))
            if len(articles) >= 15:
                break
        return articles

    def _parse_generic_html(self, portal_name: str, url: str, category: str) -> List[RawArticle]:
        articles = []
        html_doc = fetch_url_with_retry(url, timeout=12, max_retries=2)
        if not html_doc:
            return articles

        # Look for typical heading anchor links
        matches = re.findall(
            r'<h\d[^>]*>\s*<a\s+[^>]*href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>\s*</h\d>',
            html_doc,
            re.IGNORECASE | re.DOTALL
        )
        seen_urls = set()
        for link, text in matches:
            clean_title = self._clean_text(text)
            full_url = urljoin(url, link)
            if not clean_title or full_url in seen_urls or len(clean_title) < 10:
                continue
            seen_urls.add(full_url)
            articles.append(RawArticle(
                title=clean_title,
                url=full_url,
                source=portal_name,
                category=category,
                language="en",
                extra={"portal": portal_name}
            ))
            if len(articles) >= 10:
                break
        return articles

    def collect(self) -> List[RawArticle]:
        self.health_status["status"] = "running"
        articles: List[RawArticle] = []
        portals = self.config.get("web_portals", [])

        for p in portals:
            p_name = p.get("name", "Portal")
            p_url = p.get("url")
            p_cat = p.get("category", "sabah")
            p_type = p.get("type", "generic_html")

            if not p_url:
                continue

            try:
                if p_type == "seehua":
                    items = self._parse_seehua(p_name, p_url, p_cat)
                elif p_type == "sinchew":
                    items = self._parse_sinchew(p_name, p_url, p_cat)
                else:
                    items = self._parse_generic_html(p_name, p_url, p_cat)

                articles.extend(items)
                self.health_status[p_name] = f"OK ({len(items)} items)"
            except Exception as e:
                self.health_status["errors"].append(f"{p_name}: {str(e)}")

        self.health_status["items_count"] = len(articles)
        self.health_status["status"] = "completed" if articles else "warning"
        return articles
