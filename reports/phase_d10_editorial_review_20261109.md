# Phase D-10 — Editorial Review Extraction & Risk Audit Report

**Repository:** `C:\simon kankan`  
**Target News Date:** `2026-11-09`  
**Review Date (MYT):** `2026-11-09 12:30:00`  
**Source Preview File:** [`reports/news_preview_20261109.json`](file:///C:/simon%20kankan/reports/news_preview_20261109.json)  
**Mode:** STRICTLY READ-ONLY EDITORIAL EXTRACTION  

---

## 1. Operational Verification & Baseline Confirmation

- **Preview File Integrity:** Successfully loaded and parsed `reports/news_preview_20261109.json`.
- **Accepted Articles Count:** Confirmed exactly **18** accepted articles (matches Phase D-9 report).
- **Rejected Articles Count:** Confirmed exactly **6** rejected articles (matches Phase D-9 report).
- **Validation Audit Logs:** Confirmed exactly **24** total audited records.
- **API Requests Sent:** `0` (Zero Gemini API requests emitted; fail-closed).
- **Production Files Status:** `news_data.json` and `index.html` remain 100% untouched.

---

## 2. Complete Extraction of All 18 Accepted Articles

> [!IMPORTANT]
> All texts below preserve 100% of original generated wording without rewriting, polishing, or silent translation correction.

### Article 1: `art_sabah_1` [SABAH]

- **Article ID:** `art_sabah_1`
- **Category:** `sabah` (Geographic Scope: `sandakan`)
- **Chinese Headline:** 沙巴地政运动会山打根开幕 携手提升市容迎接2027旅游年 [Astro Awani + Bernama 双核实]
- **Bahasa Malaysia Headline:** Laporan Berita: 沙巴地政运动会山打根开幕 携手提升市容迎接2027旅游年
- **Original Source Name:** 诗华日报沙巴版
- **Original Source URL:** [https://news.seehua.com/post/1601871](https://news.seehua.com/post/1601871)
- **Original Publication Timestamp:** `2026-11-08T15:05:59+08:00`
- **News Event Date:** Estimated 2026-11-07 to 2026-11-09 (derived from publication context)
- **Fact IDs & Source Evidence:** `None` (Track B deterministic fallback executed with empty Fact ID bindings `[]`)
- **D-7 Validation Verdict:** `is_valid: True`, status: `VERIFIED`, errors: `[]`, warnings: `[]`
- **Missing / Uncertain Information:** Full investigative article body not fetched; source evidence provenance ungrounded; BM title un-translated.

#### Complete Chinese Body (`detail`)
```text
【权威动态播报】沙巴地政运动会山打根开幕 携手提升市容迎接2027旅游年。据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：Astro Awani, Bernama, Bing News Sandakan (EN), Borneo Post, Malay Mail, NST Online, The Edge Malaysia, The Sun Malaysia, 诗华日报沙巴版。
```

#### Complete Bahasa Malaysia Body (`detailBM`)
```text
Notis Berita Rasmi: 沙巴地政运动会山打根开幕 携手提升市容迎接2027旅游年.

Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: Astro Awani, Bernama, Bing News Sandakan (EN), Borneo Post, Malay Mail, NST Online, The Edge Malaysia, The Sun Malaysia, 诗华日报沙巴版.
```

#### Editorial Risk Assessment
- **Headline Grounding:** Headline derived from real RSS title; however, editorial verification badge is synthetic.
- **Event Freshness (New vs Old):** Published 2026-11-08 (within 24-36h sliding window).
- **Publication Date vs Event Date:** Potential conflation. RSS publication timestamp does not clarify the exact hour or day the incident or event took place.
- **Unsupported Claims / Entities:** Body text relies on boiler-plate template (`【权威动态播报】...`). For sports articles, raw HTML snippets from Google News RSS were injected into body text.
- **Cross-Lingual Parity:** **FAIL / HIGH RISK.** BM headline is merely a prefix `Laporan Berita:` attached to the untranslated Chinese headline. BM body is generic boilerplate.
- **Source Retrieval Depth:** **SNIPPET ONLY.** Full web page was not retrieved; only RSS title and metadata were processed.
- **Sabah / Sandakan Relevance:** **HIGH.** Pertains to Sabah state affairs.

---

### Article 2: `art_sabah_2` [SABAH]

- **Article ID:** `art_sabah_2`
- **Category:** `sabah` (Geographic Scope: `sabah`)
- **Chinese Headline:** 兵南邦凌晨夺命车祸 骑士失控冲沟渠当场毙命 [诗华日报沙巴版 实时发布]
- **Bahasa Malaysia Headline:** Laporan Berita: 兵南邦凌晨夺命车祸 骑士失控冲沟渠当场毙命
- **Original Source Name:** 诗华日报沙巴版
- **Original Source URL:** [https://news.seehua.com/post/1602304](https://news.seehua.com/post/1602304)
- **Original Publication Timestamp:** `2026-11-09T11:37:07+08:00`
- **News Event Date:** Estimated 2026-11-07 to 2026-11-09 (derived from publication context)
- **Fact IDs & Source Evidence:** `None` (Track B deterministic fallback executed with empty Fact ID bindings `[]`)
- **D-7 Validation Verdict:** `is_valid: True`, status: `VERIFIED`, errors: `[]`, warnings: `[]`
- **Missing / Uncertain Information:** Full investigative article body not fetched; source evidence provenance ungrounded; BM title un-translated.

#### Complete Chinese Body (`detail`)
```text
【权威动态播报】兵南邦凌晨夺命车祸 骑士失控冲沟渠当场毙命。据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：诗华日报沙巴版。
```

#### Complete Bahasa Malaysia Body (`detailBM`)
```text
Notis Berita Rasmi: 兵南邦凌晨夺命车祸 骑士失控冲沟渠当场毙命.

Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: 诗华日报沙巴版.
```

#### Editorial Risk Assessment
- **Headline Grounding:** Headline derived from real RSS title; however, editorial verification badge is synthetic.
- **Event Freshness (New vs Old):** Fresh event published on target date (2026-11-09).
- **Publication Date vs Event Date:** Potential conflation. RSS publication timestamp does not clarify the exact hour or day the incident or event took place.
- **Unsupported Claims / Entities:** Body text relies on boiler-plate template (`【权威动态播报】...`). For sports articles, raw HTML snippets from Google News RSS were injected into body text.
- **Cross-Lingual Parity:** **FAIL / HIGH RISK.** BM headline is merely a prefix `Laporan Berita:` attached to the untranslated Chinese headline. BM body is generic boilerplate.
- **Source Retrieval Depth:** **SNIPPET ONLY.** Full web page was not retrieved; only RSS title and metadata were processed.
- **Sabah / Sandakan Relevance:** **HIGH.** Pertains to Sabah state affairs.

---

### Article 3: `art_sabah_3` [SABAH]

- **Article ID:** `art_sabah_3`
- **Category:** `sabah` (Geographic Scope: `sabah`)
- **Chinese Headline:** 兵南邦马拉昆花园 一间双层排屋发生火灾 [诗华日报沙巴版 实时发布]
- **Bahasa Malaysia Headline:** Laporan Berita: 兵南邦马拉昆花园 一间双层排屋发生火灾
- **Original Source Name:** 诗华日报沙巴版
- **Original Source URL:** [https://news.seehua.com/post/1602062](https://news.seehua.com/post/1602062)
- **Original Publication Timestamp:** `2026-11-08T20:00:06+08:00`
- **News Event Date:** Estimated 2026-11-07 to 2026-11-09 (derived from publication context)
- **Fact IDs & Source Evidence:** `None` (Track B deterministic fallback executed with empty Fact ID bindings `[]`)
- **D-7 Validation Verdict:** `is_valid: True`, status: `VERIFIED`, errors: `[]`, warnings: `[]`
- **Missing / Uncertain Information:** Full investigative article body not fetched; source evidence provenance ungrounded; BM title un-translated.

#### Complete Chinese Body (`detail`)
```text
【权威动态播报】兵南邦马拉昆花园 一间双层排屋发生火灾。据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：诗华日报沙巴版。
```

#### Complete Bahasa Malaysia Body (`detailBM`)
```text
Notis Berita Rasmi: 兵南邦马拉昆花园 一间双层排屋发生火灾.

Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: 诗华日报沙巴版.
```

#### Editorial Risk Assessment
- **Headline Grounding:** Headline derived from real RSS title; however, editorial verification badge is synthetic.
- **Event Freshness (New vs Old):** Published 2026-11-08 (within 24-36h sliding window).
- **Publication Date vs Event Date:** Potential conflation. RSS publication timestamp does not clarify the exact hour or day the incident or event took place.
- **Unsupported Claims / Entities:** Body text relies on boiler-plate template (`【权威动态播报】...`). For sports articles, raw HTML snippets from Google News RSS were injected into body text.
- **Cross-Lingual Parity:** **FAIL / HIGH RISK.** BM headline is merely a prefix `Laporan Berita:` attached to the untranslated Chinese headline. BM body is generic boilerplate.
- **Source Retrieval Depth:** **SNIPPET ONLY.** Full web page was not retrieved; only RSS title and metadata were processed.
- **Sabah / Sandakan Relevance:** **HIGH.** Pertains to Sabah state affairs.

---

### Article 4: `art_sabah_5` [SABAH]

- **Article ID:** `art_sabah_5`
- **Category:** `sabah` (Geographic Scope: `sabah`)
- **Chinese Headline:** 积压数十年土地申请有望解决 沙巴5000英亩土地展开测量 [诗华日报沙巴版 实时发布]
- **Bahasa Malaysia Headline:** Laporan Berita: 积压数十年土地申请有望解决 沙巴5000英亩土地展开测量
- **Original Source Name:** 诗华日报沙巴版
- **Original Source URL:** [https://news.seehua.com/post/1601832](https://news.seehua.com/post/1601832)
- **Original Publication Timestamp:** `2026-11-08T14:07:43+08:00`
- **News Event Date:** Estimated 2026-11-07 to 2026-11-09 (derived from publication context)
- **Fact IDs & Source Evidence:** `None` (Track B deterministic fallback executed with empty Fact ID bindings `[]`)
- **D-7 Validation Verdict:** `is_valid: True`, status: `VERIFIED`, errors: `[]`, warnings: `[]`
- **Missing / Uncertain Information:** Full investigative article body not fetched; source evidence provenance ungrounded; BM title un-translated.

#### Complete Chinese Body (`detail`)
```text
【权威动态播报】积压数十年土地申请有望解决 沙巴5000英亩土地展开测量。据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：诗华日报沙巴版。
```

#### Complete Bahasa Malaysia Body (`detailBM`)
```text
Notis Berita Rasmi: 积压数十年土地申请有望解决 沙巴5000英亩土地展开测量.

Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: 诗华日报沙巴版.
```

#### Editorial Risk Assessment
- **Headline Grounding:** Headline derived from real RSS title; however, editorial verification badge is synthetic.
- **Event Freshness (New vs Old):** Published 2026-11-08 (within 24-36h sliding window).
- **Publication Date vs Event Date:** Potential conflation. RSS publication timestamp does not clarify the exact hour or day the incident or event took place.
- **Unsupported Claims / Entities:** Body text relies on boiler-plate template (`【权威动态播报】...`). For sports articles, raw HTML snippets from Google News RSS were injected into body text.
- **Cross-Lingual Parity:** **FAIL / HIGH RISK.** BM headline is merely a prefix `Laporan Berita:` attached to the untranslated Chinese headline. BM body is generic boilerplate.
- **Source Retrieval Depth:** **SNIPPET ONLY.** Full web page was not retrieved; only RSS title and metadata were processed.
- **Sabah / Sandakan Relevance:** **HIGH.** Pertains to Sabah state affairs.

---

### Article 5: `art_sabah_6` [SABAH]

- **Article ID:** `art_sabah_6`
- **Category:** `sabah` (Geographic Scope: `sabah`)
- **Chinese Headline:** 指签证漏洞恐成诈骗通道 曾子文促加强沙巴入境监管 [诗华日报沙巴版 实时发布]
- **Bahasa Malaysia Headline:** Laporan Berita: 指签证漏洞恐成诈骗通道 曾子文促加强沙巴入境监管
- **Original Source Name:** 诗华日报沙巴版
- **Original Source URL:** [https://news.seehua.com/post/1601746](https://news.seehua.com/post/1601746)
- **Original Publication Timestamp:** `2026-11-08T11:53:51+08:00`
- **News Event Date:** Estimated 2026-11-07 to 2026-11-09 (derived from publication context)
- **Fact IDs & Source Evidence:** `None` (Track B deterministic fallback executed with empty Fact ID bindings `[]`)
- **D-7 Validation Verdict:** `is_valid: True`, status: `VERIFIED`, errors: `[]`, warnings: `[]`
- **Missing / Uncertain Information:** Full investigative article body not fetched; source evidence provenance ungrounded; BM title un-translated.

#### Complete Chinese Body (`detail`)
```text
【权威动态播报】指签证漏洞恐成诈骗通道 曾子文促加强沙巴入境监管。据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：诗华日报沙巴版。
```

#### Complete Bahasa Malaysia Body (`detailBM`)
```text
Notis Berita Rasmi: 指签证漏洞恐成诈骗通道 曾子文促加强沙巴入境监管.

Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: 诗华日报沙巴版.
```

#### Editorial Risk Assessment
- **Headline Grounding:** Headline derived from real RSS title; however, editorial verification badge is synthetic.
- **Event Freshness (New vs Old):** Published 2026-11-08 (within 24-36h sliding window).
- **Publication Date vs Event Date:** Potential conflation. RSS publication timestamp does not clarify the exact hour or day the incident or event took place.
- **Unsupported Claims / Entities:** Body text relies on boiler-plate template (`【权威动态播报】...`). For sports articles, raw HTML snippets from Google News RSS were injected into body text.
- **Cross-Lingual Parity:** **FAIL / HIGH RISK.** BM headline is merely a prefix `Laporan Berita:` attached to the untranslated Chinese headline. BM body is generic boilerplate.
- **Source Retrieval Depth:** **SNIPPET ONLY.** Full web page was not retrieved; only RSS title and metadata were processed.
- **Sabah / Sandakan Relevance:** **HIGH.** Pertains to Sabah state affairs.

---

### Article 6: `art_sabah_8` [SABAH]

- **Article ID:** `art_sabah_8`
- **Category:** `sabah` (Geographic Scope: `sabah`)
- **Chinese Headline:** 摩托失控坠入石沟 41岁骑士丧命 [沙巴星洲日报 实时发布]
- **Bahasa Malaysia Headline:** Laporan Berita: 摩托失控坠入石沟 41岁骑士丧命
- **Original Source Name:** 沙巴星洲日报
- **Original Source URL:** [https://sabah.sinchew.com.my/news/20261109/sabah/8050285](https://sabah.sinchew.com.my/news/20261109/sabah/8050285)
- **Original Publication Timestamp:** `2026-11-09T07:00:00+08:00`
- **News Event Date:** Estimated 2026-11-07 to 2026-11-09 (derived from publication context)
- **Fact IDs & Source Evidence:** `None` (Track B deterministic fallback executed with empty Fact ID bindings `[]`)
- **D-7 Validation Verdict:** `is_valid: True`, status: `VERIFIED`, errors: `[]`, warnings: `[]`
- **Missing / Uncertain Information:** Full investigative article body not fetched; source evidence provenance ungrounded; BM title un-translated.

#### Complete Chinese Body (`detail`)
```text
【权威动态播报】摩托失控坠入石沟 41岁骑士丧命。据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：沙巴星洲日报。
```

#### Complete Bahasa Malaysia Body (`detailBM`)
```text
Notis Berita Rasmi: 摩托失控坠入石沟 41岁骑士丧命.

Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: 沙巴星洲日报.
```

#### Editorial Risk Assessment
- **Headline Grounding:** Headline derived from real RSS title; however, editorial verification badge is synthetic.
- **Event Freshness (New vs Old):** Fresh event published on target date (2026-11-09).
- **Publication Date vs Event Date:** Potential conflation. RSS publication timestamp does not clarify the exact hour or day the incident or event took place.
- **Unsupported Claims / Entities:** Body text relies on boiler-plate template (`【权威动态播报】...`). For sports articles, raw HTML snippets from Google News RSS were injected into body text.
- **Cross-Lingual Parity:** **FAIL / HIGH RISK.** BM headline is merely a prefix `Laporan Berita:` attached to the untranslated Chinese headline. BM body is generic boilerplate.
- **Source Retrieval Depth:** **SNIPPET ONLY.** Full web page was not retrieved; only RSS title and metadata were processed.
- **Sabah / Sandakan Relevance:** **HIGH.** Pertains to Sabah state affairs.

---

### Article 7: `art_national_13` [NATIONAL]

- **Article ID:** `art_national_13`
- **Category:** `national` (Geographic Scope: `national`)
- **Chinese Headline:** 印裔虽少热度不减！沙各族齐聚兴都庙共庆屠妖节 [诗华日报 实时发布]
- **Bahasa Malaysia Headline:** Laporan Berita: 印裔虽少热度不减！沙各族齐聚兴都庙共庆屠妖节
- **Original Source Name:** 诗华日报
- **Original Source URL:** [https://news.seehua.com/post/1601742](https://news.seehua.com/post/1601742)
- **Original Publication Timestamp:** `2026-11-08T13:03:58+08:00`
- **News Event Date:** Estimated 2026-11-07 to 2026-11-09 (derived from publication context)
- **Fact IDs & Source Evidence:** `None` (Track B deterministic fallback executed with empty Fact ID bindings `[]`)
- **D-7 Validation Verdict:** `is_valid: True`, status: `VERIFIED`, errors: `[]`, warnings: `[]`
- **Missing / Uncertain Information:** Full investigative article body not fetched; source evidence provenance ungrounded; BM title un-translated.

#### Complete Chinese Body (`detail`)
```text
【权威动态播报】印裔虽少热度不减！沙各族齐聚兴都庙共庆屠妖节。据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：诗华日报。
```

#### Complete Bahasa Malaysia Body (`detailBM`)
```text
Notis Berita Rasmi: 印裔虽少热度不减！沙各族齐聚兴都庙共庆屠妖节.

Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: 诗华日报.
```

#### Editorial Risk Assessment
- **Headline Grounding:** Headline derived from real RSS title; however, editorial verification badge is synthetic.
- **Event Freshness (New vs Old):** Published 2026-11-08 (within 24-36h sliding window).
- **Publication Date vs Event Date:** Potential conflation. RSS publication timestamp does not clarify the exact hour or day the incident or event took place.
- **Unsupported Claims / Entities:** Body text relies on boiler-plate template (`【权威动态播报】...`). For sports articles, raw HTML snippets from Google News RSS were injected into body text.
- **Cross-Lingual Parity:** **FAIL / HIGH RISK.** BM headline is merely a prefix `Laporan Berita:` attached to the untranslated Chinese headline. BM body is generic boilerplate.
- **Source Retrieval Depth:** **SNIPPET ONLY.** Full web page was not retrieved; only RSS title and metadata were processed.
- **Sabah / Sandakan Relevance:** **MODERATE TO LOW.** National news,บาง条目 actually from Sarawak (Kanowit, Simanggang).

---

### Article 8: `art_national_14` [NATIONAL]

- **Article ID:** `art_national_14`
- **Category:** `national` (Geographic Scope: `national`)
- **Chinese Headline:** 电单车遭四驱车撞击 45岁后座乘客送院两天不治 [诗华日报 实时发布]
- **Bahasa Malaysia Headline:** Laporan Berita: 电单车遭四驱车撞击 45岁后座乘客送院两天不治
- **Original Source Name:** 诗华日报
- **Original Source URL:** [https://news.seehua.com/post/1601743](https://news.seehua.com/post/1601743)
- **Original Publication Timestamp:** `2026-11-08T11:50:06+08:00`
- **News Event Date:** Estimated 2026-11-07 to 2026-11-09 (derived from publication context)
- **Fact IDs & Source Evidence:** `None` (Track B deterministic fallback executed with empty Fact ID bindings `[]`)
- **D-7 Validation Verdict:** `is_valid: True`, status: `VERIFIED`, errors: `[]`, warnings: `[]`
- **Missing / Uncertain Information:** Full investigative article body not fetched; source evidence provenance ungrounded; BM title un-translated.

#### Complete Chinese Body (`detail`)
```text
【权威动态播报】电单车遭四驱车撞击 45岁后座乘客送院两天不治。据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：诗华日报。
```

#### Complete Bahasa Malaysia Body (`detailBM`)
```text
Notis Berita Rasmi: 电单车遭四驱车撞击 45岁后座乘客送院两天不治.

Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: 诗华日报.
```

#### Editorial Risk Assessment
- **Headline Grounding:** Headline derived from real RSS title; however, editorial verification badge is synthetic.
- **Event Freshness (New vs Old):** Published 2026-11-08 (within 24-36h sliding window).
- **Publication Date vs Event Date:** Potential conflation. RSS publication timestamp does not clarify the exact hour or day the incident or event took place.
- **Unsupported Claims / Entities:** Body text relies on boiler-plate template (`【权威动态播报】...`). For sports articles, raw HTML snippets from Google News RSS were injected into body text.
- **Cross-Lingual Parity:** **FAIL / HIGH RISK.** BM headline is merely a prefix `Laporan Berita:` attached to the untranslated Chinese headline. BM body is generic boilerplate.
- **Source Retrieval Depth:** **SNIPPET ONLY.** Full web page was not retrieved; only RSS title and metadata were processed.
- **Sabah / Sandakan Relevance:** **MODERATE TO LOW.** National news,บาง条目 actually from Sarawak (Kanowit, Simanggang).

---

### Article 9: `art_national_15` [NATIONAL]

- **Article ID:** `art_national_15`
- **Category:** `national` (Geographic Scope: `sarawak`)
- **Chinese Headline:** 加拿逸24户长屋凌晨失火 约80%被烧毁 [诗华日报 (砂拉越版) 实时发布]
- **Bahasa Malaysia Headline:** Laporan Berita: 加拿逸24户长屋凌晨失火 约80%被烧毁
- **Original Source Name:** 诗华日报 (砂拉越版)
- **Original Source URL:** [https://news.seehua.com/post/1602284](https://news.seehua.com/post/1602284)
- **Original Publication Timestamp:** `2026-11-09T10:52:33+08:00`
- **News Event Date:** Estimated 2026-11-07 to 2026-11-09 (derived from publication context)
- **Fact IDs & Source Evidence:** `None` (Track B deterministic fallback executed with empty Fact ID bindings `[]`)
- **D-7 Validation Verdict:** `is_valid: True`, status: `VERIFIED`, errors: `[]`, warnings: `[]`
- **Missing / Uncertain Information:** Full investigative article body not fetched; source evidence provenance ungrounded; BM title un-translated.

#### Complete Chinese Body (`detail`)
```text
【权威动态播报】加拿逸24户长屋凌晨失火 约80%被烧毁。据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：诗华日报 (砂拉越版)。
```

#### Complete Bahasa Malaysia Body (`detailBM`)
```text
Notis Berita Rasmi: 加拿逸24户长屋凌晨失火 约80%被烧毁.

Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: 诗华日报 (砂拉越版).
```

#### Editorial Risk Assessment
- **Headline Grounding:** Headline derived from real RSS title; however, editorial verification badge is synthetic.
- **Event Freshness (New vs Old):** Fresh event published on target date (2026-11-09).
- **Publication Date vs Event Date:** Potential conflation. RSS publication timestamp does not clarify the exact hour or day the incident or event took place.
- **Unsupported Claims / Entities:** Body text relies on boiler-plate template (`【权威动态播报】...`). For sports articles, raw HTML snippets from Google News RSS were injected into body text.
- **Cross-Lingual Parity:** **FAIL / HIGH RISK.** BM headline is merely a prefix `Laporan Berita:` attached to the untranslated Chinese headline. BM body is generic boilerplate.
- **Source Retrieval Depth:** **SNIPPET ONLY.** Full web page was not retrieved; only RSS title and metadata were processed.
- **Sabah / Sandakan Relevance:** **MODERATE TO LOW.** National news,บาง条目 actually from Sarawak (Kanowit, Simanggang).

---

### Article 10: `art_national_16` [NATIONAL]

- **Article ID:** `art_national_16`
- **Category:** `national` (Geographic Scope: `national`)
- **Chinese Headline:** 连达立：打造泛道休息站 实曼归公园料宪报公布 [诗华日报 实时发布]
- **Bahasa Malaysia Headline:** Laporan Berita: 连达立：打造泛道休息站 实曼归公园料宪报公布
- **Original Source Name:** 诗华日报
- **Original Source URL:** [https://news.seehua.com/post/1602130](https://news.seehua.com/post/1602130)
- **Original Publication Timestamp:** `2026-11-08T22:31:31+08:00`
- **News Event Date:** Estimated 2026-11-07 to 2026-11-09 (derived from publication context)
- **Fact IDs & Source Evidence:** `None` (Track B deterministic fallback executed with empty Fact ID bindings `[]`)
- **D-7 Validation Verdict:** `is_valid: True`, status: `VERIFIED`, errors: `[]`, warnings: `[]`
- **Missing / Uncertain Information:** Full investigative article body not fetched; source evidence provenance ungrounded; BM title un-translated.

#### Complete Chinese Body (`detail`)
```text
【权威动态播报】连达立：打造泛道休息站 实曼归公园料宪报公布。据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：诗华日报。
```

#### Complete Bahasa Malaysia Body (`detailBM`)
```text
Notis Berita Rasmi: 连达立：打造泛道休息站 实曼归公园料宪报公布.

Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: 诗华日报.
```

#### Editorial Risk Assessment
- **Headline Grounding:** Headline derived from real RSS title; however, editorial verification badge is synthetic.
- **Event Freshness (New vs Old):** Published 2026-11-08 (within 24-36h sliding window).
- **Publication Date vs Event Date:** Potential conflation. RSS publication timestamp does not clarify the exact hour or day the incident or event took place.
- **Unsupported Claims / Entities:** Body text relies on boiler-plate template (`【权威动态播报】...`). For sports articles, raw HTML snippets from Google News RSS were injected into body text.
- **Cross-Lingual Parity:** **FAIL / HIGH RISK.** BM headline is merely a prefix `Laporan Berita:` attached to the untranslated Chinese headline. BM body is generic boilerplate.
- **Source Retrieval Depth:** **SNIPPET ONLY.** Full web page was not retrieved; only RSS title and metadata were processed.
- **Sabah / Sandakan Relevance:** **MODERATE TO LOW.** National news,บาง条目 actually from Sarawak (Kanowit, Simanggang).

---

### Article 11: `art_sports_17` [SPORTS]

- **Article ID:** `art_sports_17`
- **Category:** `sports` (Geographic Scope: `national`)
- **Chinese Headline:** Football: Mukhairi's own goal costs Selangor dearly as Kuching City set up FA Cup final with JDT [Borneo Post + The Star 双核实]
- **Bahasa Malaysia Headline:** Laporan Berita: Football: Mukhairi's own goal costs Selangor dearly as Kuching City set up FA Cup final with JDT
- **Original Source Name:** The Star
- **Original Source URL:** [https://news.google.com/rss/articles/CBMi2AFBVV95cUxQZDBZNVRVQ1hvYjZQRFp1OGZqcFFlZXR2UWZOUUQxVVR4Ujg1VERJcmxwMEU2bWtwN0N4UklBNjhicWw4V05ISEpxbXFuVFdMTUdCNnl3YWRuazBSVTY4NjN4bDRRdTFhTFdwOW5YYW5ZQkJ1OGNmeEtyb25RdTRlanZsYTdnc2R2Y09Ra1lTR1YyWEJkZG1Tdm8teDZpeHFqQk84ZG92cExYYVlPdzRBX3ZuckpOUHkzeEVhMWk1ajJtNHdIZmJtcUpPNlBJUnJpZEV6Nmw4UFY?oc=5](https://news.google.com/rss/articles/CBMi2AFBVV95cUxQZDBZNVRVQ1hvYjZQRFp1OGZqcFFlZXR2UWZOUUQxVVR4Ujg1VERJcmxwMEU2bWtwN0N4UklBNjhicWw4V05ISEpxbXFuVFdMTUdCNnl3YWRuazBSVTY4NjN4bDRRdTFhTFdwOW5YYW5ZQkJ1OGNmeEtyb25RdTRlanZsYTdnc2R2Y09Ra1lTR1YyWEJkZG1Tdm8teDZpeHFqQk84ZG92cExYYVlPdzRBX3ZuckpOUHkzeEVhMWk1ajJtNHdIZmJtcUpPNlBJUnJpZEV6Nmw4UFY?oc=5)
- **Original Publication Timestamp:** `2026-11-08T15:19:00+00:00`
- **News Event Date:** Estimated 2026-11-07 to 2026-11-09 (derived from publication context)
- **Fact IDs & Source Evidence:** `None` (Track B deterministic fallback executed with empty Fact ID bindings `[]`)
- **D-7 Validation Verdict:** `is_valid: True`, status: `VERIFIED`, errors: `[]`, warnings: `[]`
- **Missing / Uncertain Information:** Full investigative article body not fetched; source evidence provenance ungrounded; BM title un-translated.

#### Complete Chinese Body (`detail`)
```text
【权威动态播报】<ol><li><a href="https://news.google.com/rss/articles/CBMi2AFBVV95cUxQZDBZNVRVQ1hvYjZQRFp1OGZqcFFlZXR2UWZOUUQxVVR4Ujg1VERJcmxwMEU2bWtwN0N4UklBNjhicWw4V05ISEpxbXFuVFdMTUdCNnl3YWRuazBSVTY4NjN4bDRRdTFhTFdwOW5YYW5ZQkJ1OGNmeEtyb25RdTRlanZsYTdnc2R2Y09Ra1lTR1YyWEJkZG1Tdm8teDZpeHFqQk84ZG92cExYYVlPdzRBX3ZuckpOUHkzeEVhMWk1ajJtNHdIZmJtcUpPNlBJUnJpZEV6Nmw4UFY?oc=5" target="_blank">Football: Mukhairi's own goal costs Selangor dearly as Kuching City set up FA Cup final with JDT</a>&nbsp;&nbsp;<font color="#6f6f6f">The Star</font></li><li><a href="https://news.google.com/rss/articles/CBMiggFBVV95cUxPUm5hTVR6d3BVZDBrRXhTZmFSM2lCMDZDai05RnI0TzNJOENuc3NoSnpUcnBYWUdRMU50ZmZFZjZ3dXZEWFBwTUdHMWotdlptVDBCcTRKcUlVcXRUUzVLTndrTS02VDIyNE1lbXNCbEhULUdTRmZqUWcxallvU3FMdlhn?oc=5" target="_blank">Kuching City Claw Back To Reach FA Cup Final</a>&nbsp;&nbsp;<font color="#6f6f6f">Sarawak Tribune</font></li><li><a href="https://news.google.com/rss/articles/CBMirgFBVV95cUxNcEk5R2VXREJyN2FrRGpFak52ZVpvc2MyZ29zeHpRNXFJbnRHdzRIU1VZNklOemRsVlRNSk9BaDFnSHp2QlZyQUdrdGg0Rkh2TUNDTDFmaEtLTjhCVDlweVE4SWdqckJGRlNfMkd1TTUtRndBeVcyM3poMXlzUU1sQWxMR21QQ3ozck16ZHhLSm9SZTF0aVpodTFCNWJEd1RFNk5KWm00RlpadFM3b3fSAbMBQVVfeXFMT21EczFFdW1YSktTMi10TTVPY2lfT2RHTlJLTHRoNGVuc1JZOEo3YzRhQ3l6bVF2S1MzOGpYR0RtN2NlTGFfR1luMDZkRWhYbWUzanBwUV9INDBLZGltOHctMm9wTjZINWZadUJNNHNDQW13VjROZWFUZ2ViNGJaaFNRWDUyeGVZZVhCaEc3WXEyNEZqbzl6a2tZbFZsbExUUzFVSmQ1d2ZqSU53RDBHb1NBME0?oc=5" target="_blank">Selangor crash out of FA Cup semi-finals amid ugly scenes</a>&nbsp;&nbsp;<font color="#6f6f6f">NST Online</font></li><li><a href="https://news.google.com/rss/articles/CBMi1AFBVV95cUxNcVVqRzBxMzJPRktaUzBnWFpjbld3VGpyT2prZF85UWxIQ0t0d1RJZ0o1NUZ3dldlTDBqT0VEb2hnUldfZDc2VkFZMUQ0aFlMMEM5MnRvckVqYzlWczNZcFdqTk9PYmg4VlRwU0pvUE1VcW9HQktLLXVLUGswbi0zU1VybmtneVNvX3hHODh3WU1GNWhCRWY3UDdqbUxQNzJOUGxNZjRybnlyNHkzeUFFM2dCbnBDTF8zOXZsQThNSkR4M09lSlRpTzhIVEE5N2s1ZnhmMQ?oc=5" target="_blank">Football: Pan-gon insists his side have the strength and depth to overcome disciplinary setbacks</a>&nbsp;&nbsp;<font color="#6f6f6f">The Star</font></li><li><a href="https://news.google.com/rss/articles/CBMivAFBVV95cUxQMWx4WWxiWC05UTQtVUhsWmVENWVQUm1nb1hYZ0hGZVNJNzA4N25zWHdXdFdkUTNpeDNuUnY3cXpyaExSb2RiQlJWR2ZnZDkxc3Z6MmZ1cksyYUdROTItNUZmc0RJblVyN2FEcmUxV3BDWDQwdzRzQm9paFdKU0h0QWRWSVJRYWlPOXg0aFJ1SGpJaUZ6SmRUQmlNeHpYMlh5a3g5MGVWYVR4UllyejBtRFdCeDRiNmFGWjEwTA?oc=5" target="_blank">Aidil hails collective effort behind Kuching City’s historic FA Cup final berth</a>&nbsp;&nbsp;<font color="#6f6f6f">Borneo Post</font></li></ol>。据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：Borneo Post, The Star。
```

#### Complete Bahasa Malaysia Body (`detailBM`)
```text
Notis Berita Rasmi: <ol><li><a href="https://news.google.com/rss/articles/CBMi2AFBVV95cUxQZDBZNVRVQ1hvYjZQRFp1OGZqcFFlZXR2UWZOUUQxVVR4Ujg1VERJcmxwMEU2bWtwN0N4UklBNjhicWw4V05ISEpxbXFuVFdMTUdCNnl3YWRuazBSVTY4NjN4bDRRdTFhTFdwOW5YYW5ZQkJ1OGNmeEtyb25RdTRlanZsYTdnc2R2Y09Ra1lTR1YyWEJkZG1Tdm8teDZpeHFqQk84ZG92cExYYVlPdzRBX3ZuckpOUHkzeEVhMWk1ajJtNHdIZmJtcUpPNlBJUnJpZEV6Nmw4UFY?oc=5" target="_blank">Football: Mukhairi's own goal costs Selangor dearly as Kuching City set up FA Cup final with JDT</a>&nbsp;&nbsp;<font color="#6f6f6f">The Star</font></li><li><a href="https://news.google.com/rss/articles/CBMiggFBVV95cUxPUm5hTVR6d3BVZDBrRXhTZmFSM2lCMDZDai05RnI0TzNJOENuc3NoSnpUcnBYWUdRMU50ZmZFZjZ3dXZEWFBwTUdHMWotdlptVDBCcTRKcUlVcXRUUzVLTndrTS02VDIyNE1lbXNCbEhULUdTRmZqUWcxallvU3FMdlhn?oc=5" target="_blank">Kuching City Claw Back To Reach FA Cup Final</a>&nbsp;&nbsp;<font color="#6f6f6f">Sarawak Tribune</font></li><li><a href="https://news.google.com/rss/articles/CBMirgFBVV95cUxNcEk5R2VXREJyN2FrRGpFak52ZVpvc2MyZ29zeHpRNXFJbnRHdzRIU1VZNklOemRsVlRNSk9BaDFnSHp2QlZyQUdrdGg0Rkh2TUNDTDFmaEtLTjhCVDlweVE4SWdqckJGRlNfMkd1TTUtRndBeVcyM3poMXlzUU1sQWxMR21QQ3ozck16ZHhLSm9SZTF0aVpodTFCNWJEd1RFNk5KWm00RlpadFM3b3fSAbMBQVVfeXFMT21EczFFdW1YSktTMi10TTVPY2lfT2RHTlJLTHRoNGVuc1JZOEo3YzRhQ3l6bVF2S1MzOGpYR0RtN2NlTGFfR1luMDZkRWhYbWUzanBwUV9INDBLZGltOHctMm9wTjZINWZadUJNNHNDQW13VjROZWFUZ2ViNGJaaFNRWDUyeGVZZVhCaEc3WXEyNEZqbzl6a2tZbFZsbExUUzFVSmQ1d2ZqSU53RDBHb1NBME0?oc=5" target="_blank">Selangor crash out of FA Cup semi-finals amid ugly scenes</a>&nbsp;&nbsp;<font color="#6f6f6f">NST Online</font></li><li><a href="https://news.google.com/rss/articles/CBMi1AFBVV95cUxNcVVqRzBxMzJPRktaUzBnWFpjbld3VGpyT2prZF85UWxIQ0t0d1RJZ0o1NUZ3dldlTDBqT0VEb2hnUldfZDc2VkFZMUQ0aFlMMEM5MnRvckVqYzlWczNZcFdqTk9PYmg4VlRwU0pvUE1VcW9HQktLLXVLUGswbi0zU1VybmtneVNvX3hHODh3WU1GNWhCRWY3UDdqbUxQNzJOUGxNZjRybnlyNHkzeUFFM2dCbnBDTF8zOXZsQThNSkR4M09lSlRpTzhIVEE5N2s1ZnhmMQ?oc=5" target="_blank">Football: Pan-gon insists his side have the strength and depth to overcome disciplinary setbacks</a>&nbsp;&nbsp;<font color="#6f6f6f">The Star</font></li><li><a href="https://news.google.com/rss/articles/CBMivAFBVV95cUxQMWx4WWxiWC05UTQtVUhsWmVENWVQUm1nb1hYZ0hGZVNJNzA4N25zWHdXdFdkUTNpeDNuUnY3cXpyaExSb2RiQlJWR2ZnZDkxc3Z6MmZ1cksyYUdROTItNUZmc0RJblVyN2FEcmUxV3BDWDQwdzRzQm9paFdKU0h0QWRWSVJRYWlPOXg0aFJ1SGpJaUZ6SmRUQmlNeHpYMlh5a3g5MGVWYVR4UllyejBtRFdCeDRiNmFGWjEwTA?oc=5" target="_blank">Aidil hails collective effort behind Kuching City’s historic FA Cup final berth</a>&nbsp;&nbsp;<font color="#6f6f6f">Borneo Post</font></li></ol>.

Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: Borneo Post, The Star.
```

#### Editorial Risk Assessment
- **Headline Grounding:** Headline derived from real RSS title; however, editorial verification badge is synthetic.
- **Event Freshness (New vs Old):** Published 2026-11-08 (within 24-36h sliding window).
- **Publication Date vs Event Date:** Potential conflation. RSS publication timestamp does not clarify the exact hour or day the incident or event took place.
- **Unsupported Claims / Entities:** Body text relies on boiler-plate template (`【权威动态播报】...`). For sports articles, raw HTML snippets from Google News RSS were injected into body text.
- **Cross-Lingual Parity:** **FAIL / HIGH RISK.** BM headline is merely a prefix `Laporan Berita:` attached to the untranslated Chinese headline. BM body is generic boilerplate.
- **Source Retrieval Depth:** **SNIPPET ONLY.** Full web page was not retrieved; only RSS title and metadata were processed.
- **Sabah / Sandakan Relevance:** **LOW / IRRELEVANT.** Sports or international/celebrity general news.

---

### Article 12: `art_sports_18` [SPORTS]

- **Article ID:** `art_sports_18`
- **Category:** `sports` (Geographic Scope: `national`)
- **Chinese Headline:** Man Utd rescue Villa draw with incredible fightback, Chelsea stunned [Free Malaysia Today 实时发布]
- **Bahasa Malaysia Headline:** Laporan Berita: Man Utd rescue Villa draw with incredible fightback, Chelsea stunned
- **Original Source Name:** Free Malaysia Today
- **Original Source URL:** [https://news.google.com/rss/articles/CBMiywFBVV95cUxQRHVaUFRwRGRVRGJtN2xDME5rUUdoaUxiajY5QVR2dTducEJ2ZDFxSEVJZURRQkJqUkpoTkVsRXhGTlRKaFVlNGY3UVNKYmFSaFVMb2VUWmpHSXljMmxEMkdDWnlpZE5RZXQ1TUtpRnRqOG9zYjBScXZwODZCR3BuY3pkdXdNNTBlaUl2RHZzZlVrSzhPbFh6MDBsTjhjNkQyZmtXRkJNUzlLQTdYWDctbHVWYlZXaU1aNTVqaGtfcXdNbG91TmFFR2N1Yw?oc=5](https://news.google.com/rss/articles/CBMiywFBVV95cUxQRHVaUFRwRGRVRGJtN2xDME5rUUdoaUxiajY5QVR2dTducEJ2ZDFxSEVJZURRQkJqUkpoTkVsRXhGTlRKaFVlNGY3UVNKYmFSaFVMb2VUWmpHSXljMmxEMkdDWnlpZE5RZXQ1TUtpRnRqOG9zYjBScXZwODZCR3BuY3pkdXdNNTBlaUl2RHZzZlVrSzhPbFh6MDBsTjhjNkQyZmtXRkJNUzlLQTdYWDctbHVWYlZXaU1aNTVqaGtfcXdNbG91TmFFR2N1Yw?oc=5)
- **Original Publication Timestamp:** `2026-11-08T21:06:35+00:00`
- **News Event Date:** Estimated 2026-11-07 to 2026-11-09 (derived from publication context)
- **Fact IDs & Source Evidence:** `None` (Track B deterministic fallback executed with empty Fact ID bindings `[]`)
- **D-7 Validation Verdict:** `is_valid: True`, status: `VERIFIED`, errors: `[]`, warnings: `[]`
- **Missing / Uncertain Information:** Full investigative article body not fetched; source evidence provenance ungrounded; BM title un-translated.

#### Complete Chinese Body (`detail`)
```text
【权威动态播报】<ol><li><a href="https://news.google.com/rss/articles/CBMiywFBVV95cUxQRHVaUFRwRGRVRGJtN2xDME5rUUdoaUxiajY5QVR2dTducEJ2ZDFxSEVJZURRQkJqUkpoTkVsRXhGTlRKaFVlNGY3UVNKYmFSaFVMb2VUWmpHSXljMmxEMkdDWnlpZE5RZXQ1TUtpRnRqOG9zYjBScXZwODZCR3BuY3pkdXdNNTBlaUl2RHZzZlVrSzhPbFh6MDBsTjhjNkQyZmtXRkJNUzlLQTdYWDctbHVWYlZXaU1aNTVqaGtfcXdNbG91TmFFR2N1Yw?oc=5" target="_blank">Man Utd rescue Villa draw with incredible fightback, Chelsea stunned</a>&nbsp;&nbsp;<font color="#6f6f6f">Free Malaysia Today</font></li><li><a href="https://news.google.com/rss/articles/CBMib0FVX3lxTE1vS1VTTEM4UFFZVnp5bjVuRExhdVJTQnlhb1hhcTcyNkY2N2x0NU15a1FNdHY5UmFqSGFPb1pfVG14SHpqc2VJMWFzT0MyeGRxVGdTaTJlVWxROFNCdHc2dnppVUI2WEEwcF9CemVyVQ?oc=5" target="_blank">Manchester United</a>&nbsp;&nbsp;<font color="#6f6f6f">BBC</font></li><li><a href="https://news.google.com/rss/articles/CBMigAJBVV95cUxPTHVUeEVLanJaUGhxV1FTRTh2dFlWSkx3RzdOUDN6Y2gtTzhvb09FUmFWYVhsSEdKV0JYa2hOQVBtRHJSWkp2c2VVMXkzYXdWbUh6Zjh1UzdmVkJpOEZnVzc0YmhQTHlFNWQ2YVdOOVN6NFVHa1dFaDFrbHVWdnZQb3FYc040OThDeUJEWmlDdHNIZldfcE5GTkQ0WHlveEU5NnhEMXNpN2RVOE5wQVZyVHhPZlkyX2lQSVU3am9hUTVIOE9Kd2NfUzE4aDJUV0dTSXJqUEZwbkNDZGJvUXA3UXlkUTlQRGEzX3RvSE5KVnh5QVV0Rl81OG5JeUZKX0RV?oc=5" target="_blank">Man Utd 4-4 Aston Villa: Patrick Dorgu levels in the 96th minute as United come from two down TWICE to earn incredible draw</a>&nbsp;&nbsp;<font color="#6f6f6f">Sky Sports</font></li><li><a href="https://news.google.com/rss/articles/CBMiqgFBVV95cUxQMC1DeXdWWVFMaUh4SDk4ZlpNVkdwRjJFSDdGOWxkNU5XTVpXRkhNQlpUZV91cXJGZFpZckRpTS1qYzlEcmNCMjVINy11WlVLRG42NlBrdThra3dnOGxzX1hWelNZV3FQTmtaMGt6R24wakFVNGltLU45aG9tdnk3YXhEYjNfZE93VFh6SUozSlhBd1pXVjdCRkUwdmwwT0lDTlZIQUtLWFB3Zw?oc=5" target="_blank">Dorgu rescues point for Manchester United in eight-goal thriller against Aston Villa</a>&nbsp;&nbsp;<font color="#6f6f6f">The Guardian</font></li><li><a href="https://news.google.com/rss/articles/CBMiqgFBVV95cUxNQzZqLXd3WkZWbnFFekVjak4xTGxEZlpFTzFhR0gxdFA0Nm1FaWwyZWxRTUU0SkxudEdJeWpGRHFuRHFWS2NNMHNWX3JkU2dYTHJxekoyU0dVZWhkZ1JoQ2JKaVFnSFlaV0xpRWx2TS1TcElRaFBOTExPMlR2TF9xNUNKV0NEaU1pWnJoVUdxejEwQjYwa0RpR1ZLLXJKOXRFWUZWVkRrT3g4dw?oc=5" target="_blank">Comedy of errors prompts Emery to leave early – all eight goals ranked by stupidity</a>&nbsp;&nbsp;<font color="#6f6f6f">The Telegraph</font></li></ol>。据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：Free Malaysia Today。
```

#### Complete Bahasa Malaysia Body (`detailBM`)
```text
Notis Berita Rasmi: <ol><li><a href="https://news.google.com/rss/articles/CBMiywFBVV95cUxQRHVaUFRwRGRVRGJtN2xDME5rUUdoaUxiajY5QVR2dTducEJ2ZDFxSEVJZURRQkJqUkpoTkVsRXhGTlRKaFVlNGY3UVNKYmFSaFVMb2VUWmpHSXljMmxEMkdDWnlpZE5RZXQ1TUtpRnRqOG9zYjBScXZwODZCR3BuY3pkdXdNNTBlaUl2RHZzZlVrSzhPbFh6MDBsTjhjNkQyZmtXRkJNUzlLQTdYWDctbHVWYlZXaU1aNTVqaGtfcXdNbG91TmFFR2N1Yw?oc=5" target="_blank">Man Utd rescue Villa draw with incredible fightback, Chelsea stunned</a>&nbsp;&nbsp;<font color="#6f6f6f">Free Malaysia Today</font></li><li><a href="https://news.google.com/rss/articles/CBMib0FVX3lxTE1vS1VTTEM4UFFZVnp5bjVuRExhdVJTQnlhb1hhcTcyNkY2N2x0NU15a1FNdHY5UmFqSGFPb1pfVG14SHpqc2VJMWFzT0MyeGRxVGdTaTJlVWxROFNCdHc2dnppVUI2WEEwcF9CemVyVQ?oc=5" target="_blank">Manchester United</a>&nbsp;&nbsp;<font color="#6f6f6f">BBC</font></li><li><a href="https://news.google.com/rss/articles/CBMigAJBVV95cUxPTHVUeEVLanJaUGhxV1FTRTh2dFlWSkx3RzdOUDN6Y2gtTzhvb09FUmFWYVhsSEdKV0JYa2hOQVBtRHJSWkp2c2VVMXkzYXdWbUh6Zjh1UzdmVkJpOEZnVzc0YmhQTHlFNWQ2YVdOOVN6NFVHa1dFaDFrbHVWdnZQb3FYc040OThDeUJEWmlDdHNIZldfcE5GTkQ0WHlveEU5NnhEMXNpN2RVOE5wQVZyVHhPZlkyX2lQSVU3am9hUTVIOE9Kd2NfUzE4aDJUV0dTSXJqUEZwbkNDZGJvUXA3UXlkUTlQRGEzX3RvSE5KVnh5QVV0Rl81OG5JeUZKX0RV?oc=5" target="_blank">Man Utd 4-4 Aston Villa: Patrick Dorgu levels in the 96th minute as United come from two down TWICE to earn incredible draw</a>&nbsp;&nbsp;<font color="#6f6f6f">Sky Sports</font></li><li><a href="https://news.google.com/rss/articles/CBMiqgFBVV95cUxQMC1DeXdWWVFMaUh4SDk4ZlpNVkdwRjJFSDdGOWxkNU5XTVpXRkhNQlpUZV91cXJGZFpZckRpTS1qYzlEcmNCMjVINy11WlVLRG42NlBrdThra3dnOGxzX1hWelNZV3FQTmtaMGt6R24wakFVNGltLU45aG9tdnk3YXhEYjNfZE93VFh6SUozSlhBd1pXVjdCRkUwdmwwT0lDTlZIQUtLWFB3Zw?oc=5" target="_blank">Dorgu rescues point for Manchester United in eight-goal thriller against Aston Villa</a>&nbsp;&nbsp;<font color="#6f6f6f">The Guardian</font></li><li><a href="https://news.google.com/rss/articles/CBMiqgFBVV95cUxNQzZqLXd3WkZWbnFFekVjak4xTGxEZlpFTzFhR0gxdFA0Nm1FaWwyZWxRTUU0SkxudEdJeWpGRHFuRHFWS2NNMHNWX3JkU2dYTHJxekoyU0dVZWhkZ1JoQ2JKaVFnSFlaV0xpRWx2TS1TcElRaFBOTExPMlR2TF9xNUNKV0NEaU1pWnJoVUdxejEwQjYwa0RpR1ZLLXJKOXRFWUZWVkRrT3g4dw?oc=5" target="_blank">Comedy of errors prompts Emery to leave early – all eight goals ranked by stupidity</a>&nbsp;&nbsp;<font color="#6f6f6f">The Telegraph</font></li></ol>.

Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: Free Malaysia Today.
```

#### Editorial Risk Assessment
- **Headline Grounding:** Headline derived from real RSS title; however, editorial verification badge is synthetic.
- **Event Freshness (New vs Old):** Published 2026-11-08 (within 24-36h sliding window).
- **Publication Date vs Event Date:** Potential conflation. RSS publication timestamp does not clarify the exact hour or day the incident or event took place.
- **Unsupported Claims / Entities:** Body text relies on boiler-plate template (`【权威动态播报】...`). For sports articles, raw HTML snippets from Google News RSS were injected into body text.
- **Cross-Lingual Parity:** **FAIL / HIGH RISK.** BM headline is merely a prefix `Laporan Berita:` attached to the untranslated Chinese headline. BM body is generic boilerplate.
- **Source Retrieval Depth:** **SNIPPET ONLY.** Full web page was not retrieved; only RSS title and metadata were processed.
- **Sabah / Sandakan Relevance:** **LOW / IRRELEVANT.** Sports or international/celebrity general news.

---

### Article 13: `art_sports_19` [SPORTS]

- **Article ID:** `art_sports_19`
- **Category:** `sports` (Geographic Scope: `national`)
- **Chinese Headline:** Man United in relegation zone, but Michael Carrick insists: I deserve to keep job [ESPN 实时发布]
- **Bahasa Malaysia Headline:** Laporan Berita: Man United in relegation zone, but Michael Carrick insists: I deserve to keep job
- **Original Source Name:** ESPN
- **Original Source URL:** [https://news.google.com/rss/articles/CBMijgFBVV95cUxPTXRIQzhMeURvMXlTUVNDeXFqU0NPcFR2dHZENVA2T3pqWWtVZ2k4Nnc5ZUNIcXE3X1VtVFVaSXNzajM3OUw4emNWcEJCWUxhSGVxdUpCdlplbVBoMDFJRWE4Zmd2dGt2aVdNaGNQX19YZG1BWThRZzdUZUQwc0ZPM1RJT21iNjFReE9rVjVR?oc=5](https://news.google.com/rss/articles/CBMijgFBVV95cUxPTXRIQzhMeURvMXlTUVNDeXFqU0NPcFR2dHZENVA2T3pqWWtVZ2k4Nnc5ZUNIcXE3X1VtVFVaSXNzajM3OUw4emNWcEJCWUxhSGVxdUpCdlplbVBoMDFJRWE4Zmd2dGt2aVdNaGNQX19YZG1BWThRZzdUZUQwc0ZPM1RJT21iNjFReE9rVjVR?oc=5)
- **Original Publication Timestamp:** `2026-11-08T20:27:00+00:00`
- **News Event Date:** Estimated 2026-11-07 to 2026-11-09 (derived from publication context)
- **Fact IDs & Source Evidence:** `None` (Track B deterministic fallback executed with empty Fact ID bindings `[]`)
- **D-7 Validation Verdict:** `is_valid: True`, status: `VERIFIED`, errors: `[]`, warnings: `[]`
- **Missing / Uncertain Information:** Full investigative article body not fetched; source evidence provenance ungrounded; BM title un-translated.

#### Complete Chinese Body (`detail`)
```text
【权威动态播报】<ol><li><a href="https://news.google.com/rss/articles/CBMijgFBVV95cUxPTXRIQzhMeURvMXlTUVNDeXFqU0NPcFR2dHZENVA2T3pqWWtVZ2k4Nnc5ZUNIcXE3X1VtVFVaSXNzajM3OUw4emNWcEJCWUxhSGVxdUpCdlplbVBoMDFJRWE4Zmd2dGt2aVdNaGNQX19YZG1BWThRZzdUZUQwc0ZPM1RJT21iNjFReE9rVjVR?oc=5" target="_blank">Man United in relegation zone, but Michael Carrick insists: I deserve to keep job</a>&nbsp;&nbsp;<font color="#6f6f6f">ESPN</font></li><li><a href="https://news.google.com/rss/articles/CBMiaEFVX3lxTFA2b1JLMnlrMnFJWTZNSFNvVFFaMS04LTF2OWVleTlhUXBWMTJOamhLeXkyWEFYcDRrS2RkNkVlRXlIZElQblRyc2ZDcUFFMUhaM2w0U0dlaWVsQmRXQ3BSYjhnU0VrMEx2?oc=5" target="_blank">Man Utd 4-4 Aston Villa: Bizarre and thrilling theatre as Carrick's future still in limbo</a>&nbsp;&nbsp;<font color="#6f6f6f">BBC</font></li><li><a href="https://news.google.com/rss/articles/CBMiywFBVV95cUxOV2tYWlNOanh5N0ZjNGZkNUdqT2xHWVNWT3BHcERONWlDSktXb1JNNVEyeHJkTXZ0NHhjWHplY0xROUVqdTFfM3djQmhaN3o1Z3BkTW9kajBmN3IwUTF0d0F3MzhhQjVvdUJtN25DRk0tR2VWUGtoaTF3Qms5OTRCeUR5bHdPbGlweDhGMFJvMzJGU3h2bHlFaElhMWVoR3JsTHpmVEZ2S2xyX09icnVZUkc5QlFrWWNDbk1PU2ZJc0cwYWRNZ2I1SDNFaw?oc=5" target="_blank">‘I expect to move forward’: Carrick denies risk of Manchester United sack</a>&nbsp;&nbsp;<font color="#6f6f6f">The Guardian</font></li><li><a href="https://news.google.com/rss/articles/CBMi7wFBVV95cUxPbmd5VFowdWpCaWh2Q2VVUjIzcXd6aGV4MGlnSzJ2T0Ezc0VhenVVUHVpaVFJYnFWWURJNmJYdFoydW5YdFE2bGFRcTNxTlZnaExodWltTldoeWRqa1E1TWhUd0MxdkIxMXBIREwyY09sVjhJeDNWZFA5cVI5UV9acHdEVjAwVjkycFJ5YlhFN0RfYzRDRE9WUm5sbVU2TkdneXlEb3FBdFJoelIwN1NJSzZyUUhEYS1EbjhPVks4aS1MbV9mR0tHYmE4NXZldGh0VHJVek02MUduV2s5VW15aGFReVByOHBoOHdoNC1jSQ?oc=5" target="_blank">Michael Carrick's Man Utd future uncertain as club ponder international break change - Paper Talk</a>&nbsp;&nbsp;<font color="#6f6f6f">Sky Sports</font></li><li><a href="https://news.google.com/rss/articles/CBMiuAFBVV95cUxNci1jWEZCVUQwUHhzd3FVQjd0NmdDSlFyZGhRbTRMV01XeFpFOGpoR3RacGpZYTA5SVpIdXZJT05pcG42aHNFcmd0WmRYNWFhRVlmUnB2UmEyc1dQZTFDYXhXQXBSXzlaWFdacVNUZW5Pb0p0aHRWUWdjR3NaQ1ljYnREeUZ6RlBzUmoxVUhRejhyZ1lfNHFzbGNBQmo5NUt2bmV6aGJXNFdwWFV0VG1DT08yODJYVVli?oc=5" target="_blank">Michael Carrick has painfully awkward exchange with interviewer over Man United future</a>&nbsp;&nbsp;<font color="#6f6f6f">The Independent</font></li></ol>。据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：ESPN。
```

#### Complete Bahasa Malaysia Body (`detailBM`)
```text
Notis Berita Rasmi: <ol><li><a href="https://news.google.com/rss/articles/CBMijgFBVV95cUxPTXRIQzhMeURvMXlTUVNDeXFqU0NPcFR2dHZENVA2T3pqWWtVZ2k4Nnc5ZUNIcXE3X1VtVFVaSXNzajM3OUw4emNWcEJCWUxhSGVxdUpCdlplbVBoMDFJRWE4Zmd2dGt2aVdNaGNQX19YZG1BWThRZzdUZUQwc0ZPM1RJT21iNjFReE9rVjVR?oc=5" target="_blank">Man United in relegation zone, but Michael Carrick insists: I deserve to keep job</a>&nbsp;&nbsp;<font color="#6f6f6f">ESPN</font></li><li><a href="https://news.google.com/rss/articles/CBMiaEFVX3lxTFA2b1JLMnlrMnFJWTZNSFNvVFFaMS04LTF2OWVleTlhUXBWMTJOamhLeXkyWEFYcDRrS2RkNkVlRXlIZElQblRyc2ZDcUFFMUhaM2w0U0dlaWVsQmRXQ3BSYjhnU0VrMEx2?oc=5" target="_blank">Man Utd 4-4 Aston Villa: Bizarre and thrilling theatre as Carrick's future still in limbo</a>&nbsp;&nbsp;<font color="#6f6f6f">BBC</font></li><li><a href="https://news.google.com/rss/articles/CBMiywFBVV95cUxOV2tYWlNOanh5N0ZjNGZkNUdqT2xHWVNWT3BHcERONWlDSktXb1JNNVEyeHJkTXZ0NHhjWHplY0xROUVqdTFfM3djQmhaN3o1Z3BkTW9kajBmN3IwUTF0d0F3MzhhQjVvdUJtN25DRk0tR2VWUGtoaTF3Qms5OTRCeUR5bHdPbGlweDhGMFJvMzJGU3h2bHlFaElhMWVoR3JsTHpmVEZ2S2xyX09icnVZUkc5QlFrWWNDbk1PU2ZJc0cwYWRNZ2I1SDNFaw?oc=5" target="_blank">‘I expect to move forward’: Carrick denies risk of Manchester United sack</a>&nbsp;&nbsp;<font color="#6f6f6f">The Guardian</font></li><li><a href="https://news.google.com/rss/articles/CBMi7wFBVV95cUxPbmd5VFowdWpCaWh2Q2VVUjIzcXd6aGV4MGlnSzJ2T0Ezc0VhenVVUHVpaVFJYnFWWURJNmJYdFoydW5YdFE2bGFRcTNxTlZnaExodWltTldoeWRqa1E1TWhUd0MxdkIxMXBIREwyY09sVjhJeDNWZFA5cVI5UV9acHdEVjAwVjkycFJ5YlhFN0RfYzRDRE9WUm5sbVU2TkdneXlEb3FBdFJoelIwN1NJSzZyUUhEYS1EbjhPVks4aS1MbV9mR0tHYmE4NXZldGh0VHJVek02MUduV2s5VW15aGFReVByOHBoOHdoNC1jSQ?oc=5" target="_blank">Michael Carrick's Man Utd future uncertain as club ponder international break change - Paper Talk</a>&nbsp;&nbsp;<font color="#6f6f6f">Sky Sports</font></li><li><a href="https://news.google.com/rss/articles/CBMiuAFBVV95cUxNci1jWEZCVUQwUHhzd3FVQjd0NmdDSlFyZGhRbTRMV01XeFpFOGpoR3RacGpZYTA5SVpIdXZJT05pcG42aHNFcmd0WmRYNWFhRVlmUnB2UmEyc1dQZTFDYXhXQXBSXzlaWFdacVNUZW5Pb0p0aHRWUWdjR3NaQ1ljYnREeUZ6RlBzUmoxVUhRejhyZ1lfNHFzbGNBQmo5NUt2bmV6aGJXNFdwWFV0VG1DT08yODJYVVli?oc=5" target="_blank">Michael Carrick has painfully awkward exchange with interviewer over Man United future</a>&nbsp;&nbsp;<font color="#6f6f6f">The Independent</font></li></ol>.

Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: ESPN.
```

#### Editorial Risk Assessment
- **Headline Grounding:** Headline derived from real RSS title; however, editorial verification badge is synthetic.
- **Event Freshness (New vs Old):** Published 2026-11-08 (within 24-36h sliding window).
- **Publication Date vs Event Date:** Potential conflation. RSS publication timestamp does not clarify the exact hour or day the incident or event took place.
- **Unsupported Claims / Entities:** Body text relies on boiler-plate template (`【权威动态播报】...`). For sports articles, raw HTML snippets from Google News RSS were injected into body text.
- **Cross-Lingual Parity:** **FAIL / HIGH RISK.** BM headline is merely a prefix `Laporan Berita:` attached to the untranslated Chinese headline. BM body is generic boilerplate.
- **Source Retrieval Depth:** **SNIPPET ONLY.** Full web page was not retrieved; only RSS title and metadata were processed.
- **Sabah / Sandakan Relevance:** **LOW / IRRELEVANT.** Sports or international/celebrity general news.

---

### Article 14: `art_sports_20` [SPORTS]

- **Article ID:** `art_sports_20`
- **Category:** `sports` (Geographic Scope: `national`)
- **Chinese Headline:** Nottm Forest 3-1 Man City (Nov 7, 2026) Game Analysis [ESPN 实时发布]
- **Bahasa Malaysia Headline:** Laporan Berita: Nottm Forest 3-1 Man City (Nov 7, 2026) Game Analysis
- **Original Source Name:** ESPN
- **Original Source URL:** [https://news.google.com/rss/articles/CBMiY0FVX3lxTE82d2tURzYyVWYyTlpIMzd2cC0xOHZFSUtsbVYzNW9vMWUzdkRXbEY4dWdGVmF2UEJFZXh1RHlib0l6RjJpSlNaVHY5aEFDbTdxYzJ3Ykljd2RhdXBGZ0YtbE5OSQ?oc=5](https://news.google.com/rss/articles/CBMiY0FVX3lxTE82d2tURzYyVWYyTlpIMzd2cC0xOHZFSUtsbVYzNW9vMWUzdkRXbEY4dWdGVmF2UEJFZXh1RHlib0l6RjJpSlNaVHY5aEFDbTdxYzJ3Ykljd2RhdXBGZ0YtbE5OSQ?oc=5)
- **Original Publication Timestamp:** `2026-11-07T22:46:24+00:00`
- **News Event Date:** Estimated 2026-11-07 to 2026-11-09 (derived from publication context)
- **Fact IDs & Source Evidence:** `None` (Track B deterministic fallback executed with empty Fact ID bindings `[]`)
- **D-7 Validation Verdict:** `is_valid: True`, status: `VERIFIED`, errors: `[]`, warnings: `[]`
- **Missing / Uncertain Information:** Full investigative article body not fetched; source evidence provenance ungrounded; BM title un-translated.

#### Complete Chinese Body (`detail`)
```text
【权威动态播报】<ol><li><a href="https://news.google.com/rss/articles/CBMiY0FVX3lxTE82d2tURzYyVWYyTlpIMzd2cC0xOHZFSUtsbVYzNW9vMWUzdkRXbEY4dWdGVmF2UEJFZXh1RHlib0l6RjJpSlNaVHY5aEFDbTdxYzJ3Ykljd2RhdXBGZ0YtbE5OSQ?oc=5" target="_blank">Nottm Forest 3-1 Man City (Nov 7, 2026) Game Analysis</a>&nbsp;&nbsp;<font color="#6f6f6f">ESPN</font></li><li><a href="https://news.google.com/rss/articles/CBMiaEFVX3lxTFBEWmxQQ0h2TGhOdk5HNXltdUdicElPVWlyZ1hQVDRIckI1ejdoaG5FNFlKUmVGSEdRSUNZVzJQN2lkQnVGV24zNHdmZ0E0cndSNmE4Y0xGaFg0b182cmV6N2dsWFBqcEJa?oc=5" target="_blank">Nottingham Forest 3-1 Man City: Enzo Maresca's dream start turns into nightmare</a>&nbsp;&nbsp;<font color="#6f6f6f">BBC</font></li><li><a href="https://news.google.com/rss/articles/CBMirwFBVV95cUxPT2M0aTVlV1QtQ0FSMVNqWEt4UTlJb3daeXRKOENVTU1lM1JQYVJoaE5TTlFKNFl1NzhhNmxLVXlMYzFtUVlickdyaXZqOVVXXzJkVm1mdFRobXh0V1JRTk9lQ2ZLWENGUWFyaG8wZlhGeTV6S3BOWEY2a1ZTVGdzMTJBQkRsdEx0NXhSNTBNQUdHYWJiOVQ4M1BaZzQ5ZVRiak5XbHJGdksyZkpGM0NV?oc=5" target="_blank">Delap’s Nottingham Forest stunners hand Manchester City third league defeat in a row</a>&nbsp;&nbsp;<font color="#6f6f6f">The Guardian</font></li><li><a href="https://news.google.com/rss/articles/CBMihwFBVV95cUxNS25YSzlWNzBLOXo4LU1WZk5adjViWjNDcEkzaEpZcUstREZ4eDFYQ0NfbVV6azdab2lneGh6bHk2OVUyZ2lEeTBRNEpKOVdlVW4xY0g2UTJoVThPSEtZS3ZKWm8zaFBLcFB0MEdFUDROODNudzFXOVYtdHdtZmVlY3pfYUszTUU?oc=5" target="_blank">DELAP'S DOUBLE DELIGHT</a>&nbsp;&nbsp;<font color="#6f6f6f">Nottingham Forest FC</font></li><li><a href="https://news.google.com/rss/articles/CBMipwFBVV95cUxNX1hLZUpSbGNvZm15aURNbGk1RGdiQW11S0R5MDRlYWV3cHlQNVQ0dHN5SG1fZ1NTc2syY0dMSXZrTC0tNDRFemVaTkpUWEp2ZHVGTzd6YWFfTXNHQ2ZHTVdQbjN1dzlJTXlvRGhEZlVzMG4yXy1DRTVuQWhjdDRsRlVNblYyeG5SWE4xNDJ6eDFlSUJQSXpPSll5SnpldWZGSWhLWTBPQQ?oc=5" target="_blank">Man City look to be crumbling after guilty verdict</a>&nbsp;&nbsp;<font color="#6f6f6f">The Telegraph</font></li></ol>。据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：ESPN。
```

#### Complete Bahasa Malaysia Body (`detailBM`)
```text
Notis Berita Rasmi: <ol><li><a href="https://news.google.com/rss/articles/CBMiY0FVX3lxTE82d2tURzYyVWYyTlpIMzd2cC0xOHZFSUtsbVYzNW9vMWUzdkRXbEY4dWdGVmF2UEJFZXh1RHlib0l6RjJpSlNaVHY5aEFDbTdxYzJ3Ykljd2RhdXBGZ0YtbE5OSQ?oc=5" target="_blank">Nottm Forest 3-1 Man City (Nov 7, 2026) Game Analysis</a>&nbsp;&nbsp;<font color="#6f6f6f">ESPN</font></li><li><a href="https://news.google.com/rss/articles/CBMiaEFVX3lxTFBEWmxQQ0h2TGhOdk5HNXltdUdicElPVWlyZ1hQVDRIckI1ejdoaG5FNFlKUmVGSEdRSUNZVzJQN2lkQnVGV24zNHdmZ0E0cndSNmE4Y0xGaFg0b182cmV6N2dsWFBqcEJa?oc=5" target="_blank">Nottingham Forest 3-1 Man City: Enzo Maresca's dream start turns into nightmare</a>&nbsp;&nbsp;<font color="#6f6f6f">BBC</font></li><li><a href="https://news.google.com/rss/articles/CBMirwFBVV95cUxPT2M0aTVlV1QtQ0FSMVNqWEt4UTlJb3daeXRKOENVTU1lM1JQYVJoaE5TTlFKNFl1NzhhNmxLVXlMYzFtUVlickdyaXZqOVVXXzJkVm1mdFRobXh0V1JRTk9lQ2ZLWENGUWFyaG8wZlhGeTV6S3BOWEY2a1ZTVGdzMTJBQkRsdEx0NXhSNTBNQUdHYWJiOVQ4M1BaZzQ5ZVRiak5XbHJGdksyZkpGM0NV?oc=5" target="_blank">Delap’s Nottingham Forest stunners hand Manchester City third league defeat in a row</a>&nbsp;&nbsp;<font color="#6f6f6f">The Guardian</font></li><li><a href="https://news.google.com/rss/articles/CBMihwFBVV95cUxNS25YSzlWNzBLOXo4LU1WZk5adjViWjNDcEkzaEpZcUstREZ4eDFYQ0NfbVV6azdab2lneGh6bHk2OVUyZ2lEeTBRNEpKOVdlVW4xY0g2UTJoVThPSEtZS3ZKWm8zaFBLcFB0MEdFUDROODNudzFXOVYtdHdtZmVlY3pfYUszTUU?oc=5" target="_blank">DELAP'S DOUBLE DELIGHT</a>&nbsp;&nbsp;<font color="#6f6f6f">Nottingham Forest FC</font></li><li><a href="https://news.google.com/rss/articles/CBMipwFBVV95cUxNX1hLZUpSbGNvZm15aURNbGk1RGdiQW11S0R5MDRlYWV3cHlQNVQ0dHN5SG1fZ1NTc2syY0dMSXZrTC0tNDRFemVaTkpUWEp2ZHVGTzd6YWFfTXNHQ2ZHTVdQbjN1dzlJTXlvRGhEZlVzMG4yXy1DRTVuQWhjdDRsRlVNblYyeG5SWE4xNDJ6eDFlSUJQSXpPSll5SnpldWZGSWhLWTBPQQ?oc=5" target="_blank">Man City look to be crumbling after guilty verdict</a>&nbsp;&nbsp;<font color="#6f6f6f">The Telegraph</font></li></ol>.

Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: ESPN.
```

#### Editorial Risk Assessment
- **Headline Grounding:** Headline derived from real RSS title; however, editorial verification badge is synthetic.
- **Event Freshness (New vs Old):** Published 2026-11-07 (near edge of sliding window).
- **Publication Date vs Event Date:** Potential conflation. RSS publication timestamp does not clarify the exact hour or day the incident or event took place.
- **Unsupported Claims / Entities:** Body text relies on boiler-plate template (`【权威动态播报】...`). For sports articles, raw HTML snippets from Google News RSS were injected into body text.
- **Cross-Lingual Parity:** **FAIL / HIGH RISK.** BM headline is merely a prefix `Laporan Berita:` attached to the untranslated Chinese headline. BM body is generic boilerplate.
- **Source Retrieval Depth:** **SNIPPET ONLY.** Full web page was not retrieved; only RSS title and metadata were processed.
- **Sabah / Sandakan Relevance:** **LOW / IRRELEVANT.** Sports or international/celebrity general news.

---

### Article 15: `art_sports_21` [SPORTS]

- **Article ID:** `art_sports_21`
- **Category:** `sports` (Geographic Scope: `national`)
- **Chinese Headline:** Korea Open: Indomitable An Equals Greatest Season [BWF World Tour 实时发布]
- **Bahasa Malaysia Headline:** Laporan Berita: Korea Open: Indomitable An Equals Greatest Season
- **Original Source Name:** BWF World Tour
- **Original Source URL:** [https://news.google.com/rss/articles/CBMirgFBVV95cUxPUENWMmNRWGdESTlFUndCLUhFY1VCbS1VU1FLWENJeUNYZGtMUTVKdlJIVXdsS0c3cndBckJvVXNhbmZLYUVmNmxuZTVydTRUek1RR0tIM2oxN0hmaDlMM25lUkJkSHZSZE1od3FFZ0ZOME1rY1h1VDA3Ym1OYkw0MmpaeUJmRWQxLUhSZzZ2cEpSVXRwUWlfdGdhRFRGMTlyWlNFV2NrMk11YnJQd3c?oc=5](https://news.google.com/rss/articles/CBMirgFBVV95cUxPUENWMmNRWGdESTlFUndCLUhFY1VCbS1VU1FLWENJeUNYZGtMUTVKdlJIVXdsS0c3cndBckJvVXNhbmZLYUVmNmxuZTVydTRUek1RR0tIM2oxN0hmaDlMM25lUkJkSHZSZE1od3FFZ0ZOME1rY1h1VDA3Ym1OYkw0MmpaeUJmRWQxLUhSZzZ2cEpSVXRwUWlfdGdhRFRGMTlyWlNFV2NrMk11YnJQd3c?oc=5)
- **Original Publication Timestamp:** `2026-11-08T10:24:05+00:00`
- **News Event Date:** Estimated 2026-11-07 to 2026-11-09 (derived from publication context)
- **Fact IDs & Source Evidence:** `None` (Track B deterministic fallback executed with empty Fact ID bindings `[]`)
- **D-7 Validation Verdict:** `is_valid: True`, status: `VERIFIED`, errors: `[]`, warnings: `[]`
- **Missing / Uncertain Information:** Full investigative article body not fetched; source evidence provenance ungrounded; BM title un-translated.

#### Complete Chinese Body (`detail`)
```text
【权威动态播报】<ol><li><a href="https://news.google.com/rss/articles/CBMirgFBVV95cUxPUENWMmNRWGdESTlFUndCLUhFY1VCbS1VU1FLWENJeUNYZGtMUTVKdlJIVXdsS0c3cndBckJvVXNhbmZLYUVmNmxuZTVydTRUek1RR0tIM2oxN0hmaDlMM25lUkJkSHZSZE1od3FFZ0ZOME1rY1h1VDA3Ym1OYkw0MmpaeUJmRWQxLUhSZzZ2cEpSVXRwUWlfdGdhRFRGMTlyWlNFV2NrMk11YnJQd3c?oc=5" target="_blank">Korea Open: Indomitable An Equals Greatest Season</a>&nbsp;&nbsp;<font color="#6f6f6f">BWF World Tour</font></li><li><a href="https://news.google.com/rss/articles/CBMihgFBVV95cUxPc1pvTFBEU1NTRDlaQldFS0dfOUg5OTJWd1FLa3lPNnRKVGl0SjUybGpLaWcxWGwxT0g3cmxoQW1YaDR2ZmtYdUVOQ0JZNmJxeHg0c3g1U21za3FaZjNGVDROaGhhUVBia082MEpVTGVFanpHTER6YXl2eWNNYkZzaktTd2RjQQ?oc=5" target="_blank">An Se-young Ties Record, Eyes Historic 12th</a>&nbsp;&nbsp;<font color="#6f6f6f">조선일보</font></li><li><a href="https://news.google.com/rss/articles/CBMiZkFVX3lxTFA3cHZ5NVF3a3h4TjR4MVZQMHFzNnU5bDJwSlhONl9xeG8tWExWRTRGZk9NSi1uMVdFYkNYbVduUmZfN2IzRWtNRWJXSGJhcUVSdkY3U2EwbExQY0ZhdXlWa2RiM2pydw?oc=5" target="_blank">An Se-young extends winning streak to 55 matches</a>&nbsp;&nbsp;<font color="#6f6f6f">동아일보</font></li><li><a href="https://news.google.com/rss/articles/CBMiekFVX3lxTE1aTnBqVFRKR0NDODg5dmtaOThJUms3UTRfTU8wc3d0dGgzM2h1UUJiWXg3ZTRBN2pzSmtZekZCOEdXd25jUVh2ZXRYZ1VrSllLdU9kYXliQXJhQUo1ZC1id2FWd3ItbzZLNVYzYTRid083RTB0M3ZpdTVB?oc=5" target="_blank">"An Se-young, same 11 wins but this year is even more remarkable" — Foreign media take note of historic achievement... Dominates World Championships and Asian Games for a "historic season"</a>&nbsp;&nbsp;<font color="#6f6f6f">스타뉴스</font></li><li><a href="https://news.google.com/rss/articles/CBMickFVX3lxTE16d3NtZ0FhS3RtU3BwV1J2ZWplTk9UbFlxM3dYbks2TTBnaTNxZzd2RDJKUklhaklub01XSTliaThxSWVQT0NSak1EVzlneHN6MlFfWWlvczh6NFIxMHJ5YmFhZUF6RlYwb1BXOEo5ZDdSZw?oc=5" target="_blank">An wins Korea Open for 11th badminton title of year</a>&nbsp;&nbsp;<font color="#6f6f6f">AFP.com</font></li></ol>。据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：BWF World Tour。
```

#### Complete Bahasa Malaysia Body (`detailBM`)
```text
Notis Berita Rasmi: <ol><li><a href="https://news.google.com/rss/articles/CBMirgFBVV95cUxPUENWMmNRWGdESTlFUndCLUhFY1VCbS1VU1FLWENJeUNYZGtMUTVKdlJIVXdsS0c3cndBckJvVXNhbmZLYUVmNmxuZTVydTRUek1RR0tIM2oxN0hmaDlMM25lUkJkSHZSZE1od3FFZ0ZOME1rY1h1VDA3Ym1OYkw0MmpaeUJmRWQxLUhSZzZ2cEpSVXRwUWlfdGdhRFRGMTlyWlNFV2NrMk11YnJQd3c?oc=5" target="_blank">Korea Open: Indomitable An Equals Greatest Season</a>&nbsp;&nbsp;<font color="#6f6f6f">BWF World Tour</font></li><li><a href="https://news.google.com/rss/articles/CBMihgFBVV95cUxPc1pvTFBEU1NTRDlaQldFS0dfOUg5OTJWd1FLa3lPNnRKVGl0SjUybGpLaWcxWGwxT0g3cmxoQW1YaDR2ZmtYdUVOQ0JZNmJxeHg0c3g1U21za3FaZjNGVDROaGhhUVBia082MEpVTGVFanpHTER6YXl2eWNNYkZzaktTd2RjQQ?oc=5" target="_blank">An Se-young Ties Record, Eyes Historic 12th</a>&nbsp;&nbsp;<font color="#6f6f6f">조선일보</font></li><li><a href="https://news.google.com/rss/articles/CBMiZkFVX3lxTFA3cHZ5NVF3a3h4TjR4MVZQMHFzNnU5bDJwSlhONl9xeG8tWExWRTRGZk9NSi1uMVdFYkNYbVduUmZfN2IzRWtNRWJXSGJhcUVSdkY3U2EwbExQY0ZhdXlWa2RiM2pydw?oc=5" target="_blank">An Se-young extends winning streak to 55 matches</a>&nbsp;&nbsp;<font color="#6f6f6f">동아일보</font></li><li><a href="https://news.google.com/rss/articles/CBMiekFVX3lxTE1aTnBqVFRKR0NDODg5dmtaOThJUms3UTRfTU8wc3d0dGgzM2h1UUJiWXg3ZTRBN2pzSmtZekZCOEdXd25jUVh2ZXRYZ1VrSllLdU9kYXliQXJhQUo1ZC1id2FWd3ItbzZLNVYzYTRid083RTB0M3ZpdTVB?oc=5" target="_blank">"An Se-young, same 11 wins but this year is even more remarkable" — Foreign media take note of historic achievement... Dominates World Championships and Asian Games for a "historic season"</a>&nbsp;&nbsp;<font color="#6f6f6f">스타뉴스</font></li><li><a href="https://news.google.com/rss/articles/CBMickFVX3lxTE16d3NtZ0FhS3RtU3BwV1J2ZWplTk9UbFlxM3dYbks2TTBnaTNxZzd2RDJKUklhaklub01XSTliaThxSWVQT0NSak1EVzlneHN6MlFfWWlvczh6NFIxMHJ5YmFhZUF6RlYwb1BXOEo5ZDdSZw?oc=5" target="_blank">An wins Korea Open for 11th badminton title of year</a>&nbsp;&nbsp;<font color="#6f6f6f">AFP.com</font></li></ol>.

Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: BWF World Tour.
```

#### Editorial Risk Assessment
- **Headline Grounding:** Headline derived from real RSS title; however, editorial verification badge is synthetic.
- **Event Freshness (New vs Old):** Published 2026-11-08 (within 24-36h sliding window).
- **Publication Date vs Event Date:** Potential conflation. RSS publication timestamp does not clarify the exact hour or day the incident or event took place.
- **Unsupported Claims / Entities:** Body text relies on boiler-plate template (`【权威动态播报】...`). For sports articles, raw HTML snippets from Google News RSS were injected into body text.
- **Cross-Lingual Parity:** **FAIL / HIGH RISK.** BM headline is merely a prefix `Laporan Berita:` attached to the untranslated Chinese headline. BM body is generic boilerplate.
- **Source Retrieval Depth:** **SNIPPET ONLY.** Full web page was not retrieved; only RSS title and metadata were processed.
- **Sabah / Sandakan Relevance:** **LOW / IRRELEVANT.** Sports or international/celebrity general news.

---

### Article 16: `art_general_22` [GENERAL]

- **Article ID:** `art_general_22`
- **Category:** `general` (Geographic Scope: `national`)
- **Chinese Headline:** 马哈迪屠妖节外出购物 精神奕奕与民互动 [诗华日报 实时发布]
- **Bahasa Malaysia Headline:** Laporan Berita: 马哈迪屠妖节外出购物 精神奕奕与民互动
- **Original Source Name:** 诗华日报
- **Original Source URL:** [https://news.seehua.com/post/1602322](https://news.seehua.com/post/1602322)
- **Original Publication Timestamp:** `2026-11-09T11:06:54+08:00`
- **News Event Date:** Estimated 2026-11-07 to 2026-11-09 (derived from publication context)
- **Fact IDs & Source Evidence:** `None` (Track B deterministic fallback executed with empty Fact ID bindings `[]`)
- **D-7 Validation Verdict:** `is_valid: True`, status: `VERIFIED`, errors: `[]`, warnings: `[]`
- **Missing / Uncertain Information:** Full investigative article body not fetched; source evidence provenance ungrounded; BM title un-translated.

#### Complete Chinese Body (`detail`)
```text
【权威动态播报】马哈迪屠妖节外出购物 精神奕奕与民互动。据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：诗华日报。
```

#### Complete Bahasa Malaysia Body (`detailBM`)
```text
Notis Berita Rasmi: 马哈迪屠妖节外出购物 精神奕奕与民互动.

Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: 诗华日报.
```

#### Editorial Risk Assessment
- **Headline Grounding:** Headline derived from real RSS title; however, editorial verification badge is synthetic.
- **Event Freshness (New vs Old):** Fresh event published on target date (2026-11-09).
- **Publication Date vs Event Date:** Potential conflation. RSS publication timestamp does not clarify the exact hour or day the incident or event took place.
- **Unsupported Claims / Entities:** Body text relies on boiler-plate template (`【权威动态播报】...`). For sports articles, raw HTML snippets from Google News RSS were injected into body text.
- **Cross-Lingual Parity:** **FAIL / HIGH RISK.** BM headline is merely a prefix `Laporan Berita:` attached to the untranslated Chinese headline. BM body is generic boilerplate.
- **Source Retrieval Depth:** **SNIPPET ONLY.** Full web page was not retrieved; only RSS title and metadata were processed.
- **Sabah / Sandakan Relevance:** **LOW / IRRELEVANT.** Sports or international/celebrity general news.

---

### Article 17: `art_general_23` [GENERAL]

- **Article ID:** `art_general_23`
- **Category:** `general` (Geographic Scope: `national`)
- **Chinese Headline:** 黄仁勋婚外情风波 特朗普发声力挺：他是品格高尚的人 [诗华日报 实时发布]
- **Bahasa Malaysia Headline:** Laporan Berita: 黄仁勋婚外情风波 特朗普发声力挺：他是品格高尚的人
- **Original Source Name:** 诗华日报
- **Original Source URL:** [https://news.seehua.com/post/1602252](https://news.seehua.com/post/1602252)
- **Original Publication Timestamp:** `2026-11-09T10:15:37+08:00`
- **News Event Date:** Estimated 2026-11-07 to 2026-11-09 (derived from publication context)
- **Fact IDs & Source Evidence:** `None` (Track B deterministic fallback executed with empty Fact ID bindings `[]`)
- **D-7 Validation Verdict:** `is_valid: True`, status: `VERIFIED`, errors: `[]`, warnings: `[]`
- **Missing / Uncertain Information:** Full investigative article body not fetched; source evidence provenance ungrounded; BM title un-translated.

#### Complete Chinese Body (`detail`)
```text
【权威动态播报】黄仁勋婚外情风波 特朗普发声力挺：他是品格高尚的人。据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：诗华日报。
```

#### Complete Bahasa Malaysia Body (`detailBM`)
```text
Notis Berita Rasmi: 黄仁勋婚外情风波 特朗普发声力挺：他是品格高尚的人.

Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: 诗华日报.
```

#### Editorial Risk Assessment
- **Headline Grounding:** Headline derived from real RSS title; however, editorial verification badge is synthetic.
- **Event Freshness (New vs Old):** Fresh event published on target date (2026-11-09).
- **Publication Date vs Event Date:** Potential conflation. RSS publication timestamp does not clarify the exact hour or day the incident or event took place.
- **Unsupported Claims / Entities:** Body text relies on boiler-plate template (`【权威动态播报】...`). For sports articles, raw HTML snippets from Google News RSS were injected into body text.
- **Cross-Lingual Parity:** **FAIL / HIGH RISK.** BM headline is merely a prefix `Laporan Berita:` attached to the untranslated Chinese headline. BM body is generic boilerplate.
- **Source Retrieval Depth:** **SNIPPET ONLY.** Full web page was not retrieved; only RSS title and metadata were processed.
- **Sabah / Sandakan Relevance:** **LOW / IRRELEVANT.** Sports or international/celebrity general news.

---

### Article 18: `art_general_24` [GENERAL]

- **Article ID:** `art_general_24`
- **Category:** `general` (Geographic Scope: `national`)
- **Chinese Headline:** 公司聚餐为避酒做150个深蹲 男子双腿肿痛确诊横纹肌溶解 [诗华日报 实时发布]
- **Bahasa Malaysia Headline:** Laporan Berita: 公司聚餐为避酒做150个深蹲 男子双腿肿痛确诊横纹肌溶解
- **Original Source Name:** 诗华日报
- **Original Source URL:** [https://news.seehua.com/post/1602205](https://news.seehua.com/post/1602205)
- **Original Publication Timestamp:** `2026-11-09T08:12:46+08:00`
- **News Event Date:** Estimated 2026-11-07 to 2026-11-09 (derived from publication context)
- **Fact IDs & Source Evidence:** `None` (Track B deterministic fallback executed with empty Fact ID bindings `[]`)
- **D-7 Validation Verdict:** `is_valid: True`, status: `VERIFIED`, errors: `[]`, warnings: `[]`
- **Missing / Uncertain Information:** Full investigative article body not fetched; source evidence provenance ungrounded; BM title un-translated.

#### Complete Chinese Body (`detail`)
```text
【权威动态播报】公司聚餐为避酒做150个深蹲 男子双腿肿痛确诊横纹肌溶解。据官方通报与媒体实时走访，本项进展直接关系到本地民众切身利益，相关部门已责令责任单位加快落实进度并实施严密监控。事件发生后，各方代表提醒公众保持理性并密切关注后续官方指引。来源：诗华日报。
```

#### Complete Bahasa Malaysia Body (`detailBM`)
```text
Notis Berita Rasmi: 公司聚餐为避酒做150个深蹲 男子双腿肿痛确诊横纹肌溶解.

Pihak berkuasa dan agensi berkaitan telah menggerakkan pasukan bertugas bagi memantau rapi perkembangan terkini demi memastikan keselamatan serta kebajikan masyarakat sentiasa terjamin. Orang ramai dinasihatkan untuk merujuk kepada hebahan rasmi. Disahkan oleh: 诗华日报.
```

#### Editorial Risk Assessment
- **Headline Grounding:** Headline derived from real RSS title; however, editorial verification badge is synthetic.
- **Event Freshness (New vs Old):** Fresh event published on target date (2026-11-09).
- **Publication Date vs Event Date:** Potential conflation. RSS publication timestamp does not clarify the exact hour or day the incident or event took place.
- **Unsupported Claims / Entities:** Body text relies on boiler-plate template (`【权威动态播报】...`). For sports articles, raw HTML snippets from Google News RSS were injected into body text.
- **Cross-Lingual Parity:** **FAIL / HIGH RISK.** BM headline is merely a prefix `Laporan Berita:` attached to the untranslated Chinese headline. BM body is generic boilerplate.
- **Source Retrieval Depth:** **SNIPPET ONLY.** Full web page was not retrieved; only RSS title and metadata were processed.
- **Sabah / Sandakan Relevance:** **LOW / IRRELEVANT.** Sports or international/celebrity general news.

---

## 3. Extraction & Analysis of Rejected Articles (6 Items)

| # | Article ID | Category | Chinese Headline | Exact D-7 Rejection Reasons |
|---|---|---|---|---|
| 1 | `art_sabah_4` | `sabah` | 沙巴预算案12月4日提呈 哈芝芝：着重解决民生问题 [诗华日报沙巴版 实时发布] | • Headline contains unanchored named person '哈芝芝' (hajiji) |
| 2 | `art_sabah_7` | `sabah` | 沙巴乡区图书馆应转型数码学习中心 马西迪：助居民掌握科技 [诗华日报沙巴版 实时发布] | • Headline contains unanchored named person '马西迪' (masidi_manjun) |
| 3 | `art_national_9` | `national` | Malaysia’s health ministry to conduct inspections at Gardenia over consumer complaints [The Straits Times 实时发布] | • Global unanchored monetary value in ZH text: MYR 9<br>• Global unanchored monetary value in BM text: MYR 9 |
| 4 | `art_national_10` | `national` | No water to cook or bathe: Indonesians protest data centre boom as Malaysia expands its own [NST Online 实时发布] | • Global unanchored monetary value in ZH text: MYR 3<br>• Global unanchored monetary value in BM text: MYR 3 |
| 5 | `art_national_11` | `national` | 沙今年18村获批昌明领养甘榜计划 穆斯达法：获900万建设基... [诗华日报 实时发布] | • Headline monetary mismatch: ZH=[9000000] vs BM=[]<br>• Headline contains unanchored monetary value MYR 9000000<br>• Headline contains unanchored named person '穆斯达法' (mustapha_sakmud)<br>• Headline contains unanchored agency '昌明领养甘榜' (kam)<br>• Global unanchored monetary value in ZH text: MYR 9000000<br>• Global bilingual monetary set discrepancy: ZH=[9000000] vs BM=[] |
| 6 | `art_national_12` | `national` | 疑因购买货物欠债问题引发命案 警方不至24小时成功破案 [诗华日报 实时发布] | • Headline contains unanchored agency '警方' (pdrm) |

### Deep Rejection Diagnosis

1. **`art_sabah_4` (Chief Minister Hajiji Noor):** Correctly rejected because `哈芝芝` appeared in the headline without an explicit verified `FactItem` entity binding.
2. **`art_sabah_7` (Minister Masidi Manjun):** Correctly rejected because `马西迪` appeared in the headline without verified entity binding.
3. **`art_national_9` (Gardenia Health Inspection):** Rejected because Google News RSS HTML snippet contained unanchored number strings matched by monetary extractor.
4. **`art_national_10` (Data Centre Protest):** Rejected due to unanchored numeral patterns in raw Google News HTML snippet.
5. **`art_national_11` (Adopted Villages / Minister Mustapha Sakmud):** Correctly rejected for multiple severe factual violations: unanchored RM9,000,000 monetary figure, unanchored person `穆斯达法`, unanchored agency `昌明领养甘榜`, and bilateral parity mismatch.
6. **`art_national_12` (Murder Investigation):** Correctly rejected because agency `警方` appeared in the headline without a verified agency fact ID.

---

## 4. Synthesized Systemic Editorial Risk Review

### Risk Finding 1: Track B Fallback Template Monotony
- In Track B fallback mode, because LLM synthesis was safely bypassed (0 quota consumption), the generator relied on the deterministic fallback generator in `pipeline/synthesizer.py`.
- All non-sports articles share an identical template paragraph (`【权威动态播报】...相关部门已责令责任单位加快落实进度并实施严密监控...`). This lacks journalistic depth and provides no story-specific facts.

### Risk Finding 2: Bahasa Malaysia Title Pseudo-Translation
- For Chinese articles (`art_sabah_1` through `art_sabah_8`, `art_national_13` to `16`, and `art_general_22` to `24`), the BM title (`titleBM`) was generated by simply prepending `Laporan Berita: ` to the original Chinese headline.
- **Editorial Consequence:** A reader viewing the Bahasa Malaysia interface (`bm` language toggle) will see Chinese characters in the headline.

### Risk Finding 3: Raw HTML Tag Leaks in Sports News
- Articles `art_sports_17`, `18`, `19`, `20`, and `21` had raw HTML tags (`<ol><li><a href=...>...</a>`) ingested from Google News RSS feeds directly into their `detail` and `detailBM` text fields.
- If rendered without HTML sanitization or in plain-text markdown, this exposes raw anchor links and styling markup.

### Risk Finding 4: Geographic Inaccuracy in 'National' Category
- Article 9 (`art_national_15`, Kanowit longhouse fire) and Article 10 (`art_national_16`, Simanggang rest stop) are events in Sarawak, not Sabah.
- General news includes international entertainment/tech news (`art_general_23`, Jensen Huang / Trump) and international social news (`art_general_24`, 150 squats).

### Risk Finding 5: Snippet-Only Discovery vs. Body Retrieval
- The current automated discovery collector harvests RSS XML feeds and web portal headlines, but does not crawl full deep-page article bodies for Track B.
- While this ensures zero fabrication, it prevents detailed paragraph reporting in the offline Track B mode.

---

## 5. Editorial Recommendations for Phase D-11 (Publishing Decision)

1. **Do NOT Publish Track B Output to Production Live Site Unedited:**
   - The current preview in `reports/news_preview_20261109.json` represents a valid fail-closed safe fallback, but its editorial quality (template bodies, pseudo-BM titles, HTML tags) is unsuitable for public readers of Sabah Daily News.
2. **Actionable Path Forward:**
   - For a real publication run, either:
     a) Authorize execution within GitHub Actions where `GEMINI_API_KEY` is present to generate full-length human-quality bilingual reporting (as in Phase D-3), OR
     b) Apply human editorial corrections to the accepted Sandakan/Sabah headlines (Articles 1-6) before any publishing step.
3. **Production Integrity:**
   - Confirm that `news_data.json` and `index.html` remain completely protected.

