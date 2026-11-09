import re
from typing import List, Dict, Set, Tuple
from collectors.base import RawArticle

# Entity dictionary mapping terms to canonical concepts for cross-lingual clustering
ENTITY_MAP = {
    # Locations
    "sandakan": "LOC:SANDAKAN",
    "山打根": "LOC:SANDAKAN",
    "kota kinabalu": "LOC:KK",
    "亚庇": "LOC:KK",
    "tawau": "LOC:TAWAU",
    "斗湖": "LOC:TAWAU",
    "kudat": "LOC:KUDAT",
    "古达": "LOC:KUDAT",
    "lahad datu": "LOC:LAHAD_DATU",
    "拿笃": "LOC:LAHAD_DATU",
    "keningau": "LOC:KENINGAU",
    "根地咬": "LOC:KENINGAU",
    "semporna": "LOC:SEMPORNA",
    "仙本那": "LOC:SEMPORNA",
    "beaufort": "LOC:BEAUFORT",
    "保佛": "LOC:BEAUFORT",
    "penampang": "LOC:PENAMPANG",
    "兵南邦": "LOC:PENAMPANG",
    "tuaran": "LOC:TUARAN",
    "斗亚兰": "LOC:TUARAN",
    "papar": "LOC:PAPAR",
    "吧巴": "LOC:PAPAR",
    "tenom": "LOC:TENOM",
    "丹南": "LOC:TENOM",
    "ranau": "LOC:RANAU",
    "兰瑙": "LOC:RANAU",
    "sabah": "LOC:SABAH",
    "沙巴": "LOC:SABAH",
    "sarawak": "LOC:SARAWAK",
    "砂拉越": "LOC:SARAWAK",
    
    # Agencies / Organizations
    "mps": "ORG:MPS",
    "市议会": "ORG:MPS",
    "jans": "ORG:JANS",
    "水务局": "ORG:JANS",
    "sesb": "ORG:SESB",
    "电力": "ORG:SESB",
    "metmalaysia": "ORG:MET",
    "气象局": "ORG:MET",
    "imigresen": "ORG:JIM",
    "移民局": "ORG:JIM",
    "polis": "ORG:PDRM",
    "警方": "ORG:PDRM",
    "mma": "ORG:MMA",
    "医总": "ORG:MMA",
    "jpj": "ORG:JPJ",
    "陆路交通局": "ORG:JPJ",
    "ciltm": "ORG:CILTM",
    "特许物流与交通学会": "ORG:CILTM",
    
    # Core Topics & Keywords
    "scam": "TOPIC:SCAM",
    "penipuan": "TOPIC:SCAM",
    "电诈": "TOPIC:SCAM",
    "诈骗": "TOPIC:SCAM",
    "kemalangan": "TOPIC:ACCIDENT",
    "nahas": "TOPIC:ACCIDENT",
    "maut": "TOPIC:ACCIDENT",
    "korban": "TOPIC:ACCIDENT",
    "terbabas": "TOPIC:ACCIDENT",
    "车祸": "TOPIC:ACCIDENT",
    "夺命车祸": "TOPIC:ACCIDENT",
    "毙命": "TOPIC:ACCIDENT",
    "丧命": "TOPIC:ACCIDENT",
    "丧生": "TOPIC:ACCIDENT",
    "hujan": "TOPIC:RAIN",
    "降雨": "TOPIC:RAIN",
    "ribut": "TOPIC:STORM",
    "monsun": "TOPIC:MONSOON",
    "季风": "TOPIC:MONSOON",
    "banjir": "TOPIC:FLOOD",
    "水灾": "TOPIC:FLOOD",
    "air bersih": "TOPIC:WATER",
    "bekalan air": "TOPIC:WATER",
    "gangguan air": "TOPIC:WATER",
    "krisis air": "TOPIC:WATER",
    "masalah air": "TOPIC:WATER",
    "paip bocor": "TOPIC:WATER",
    "paip pecah": "TOPIC:WATER",
    "供水": "TOPIC:WATER",
    "水供": "TOPIC:WATER",
    "自来水": "TOPIC:WATER",
    "断水": "TOPIC:WATER",
    "水荒": "TOPIC:WATER",
    "爆管": "TOPIC:WATER",
    "水管破裂": "TOPIC:WATER",
    "badminton": "TOPIC:BADMINTON",
    "羽球": "TOPIC:BADMINTON",
    "korea open": "TOPIC:KOREA_OPEN",
    "韩国公开赛": "TOPIC:KOREA_OPEN",
    "man wei chong": "ENT:MWC",
    "万纬聪": "ENT:MWC",
    "teeh kai wun": "ENT:TKW",
    "郑凯文": "ENT:TKW",
    "najib": "ENT:NAJIB",
    "纳吉": "ENT:NAJIB",
    "kajang": "LOC:KAJANG",
    "加影": "LOC:KAJANG",
    "lrt": "TOPIC:LRT",
    "轻快铁": "TOPIC:LRT",
    "daiso": "ENT:DAISO",
    "大创": "ENT:DAISO",
    "kkia": "TOPIC:AIRPORT",
    "lapangan terbang": "TOPIC:AIRPORT",
    "airport": "TOPIC:AIRPORT",
    "机场": "TOPIC:AIRPORT",

    # Specific Events / Competitions (Phase D-11.2)
    "local government sports": "EVENT:SABAH_PBT_SPORTS",
    "sukan pbt": "EVENT:SABAH_PBT_SPORTS",
    "sukan pihak berkuasa tempatan": "EVENT:SABAH_PBT_SPORTS",
    "pbt sports": "EVENT:SABAH_PBT_SPORTS",
    "地政运动会": "EVENT:SABAH_PBT_SPORTS",
    "地方政府运动会": "EVENT:SABAH_PBT_SPORTS",
    "沙巴地方政府运动会": "EVENT:SABAH_PBT_SPORTS",
    "沙巴地政运动会": "EVENT:SABAH_PBT_SPORTS",
}

