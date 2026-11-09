import re
from typing import Dict, Any, Tuple, Optional, List

# Sabah geographic anchors (districts, towns, leaders, agencies)
SABAH_DISTRICTS = [
    # English / Malay
    "sandakan", "kota kinabalu", "tawau", "lahad datu", "kudat", "keningau",
    "semporna", "ranau", "beaufort", "penampang", "tuaran", "papar",
    "beluran", "kinabatangan", "telupid", "paitan", "tongod", "nabawan",
    "tenom", "sipitang", "kuala penyu", "kota belud", "kota marudu",
    "pitas", "kunak", "tambunan", "likas", "inanam", "menggatal", "putatan",
    "sepanggar", "libaran", "batu sapi", "karamunting", "tanjong papat",
    "elopura", "labuk", "sekong", "gum-gum", "sukau", "kundasang",
    # Chinese
    "沙巴", "山打根", "亚庇", "斗湖", "拿笃", "古达", "根地咬",
    "仙本那", "兰瑙", "保佛", "兵南邦", "斗亚兰", "吧巴",
    "比鲁兰", "京那巴当岸", "特鲁必", "拜丹", "同笃", "纳巴湾",
    "丹南", "实必丹", "瓜拉班尤", "古打毛律", "哥打马鲁都",
    "必达士", "昆达山", "坤达山", "担布南", "里卡士", "下南南",
    "孟加达", "必打丹", "实邦加", "利巴兰", "三脚石", "加拉敏丁",
    "丹绒巴拔", "伊罗普拉", "拉卜", "西加柳", "贡贡", "苏高", "肯特医院"
]

SABAH_ENTITIES = [
    "mps", "dbkk", "jans", "sesb", "sabah fc", "esscom", "jkns",
    "hajiji", "哈芝芝", "phoong jin zhe", "冯晋哲", "masidi", "马西迪",
    "jeffrey kitingan", "杰菲里", "frankie poon", "潘明丰", "vivian wong", "黄诗怡",
    "bung moktar", "邦莫达", "shafie apdal", "沙菲益", "warisan", "民兴党",
    "grs", "沙盟", "upko", "沙民统", "pbs", "沙巴团结党", "star", "沙巴立新党",
    "ldp", "自民党", "sapp", "进步党",
    "沙陆交局", "ciltm", "kkia", "庇机场", "亚庇机场"
]

# Sarawak geographic anchors (districts, towns, leaders, agencies)
SARAWAK_DISTRICTS = [
    # English / Malay
    "sarawak", "kuching", "miri", "sibu", "bintulu", "sri aman", "sarikei",
    "limbang", "lawas", "kapit", "betong", "mukah", "samarahan", "serian",
    "bau", "lundu", "marudi", "kanowit", "song", "belaga", "dalat", "daro",
    "matu", "julau", "pakan", "selangau", "tatau", "sebauh", "padawan",
    "siburan", "tebedu", "lubok antu", "simunjan", "asajaya", "gedong",
    "sebuyau", "batu kawa", "padungan", "pending", "batu lintang",
    "kota sentosa", "dudong", "bukit assek", "bawang assan", "pelawan",
    "kenyalang", "senadin", "piasau", "pujut", "lutong", "bekenu",
    # Chinese
    "砂拉越", "砂州", "古晋", "美里", "诗巫", "民都鲁", "斯里阿曼", "泗里街",
    "林梦", "老越", "加帛", "木中", "沐胶", "三马拉汉", "西连", "石隆门",
    "伦乐", "马鲁帝", "加拿逸", "桑", "布拉甲", "达叻", "达佬", "麻笃",
    "如楼", "巴干", "实兰沟", "达岛", "实包勿", "巴达旺", "西布兰", "打必禄",
    "鲁勃安都", "西文占", "雅沙再也", "日廊", "诗巫瑶", "石角", "浮罗岸",
    "朋岭", "巴都林当", "哥打圣淘沙", "都东", "武吉阿瑟", "巴旺阿山",
    "柏拉旺", "肯雅兰", "史纳汀", "卑尔骚", "埔奕", "罗东", "柏戈奴", "珠巴"
]

