import os
import re
import json
import logging
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("pipeline.facebook_verifier")

# Fixed UTC+8 for Malaysia Time (MYT)
MYT = timezone(timedelta(hours=8))

VALID_TRUST_LEVELS = {"L1", "L2", "L3", "L4"}
VALID_IDENTITY_STATUSES = {"verified", "pending", "failed"}
VALID_VERIFICATION_STATUSES = {
    "verified_official",
    "corroborated",
    "single_source",
    "unverified",
    "rejected"
}

# Serious / emergency claim keywords that MUST be corroborated if from L4 or unverified sources
SERIOUS_CLAIM_KEYWORDS = [
    # Accidents & Disasters
    "kemalangan", "maut", "mati", "terkorban", "rentung", "lemas", "karam", "runtuh",
    "kebakaran", "hangus", "letupan", "banjir", "tanah runtuh", "gempa",
    "车祸", "丧命", "身亡", "溺毙", "烧死", "倒塌", "火灾", "大火", "爆炸", "水灾", "土崩", "洪灾",
    # Crime & Public Safety
    "bunuh", "tembak", "tetak", "rompak", "ragut", "rogol", "culik", "dadah", "tangkap",
    "sindiket", "tipu", "scam", "palsu", "viral polis", "suspek", "bomba",
    "谋杀", "枪击", "砍死", "抢劫", "掠夺", "强奸", "绑架", "毒品", "被捕", "落网", "诈骗", "假冒",
    # Public health & Emergency
    "wabak", "keracunan", "darurat", "amaran bahaya",
    "疫情", "中毒", "紧急状态", "危险预警"
]

LOGIN_AND_BOILERPLATE_INDICATORS = [
    "log in", "sign up", "log masuk", "daftar akaun", "forgot password",
    "create new account", "device-based", "login/?", "checkpoint",
    "cookie notice", "privacy policy", "terms of service", "meta ©",
    "see more on facebook", "lihat lagi di facebook", "connect with friends",
    "welcome to facebook", "facebook helps you connect", "not now"
]

