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
    
    # Core Topics & Keywords
    "scam": "TOPIC:SCAM",
    "penipuan": "TOPIC:SCAM",
    "电诈": "TOPIC:SCAM",
    "诈骗": "TOPIC:SCAM",
    "hujan": "TOPIC:RAIN",
    "降雨": "TOPIC:RAIN",
    "ribut": "TOPIC:STORM",
    "monsun": "TOPIC:MONSOON",
    "季风": "TOPIC:MONSOON",
    "banjir": "TOPIC:FLOOD",
    "水灾": "TOPIC:FLOOD",
    "air": "TOPIC:WATER",
    "供水": "TOPIC:WATER",
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
}

class ArticleDeduplicator:
    def __init__(self, sim_threshold: float = 0.65):
        self.sim_threshold = sim_threshold

    def extract_entity_anchors(self, text: str) -> Set[str]:
        """Extract canonical entities and numbers from title and snippet."""
        anchors = set()
        lower_t = text.lower()
        
        for k, v in ENTITY_MAP.items():
            if k in lower_t:
                anchors.add(v)
                
        # Also extract significant numbers (e.g. 14, 210, 976, 26.9, 1000)
        nums = re.findall(r'\b\d+(?:\.\d+)?\b', text)
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

        # Check entity anchors overlap
        anchors_a = self.extract_entity_anchors(art_a.title + " " + art_a.snippet)
        anchors_b = self.extract_entity_anchors(art_b.title + " " + art_b.snippet)
        
        common_anchors = anchors_a & anchors_b
        # If at least 2 distinct semantic anchors match (e.g. LOC:SANDAKAN + TOPIC:SCAM, or ENT:MWC + TOPIC:BADMINTON)
        if len(common_anchors) >= 2:
            return True

        # Same language n-gram similarity
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
                if any(self.is_same_event(art, existing) for existing in cluster):
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

            # Merge all unique source names
            sources = set()
            for item in cluster:
                if item.source:
                    sources.add(item.source)
            if not sources:
                sources.add("官方信源")

            primary.extra["corroborating_sources"] = sorted(list(sources))
            primary.extra["cluster_size"] = len(cluster)
            canonical_articles.append(primary)

        return canonical_articles
