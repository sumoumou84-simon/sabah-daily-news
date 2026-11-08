import re
import html
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base import BaseCollector, RawArticle, fetch_url_with_retry

class AgencyCollector(BaseCollector):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("Agency_Collector", config)

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', ' ', text)
        text = html.unescape(text)
        return re.sub(r'\s+', ' ', text).strip()

    def _check_metmalaysia(self) -> List[RawArticle]:
        articles = []
        url = "https://www.met.gov.my/iklim/amaran/"
        html_doc = fetch_url_with_retry(url, timeout=10, max_retries=2)
        if html_doc:
            # Look for warnings mentioning Sabah, Sandakan, Tawau, Kudat
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html_doc, re.IGNORECASE | re.DOTALL)
            for p in paragraphs:
                cleaned = self._clean_text(p)
                if any(k in cleaned.lower() for k in ["sabah", "sandakan", "pantai timur", "hujan berterusan", "ribut petir"]):
                    articles.append(RawArticle(
                        title=f"气象局 MetMalaysia 气象与降雨警报: {cleaned[:60]}",
                        url=url,
                        source="气象局 MetMalaysia",
                        category="sabah",
                        snippet=cleaned[:200],
                        language="ms",
                        extra={"agency": "MetMalaysia"}
                    ))
                    break
        return articles

    def collect(self) -> List[RawArticle]:
        self.health_status["status"] = "running"
        articles: List[RawArticle] = []

        try:
            met_items = self._check_metmalaysia()
            articles.extend(met_items)
            self.health_status["MetMalaysia"] = f"OK ({len(met_items)} items)"
        except Exception as e:
            self.health_status["errors"].append(f"MetMalaysia: {str(e)}")

        self.health_status["items_count"] = len(articles)
        self.health_status["status"] = "completed"
        return articles