class ArticleDeduplicator:
    def __init__(self, sim_threshold: float = 0.65):
        self.sim_threshold = sim_threshold

    def extract_entity_anchors(self, text: str) -> Set[str]:
        """Extract canonical entities and significant numbers from title and snippet."""
        anchors = set()
        lower_t = text.lower()
        
        for k, v in ENTITY_MAP.items():
            if k in lower_t:
                anchors.add(v)

        # Extract significant numbers from title/snippet for specific district correlation
        norm_text = re.sub(r'(?<=\d)[,\s](?=\d{3}(?:\D|$))', '', text)
        nums = re.findall(r'(?<!\d)\d+(?:\.\d+)?(?!\d)', norm_text)
        for n in nums:
            if float(n) > 5 and n not in ("2026", "2025", "2024"):
                anchors.add(f"NUM:{n}")
                
        return anchors

    def get_char_ngrams(self, text: str, n: int = 2) -> Set[str]:
        cleaned = re.sub(r'[^\w]', '', text.lower())
        if len(cleaned) < n:
            return {cleaned}
        return {cleaned[i:i+n] for i in range(len(cleaned) - n + 1)}

    def jaccard_similarity(self, set_a: Set[str], set_b: Set[str]) -> float:
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)

    def is_same_event(self, art_a: RawArticle, art_b: RawArticle) -> bool:
        """Determines if two articles report the same event (same language or cross-lingual)."""
        # Exact URL match
        if art_a.url and art_b.url and art_a.url == art_b.url:
            return True

        # Check entity anchors overlap (use title and snippet)
        text_a = f"{art_a.title or ''} {art_a.snippet or ''}"
        text_b = f"{art_b.title or ''} {art_b.snippet or ''}"
        anchors_a = self.extract_entity_anchors(text_a)
        anchors_b = self.extract_entity_anchors(text_b)
        
        common_anchors = anchors_a & anchors_b

        # DISQUALIFIER 1: Check district conflict (e.g. KK vs Tawau, or Sandakan vs KK cannot be same local event)
        districts_a = {a for a in anchors_a if a.startswith("LOC:") and a not in ("LOC:SABAH", "LOC:SARAWAK")}
        districts_b = {a for a in anchors_b if a.startswith("LOC:") and a not in ("LOC:SABAH", "LOC:SARAWAK")}
        if districts_a and districts_b and not (districts_a & districts_b):
            return False

        # DISQUALIFIER 2: Check if titles contain explicitly conflicting numbers (e.g. 第1条 vs 第2条, or 14 vs 15)
        norm_t_a = re.sub(r'(?<=\d)[,\s](?=\d{3}(?:\D|$))', '', art_a.title or '')
        norm_t_b = re.sub(r'(?<=\d)[,\s](?=\d{3}(?:\D|$))', '', art_b.title or '')
        nums_a = {n for n in re.findall(r'(?<!\d)\d+(?:\.\d+)?(?!\d)', norm_t_a) if n not in ("2024", "2025", "2026")}
        nums_b = {n for n in re.findall(r'(?<!\d)\d+(?:\.\d+)?(?!\d)', norm_t_b) if n not in ("2024", "2025", "2026")}
        if nums_a and nums_b and not (nums_a & nums_b):
            return False

        # 1. Direct specific EVENT anchor match (e.g. EVENT:SABAH_PBT_SPORTS)
        event_anchors = {a for a in common_anchors if a.startswith("EVENT:")}
        if event_anchors:
            return True

        # 2. Specific district locations (excluding state-wide LOC:SABAH and LOC:SARAWAK)
        specific_districts = {a for a in common_anchors if a.startswith("LOC:") and a not in ("LOC:SABAH", "LOC:SARAWAK")}
        has_specific_district = len(specific_districts) > 0

        # Substantive anchors (TOPIC, ORG, ENT)
        substantive_anchors = {a for a in common_anchors if a.startswith("TOPIC:") or a.startswith("ORG:") or a.startswith("ENT:")}
        num_anchors = {a for a in common_anchors if a.startswith("NUM:")}

        # Multi-anchor match: at least 2 substantive anchors (e.g. ORG:JANS + TOPIC:WATER)
        if len(substantive_anchors) >= 2:
            return True

        # Specific district + agency/entity (e.g. LOC:SANDAKAN + ORG:MPS)
        has_agency_or_ent = any(a.startswith("ORG:") or a.startswith("ENT:") for a in substantive_anchors)
        if has_specific_district and has_agency_or_ent:
            return True

        # Specific district + matching substantive topic (e.g. LOC:PENAMPANG + TOPIC:ACCIDENT)
        # combined with matching specific number (e.g. victim age 41)
        if has_specific_district and (len(substantive_anchors) >= 1 or len(num_anchors) >= 1):
            if num_anchors or len(substantive_anchors) >= 1:
                return True

        # 3. Same language n-gram similarity
        if art_a.language == art_b.language:
            grams_a = self.get_char_ngrams(art_a.title)
            grams_b = self.get_char_ngrams(art_b.title)
            sim = self.jaccard_similarity(grams_a, grams_b)
            if sim >= self.sim_threshold:
                return True

        return False

    def cluster_and_deduplicate(self, articles: List[RawArticle]) -> List[RawArticle]:
        """Clusters duplicate reports and merges sources into canonical RawArticle instances."""
        clusters: List[List[RawArticle]] = []

        for art in articles:
            matched = False
            for cluster in clusters:
                # Star-clustering: candidate must match cluster leader to avoid transitive chaining
                if self.is_same_event(art, cluster[0]):
                    cluster.append(art)
                    matched = True
                    break
            if not matched:
                clusters.append([art])

        # Merge each cluster into a single canonical RawArticle
        canonical_articles: List[RawArticle] = []
        for cluster in clusters:
            # Pick representative: prefer Chinese version if available (primary site audience),
            # or the one with longest title/body
            def sort_key(a: RawArticle):
                lang_score = 2 if a.language == "zh" else 1
                return (lang_score, len(a.title) + len(a.body))

            cluster.sort(key=sort_key, reverse=True)
            primary = cluster[0]

            # Merge all unique source names and URLs
            sources = set()
            source_urls = set()
            for item in cluster:
                if item.source:
                    sources.add(item.source)
                if item.url:
                    source_urls.add(item.url)
            if not sources:
                sources.add("官方信源")

            primary.extra["corroborating_sources"] = sorted(list(sources))
            primary.extra["corroborating_urls"] = sorted(list(source_urls))
            primary.extra["cluster_size"] = len(cluster)

            # If multi-source corroboration exists, upgrade content_verification_status
            if len(sources) >= 2:
                current_status = primary.extra.get("content_verification_status")
                if current_status in (None, "single_source", "unverified", "rejected"):
                    primary.extra["content_verification_status"] = "corroborated"
            canonical_articles.append(primary)

        return canonical_articles