class FacebookVerificationMatrix:
    """
    Facebook Verification Matrix Engine v1.0
    Manages source registry across L1~L4, validates page identities,
    enforces independent source trust vs. content verification status,
    and filters generic page URLs / login walls.
    """
    def __init__(self, matrix_config_path: Optional[str] = None):
        self.config_path = matrix_config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
            "facebook_verification_matrix.json"
        )
        self.sources: Dict[str, Dict[str, Any]] = {}
        self.load_registry()

    def load_registry(self) -> None:
        """Load and validate all configured sources from registry JSON."""
        if not os.path.exists(self.config_path):
            logger.warning(f"Matrix config file not found at: {self.config_path}")
            return

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_sources = data.get("sources", [])
        seen_handles = set()

        for s in raw_sources:
            handle = s.get("facebook_handle", "").strip()
            if not handle:
                raise ValueError("Source missing required facebook_handle")

            handle_lower = handle.lower()
            if handle_lower in seen_handles:
                raise ValueError(f"Duplicate Facebook handle detected in registry: {handle}")
            seen_handles.add(handle_lower)

            # Validate mandatory registry fields
            self.validate_registry_fields(s)

            self.sources[handle_lower] = s

    @staticmethod
    def validate_registry_fields(entry: Dict[str, Any]) -> None:
        """Validate required fields according to Facebook Verification Matrix v1.0 specifications."""
        required = [
            "page_name",
            "facebook_handle",
            "facebook_url",
            "trust_level",
            "source_category",
            "expected_geographic_scope",
            "source_type",
            "identity_status",
            "enabled",
            "verification_notes",
            "last_checked_at"
        ]
        for field_name in required:
            if field_name not in entry:
                raise ValueError(f"Missing required matrix field: '{field_name}' in source '{entry.get('facebook_handle')}'")

        if entry["trust_level"] not in VALID_TRUST_LEVELS:
            raise ValueError(f"Invalid trust_level '{entry['trust_level']}' for {entry['facebook_handle']}. Must be one of {VALID_TRUST_LEVELS}")

        if entry["identity_status"] not in VALID_IDENTITY_STATUSES:
            raise ValueError(f"Invalid identity_status '{entry['identity_status']}' for {entry['facebook_handle']}. Must be one of {VALID_IDENTITY_STATUSES}")

        if not isinstance(entry["enabled"], bool):
            raise ValueError(f"Field 'enabled' must be boolean for {entry['facebook_handle']}")

    def get_source(self, handle: str) -> Optional[Dict[str, Any]]:
        return self.sources.get(handle.lower().strip())

    @staticmethod
    def is_genuine_post_url(url: str) -> bool:
        """
        Distinguish a genuine individual Facebook post from a generic page URL.
        Matches permalinks containing specific post/photo/video IDs.
        """
        if not url:
            return False
        clean_url = url.split("?")[0].rstrip("/") if "?" in url else url.rstrip("/")
        query = urllib.parse.urlparse(url).query
        query_dict = urllib.parse.parse_qs(query)

        # Check permalink query parameters (e.g. story_fbid, fbid, id)
        if "story_fbid" in query_dict or "fbid" in query_dict:
            return True

        # Check path patterns for individual items
        post_patterns = [
            r'facebook\.com/[^/]+/posts/(\d+|[A-Za-z0-9_-]+)',
            r'facebook\.com/[^/]+/photos/(?:a\.\d+/)?(\d+)',
            r'facebook\.com/[^/]+/videos/(\d+)',
            r'facebook\.com/permalink\.php',
            r'facebook\.com/story\.php',
            r'facebook\.com/watch/\?v=(\d+)',
            r'facebook\.com/groups/[^/]+/permalink/(\d+)',
            r'facebook\.com/groups/[^/]+/posts/(\d+)',
            r'facebook\.com/[^/]+/activity/(\d+)',
            r'facebook\.com/[^/]+/videos/(\d+)',
        ]
        for pat in post_patterns:
            if re.search(pat, url, re.IGNORECASE):
                return True

        # Matches /{handle}/<numeric_post_id>
        if re.search(r'facebook\.com/[^/]+/(\d{8,})', url, re.IGNORECASE):
            return True

        return False

    @staticmethod
    def is_generic_page_url(url: str) -> bool:
        """
        Returns True if the URL points only to a root page, about page, or feed listing
        without a specific post or item ID.
        """
        if not url:
            return True
        if not FacebookVerificationMatrix.is_genuine_post_url(url):
            # If it's a facebook domain and not an individual post, it's generic
            parsed = urllib.parse.urlparse(url)
            if "facebook.com" in parsed.netloc:
                path = parsed.path.strip("/")
                parts = [p for p in path.split("/") if p]
                if len(parts) <= 2:
                    # e.g. /mpsandakan or /mpsandakan/about or /mpsandakan/
                    return True
        return False

    @staticmethod
    def contains_login_or_boilerplate(text: str) -> bool:
        """Detect whether text represents login wall, cookie dialog, or blocked boilerplate."""
        if not text:
            return False
        lower_t = text.lower()
        return any(term in lower_t for term in LOGIN_AND_BOILERPLATE_INDICATORS)

    @staticmethod
    def contains_serious_claim(text: str) -> bool:
        """Detect if content involves serious allegations, accidents, crime, or public safety."""
        if not text:
            return False
        lower_t = text.lower()
        return any(term in lower_t for term in SERIOUS_CLAIM_KEYWORDS)

    def evaluate_verification_status(
        self,
        handle: str,
        title: str,
        body: str = "",
        evidence_type: str = "direct_post",
        is_corroborated: bool = False,
        corroborating_count: int = 1
    ) -> Tuple[str, str, str]:
        """
        Separates Source Trust Level from Content Verification Status.
        Returns:
            (source_trust_level, source_identity_status, content_verification_status)
        """
        source_meta = self.get_source(handle)
        combined_text = f"{title} {body}"

        if not source_meta:
            # Unregistered source
            trust_level = "L4"
            identity_status = "pending"
            verification_status = "unverified"
            return trust_level, identity_status, verification_status

        trust_level = source_meta.get("trust_level", "L4")
        identity_status = source_meta.get("identity_status", "pending")
        source_type = source_meta.get("source_type", "community")

        # RULE: Unverified page identities CANNOT receive verified privileges
        if identity_status != "verified":
            return trust_level, identity_status, "unverified"

        # Content verification evaluation based on source level and evidence
        has_serious_claim = self.contains_serious_claim(combined_text)

        if trust_level == "L1":
            # Hyper-local Sandakan
            if source_type == "official":
                # e.g. MPS Sandakan, Sandakan FM
                content_status = "verified_official"
            else:
                # Community reports (e.g. Sandakan Kini)
                if is_corroborated or corroborating_count >= 2:
                    content_status = "corroborated"
                else:
                    content_status = "single_source"

        elif trust_level == "L2":
            # Sabah Statewide
            if source_type == "official":
                # JANS, SESB
                content_status = "verified_official"
            else:
                if is_corroborated or corroborating_count >= 2:
                    content_status = "corroborated"
                else:
                    content_status = "single_source"

        elif trust_level == "L3":
            # National Mainstream Media (e.g. 8TV.NEWS)
            if is_corroborated or corroborating_count >= 2:
                content_status = "corroborated"
            else:
                content_status = "single_source"

        elif trust_level == "L4":
            # Trending & Lifestyle (rojaklah88, viralcham)
            # NEVER automatically classify L4 claims as verified news.
            if has_serious_claim:
                if is_corroborated or corroborating_count >= 2:
                    content_status = "corroborated"
                else:
                    # Serious uncorroborated claims from viral/lifestyle sources are rejected
                    content_status = "rejected"
            else:
                # Light viral / lifestyle leads remain unverified discovery leads
                content_status = "unverified"
        else:
            content_status = "unverified"

        # Search discovery results are discovery leads, not direct verified posts
        if evidence_type == "search_discovery" and content_status == "verified_official":
            content_status = "corroborated" if is_corroborated else "single_source"

        return trust_level, identity_status, content_status