SARAWAK_ENTITIES = [
    "gps", "砂盟", "supp", "人联党", "pbb", "土保党", "prs", "人民党",
    "pdp", "民进党", "abang johari", "阿邦佐哈里", "阿邦佐", "sim kui hian", "沈桂贤",
    "chong chieng jen", "张健仁", "sebastian ting", "陈超耀", "tiong king sing", "张庆信",
    "lee kim shin", "李景胜", "douglas uggah", "道格拉斯", "awang tengah", "阿旺登雅",
    "dbku", "mbks", "smc", "诗巫市议会", "mbm", "美里市政局", "petros", "unifor"
]

# Peninsular locations (Phase D-11.2 - Prevent national/peninsular news leaking into Sabah/Sandakan)
PENINSULAR_LOCATIONS = [
    "selangor", "雪兰莪", "shah alam", "莎阿南", "taman sri muda", "太子园",
    "klang", "巴生", "petaling jaya", "八打灵再也", "subang", "梳邦", "puchong", "蒲种",
    "kuala lumpur", "吉隆坡", "putrajaya", "布城", "cyberjaya", "赛城",
    "penang", "槟城", "pulau pinang", "槟州", "george town", "乔治市", "butterworth", "北海",
    "perak", "霹雳", "ipoh", "怡保", "taiping", "太平",
    "johor", "柔佛", "johor bahru", "新山", "muar", "麻坡", "batu pahat", "峇株巴辖",
    "kedah", "吉打", "alor setar", "亚罗士打", "sungai petani", "双溪大年",
    "kelantan", "吉兰丹", "kota bharu", "哥打峇鲁",
    "terengganu", "登嘉楼", "kuala terengganu", "瓜拉登嘉楼",
    "pahang", "彭亨", "kuantan", "关丹", "cameron highlands", "金马仑",
    "melaka", "马六甲", "malacca",
    "negeri sembilan", "森美兰", "seremban", "芙蓉",
    "perlis", "玻璃市", "kangar", "加央"
]

