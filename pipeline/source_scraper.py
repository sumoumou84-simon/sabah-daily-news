#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sabah Daily News — Phase D-11: Source Body Scraper & Substantive Content Extractor
Reuses collectors.base.fetch_url_with_retry.
Extracts clean, substantive article text from original publisher pages while strictly preserving
existing confirmed news status and corroboration records.
"""

import re
import html
import json
import logging
import ssl
import urllib.request
import urllib.parse
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import urlparse
from collectors.base import RawArticle, fetch_url_with_retry

logger = logging.getLogger("pipeline.source_scraper")

# Domain-specific paragraph and container regexes
PUBLISHER_CONTAINER_PATTERNS = {
    "seehua.com": r'<div[^>]*class=[\'"][^\'"]*(?:post-content|entry-content)[^\'"]*[\'"][^>]*>(.*?)</div>\s*<(?:div class=[\'"]relpost|footer|div class=[\'"]post-tags)',
    "theborneopost.com": r'<div[^>]*class=[\'"][^\'"]*(?:post-content|entry-content)[^\'"]*[\'"][^>]*>(.*?)</div>\s*<(?:div class=[\'"]relpost|footer|div class=[\'"]post-tags)',
    "dailyexpress.com.my": r'<(?:div|td)[^>]*id=[\'"](?:content_area|news_details)[\'"][^>]*>(.*?)</(?:div|td)>',
    "sinchew.com.my": r'<div[^>]*class=[\'"][^\'"]*(?:article-content|content-wrapper)[^\'"]*[\'"][^>]*>(.*?)</div>\s*<(?:div class=[\'"]ad-|footer)',
    "thestar.com.my": r'<div[^>]*id=[\'"]story-body[\'"][^>]*>(.*?)(?:<!-- recommended-reading|<div[^>]*id=[\'"]story-recom|<div[^>]*class=[\'"]tag-list)',
    "sabahmedia.com": r'<div[^>]*class=[\'"][^\'"]*(?:entry-content|post-content)[^\'"]*[\'"][^>]*>(.*?)</div>',
    "freemalaysiatoday.com": r'<div[^>]*class=[\'"][^\'"]*(?:entry-content|post-content)[^\'"]*[\'"][^>]*>(.*?)</div>',
    "bernama.com": r'<div[^>]*class=[\'"][^\'"]*news-details[^\'"]*[\'"][^>]*>(.*?)</div>',
    "nst.com.my": r'<div[^>]*class=[\'"][^\'"]*field-item even[^\'"]*[\'"][^>]*>(.*?)</div>'
}

UNWANTED_BLOCK_PATTERNS = [
    r'<script[^>]*>.*?</script>',
    r'<style[^>]*>.*?</style>',
    r'<!--.*?-->',
    r'<div[^>]*class=[\'"][^\'"]*(?:relpost|share|ad-|social|banner)[^\'"]*[\'"][^>]*>.*?</div>',
    r'<ol[^>]*>.*?</ol>',  # Google News RSS link lists
    r'<ul[^>]*>.*?</ul>',
    r'<figure[^>]*>.*?</figure>'
]


class SourceScraper:
    """
    Substantive Webpage Content Extractor with Google News redirect resolution
    and authentic publisher container extraction.
    Reuses existing fetch_url_with_retry without reinventing HTTP clients.
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config or {}

    @staticmethod
    def resolve_google_news_redirect(gn_url: str, timeout: int = 12) -> Optional[str]:
        """
        Resolve Google News redirect URL (news.google.com/rss/articles/...)
        to the authentic publisher destination URL using Google's batchexecute RPC.
        """
        if not gn_url or "news.google.com" not in gn_url:
            return gn_url

        m_id = re.search(r'articles/([^/?]+)', gn_url)
        if not m_id:
            return gn_url
        art_id = m_id.group(1)

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        fetch_url = f"https://news.google.com/articles/{art_id}?hl=en-MY&gl=MY&ceid=MY%3Aen"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        try:
            req = urllib.request.Request(fetch_url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                page_html = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            logger.warning(f"Failed to fetch Google News article token page for {art_id}: {e}")
            return None

        m_sg = re.search(r'data-n-a-sg="([^"]+)"', page_html)
        m_ts = re.search(r'data-n-a-ts="([^"]+)"', page_html)
        if not m_sg or not m_ts:
            logger.warning(f"Could not extract Google News signature tokens for {art_id}")
            return None

        sig = m_sg.group(1)
        ts = m_ts.group(1)

        payload_data = [
            "garturlreq",
            [["X", "X", ["X", "X"], None, None, 1, 1, "US:en", None, 1, None, None, None, None, None, 0, 1],
             "X", "X", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0],
            art_id,
            int(ts),
            sig
        ]

        req_body = [[["Fbv4je", json.dumps(payload_data), None, "generic"]]]
        post_data = urllib.parse.urlencode({"f.req": json.dumps(req_body)}).encode("utf-8")

        rpc_url = "https://news.google.com/_/DotsSplashUi/data/batchexecute?rpcids=Fbv4je"
        rpc_headers = {
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

        try:
            rpc_req = urllib.request.Request(rpc_url, data=post_data, headers=rpc_headers)
            with urllib.request.urlopen(rpc_req, timeout=timeout, context=ctx) as rpc_resp:
                resp_text = rpc_resp.read().decode("utf-8", errors="replace")
                for line in resp_text.split("\n\n"):
                    if line.startswith(")]}'"):
                        line = line[4:].strip()
                    try:
                        parsed = json.loads(line)
                        res_json = json.loads(parsed[0][2])
                        dest_url = res_json[1]
                        if dest_url and dest_url.startswith("http"):
                            logger.info(f"Resolved Google News redirect: {gn_url[:50]}... -> {dest_url}")
                            return dest_url
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Google News batchexecute RPC failed for {art_id}: {e}")

        return None

    @staticmethod
    def resolve_bing_news_redirect(bing_url: str) -> str:
        """Unwrap Bing News click tracker URL to find true publisher URL."""
        if not bing_url or "bing.com/news/apiclick" not in bing_url:
            return bing_url
        m = re.search(r'[?&](?:amp%3B|amp;)?url=([^&]+)', bing_url)
        if m:
            unquoted = urllib.parse.unquote(m.group(1))
            if unquoted.startswith("http"):
                return unquoted
        return bing_url

    def clean_html(self, raw_html: str) -> str:
        """Strip scripts, styles, unwanted widgets, and HTML tags."""
        if not raw_html:
            return ""

        text = raw_html
        for pat in UNWANTED_BLOCK_PATTERNS:
            text = re.sub(pat, ' ', text, flags=re.DOTALL | re.IGNORECASE)

        # Replace paragraph and line breaks with newlines
        text = re.sub(r'</?(?:p|div|br|h\d)[^>]*>', '\n', text, flags=re.IGNORECASE)
        # Strip all other HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        text = html.unescape(text)

        # Normalize lines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n\n".join(lines)

    def extract_paragraphs_from_html(self, html_doc: str, domain: str) -> List[str]:
        """Extract substantive article paragraphs using domain rules or generic fallback."""
        matched_container = None
        for pub_domain, pat in PUBLISHER_CONTAINER_PATTERNS.items():
            if pub_domain in domain:
                m = re.search(pat, html_doc, flags=re.DOTALL | re.IGNORECASE)
                if m:
                    matched_container = m.group(1)
                    break

        if not matched_container:
            # Fallback to standard HTML5 article or main-content container
            m_art = re.search(r'<article[^>]*>(.*?)</article>', html_doc, flags=re.DOTALL | re.IGNORECASE)
            if m_art:
                matched_container = m_art.group(1)

        target_html = matched_container if matched_container else html_doc

        boilerplate_lines = [
            "subscribe", "sign up", "advertisement", "all rights reserved",
            "copyright", "log in", "cookie", "disclaimer", "privacy policy",
            "facebook", "twitter", "whatsapp", "telegram", "点击查看", "更多精彩",
            "stay signed in to save", "redeem your rewards", "your rewards are waiting"
        ]

        # First pass: try extracting dedicated <p> elements
        p_matches = re.findall(r'<p[^>]*>(.*?)</p>', target_html, flags=re.DOTALL | re.IGNORECASE)
        if p_matches:
            paragraphs = []
            for p_raw in p_matches:
                p_clean = re.sub(r'<[^>]+>', ' ', p_raw)
                p_clean = html.unescape(p_clean).strip()
                if len(p_clean) < 25:
                    continue
                lower_p = p_clean.lower()
                if any(b in lower_p for b in boilerplate_lines):
                    continue
                paragraphs.append(p_clean)
            if len(paragraphs) >= 2:
                return paragraphs

        # Second pass: fallback to clean text lines
        clean_text = self.clean_html(target_html)
        paragraphs = []
        for p in clean_text.split("\n\n"):
            p_strip = p.strip()
            if len(p_strip) < 25:
                continue
            lower_p = p_strip.lower()
            if any(b in lower_p for b in boilerplate_lines):
                continue
            paragraphs.append(p_strip)

        return paragraphs

    def extract_substantive_body(self, html_doc: str, url: str) -> Tuple[Optional[str], str]:
        """
        Extract clean body text from HTML document.
        Returns: (body_text_or_None, status_code)
        """
        if not html_doc:
            return None, "EMPTY_HTTP_RESPONSE"

        # Check for genuine Cloudflare challenge / anti-bot blocks (avoid matching CDN script tags)
        lower_html = html_doc.lower()
        is_cf_challenge = (
            "<title>just a moment...</title>" in lower_html or
            "<title>attention required! | cloudflare</title>" in lower_html or
            "cf-browser-verification" in lower_html or
            "challenge-running" in lower_html or
            ("access denied" in lower_html and len(html_doc) < 3000) or
            ("please enable javascript" in lower_html and len(html_doc) < 3000)
        )
        if is_cf_challenge:
            return None, "ACCESS_BLOCKED_OR_CHALLENGE"

        if "subscribe to continue" in lower_html or "login to read full article" in lower_html or "付费阅读" in lower_html:
            return None, "PAYWALL_DETECTED"

        domain = urlparse(url).netloc.lower()
        paragraphs = self.extract_paragraphs_from_html(html_doc, domain)

        if not paragraphs:
            return None, "NO_ARTICLE_BODY_FOUND"

        combined_body = "\n\n".join(paragraphs)

        # Verify substantive volume: at least 2 paragraphs and >= 70 characters
        if len(paragraphs) < 2 or len(combined_body) < 70:
            return combined_body, "PARTIAL_BODY_EXTRACTED"

        return combined_body, "FULL_BODY_EXTRACTED"

    def retrieve_article_body(self, art: RawArticle) -> RawArticle:
        """
        Enriches a RawArticle with full substantive body text.
        Crucial preservation invariant: If extraction fails or is blocked,
        the article's confirmed status is NEVER downgraded or marked unconfirmed.
        """
        # If body is already substantive, retain it
        if art.body and len(art.body) >= 200:
            art.extra["retrieval_status"] = "FULL_BODY_EXTRACTED"
            art.extra["extraction_status"] = "FULL_BODY_EXTRACTED"
            return art

        if not art.url or not art.url.startswith("http"):
            art.extra["retrieval_status"] = "INVALID_URL"
            art.extra["extraction_status"] = "INVALID_URL"
            return art

        original_url = art.url
        resolved_url = original_url

        # 1. Resolve redirect wrappers (Google News or Bing News)
        if "news.google.com" in original_url:
            resolved = self.resolve_google_news_redirect(original_url)
            if resolved:
                resolved_url = resolved
                art.extra["original_url"] = original_url
                art.extra["final_url"] = resolved_url
            else:
                art.extra["original_url"] = original_url
                art.extra["final_url"] = original_url
                art.extra["retrieval_status"] = "REDIRECT_RESOLUTION_FAILED"
                art.extra["extraction_status"] = "REDIRECT_RESOLUTION_FAILED"
                if not art.body:
                    art.body = art.snippet or art.title
                    art.extra["body_is_snippet_fallback"] = True
                logger.warning(f"Redirect resolution failed for Google News URL: {original_url[:60]}")
                return art
        elif "bing.com/news/apiclick" in original_url:
            resolved = self.resolve_bing_news_redirect(original_url)
            if resolved:
                resolved_url = resolved
                art.extra["original_url"] = original_url
                art.extra["final_url"] = resolved_url

        # 2. Reuse existing robust HTTP fetcher
        html_doc = fetch_url_with_retry(resolved_url, timeout=12, max_retries=2)
        if not html_doc:
            art.extra["retrieval_status"] = "HTTP_ERROR"
            art.extra["extraction_status"] = "HTTP_ERROR"
            if not art.body:
                art.body = art.snippet or art.title
                art.extra["body_is_snippet_fallback"] = True
            logger.info(f"HTTP fetch returned empty or failed for: {resolved_url[:50]}")
            return art

        # 3. Extract substantive paragraphs
        extracted_body, status = self.extract_substantive_body(html_doc, resolved_url)

        if extracted_body and status == "FULL_BODY_EXTRACTED":
            art.body = extracted_body
            art.extra["retrieval_status"] = "FULL_BODY_EXTRACTED"
            art.extra["extraction_status"] = "FULL_BODY_EXTRACTED"
            logger.info(f"Successfully extracted full body for: {art.title[:40]} ({len(extracted_body)} chars)")
        elif extracted_body and status == "PARTIAL_BODY_EXTRACTED":
            art.body = extracted_body
            art.extra["retrieval_status"] = "PARTIAL_BODY_EXTRACTED"
            art.extra["extraction_status"] = "PARTIAL_BODY_EXTRACTED"
            logger.info(f"Extracted partial substantive body for: {art.title[:40]} ({len(extracted_body)} chars)")
        else:
            # PRESERVE EXISTING WORK: do not discard or unconfirm, accurately record failure reason
            art.extra["retrieval_status"] = status
            art.extra["extraction_status"] = status
            if not art.body:
                art.body = art.snippet or art.title
                art.extra["body_is_snippet_fallback"] = True
            logger.info(f"Extraction blocked or failed for: {art.title[:40]} (Status: {status})")

        return art

    def enrich_batch_with_source_bodies(self, articles: List[RawArticle]) -> List[RawArticle]:
        """Process a list of RawArticle records sequentially."""
        return [self.retrieve_article_body(a) for a in articles]
