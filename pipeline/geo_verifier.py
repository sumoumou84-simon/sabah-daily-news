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
    "ldp", "自民党", "sapp", "进步党"
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
        - Strict isolation between Sabah and Sarawak.
        - Reclassifies or rejects geographic mismatches.
        """
        combined_text = f"{title} {snippet} {body}"
        found_sabah, found_sarawak = self.inspect_text(combined_text)

        # Also inspect URL indicators
        url_lower = (url or "").lower()
        if "cat=8" in url_lower or "sabah.sinchew" in url_lower or "/news/sabah" in url_lower:
            if "sabah_url_indicator" not in found_sabah:
                found_sabah.append("sabah_url_indicator")

        if "cat=3" in url_lower or "/news/sarawak" in url_lower or "sinchew.com.my/category/砂拉越" in url_lower:
            if "sarawak_url_indicator" not in found_sarawak:
                found_sarawak.append("sarawak_url_indicator")

        is_sabah = len(found_sabah) > 0
        is_sarawak = len(found_sarawak) > 0

        # Scope determination
        geo_scope = "national"
        if any(term in combined_text.lower() for term in ["sandakan", "山打根", "mps", "肯特医院"]):
            geo_scope = "sandakan"
        elif is_sabah and not is_sarawak:
            geo_scope = "sabah"
        elif is_sarawak and not is_sabah:
            geo_scope = "sarawak"

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

        if proposed_category == "sabah":
            # If proposed category is Sabah, but the article has Sarawak anchors and NO Sabah anchors:
            if is_sarawak and not (set(found_sabah) - {"sabah_url_indicator"}):
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