class GeographicVerifier:
    def __init__(self):
        pass

    def inspect_text(self, text: str) -> Tuple[List[str], List[str]]:
        """Return found Sabah and Sarawak anchor mentions."""
        lower_t = text.lower()
        found_sabah = []
        found_sarawak = []

        for anchor in SABAH_DISTRICTS + SABAH_ENTITIES:
            pattern = r'\b' + re.escape(anchor) + r'\b' if anchor.isascii() else re.escape(anchor)
            if re.search(pattern, lower_t):
                found_sabah.append(anchor)

        for anchor in SARAWAK_DISTRICTS + SARAWAK_ENTITIES:
            pattern = r'\b' + re.escape(anchor) + r'\b' if anchor.isascii() else re.escape(anchor)
            if re.search(pattern, lower_t):
                found_sarawak.append(anchor)

        return found_sabah, found_sarawak

    def inspect_peninsular(self, text: str) -> List[str]:
        """Return found Peninsular Malaysia anchor mentions."""
        lower_t = text.lower()
        found_peninsular = []
        for anchor in PENINSULAR_LOCATIONS:
            pattern = r'\b' + re.escape(anchor) + r'\b' if anchor.isascii() else re.escape(anchor)
            if re.search(pattern, lower_t):
                found_peninsular.append(anchor)
        return found_peninsular

    def verify(
        self,
        title: str,
        snippet: str = "",
        body: str = "",
        url: str = "",
        source: str = "",
        proposed_category: str = "general"
    ) -> Dict[str, Any]:
        """
        Strict Geographic Verification Engine:
        - Never classify an article as Sabah news merely because publisher is Sabah-facing.
        - Geographic classification for Sandakan/Sabah requires actual evidence in title or body.
        - Strict isolation between Sabah, Sarawak, and Peninsular Malaysia.
        - RSS query tokens or feed names alone NEVER trigger Sandakan or Sabah classification.
        - Reclassifies or rejects geographic mismatches.
        """
        # Authoritative content text: title + body (ignore query tokens in snippet)
        content_text = f"{title or ''} {body or ''}"
        content_lower = content_text.lower()

        found_sabah_content, found_sarawak_content = self.inspect_text(content_text)
        found_peninsular_content = self.inspect_peninsular(content_text)

        # Also inspect URL indicators
        url_lower = (url or "").lower()
        has_sabah_url = "cat=8" in url_lower or "sabah.sinchew" in url_lower or "/news/sabah" in url_lower
        has_sarawak_url = "cat=3" in url_lower or "/news/sarawak" in url_lower or "sinchew.com.my/category/砂拉越" in url_lower

        found_sabah = list(set(found_sabah_content))
        if has_sabah_url and "sabah_url_indicator" not in found_sabah:
            found_sabah.append("sabah_url_indicator")

        found_sarawak = list(set(found_sarawak_content))
        if has_sarawak_url and "sarawak_url_indicator" not in found_sarawak:
            found_sarawak.append("sarawak_url_indicator")

        # Explicit Sandakan check ONLY in content_text (title + body)
        sandakan_terms = ["sandakan", "山打根", "肯特医院", "hospital duchess of kent", "hdok", "majlis perbandaran sandakan"]
        has_sandakan = any(term in content_lower for term in sandakan_terms)
        if not has_sandakan and ("mps" in (title or "").lower() or "mps" in (body or "").lower()):
            if not any(pen in content_lower for pen in ["selayang", "seremban"]):
                has_sandakan = True

        has_real_sabah_content = len(found_sabah_content) > 0
        has_peninsular = len(found_peninsular_content) > 0

        # Scope determination
        if has_peninsular and not has_real_sabah_content:
            # Clear Peninsular news leaking into query results
            geo_scope = "national"
            is_sabah = False
            is_sarawak = len(found_sarawak_content) > 0
        elif has_sandakan:
            geo_scope = "sandakan"
            is_sabah = True
            is_sarawak = False
        elif has_real_sabah_content or (has_sabah_url and not found_sarawak_content and not has_peninsular):
            geo_scope = "sabah"
            is_sabah = True
            is_sarawak = False
        elif len(found_sarawak) > 0 and not has_real_sabah_content:
            geo_scope = "sarawak"
            is_sabah = False
            is_sarawak = True
        else:
            geo_scope = "national"
            is_sabah = False
            is_sarawak = False

        # Publisher Correction
        corrected_source = source
        if "诗华" in source:
            if is_sarawak and not is_sabah:
                corrected_source = "诗华日报 (砂拉越版)"
            elif "cat=3" in url_lower:
                corrected_source = "诗华日报 (砂拉越版)"
            elif is_sabah or "cat=8" in url_lower:
                corrected_source = "诗华日报沙巴版"
            else:
                corrected_source = "诗华日报"

        # Classification Logic
        verified_category = proposed_category
        rejection_reason = None

        if has_peninsular and not has_real_sabah_content:
            if proposed_category == "sabah":
                verified_category = "national"
                rejection_reason = (
                    f"GEOGRAPHIC_MISMATCH: Article concerns Peninsular Malaysia ({', '.join(found_peninsular_content[:3])}) "
                    f"with no Sabah relevance. Reclassified to national."
                )
        elif proposed_category == "sabah":
            # If proposed category is Sabah, but the article has Sarawak anchors and NO Sabah anchors:
            if is_sarawak and not has_real_sabah_content:
                verified_category = "national"  # Demote from Sabah to National/Regional
                rejection_reason = (
                    f"GEOGRAPHIC_MISMATCH: Article concerns Sarawak ({', '.join(found_sarawak[:3])}) "
                    f"with no Sabah relevance. Reclassified to national."
                )
            elif not is_sabah:
                # No Sabah anchors at all
                verified_category = "national"
                rejection_reason = "GEOGRAPHIC_MISMATCH: No Sabah entities or locations found. Reclassified to national."

        return {
            "verified_category": verified_category,
            "geo_scope": geo_scope,
            "is_sabah": is_sabah,
            "is_sarawak": is_sarawak,
            "found_sabah": found_sabah,
            "found_sarawak": found_sarawak,
            "corrected_source": corrected_source,
            "rejection_reason": rejection_reason
        }
