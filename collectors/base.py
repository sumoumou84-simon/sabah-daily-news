import time
import ssl
import urllib.request
import urllib.error
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger("collectors.base")

@dataclass
class RawArticle:
    title: str
    url: str
    source: str
    category: str = "general"  # sabah, national, sports, general
    published_at: Optional[datetime] = None
    snippet: str = ""
    body: str = ""
    language: str = "zh"  # zh, en, ms
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "category": self.category,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "snippet": self.snippet,
            "body": self.body,
            "language": self.language,
            "extra": self.extra
        }

def get_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def fetch_url_with_retry(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 12,
    max_retries: int = 2,
    backoff: float = 1.5
) -> Optional[str]:
    """Robust HTTP fetcher with exponential backoff, SSL tolerance, and browser user agent."""
    default_headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/124.0.0.0 Safari/537.36'
        ),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,ms;q=0.6',
    }
    if headers:
        default_headers.update(headers)

    ctx = get_ssl_context()

    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=default_headers)
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                raw_bytes = resp.read()
                # Try UTF-8 first, fallback to latin-1/gb18030
                try:
                    return raw_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        return raw_bytes.decode('gb18030', errors='ignore')
                    except Exception:
                        return raw_bytes.decode('latin-1', errors='ignore')
        except urllib.error.HTTPError as e:
            logger.warning(f"HTTP {e.code} while fetching {url} (Attempt {attempt}/{max_retries})")
            if e.code in (403, 404, 410):
                # Permanent client error; retrying unlikely to help
                return None
        except Exception as e:
            logger.warning(f"Error fetching {url}: {e} (Attempt {attempt}/{max_retries})")

        if attempt < max_retries:
            time.sleep(backoff * attempt)

    return None

class BaseCollector:
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.health_status = {
            "name": self.name,
            "status": "idle",
            "items_count": 0,
            "errors": []
        }

    def collect(self) -> List[RawArticle]:
        raise NotImplementedError
