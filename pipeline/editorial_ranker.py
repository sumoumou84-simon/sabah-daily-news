#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sabah Daily News — Phase D-11: Editorial Ranker & Daily Top-10 Selection Engine
Enforces:
1. Strict Geographic Hierarchy: Sandakan > Sabah > National with Sabah Impact > International with Sabah Impact.
2. Sarawak Isolation: Sarawak-only stories are strictly excluded, regardless of high-impact keywords.
3. Routine Low-Value Exclusion: Routine ceremonies, galas, courtesy visits, and maintenance notices are dropped.
4. Protection of Major News: Does not accidentally exclude policy decisions, serious incidents, infrastructure milestones, or major sports results.
5. Deterministic Tie-Breaking: Produces 100% reproducible rankings for the same input.
"""

import re
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collectors.base import RawArticle
from pipeline.geo_verifier import GeographicVerifier
from pipeline.deduplicator import ArticleDeduplicator

MYT = timezone(timedelta(hours=8))

# Routine ceremonial and low-value announcement patterns
ROUTINE_EVENT_PATTERNS = [
    r"(?:晚宴|会庆|周年庆|周年会庆|联欢晚宴|庆典晚会|新春团拜|切蛋糕)",
    r"(?:挥旗礼|火炬行|友谊赛|羽球邀请赛|高尔夫球赛|健走活动)",
    r"(?:常态供水|例行检修|清洗水池|例行水压测试)",
    r"(?:礼貌拜会|友好访问|拍照留念|赠送纪念品|互相交流)",
    r"(?:恭贺|寿辰|荣休|讣告|挽词|会员大会召集)",
    r"(?:敦聘|委任状|宣誓就职|就职典礼|出任顾问|受委顾问|分享会|讲座会|交流营|夏令营|急救营|训练营|生活营|露营)",
    r"(?:小城故事|小影小憾|茶余饭后|人在江湖|微言大义|读者投书|读者来信|副刊|专栏|随笔|散文|回忆录|游记|摄影展|摄影集|特辑|征文)",
    r"【(?:小影小憾|小城故事|副刊|专栏|随笔|散文|散记|回忆|感言|心语|杂谈|杂感|视角|漫谈|短波|读者|心声)】"
]

# Protected high-impact news patterns (NEVER drop if any match)
# Phase D-11.3: Expanded to explicitly cover land reforms, immigration/visa enforcement,
# tourism special budgets, transport/aviation infrastructure, and education/health developments.
# Replaced isolated '拨款' with specific government budget/allocation patterns to prevent
# routine social dinners with small guest donations from masquerading as public policy.
PROTECTED_HIGH_IMPACT_PATTERNS = [
    r"(?:水灾|暴雨预警|滑坡|火灾|沉船|空难|夺命车祸|命案|搜救|淹水)",
    r"(?:财政预算案|联邦拨款|发展拨款|州预算|特别预算|特别拨款|专项拨款|修缮拨款|税收|公积金|补贴|通胀|电费|水费调整|旅游预算)",
    r"(?:州议会|内阁决议|宪报公布|法庭判决|选举|选区|施政)",
    r"(?:泛婆大道|机场扩建|机场发展|ciltm|kkia|港口|深水码头|医院落成|水坝|供电网|通车|竣工|公路维修|基建提升)",
    r"(?:经贸峰会|外资引进|工业园|跨国直航|RCEP|招商|低息贷款|中小企业)",
    r"(?:土地测量|土地申请|地契|原住民习俗地|5000英亩|土地改革)",
    r"(?:入境监管|签证漏洞|边防|边境管制|反诈骗|防诈|伪装乘客|交通执法)",
    r"(?:大学转型|校舍修缮|微型华小|数码中心|数码学习|透析中心|医疗设备)",
    r"(?:奥运|亚运|汤尤杯|全英赛)"
]

# Keywords indicating national or international news has material impact on Sabah
# Phase D-11.2: Removed generic "砂拉越" and "婆罗洲" which caused false Sabah relevance
SABAH_RELEVANCE_PATTERNS = [
    r"(?:沙巴|东马|联邦拨款|1963年马来西亚协定|ma63)",
    r"(?:海运费|沿海贸易政策|cabotage|沙巴航线|东马航线|内陆航线)",
    r"(?:东安局|esscom|沙巴东海岸|菲律宾边境|印尼新首都|努山塔拉|nusantara)",
    r"(?:马石油|petronas|石油税|沙巴电力|sesb|泛婆大道|pan borneo)"
]


class EditorialRanker:
    """
    Deterministic Top-10 Editorial Selection Engine.
    Operates on confirmed, deduplicated RawArticle records.
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config or {}
        self.geo_verifier = GeographicVerifier()
        self.deduplicator = ArticleDeduplicator()

    def is_routine_exclusion(self, text: str, title: str = "") -> bool:
        """
        Check if an article is routine social fluff, low-value ceremony, or opinion/column essay.
        Phase D-11.4 Correction A: Strict Column & Non-News Feature Exclusion.
        - Excludes newspaper columns, opinion pieces, and feature essays (e.g. 【小影小憾】, 【小城故事】).
        - Excludes routine dinners, anniversary celebrations, AGM courtesies, and youth camps.
        - Preserves genuine public-interest community, heritage, tourism, and environmental hard news.
        """
        lower_t = text.lower()
        lower_title = (title or "").lower()

        # 1. COLUMN & OPINION FEATURE CHECK (Highest Priority Exclusion)
        # Recognizes standard Chinese Malaysian column banners and brackets
        column_patterns = [
            r"【(?:小影小憾|小城故事|人在江湖|茶余饭后|微言大义|读者投书|读者来信|言论|专栏|副刊|随笔|散文|漫谈|心语|杂感|特辑|征文|回忆录|游记|摄影展|摄影集)】",
            r"^(?:【[^】]+】)?\s*(?:专栏|副刊|随笔|散文|回忆录|游记)[：:\s]",
            r"(?:小影小憾|小城故事|茶余饭后|人在江湖|微言大义|读者投书|读者来信)"
        ]
        is_column = any(re.search(pat, lower_title) for pat in column_patterns) or \
                    any(re.search(pat, lower_t) for pat in column_patterns)

        if is_column:
            # Only emergency breaking news (accidents/disasters) can ever override a column flag
            is_emergency = bool(re.search(r"(?:水灾|暴雨预警|滑坡|火灾|沉船|空难|夺命车祸|命案)", lower_title))
            if not is_emergency:
                return True

        # 2. ROUTINE CEREMONY & ANNOUNCEMENT CHECK ON TITLE
        if lower_title:
            is_emergency = bool(re.search(r"(?:水灾|暴雨预警|滑坡|火灾|沉船|空难|夺命车祸|命案)", lower_title))
            if not is_emergency:
                for pat in ROUTINE_EVENT_PATTERNS:
                    if re.search(pat, lower_title):
                        return True

        # 3. HIGH-IMPACT POLICY & EMERGENCY EXEMPTION FOR BODY CONTENT
        for pat in PROTECTED_HIGH_IMPACT_PATTERNS:
            if re.search(pat, lower_t):
                return False

        # 4. ROUTINE PATTERNS IN BODY CONTENT
        for pat in ROUTINE_EVENT_PATTERNS:
            if re.search(pat, lower_t):
                return True

        return False

    def has_sabah_material_impact(self, text: str) -> bool:
        """Check whether a national or international story materially affects Sabah."""
        lower_t = text.lower()
        for pat in SABAH_RELEVANCE_PATTERNS:
            if re.search(pat, lower_t):
                return True
        return False

    def has_sabah_sports_relevance(self, text: str) -> bool:
        """Check whether a sports story involves Sabah teams, athletes, or venues."""
        lower_t = text.lower()
        sabah_sports_patterns = [
            r"(?:sabah fc|沙巴队|沙巴足球|沙巴健儿|沙巴选手|沙巴代表团|沙巴运动员)",
            r"(?:likas stadium|stadium likas|里卡士体育场|里卡士体育馆)",
            r"(?:sukan sabah|sukan pbt|地方政府运动会|沙巴运动会|saga)",
        ]
        return any(re.search(pat, lower_t) for pat in sabah_sports_patterns)

    def score_article(self, art: RawArticle) -> Tuple[int, str]:
        """
        Calculate deterministic editorial score and category qualification.
        Returns: (score, reason)
        """
        combined_text = f"{art.title} {art.snippet} {art.body}"
        geo_res = self.geo_verifier.verify(
            title=art.title,
            snippet=art.snippet,
            body=art.body,
            url=art.url,
            source=art.source,
            proposed_category=art.category
        )

        is_sabah = geo_res.get("is_sabah", False) or art.extra.get("is_sabah", False)
        is_sarawak = geo_res.get("is_sarawak", False) or art.extra.get("is_sarawak", False)
        geo_scope = geo_res.get("geo_scope") or art.extra.get("geo_scope", "")

        lower_t = combined_text.lower()
        content_text = f"{art.title or ''} {art.body or ''}"
        content_lower = content_text.lower()

        sarawak_kw = ["砂拉越", "sarawak", "古晋", "kuching", "美里", "miri", "诗巫", "sibu", "民都鲁", "bintulu"]
        sabah_kw = ["沙巴", "sabah", "山打根", "sandakan", "亚庇", "kota kinabalu", "斗湖", "tawau", "拿笃", "lahad datu", "兵南邦", "penampang"]
        has_sarawak = any(k in content_lower for k in sarawak_kw) or is_sarawak
        has_sabah = any(k in content_lower for k in sabah_kw) or is_sabah

        # 1. STRICT SARAWAK EXCLUSION:
        # A Sarawak-only incident must NOT enter the Sabah list, regardless of keywords like "fire".
        if has_sarawak and not has_sabah:
            return -1000, "EXCLUDED_SARAWAK_ONLY"

        # 2. ROUTINE CEREMONY / FLUFF EXCLUSION
        if self.is_routine_exclusion(combined_text, title=art.title):
            return -500, "EXCLUDED_ROUTINE_FLUFF"

        # 3. SPORTS RELEVANCE GATE (Phase D-11.2)
        # Non-Sabah domestic matches (e.g. Selangor vs. Kuching City FC) must be strictly excluded.
        is_sports = (art.category == "sports" or "piala fa" in lower_t or "fa cup" in lower_t)
        is_major_intl_sports = bool(re.search(r"(?:奥运|亚运|汤尤杯|全英赛|korea open|韩国公开赛|man wei chong|万纬聪)", lower_t))
        if is_sports:
            has_sports_sabah = is_sabah or self.has_sabah_sports_relevance(combined_text)
            if not (has_sports_sabah or is_major_intl_sports):
                return -300, "EXCLUDED_UNRELATED_NATIONAL_OR_INTL"

        # 4. GEOGRAPHIC BASE SCORING
        score = 0
        sandakan_terms = ["sandakan", "山打根", "肯特医院", "hospital duchess of kent", "majlis perbandaran sandakan"]
        has_sandakan_content = any(term in content_lower for term in sandakan_terms)
        if not has_sandakan_content and ("mps" in (art.title or "").lower() or "mps" in (art.body or "").lower()):
            if not any(pen in content_lower for pen in ["selayang", "seremban"]):
                has_sandakan_content = True

        # Sandakan score requires actual content evidence, never Google News query feed tokens
        is_sandakan = (geo_scope == "sandakan" or has_sandakan_content) and is_sabah

        if is_sandakan:
            score += 40
        elif is_sabah:
            score += 25
        elif art.category in ("national", "sports", "general", "sabah"):
            # National / Sports / International must have meaningful Sabah relevance
            if self.has_sabah_material_impact(combined_text):
                score += 15
            elif art.category == "sports" and is_major_intl_sports:
                score += 8  # Major world stage badminton/Olympic sports of national interest
            else:
                return -300, "EXCLUDED_UNRELATED_NATIONAL_OR_INTL"
        else:
            return -300, "EXCLUDED_UNRELATED_OTHER"

        # 5. TOPIC & PUBLIC IMPACT BOOST (Phase D-11.3: Incident Damping & Policy Boost)
        is_routine_incident = bool(
            re.search(r"(?:骑士失控|摩托失控|单车失控|轿车失控|一间双层排屋|一间独立式|一间木屋|排屋发生火灾|住宅遇火劫|杂货赊账|口角|寻仇)", combined_text)
        )
        has_major_impact = False
        for pat in PROTECTED_HIGH_IMPACT_PATTERNS:
            if re.search(pat, combined_text.lower()):
                has_major_impact = True
                break

        if has_major_impact:
            if is_routine_incident:
                score += 8   # Localized single-incident public safety baseline
            else:
                score += 15  # Major policy, budget, land, infrastructure, disaster, or border development

        # 6. MULTI-SOURCE CORROBORATION BOOST
        corrob_sources = art.extra.get("corroborating_sources", [])
        if len(corrob_sources) >= 2:
            score += 10
        elif art.extra.get("content_verification_status") == "corroborated":
            score += 10

        # 7. TIMELINESS / FRESHNESS BOOST
        if art.published_at:
            try:
                now_myt = datetime.now(MYT)
                dt = art.published_at
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=MYT)
                else:
                    dt = dt.astimezone(MYT)
                hours_old = (now_myt - dt).total_seconds() / 3600.0
                if hours_old <= 24:
                    score += 5
                elif hours_old <= 36:
                    score += 2
            except Exception:
                pass

        return score, "QUALIFIED"

    def rank_and_select_top_10(self, articles: List[RawArticle], target_count: int = 10) -> List[RawArticle]:
        """
        Rank all confirmed articles and select the top N (default 10) qualifying stories.
        Enforces deterministic tie-breaking, Top-10 duplicate suppression, and
        routine incident diversity damping (Phase D-11.3 Correction C).
        """
        scored_candidates = []

        for art in articles:
            score, status = self.score_article(art)
            if score > 0 and status == "QUALIFIED":
                art.extra["editorial_score"] = score
                art.extra["ranking_status"] = status
                scored_candidates.append(art)
            else:
                art.extra["editorial_score"] = score
                art.extra["ranking_status"] = status

        # Deterministic sorting:
        # 1. Primary: editorial_score (descending)
        # 2. Secondary: published_at (descending, undated last)
        # 3. Tertiary: substantive body length (descending)
        # 4. Quaternary: SHA256 of URL (ascending, guarantees 100% deterministic tie-break)
        def sort_key(a: RawArticle):
            score = a.extra.get("editorial_score", 0)
            pub_ts = 0.0
            if a.published_at:
                try:
                    pub_ts = a.published_at.timestamp()
                except Exception:
                    pub_ts = 0.0
            body_len = len(a.body or a.snippet or "")
            url_hash = hashlib.sha256(a.url.encode("utf-8")).hexdigest()
            return (-score, -pub_ts, -body_len, url_hash)

        scored_candidates.sort(key=sort_key)

        # Routine Incident Diversity Control (Phase D-11.3 Correction C):
        # Prevent repeated minor localized incidents (single-vehicle accidents, single-house fires, isolated disputes)
        # from crowding out major policy, economy, infrastructure, and public interest developments.
        def get_routine_incident_type(art: RawArticle) -> Optional[str]:
            t = (art.title or "").lower()
            if any(k in t for k in ["骑士失控", "摩托失控", "单车失控", "轿车失控"]):
                return "ROUTINE_SINGLE_ACCIDENT"
            if any(k in t for k in ["一间双层排屋", "一间独立式", "一间木屋", "排屋发生火灾", "住宅遇火劫"]):
                return "ROUTINE_SINGLE_FIRE"
            if any(k in t for k in ["杂货赊账", "口角", "寻仇", "私人纠纷"]):
                return "ROUTINE_ISOLATED_DISPUTE"
            return None

        selected: List[RawArticle] = []
        reserve_candidates: List[RawArticle] = []

        for candidate in scored_candidates:
            matched_selected = None
            for s in selected:
                if self.deduplicator.is_same_event(candidate, s):
                    matched_selected = s
                    break

            if matched_selected is not None:
                # Merge corroborating sources and URLs into the already selected article
                sources = set(matched_selected.extra.get("corroborating_sources", []))
                if matched_selected.source:
                    sources.add(matched_selected.source)
                if candidate.source:
                    sources.add(candidate.source)
                for src in candidate.extra.get("corroborating_sources", []):
                    sources.add(src)
                matched_selected.extra["corroborating_sources"] = sorted(list(sources))

                urls = set(matched_selected.extra.get("corroborating_urls", []))
                if matched_selected.url:
                    urls.add(matched_selected.url)
                if candidate.url:
                    urls.add(candidate.url)
                for u in candidate.extra.get("corroborating_urls", []):
                    urls.add(u)
                matched_selected.extra["corroborating_urls"] = sorted(list(urls))

                matched_selected.extra["cluster_size"] = (
                    matched_selected.extra.get("cluster_size", 1) + candidate.extra.get("cluster_size", 1)
                )
                if len(sources) >= 2:
                    matched_selected.extra["content_verification_status"] = "corroborated"
                # Skip candidate, allowing next candidate to fill the slot
                continue

            # Routine incident diversity damping
            inc_type = get_routine_incident_type(candidate)
            if inc_type is not None:
                already_has_type = any(get_routine_incident_type(s) == inc_type for s in selected)
                if already_has_type:
                    reserve_candidates.append(candidate)
                    continue

            selected.append(candidate)
            if len(selected) >= target_count:
                break

        # Fill remaining slots from reserve candidates if needed to guarantee up to target_count
        if len(selected) < target_count and reserve_candidates:
            for reserve in reserve_candidates:
                if not any(self.deduplicator.is_same_event(reserve, s) for s in selected):
                    selected.append(reserve)
                    if len(selected) >= target_count:
                        break

        return selected
