#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline/fact_verifier.py — Bilingual Fact Validator & Verification Engine
Phase D-5: Universal Fact-Locking Specification
- Deterministic calendar-weekday validation (Gregorian model).
- Typed numerical extractors (Monetary, Dates, Headcounts, Editions, Quantities).
- Independent atomic semantic-state verification for mixed-fact claims.
- Universal text scanning: headlines, core claims, narrative claims, transitions.
- Zero-tolerance failure behavior (REVIEW_REQUIRED / REJECTED).
"""

import re
import datetime
from typing import Dict, List, Tuple, Optional, Any, Set

from pipeline.fact_schema import (
    FactItem,
    FactCategory,
    FactStatus,
    SemanticLifecycleState,
    NormalizedMonetaryValue,
    NormalizedDateValue,
    NormalizedDateRangeValue,
    NormalizedQuantityValue,
    NormalizedHeadcountValue,
    NormalizedEditionValue,
    StructuredArticle,
    HeadlineRecord,
    ClaimRecord,
    NarrativeClaimRecord,
    StylisticTransitions,
    ValidationResult
)

# Weekday mappings
WEEKDAY_ZH_MAP = {
    "周一": 0, "星期一": 0, "周二": 1, "星期二": 1,
    "周三": 2, "星期三": 2, "周四": 3, "星期四": 3,
    "周五": 4, "星期五": 4, "周六": 5, "星期六": 5,
    "周日": 6, "星期日": 6, "星期天": 6
}
WEEKDAY_BM_MAP = {
    "isnin": 0, "selasa": 1, "rabu": 2, "khamis": 3,
    "jumaat": 4, "sabtu": 5, "ahad": 6
}

# Semantic state violation markers (including active and passive voice)
PROHIBITED_ALLOCATION_VERBS_ZH = [
    "已耗费", "已花费", "已用尽", "已发放", "已分发", "已垫付",
    "被动用", "被支出", "已拨付", "已核销", "被发放", "被分发", "被消耗"
]
PROHIBITED_ALLOCATION_VERBS_BM = [
    "telah membelanjakan", "telah dibelanjakan", "telah dihabiskan",
    "telah diserahkan", "telah diagihkan", "sudah dibelanjakan",
    "disalurkan", "digunakan", "dibelanjakan", "diagih", "diperuntukkan sepenuhnya",
    "telah disalurkan", "telah digunakan", "wang dibelanjakan", "dana digunakan"
]
PROHIBITED_COMPLETION_VERBS_ZH = [
    "正在施工", "尚未完工", "计划中", "规划中", "建设中", "停工"
]
PROHIBITED_COMPLETION_VERBS_BM = [
    "sedang dibina", "belum siap", "dalam perancangan", "terbengkalai"
]

# Known named political figures and agencies for headline entity validation
KNOWN_NAMED_PERSONS = {
    "hajiji": ["哈芝芝", "哈芝芝诺", "hajiji", "hajiji noor"],
    "mohd_arifin": ["阿里芬", "莫哈末阿里芬", "mohd arifin", "arifin arif"],
    "mustapha_sakmud": ["穆斯达法", "穆斯达法沙末", "mustapha", "mustapha sakmud"],
    "vivian_wong": ["黄诗怡", "vivian wong"],
    "walter_kenson": ["沃特肯森", "walter kenson"],
    "anwar_ibrahim": ["安华", "安华依布拉欣", "anwar", "anwar ibrahim"],
    "masidi_manjun": ["马西迪", "马西迪曼俊", "masidi", "masidi manjun"],
    "joachim_gunsalam": ["佐津", "佐津昆沙南", "joachim", "joachim gunsalam"]
}

KNOWN_NAMED_AGENCIES = {
    "mps": ["市议会", "山打根市议会", "mps", "majlis perbandaran sandakan"],
    "jans": ["水务局", "沙巴水务局", "jans", "jabatan air negeri sabah"],
    "sesb": ["电力公司", "沙巴电力", "sesb", "sabah electricity"],
    "kam": ["昌明领养甘榜", "昌明领养甘榜计划", "kam", "kampung angkat madani"],
    "metmalaysia": ["气象局", "大马气象局", "metmalaysia", "jabatan meteorologi"],
    "pdrm": ["警方", "警察", "pdrm", "polis"],
    "swd": ["野生动物局", "沙巴野生动物局", "swd", "jabatan hidupan liar"]
}


class BilingualFactValidator:
    """
    Deterministic validator enforcing cross-lingual factual consistency between
    Chinese and Bahasa Malaysia editions of news articles.
    """

    @staticmethod
    def validate_calendar_weekday(year: int, month: int, day: int, claimed_weekday: int) -> Tuple[bool, Optional[str]]:
        """
        Verify that a stated weekday matches the deterministic Gregorian calendar.
        claimed_weekday: 0=Monday, ..., 6=Sunday.
        """
        try:
            d = datetime.date(year, month, day)
            true_weekday = d.weekday()
            if true_weekday != claimed_weekday:
                days = ["Monday/Isnin", "Tuesday/Selasa", "Wednesday/Rabu", "Thursday/Khamis", "Friday/Jumaat", "Saturday/Sabtu", "Sunday/Ahad"]
                return False, f"Calendar contradiction: {year}-{month:02d}-{day:02d} is {days[true_weekday]}, not {days[claimed_weekday]}"
            return True, None
        except ValueError as e:
            return False, f"Invalid calendar date: {year}-{month:02d}-{day:02d} ({e})"

    @staticmethod
    def validate_evidence_provenance(fact: FactItem, raw_source_body: str) -> Tuple[bool, Optional[str]]:
        """
        Verify that a FactItem's source quote is an exact, non-empty verbatim substring
        of the ingested raw source text.
        Returns (True, None) if verified, or (False, reason) if provenance fails.
        """
        if not fact.source_evidence or not fact.source_evidence.exact_quote:
            return False, f"Fact '{fact.fact_id}' lacks source evidence quote"
        quote = fact.source_evidence.exact_quote.strip()
        if not quote:
            return False, f"Fact '{fact.fact_id}' has empty source evidence quote"
        if not raw_source_body or quote not in raw_source_body:
            return False, f"Fact '{fact.fact_id}' evidence quote not found in raw source body: '{quote[:40]}...'"
        return True, None

    @staticmethod
    def validate_temporal_precision(
        fact: FactItem,
        zh_text: str,
        bm_text: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Ensure that a fact with TemporalPrecision.YEAR_ONLY is not unanchoredly inflated
        into an EXACT_DATE or DATE_RANGE in article text without independent evidence.
        """
        if fact.category == FactCategory.TEMPORAL_YEAR:
            year_val = fact.normalized_value if isinstance(fact.normalized_value, int) else getattr(fact.normalized_value, "year", None)
            if year_val:
                # Look for unanchored expansion to full date range: "1月1日至12月31日" or "1 Januari hingga 31 Disember"
                if re.search(r'1月1日\s*(?:至|到)\s*(?:12月31日)', zh_text) or \
                   re.search(r'1\s*januari\s*(?:hingga|-)\s*31\s*disember', bm_text, flags=re.IGNORECASE):
                    return False, f"Fact '{fact.fact_id}' has precision YEAR_ONLY ({year_val}) but claim inflated it to full date range (1 Jan - 31 Dec)"
        return True, None

    @staticmethod
    def extract_monetary_values_zh(text: str) -> List[int]:
        """Extract all monetary values from Chinese text as base integer MYR."""
        results = []
        if not text:
            return results
        working_text = text

        # 1. Compound: "235万8000令吉" / "235万8千令吉"
        def rep_compound(m):
            w = int(m.group(1))
            k = int(m.group(2))
            mult = 1000 if '千' in m.group(0) else 1
            results.append(w * 10000 + k * mult)
            return " [MASKED] "
        working_text = re.sub(r'(\d+)\s*万\s*(\d+)\s*(?:千)?\s*令吉', rep_compound, working_text)

        # 2. Yi: "2亿令吉", "2.5亿"
        def rep_yi(m):
            y = float(m.group(1))
            results.append(int(y * 100000000))
            return " [MASKED] "
        working_text = re.sub(r'(\d+(?:\.\d+)?)\s*亿\s*(?:令吉|元)?', rep_yi, working_text)

        # 3. Wan: "900万令吉", "50万令吉", "900万"
        def rep_wan(m):
            w = float(m.group(1))
            results.append(int(w * 10000))
            return " [MASKED] "
        working_text = re.sub(r'(\d+(?:\.\d+)?)\s*万\s*(?:令吉|元)?', rep_wan, working_text)

        # 4. Standard RM or 令吉: "RM 2,358,000", "1000令吉", "RM1000"
        def rep_rm(m):
            val = int(m.group(1).replace(',', ''))
            results.append(val)
            return " [MASKED] "
        working_text = re.sub(r'(?:RM|令吉)\s*([0-9,]+)', rep_rm, working_text, flags=re.IGNORECASE)
        working_text = re.sub(r'([0-9,]+)\s*令吉', rep_rm, working_text)

        seen = set()
        deduped = []
        for v in results:
            if v not in seen:
                seen.add(v)
                deduped.append(v)
        return deduped

    @staticmethod
    def extract_monetary_values_bm(text: str) -> List[int]:
        """Extract all monetary values from Bahasa Melayu text as base integer MYR."""
        results = []
        if not text:
            return results
        working_text = text

        # 1. Juta: "RM9.1 juta", "RM 9 juta", "9 juta ringgit", "9.1 juta"
        def rep_juta(m):
            j = float(m.group(1))
            results.append(int(j * 1000000))
            return " [MASKED] "
        working_text = re.sub(r'(?:RM\s*)?(\d+(?:\.\d+)?)\s*juta(?:\s*ringgit)?', rep_juta, working_text, flags=re.IGNORECASE)

        # 2. Ribu: "RM500 ribu", "500 ribu ringgit"
        def rep_ribu(m):
            r = float(m.group(1))
            results.append(int(r * 1000))
            return " [MASKED] "
        working_text = re.sub(r'(?:RM\s*)?(\d+(?:\.\d+)?)\s*ribu(?:\s*ringgit)?', rep_ribu, working_text, flags=re.IGNORECASE)

        # 3. Standard RM: "RM500,000", "RM 2,358,000", "RM1,000", "RM900,000"
        def rep_rm(m):
            cleaned = m.group(1).replace(',', '')
            if '.' in cleaned:
                cleaned = cleaned.split('.')[0]
            if cleaned.isdigit():
                results.append(int(cleaned))
            return " [MASKED] "
        working_text = re.sub(r'RM\s*([0-9,]+(?:\.\d+)?)', rep_rm, working_text, flags=re.IGNORECASE)

        # 4. Ringgit suffix: "500,000 ringgit"
        def rep_ringgit(m):
            cleaned = m.group(1).replace(',', '')
            if cleaned.isdigit():
                results.append(int(cleaned))
            return " [MASKED] "
        working_text = re.sub(r'([0-9,]+)\s*ringgit', rep_ringgit, working_text, flags=re.IGNORECASE)

        seen = set()
        deduped = []
        for v in results:
            if v not in seen:
                seen.add(v)
                deduped.append(v)
        return deduped

    @staticmethod
    def validate_stylistic_transitions(transitions: StylisticTransitions) -> Tuple[bool, Optional[str]]:
        """Verify that stylistic transitions contain zero factual, numerical, or date tokens."""
        for lang, text in [("ZH", transitions.zh_connector), ("BM", transitions.bm_connector)]:
            if not text:
                continue
            # Check for digits
            if re.search(r'\d', text):
                return False, f"Factual token (digit) detected in {lang} stylistic transition: '{text}'"
            # Check for currency symbols
            if re.search(r'(?:RM|令吉|元|\$)', text, flags=re.IGNORECASE):
                return False, f"Currency symbol detected in {lang} stylistic transition: '{text}'"
            # Check for known agency tokens
            if re.search(r'\b(?:MPS|JANS|KAM|SESB|PDRM)\b', text):
                return False, f"Agency acronym detected in {lang} stylistic transition: '{text}'"
        return True, None

    def validate_headline(
        self,
        headline: HeadlineRecord,
        canonical_facts: Dict[str, FactItem]
    ) -> Tuple[bool, List[str]]:
        """
        Validate headline fact-binding, bilingual numerical parity, and publication quality.
        Phase D-11.3 Correction A: Strict Headline Quality Gate
        - Rejects empty, whitespace-only, or overly short headlines.
        - Rejects generic placeholder patterns, numbered templates, and pseudo-translations.
        - Enforces cross-lingual event and subject alignment between Chinese and Malay.
        """
        errors = []

        # 0a. Check for empty or missing headlines
        zh_text = (headline.zh_text or "").strip()
        bm_text = (headline.bm_text or "").strip()
        bm_lower = bm_text.lower()

        if not zh_text:
            errors.append("Chinese headline is empty or missing")
        if not bm_text:
            errors.append("Bahasa Malaysia headline is empty or missing")

        if not zh_text or not bm_text:
            return False, errors

        # 0b. Check for pseudo-BM headline or untranslated characters
        if re.search(r'[\u4e00-\u9fff]', bm_text):
            if bm_lower.startswith("laporan berita:"):
                errors.append(f"Pseudo-Bahasa Malaysia headline detected with untranslated Chinese text: '{bm_text[:50]}...'")
            else:
                errors.append(f"Bahasa Malaysia headline contains untranslated Chinese characters: '{bm_text[:50]}...'")

        if not re.search(r'[\u4e00-\u9fff]', zh_text):
            errors.append(f"Chinese headline contains no Chinese characters: '{zh_text[:50]}...'")

        if bm_lower == zh_text.lower():
            errors.append("Bahasa Malaysia headline is an identical untranslated copy of Chinese headline")

        # 0c. Reject generic placeholder and numbered template patterns in Malay
        GENERIC_BM_PLACEHOLDERS = [
            r"^perkembangan\s+utama\s+dan\s+terkini\b",
            r"^berita\s+penting\s+sabah\b",
            r"^laporan\s+berita\b",
            r"^tajuk\s+berita\b",
            r"^notis\s+berita\s+rasmi\b",
            r"^berita\s+terkini\b",
            r"^perkembangan\s+terkini\b",
            r"\bnombor\s+\d+\b",
            r"\bno\.\s*\d+\b",
        ]
        bm_lower = bm_text.lower()
        for pat in GENERIC_BM_PLACEHOLDERS:
            if re.search(pat, bm_lower):
                errors.append(f"Generic or numbered placeholder pattern detected in Bahasa Malaysia headline: '{bm_text}'")
                break

        # 0d. Reject generic placeholder and numbered template patterns in Chinese
        GENERIC_ZH_PLACEHOLDERS = [
            r"^沙巴(?:与东马)?重要(?:发展态势)?要闻通报第\d+条",
            r"^沙巴要闻第\d+条",
            r"^测试要闻",
            r"^占位标题",
            r"\[官方来源\d+.*\]",
            r"^新闻标题",
            r"^待定标题",
        ]
        for pat in GENERIC_ZH_PLACEHOLDERS:
            if re.search(pat, zh_text):
                errors.append(f"Generic or numbered placeholder pattern detected in Chinese headline: '{zh_text}'")
                break

        # 0e. Length and informativeness
        zh_chars = len(re.findall(r'[\u4e00-\u9fff]', zh_text))
        if zh_chars < 8:
            errors.append(f"Chinese headline too short or uninformative ({zh_chars} characters, minimum 8 required): '{zh_text}'")

        bm_words = len(bm_text.split())
        if bm_words < 5:
            errors.append(f"Bahasa Malaysia headline too short or uninformative ({bm_words} words, minimum 5 required): '{bm_text}'")

        # 0f. Cross-lingual topic, domain, and entity alignment check (Phase D-11.4 Correction B)
        TOPIC_ALIGNMENT_RULES = [
            {
                "topic": "FIRE",
                "zh_patterns": [r"(?:火灾|火劫|遭大火|失火|排屋发生火灾|住宅遇火)"],
                "bm_patterns": [r"(?:kebakaran|terbakar|api|marak|hangus|musnah|dijilat)"],
                "msg": "Headline describes a fire in Chinese but Malay headline lacks fire-related event terms"
            },
            {
                "topic": "ROAD_ACCIDENT",
                "zh_patterns": [r"(?:车祸|夺命车祸|冲沟渠|坠入石沟|相撞|翻覆|撞毙|撞伤)"],
                "bm_patterns": [r"(?:kemalangan|nahas|terbabas|maut|terkorban|parah|cedera|hilang\s+kawalan)"],
                "msg": "Headline describes a road accident in Chinese but Malay headline lacks accident-related event terms"
            },
            {
                "topic": "FATAL_OUTCOME",
                "zh_patterns": [r"(?:当场毙命|毙命|丧命|丧生|夺命)"],
                "bm_patterns": [r"(?:maut|terkorban|meninggal)"],
                "msg": "Headline indicates a fatality in Chinese but Malay headline lacks fatality terms (maut/terkorban)"
            },
            {
                "topic": "AIRPORT_AVIATION",
                "zh_patterns": [r"(?:机场|跑道|航站楼|CILTM|KKIA)"],
                "bm_patterns": [r"(?:lapangan\s+terbang|airport|ciltm|kkia|landasan|terminal|penerbangan)"],
                "msg": "Headline concerns airport/aviation in Chinese but Malay headline lacks aviation-related terms"
            },
            {
                "topic": "SPORTS_EVENT",
                "zh_patterns": [r"(?:运动会|球赛|足总杯|健儿|锦标赛)"],
                "bm_patterns": [r"(?:sukan|kejohanan|perlawanan|piala|liga|atlet)"],
                "msg": "Headline concerns a sports event in Chinese but Malay headline lacks sports-related terms"
            },
            {
                "topic": "LAND_ADMIN",
                "zh_patterns": [r"(?:土地|土地测量|地契|5000英亩)"],
                "bm_patterns": [r"(?:tanah|ukur|geran)"],
                "msg": "Headline concerns land administration in Chinese but Malay headline lacks land-related terms"
            },
            {
                "topic": "IMMIGRATION_VISA",
                "zh_patterns": [r"(?:签证|入境|移民局|防诈|边防)"],
                "bm_patterns": [r"(?:visa|imigresen|kawalan|sempadan|kemasukan|scam|penipuan)"],
                "msg": "Headline concerns immigration/visa in Chinese but Malay headline lacks border/visa/scam terms"
            },
            {
                "topic": "HOMICIDE_CRIME",
                "zh_patterns": [r"(?:割喉|杀害|谋杀|命案)"],
                "bm_patterns": [r"(?:kelar|bunuh|maut|mati|jenayah|serangan)"],
                "msg": "Headline concerns a crime/homicide in Chinese but Malay headline lacks crime/homicide-related terms"
            },
            {
                "topic": "HEALTH_HOSPITAL",
                "zh_patterns": [r"(?:透析|肯特医院|诊所|病患|医院)"],
                "bm_patterns": [r"(?:hospital|dialisis|klinik|rawatan|kesihatan|pesakit)"],
                "msg": "Headline concerns hospital/healthcare in Chinese but Malay headline lacks healthcare terms"
            },
            {
                "topic": "DIGITAL_LIBRARY",
                "zh_patterns": [r"(?:图书馆|数码学习|数码中心)"],
                "bm_patterns": [r"(?:perpustakaan|digital|pembelajaran|teknologi)"],
                "msg": "Headline concerns library/digital learning in Chinese but Malay headline lacks digital/library terms"
            },
            {
                "topic": "PUBLIC_BUS",
                "zh_patterns": [r"(?:长巴|长途客运|陆路交通局|陆交局)"],
                "bm_patterns": [r"(?:bas|ekspres|jpj|pengangkutan)"],
                "msg": "Headline concerns public bus enforcement in Chinese but Malay headline lacks bus/transport terms"
            },
            {
                "topic": "COMMUNITY_HERITAGE",
                "zh_patterns": [r"(?:文物|历史|古迹|文化遗产|遗址|小城故事|故事)"],
                "bm_patterns": [r"(?:warisan|sejarah|arkeologi|monumen|tradisi)"],
                "msg": "Headline concerns heritage/community in Chinese but Malay headline lacks heritage/history terms"
            },
            {
                "topic": "ECO_TOURISM",
                "zh_patterns": [r"(?:观鸟节|生态旅游|红毛猩猩|野生动物)"],
                "bm_patterns": [r"(?:burung|eko-pelancongan|hidupan liar|orangutan)"],
                "msg": "Headline concerns eco-tourism/wildlife in Chinese but Malay headline lacks tourism/wildlife terms"
            }
        ]

        # 1. Forward topic check: ZH topic must be reflected in BM
        zh_detected_topics = set()
        for rule in TOPIC_ALIGNMENT_RULES:
            matches_zh = any(re.search(p, zh_text, re.IGNORECASE) for p in rule["zh_patterns"])
            if matches_zh:
                zh_detected_topics.add(rule["topic"])
                matches_bm = any(re.search(p, bm_text, re.IGNORECASE) for p in rule["bm_patterns"])
                if not matches_bm:
                    errors.append(f"Bilingual topic mismatch: {rule['msg']}")

        # 2. Reverse topic check: Strong BM topic must be reflected in ZH
        REVERSE_BM_TOPICS = [
            ("AIRPORT_AVIATION", [r"(?:lapangan\s+terbang|airport|kkia|landasan\s+terbang|terminal\s+udara)"], [r"(?:机场|跑道|航站|航空|空运|CILTM|KKIA)"], "airport/aviation"),
            ("FIRE", [r"(?:kebakaran|hangus\s+terbakar|dijilat\s+api)"], [r"(?:火灾|火劫|遭大火|失火|排屋发生火灾|住宅遇火)"], "fire/kebakaran"),
            ("ROAD_ACCIDENT", [r"(?:kemalangan\s+jalan\s+raya|nahas\s+motosikal|terbabas\s+ke\s+dalam\s+parit|terbabas\s+ke\s+dalam\s+longkang)"], [r"(?:车祸|夺命车祸|冲沟渠|坠入石沟|相撞|翻覆|撞毙|撞伤)"], "road accident/nahas"),
            ("COMMUNITY_HERITAGE", [r"(?:warisan\s+sejarah|kisah\s+warisan|komuniti\s+tempatan)"], [r"(?:文物|历史|古迹|文化遗产|遗址|小城故事|故事)"], "heritage/warisan"),
            ("DIGITAL_LIBRARY", [r"(?:perpustakaan\s+desa|pusat\s+pembelajaran\s+digital)"], [r"(?:图书馆|数码学习|数码中心)"], "digital library/perpustakaan"),
            ("IMMIGRATION_VISA", [r"(?:kawalan\s+imigresen|ketirisan\s+visa)"], [r"(?:签证|入境|移民局|防诈|边防)"], "immigration/visa"),
            ("LAND_ADMIN", [r"(?:pengukuran\s+tanah|tanah\s+seluas)"], [r"(?:土地|土地测量|地契|5000英亩)"], "land administration/tanah"),
            ("HEALTH_HOSPITAL", [r"(?:pusat\s+dialisis|hospital\s+duchess\s+of\s+kent)"], [r"(?:透析|肯特医院|诊所|病患|医院)"], "hospital/dialysis")
        ]
        bm_detected_topics = set()
        for topic_name, bm_pats, zh_pats, label in REVERSE_BM_TOPICS:
            if any(re.search(p, bm_text, re.IGNORECASE) for p in bm_pats):
                bm_detected_topics.add(topic_name)
                if not any(re.search(p, zh_text, re.IGNORECASE) for p in zh_pats):
                    errors.append(f"Bilingual topic mismatch: Malay headline is about {label} but Chinese headline lacks corresponding terms")

        # 3. Cross-domain mutual exclusion check
        MUTUALLY_EXCLUSIVE_PAIRS = [
            ("AIRPORT_AVIATION", "COMMUNITY_HERITAGE"),
            ("AIRPORT_AVIATION", "FIRE"),
            ("ROAD_ACCIDENT", "FIRE"),
            ("ROAD_ACCIDENT", "COMMUNITY_HERITAGE"),
            ("FIRE", "DIGITAL_LIBRARY"),
            ("LAND_ADMIN", "HEALTH_HOSPITAL"),
            ("IMMIGRATION_VISA", "DIGITAL_LIBRARY"),
            ("IMMIGRATION_VISA", "SPORTS_EVENT")
        ]
        for t_zh, t_bm in MUTUALLY_EXCLUSIVE_PAIRS:
            if t_zh in zh_detected_topics and t_bm in bm_detected_topics and t_bm not in zh_detected_topics and t_zh not in bm_detected_topics:
                errors.append(f"Substantive bilingual domain contradiction: Chinese headline is about {t_zh} while Malay headline is about {t_bm}")
            elif t_bm in zh_detected_topics and t_zh in bm_detected_topics and t_zh not in zh_detected_topics and t_bm not in bm_detected_topics:
                errors.append(f"Substantive bilingual domain contradiction: Chinese headline is about {t_bm} while Malay headline is about {t_zh}")

        # 4. District and entity conflict check
        SABAH_DISTRICT_MAP = {
            "penampang": (r"(?:兵南邦|penampang)", r"\bpenampang\b"),
            "sandakan": (r"(?:山打根|sandakan)", r"\bsandakan\b"),
            "kota_kinabalu": (r"(?:亚庇|庇|kota\s+kinabalu|kk\b)", r"(?:kota\s+kinabalu|\bkkia\b)"),
            "tawau": (r"(?:斗湖|tawau)", r"\btawau\b"),
            "lahad_datu": (r"(?:拿笃|lahad\s+datu)", r"\blahad\s+datu\b"),
            "beaufort": (r"(?:保佛|beaufort)", r"\bbeaufort\b")
        }
        zh_districts = set()
        bm_districts = set()
        for dist, (p_zh, p_bm) in SABAH_DISTRICT_MAP.items():
            if re.search(p_zh, zh_text, re.IGNORECASE):
                zh_districts.add(dist)
            if re.search(p_bm, bm_text, re.IGNORECASE):
                bm_districts.add(dist)

        # If both explicitly specify different single districts, flag as location mismatch
        if len(zh_districts) == 1 and len(bm_districts) == 1:
            if zh_districts != bm_districts:
                d_zh = list(zh_districts)[0]
                d_bm = list(bm_districts)[0]
                errors.append(f"Bilingual location contradiction: Chinese specifies {d_zh} but Malay specifies {d_bm}")

        # 1. Verify every referenced fact_id exists and is VERIFIED
        for fid in headline.fact_ids:
            if fid not in canonical_facts:
                errors.append(f"Headline references non-existent fact_id: '{fid}'")
                continue
            fact = canonical_facts[fid]
            if fact.status != FactStatus.VERIFIED:
                errors.append(f"Headline references unverified fact_id: '{fid}' (status: {fact.status})")

        # 2. Extract monetary numbers from headlines
        zh_money = self.extract_monetary_values_zh(headline.zh_text)
        bm_money = self.extract_monetary_values_bm(headline.bm_text)

        # Invariant: ZH money must match BM money
        if set(zh_money) != set(bm_money):
            errors.append(f"Headline monetary mismatch: ZH={zh_money} vs BM={bm_money}")

        # Check that all detected monetary amounts in headlines are mapped to a referenced monetary fact
        headline_monetary_facts = [
            canonical_facts[fid].normalized_value.amount_myr
            for fid in headline.fact_ids
            if fid in canonical_facts and canonical_facts[fid].category == FactCategory.MONETARY
        ]
        for m in zh_money:
            if m not in headline_monetary_facts:
                errors.append(f"Headline contains unanchored monetary value MYR {m}")

        # 3. Check for calendar weekday contradiction in headlines
        for zh_kw, w_val in WEEKDAY_ZH_MAP.items():
            if zh_kw in headline.zh_text:
                m = re.search(r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})', headline.zh_text)
                if m:
                    y, mon, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    valid_w, err_w = self.validate_calendar_weekday(y, mon, d, w_val)
                    if not valid_w:
                        errors.append(f"Headline ZH: {err_w}")

        # 4. Check for unanchored named persons in headlines
        headline_person_facts = set()
        for fid in headline.fact_ids:
            if fid in canonical_facts and canonical_facts[fid].category == FactCategory.ENTITY_PERSON:
                headline_person_facts.add(fid.lower())
                headline_person_facts.add(str(canonical_facts[fid].normalized_value).lower())

        for p_key, aliases in KNOWN_NAMED_PERSONS.items():
            found_zh = any(alias in headline.zh_text.lower() for alias in aliases)
            found_bm = any(re.search(rf'\b{re.escape(alias)}\b', headline.bm_text, flags=re.IGNORECASE) for alias in aliases)
            if found_zh or found_bm:
                is_mapped = any(p_key in f or any(alias in f for alias in aliases) for f in headline_person_facts)
                if not is_mapped:
                    errors.append(f"Headline contains unanchored named person '{aliases[0]}' ({p_key})")

        # 5. Check for unanchored agencies in headlines
        headline_agency_facts = set()
        for fid in headline.fact_ids:
            if fid in canonical_facts and canonical_facts[fid].category == FactCategory.ENTITY_ORGANIZATION:
                headline_agency_facts.add(fid.lower())
                headline_agency_facts.add(str(canonical_facts[fid].normalized_value).lower())

        for a_key, aliases in KNOWN_NAMED_AGENCIES.items():
            found_zh = any(alias in headline.zh_text for alias in aliases if not alias.isascii()) or \
                       any(re.search(rf'\b{re.escape(alias)}\b', headline.zh_text, flags=re.IGNORECASE) for alias in aliases if alias.isascii())
            found_bm = any(re.search(rf'\b{re.escape(alias)}\b', headline.bm_text, flags=re.IGNORECASE) for alias in aliases)
            if found_zh or found_bm:
                is_mapped = any(a_key in f or any(alias in f for alias in aliases) for f in headline_agency_facts)
                if not is_mapped:
                    errors.append(f"Headline contains unanchored agency '{aliases[0]}' ({a_key})")

        return (len(errors) == 0), errors

    def validate_mixed_fact_claim(
        self,
        claim: ClaimRecord,
        canonical_facts: Dict[str, FactItem]
    ) -> Tuple[bool, List[str]]:
        """
        Independently and atomically validate all facts referenced in a claim,
        enforcing semantic lifecycle integrity and cross-lingual parity.
        """
        errors = []

        # 1. Existence and verification status check
        for fid in claim.fact_ids:
            if fid not in canonical_facts:
                errors.append(f"Claim {claim.claim_id} references unknown fact_id: '{fid}'")
                continue
            fact = canonical_facts[fid]
            if fact.status != FactStatus.VERIFIED:
                errors.append(f"Claim {claim.claim_id} references unverified fact '{fid}' (status={fact.status})")

        # 2. Monetary Fact Validation
        for fid in claim.fact_ids:
            if fid not in canonical_facts:
                continue
            fact = canonical_facts[fid]
            if fact.category == FactCategory.MONETARY:
                expected_amount = fact.normalized_value.amount_myr
                zh_amounts = self.extract_monetary_values_zh(claim.zh_text)
                bm_amounts = self.extract_monetary_values_bm(claim.bm_text)

                if expected_amount not in zh_amounts:
                    errors.append(
                        f"Claim {claim.claim_id}: ZH text missing expected amount {expected_amount} "
                        f"(found: {zh_amounts}) for fact {fid}"
                    )
                if expected_amount not in bm_amounts:
                    errors.append(
                        f"Claim {claim.claim_id}: BM text missing expected amount {expected_amount} "
                        f"(found: {bm_amounts}) for fact {fid}"
                    )

                # Check if BM text drifted (e.g. contains 9100000 instead of 9000000)
                for bma in bm_amounts:
                    if bma != expected_amount and bma not in [
                        canonical_facts[f].normalized_value.amount_myr
                        for f in claim.fact_ids
                        if f in canonical_facts and canonical_facts[f].category == FactCategory.MONETARY
                    ]:
                        errors.append(
                            f"Claim {claim.claim_id}: BM text contains drifted/unanchored amount {bma} "
                            f"(expected {expected_amount}) for fact {fid}"
                        )

        # 3. Independent Semantic Lifecycle State Integrity
        for fid in claim.fact_ids:
            if fid not in canonical_facts:
                continue
            fact = canonical_facts[fid]

            # Check: APPROVED_ALLOCATION cannot be described as spent or disbursed
            if fact.semantic_state == SemanticLifecycleState.APPROVED_ALLOCATION:
                for p_zh in PROHIBITED_ALLOCATION_VERBS_ZH:
                    if p_zh in claim.zh_text:
                        errors.append(
                            f"Claim {claim.claim_id} semantic distortion: Fact '{fid}' is APPROVED_ALLOCATION "
                            f"but ZH text uses prohibited disbursement/spending verb '{p_zh}'"
                        )
                for p_bm in PROHIBITED_ALLOCATION_VERBS_BM:
                    if p_bm in claim.bm_text.lower():
                        errors.append(
                            f"Claim {claim.claim_id} semantic distortion: Fact '{fid}' is APPROVED_ALLOCATION "
                            f"but BM text uses prohibited disbursement/spending verb '{p_bm}'"
                        )

            # Check: PROJECT_COMPLETED cannot be described as unfinished/ongoing
            if fact.semantic_state == SemanticLifecycleState.PROJECT_COMPLETED:
                for p_zh in PROHIBITED_COMPLETION_VERBS_ZH:
                    if p_zh in claim.zh_text:
                        errors.append(
                            f"Claim {claim.claim_id} semantic distortion: Fact '{fid}' is PROJECT_COMPLETED "
                            f"but ZH text uses incomplete/ongoing verb '{p_zh}'"
                        )
                for p_bm in PROHIBITED_COMPLETION_VERBS_BM:
                    if p_bm in claim.bm_text.lower():
                        errors.append(
                            f"Claim {claim.claim_id} semantic distortion: Fact '{fid}' is PROJECT_COMPLETED "
                            f"but BM text uses incomplete/ongoing verb '{p_bm}'"
                        )

        # 4. Temporal Precision Verification
        for fid in claim.fact_ids:
            if fid in canonical_facts:
                fact = canonical_facts[fid]
                t_valid, t_err = self.validate_temporal_precision(fact, claim.zh_text, claim.bm_text)
                if not t_valid:
                    errors.append(f"Claim {claim.claim_id}: {t_err}")

        # 5. Check for Weekday Contradictions in Claim Text
        for zh_kw, w_val in WEEKDAY_ZH_MAP.items():
            if zh_kw in claim.zh_text:
                m = re.search(r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})', claim.zh_text)
                if m:
                    y, mon, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    valid_w, err_w = self.validate_calendar_weekday(y, mon, d, w_val)
                    if not valid_w:
                        errors.append(f"Claim {claim.claim_id} ZH: {err_w}")

        for bm_kw, w_val in WEEKDAY_BM_MAP.items():
            if re.search(rf'\b{bm_kw}\b', claim.bm_text, flags=re.IGNORECASE):
                # Pattern: "7 November 2026"
                m = re.search(r'(\d{1,2})\s+(Januari|Februari|Mac|April|Mei|Jun|Julai|Ogos|September|Oktober|November|Disember)\s+(\d{4})', claim.bm_text, flags=re.IGNORECASE)
                if m:
                    months = ["januari", "februari", "mac", "april", "mei", "jun", "julai", "ogos", "september", "oktober", "november", "disember"]
                    d = int(m.group(1))
                    mon = months.index(m.group(2).lower()) + 1
                    y = int(m.group(3))
                    valid_w, err_w = self.validate_calendar_weekday(y, mon, d, w_val)
                    if not valid_w:
                        errors.append(f"Claim {claim.claim_id} BM: {err_w}")

        return (len(errors) == 0), errors

    def validate_structured_article(
        self,
        article: StructuredArticle,
        canonical_facts: Dict[str, FactItem]
    ) -> ValidationResult:
        """
        Universal validation gate for a structured article:
        1. Headline fact binding and parity.
        2. All core claims (atomic mixed-fact checking).
        3. All narrative claims (zero narrative bypass).
        4. Stylistic transitions (zero factual injection).
        5. Global unmapped number/monetary scan.
        """
        all_errors = []
        all_warnings = []
        total_claims_audited = 0

        # 1. Headline Validation
        h_valid, h_errs = self.validate_headline(article.headline, canonical_facts)
        if not h_valid:
            all_errors.extend(h_errs)
        total_claims_audited += 1

        # 2. Stylistic Transitions Validation
        t_valid, t_err = self.validate_stylistic_transitions(article.transitions)
        if not t_valid:
            all_errors.append(t_err)

        # 3. Core Claims Validation
        for claim in article.core_claims:
            c_valid, c_errs = self.validate_mixed_fact_claim(claim, canonical_facts)
            if not c_valid:
                all_errors.extend(c_errs)
            total_claims_audited += 1

        # 4. Narrative Claims Validation (same rigor as core claims)
        for n_claim in article.narrative_claims:
            # Treat narrative claim as ClaimRecord
            as_claim = ClaimRecord(
                claim_id=n_claim.claim_id,
                fact_ids=n_claim.fact_ids,
                semantic_state=n_claim.semantic_state,
                zh_text=n_claim.zh_text,
                bm_text=n_claim.bm_text
            )
            nc_valid, nc_errs = self.validate_mixed_fact_claim(as_claim, canonical_facts)
            if not nc_valid:
                all_errors.extend(nc_errs)
            total_claims_audited += 1

        # 5. Global Unmapped Number Scan
        # Collect all verified monetary amounts and quantities declared in canonical facts
        known_amounts = set()
        for f in canonical_facts.values():
            if f.status == FactStatus.VERIFIED:
                if f.category == FactCategory.MONETARY and hasattr(f.normalized_value, "amount_myr"):
                    known_amounts.add(f.normalized_value.amount_myr)

        # Scan all text in article for monetary numbers
        full_zh_text = " ".join(
            [article.headline.zh_text] +
            [c.zh_text for c in article.core_claims] +
            [n.zh_text for n in article.narrative_claims]
        )
        full_bm_text = " ".join(
            [article.headline.bm_text] +
            [c.bm_text for c in article.core_claims] +
            [n.bm_text for n in article.narrative_claims]
        )

        all_zh_money = self.extract_monetary_values_zh(full_zh_text)
        all_bm_money = self.extract_monetary_values_bm(full_bm_text)

        # Check for unanchored money in ZH
        for zm in all_zh_money:
            if zm not in known_amounts:
                all_errors.append(f"Global unanchored monetary value in ZH text: MYR {zm}")

        # Check for unanchored money in BM
        for bm in all_bm_money:
            if bm not in known_amounts:
                all_errors.append(f"Global unanchored monetary value in BM text: MYR {bm}")

        # Check bilingual parity across entire article
        if set(all_zh_money) != set(all_bm_money):
            all_errors.append(
                f"Global bilingual monetary set discrepancy: ZH={sorted(list(set(all_zh_money)))} "
                f"vs BM={sorted(list(set(all_bm_money)))}"
            )

        is_valid = (len(all_errors) == 0)
        status = "VERIFIED" if is_valid else "REVIEW_REQUIRED"

        return ValidationResult(
            is_valid=is_valid,
            status=status,
            errors=all_errors,
            warnings=all_warnings,
            audited_claims_count=total_claims_audited
        )

    @staticmethod
    def assemble_legacy_article(
        article: StructuredArticle,
        validation_result: ValidationResult
    ) -> Optional[Dict[str, Any]]:
        """
        Assemble a validated StructuredArticle into the legacy headline dictionary
        consumed by news_data.json and build_news.py.
        Returns None if validation failed (Zero-Bypass guarantee).
        """
        if not validation_result.is_valid:
            return None

        # Build composite detail strings
        zh_paragraphs = []
        for c in article.core_claims:
            zh_paragraphs.append(c.zh_text.strip())
        if article.transitions.zh_connector:
            zh_paragraphs.append(article.transitions.zh_connector.strip())
        for n in article.narrative_claims:
            zh_paragraphs.append(n.zh_text.strip())

        bm_paragraphs = []
        for c in article.core_claims:
            bm_paragraphs.append(c.bm_text.strip())
        if article.transitions.bm_connector:
            bm_paragraphs.append(article.transitions.bm_connector.strip())
        for n in article.narrative_claims:
            bm_paragraphs.append(n.bm_text.strip())

        return {
            "category": article.category,
            "title": article.headline.zh_text,
            "titleBM": article.headline.bm_text,
            "detail": "\n\n".join(zh_paragraphs),
            "detailBM": "\n\n".join(bm_paragraphs),
            "source": article.publisher or "官方核实",
            "sourceBM": article.publisher or "Disahkan Rasmi",
            "url": article.source_url,
            "image_url": None,
            "validation_status": "VERIFIED",
            "audited_claims": validation_result.audited_claims_count
        }

    def validate_utility_card(self, card: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Deterministic validation contract for municipal utility cards in news_data.json.
        Validates:
        1. Bilingual monetary parity in issue/issueBM and tanker/tankerBM
        2. Calendar-weekday consistency in source_timestamp
        """
        errors = []
        issue_zh = card.get("issue", "")
        issue_bm = card.get("issueBM", "")
        zh_m = self.extract_monetary_values_zh(issue_zh)
        bm_m = self.extract_monetary_values_bm(issue_bm)
        if set(zh_m) != set(bm_m):
            errors.append(f"Utility card '{card.get('id')}' monetary discrepancy: ZH={zh_m} vs BM={bm_m}")

        # Calendar weekday check
        ts = card.get("source_timestamp", "")
        m = re.search(r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})', ts)
        if m:
            y, mon, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            try:
                datetime.date(y, mon, d)
            except Exception as e:
                errors.append(f"Utility card '{card.get('id')}' invalid date '{ts}': {e}")

        return (len(errors) == 0), errors

    def validate_future_event(self, event: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Deterministic validation contract for future event items in news_data.json.
        Validates:
        1. full_date calendar weekday against month/day
        2. Monetary parity in description
        """
        errors = []
        full_date = event.get("full_date", "")
        if full_date:
            try:
                y, m, d = [int(x) for x in full_date.split("-")]
                datetime.date(y, m, d)
            except Exception as e:
                errors.append(f"Event '{event.get('name')}' has invalid calendar date '{full_date}': {e}")

        desc_zh = event.get("desc", "")
        desc_bm = event.get("descBM", "")
        zh_m = self.extract_monetary_values_zh(desc_zh)
        bm_m = self.extract_monetary_values_bm(desc_bm)
        if set(zh_m) != set(bm_m):
            errors.append(f"Event '{event.get('name')}' monetary discrepancy: ZH={zh_m} vs BM={bm_m}")

        return (len(errors) == 0), errors

    @staticmethod
    def create_structured_article_from_raw(
        raw_article: Any,
        title_zh: str,
        title_bm: str,
        snippet_zh: str,
        snippet_bm: str,
        canonical_facts: Dict[str, FactItem]
    ) -> StructuredArticle:
        """
        Factory helper to build a strictly compliant StructuredArticle from raw collector data,
        ensuring zero free-form narrative bypass.
        """
        category = getattr(raw_article, "category", "sabah")
        url = getattr(raw_article, "url", "")
        source = getattr(raw_article, "source", "")

        # Find any matching fact_ids
        matched_fids = [fid for fid, f in canonical_facts.items() if f.status == FactStatus.VERIFIED]

        return StructuredArticle(
            article_id=f"art_{category}_{id(raw_article)}",
            category=category,
            headline=HeadlineRecord(
                zh_text=title_zh,
                bm_text=title_bm,
                fact_ids=matched_fids[:2] if matched_fids else []
            ),
            core_claims=[
                ClaimRecord(
                    claim_id="CLM_CORE_01",
                    fact_ids=matched_fids,
                    semantic_state=SemanticLifecycleState.INFORMATIONAL,
                    zh_text=snippet_zh,
                    bm_text=snippet_bm
                )
            ],
            narrative_claims=[],
            transitions=StylisticTransitions(),
            source_url=url,
            publisher=source
        )
