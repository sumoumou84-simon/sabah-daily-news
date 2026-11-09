#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_bilingual_fact_validator.py — Offline Unit & Regression Tests
Phase D-7: Live Pipeline Fact-Locking Integration & Zero-Bypass Verification
Verifies:
1. Deterministic calendar-weekday validation (C-7).
2. Strict non-linear fact status verification (C-8).
3. Native temporal precision preservation (C-9).
4. Independent atomic semantic-state verification on mixed-fact claims (C-10).
5. Headline fact-binding and unmapped token rejection.
6. Narrative claim verification and transition injection protection.
7. Exact Phase D-3 regressions (Article 1, Article 2, Article 3).
8. Legacy output assembler fails closed on invalid articles.
9. Identical hallucinated monetary values in Chinese and Malay (P0-1).
10. Unsupported named person in headline (P1-5).
11. Unsupported agency in headline (P1-5).
12. Allocation rewritten as expenditure using Malay passive voice (P1-7).
13. Allocation rewritten as expenditure using Chinese passive voice (P1-7).
14. SourceEvidence quote not found in ingested raw text (P0-4).
15. Track B narrative bypass attempt (P0-2).
16. Utilities and events containing unanchored factual claims (P1-6).
17. Year-only fact expanded into an exact date range (P1-8).
18. Synthesizer rejecting 10 or 11 articles when configured minimum is 12 (P0-3).
19. Both tracks rejecting the same invalid structured article.
20. Every persistence path requiring successful validation.
"""

import unittest
from unittest.mock import patch, MagicMock

from pipeline.fact_schema import (
    FactItem,
    FactCategory,
    FactStatus,
    SemanticLifecycleState,
    NormalizedMonetaryValue,
    NormalizedDateValue,
    NormalizedQuantityValue,
    NormalizedHeadcountValue,
    NormalizedEditionValue,
    SourceEvidence,
    HeadlineRecord,
    ClaimRecord,
    NarrativeClaimRecord,
    StylisticTransitions,
    StructuredArticle
)
from pipeline.fact_verifier import BilingualFactValidator
from pipeline.synthesizer import NewsSynthesizer


class TestBilingualFactValidator(unittest.TestCase):

    def setUp(self):
        self.validator = BilingualFactValidator()
        self.source_ev_dummy = SourceEvidence(
            exact_quote="测试证据引用",
            source_url="https://news.seehua.com/post/test",
            publisher="诗华日报",
            retrieved_at="2026-11-09T10:00:00+08:00"
        )

    # -------------------------------------------------------------------------
    # 1. Calendar and Weekday Consistency (C-7)
    # -------------------------------------------------------------------------
    def test_01_calendar_weekday_verification(self):
        # 7 November 2026 is Saturday (5)
        valid, msg = self.validator.validate_calendar_weekday(2026, 11, 7, 5)
        self.assertTrue(valid)
        self.assertIsNone(msg)

        # Claiming 7 November 2026 is Friday (4) MUST FAIL
        valid, msg = self.validator.validate_calendar_weekday(2026, 11, 7, 4)
        self.assertFalse(valid)
        self.assertIn("Calendar contradiction", msg)
        self.assertIn("Saturday/Sabtu, not Friday/Jumaat", msg)

        # 8 November 2026 is Sunday (6)
        valid, _ = self.validator.validate_calendar_weekday(2026, 11, 8, 6)
        self.assertTrue(valid)

        # 13 November 2026 is Friday (4)
        valid, _ = self.validator.validate_calendar_weekday(2026, 11, 13, 4)
        self.assertTrue(valid)

    # -------------------------------------------------------------------------
    # 2. Strict Fact Status Model (C-8)
    # -------------------------------------------------------------------------
    def test_02_unverified_fact_reference_rejected(self):
        canonical_facts = {
            "FACT_UNVERIFIED_CLAIM": FactItem(
                fact_id="FACT_UNVERIFIED_CLAIM",
                category=FactCategory.MONETARY,
                normalized_value=NormalizedMonetaryValue(amount_myr=1000000),
                semantic_state=SemanticLifecycleState.APPROVED_ALLOCATION,
                source_evidence=self.source_ev_dummy,
                status=FactStatus.UNVERIFIED  # Not VERIFIED!
            )
        }
        claim = ClaimRecord(
            claim_id="CLM_001",
            fact_ids=["FACT_UNVERIFIED_CLAIM"],
            semantic_state=SemanticLifecycleState.APPROVED_ALLOCATION,
            zh_text="政府批准了100万令吉拨款。",
            bm_text="Kerajaan meluluskan peruntukan RM1 juta."
        )
        valid, errors = self.validator.validate_mixed_fact_claim(claim, canonical_facts)
        self.assertFalse(valid)
        self.assertTrue(any("unverified fact" in e.lower() for e in errors))

    # -------------------------------------------------------------------------
    # 3. Monetary Extractors & Currency Normalization
    # -------------------------------------------------------------------------
    def test_03_monetary_extraction_parity(self):
        zh_text = "沙巴获批900万令吉总拨款，其中哥隆孔获得50万令吉，市议会带来约235万8000令吉经济效益与1000令吉消费。"
        bm_text = "Sabah diluluskan RM9 juta, manakala Golongkong menerima RM500,000 serta impak RM2,358,000 dan RM1,000."

        zh_vals = self.validator.extract_monetary_values_zh(zh_text)
        bm_vals = self.validator.extract_monetary_values_bm(bm_text)

        self.assertIn(9000000, zh_vals)
        self.assertIn(500000, zh_vals)
        self.assertIn(2358000, zh_vals)
        self.assertIn(1000, zh_vals)

        self.assertIn(9000000, bm_vals)
        self.assertIn(500000, bm_vals)
        self.assertIn(2358000, bm_vals)
        self.assertIn(1000, bm_vals)

        self.assertEqual(set(zh_vals), set(bm_vals))

    # -------------------------------------------------------------------------
    # 4. Mixed-Fact Claim: Independent Semantic-State Verification (C-10)
    # -------------------------------------------------------------------------
    def test_04_mixed_fact_semantic_state_violation(self):
        canonical_facts = {
            "FACT_KAM_GRANT": FactItem(
                fact_id="FACT_KAM_GRANT",
                category=FactCategory.MONETARY,
                normalized_value=NormalizedMonetaryValue(amount_myr=500000),
                semantic_state=SemanticLifecycleState.APPROVED_ALLOCATION,
                source_evidence=self.source_ev_dummy,
                status=FactStatus.VERIFIED
            ),
            "FACT_KAM_PROJECTS": FactItem(
                fact_id="FACT_KAM_PROJECTS",
                category=FactCategory.QUANTITY_ENTITY,
                normalized_value=NormalizedQuantityValue(count=4, unit="projects"),
                semantic_state=SemanticLifecycleState.PROJECT_COMPLETED,
                source_evidence=self.source_ev_dummy,
                status=FactStatus.VERIFIED
            )
        }

        # Case A: BM improperly claims grant was spent ("telah membelanjakan RM500,000")
        bad_claim_bm = ClaimRecord(
            claim_id="CLM_BAD_01",
            fact_ids=["FACT_KAM_GRANT", "FACT_KAM_PROJECTS"],
            semantic_state=SemanticLifecycleState.PROJECT_COMPLETED,
            zh_text="甘榜哥隆孔获得50万令吉拨款，并已完成4项工程。",
            bm_text="Kampung Golongkong telah membelanjakan RM500,000 untuk menyiapkan empat projek asas."
        )
        valid, errors = self.validator.validate_mixed_fact_claim(bad_claim_bm, canonical_facts)
        self.assertFalse(valid)
        self.assertTrue(any("semantic distortion" in e for e in errors))
        self.assertTrue(any("telah membelanjakan" in e for e in errors))

        # Case B: Accurate phrasing without spending conflation MUST PASS
        good_claim = ClaimRecord(
            claim_id="CLM_GOOD_01",
            fact_ids=["FACT_KAM_GRANT", "FACT_KAM_PROJECTS"],
            semantic_state=SemanticLifecycleState.PROJECT_COMPLETED,
            zh_text="甘榜哥隆孔获批50万令吉拨款，并已成功完成4项基础设施工程。",
            bm_text="Kampung Golongkong menerima peruntukan RM500,000 dan telah berjaya menyiapkan empat projek infrastruktur asas."
        )
        valid, errors = self.validator.validate_mixed_fact_claim(good_claim, canonical_facts)
        self.assertTrue(valid, f"Expected valid but got: {errors}")

    # -------------------------------------------------------------------------
    # 5. Headline Fact-Binding & Unanchored Token Rejection
    # -------------------------------------------------------------------------
    def test_05_headline_unanchored_number_rejected(self):
        canonical_facts = {
            "FACT_BUDGET_DATE": FactItem(
                fact_id="FACT_BUDGET_DATE",
                category=FactCategory.TEMPORAL_DATE,
                normalized_value=NormalizedDateValue(year=2026, month=12, day=4, weekday=4),
                semantic_state=SemanticLifecycleState.EVENT_SCHEDULED,
                source_evidence=self.source_ev_dummy,
                status=FactStatus.VERIFIED
            )
        }
        # Injected monetary number in headline not in canonical facts
        headline_unanchored = HeadlineRecord(
            zh_text="沙巴预算案12月4日提呈 拟拨款80亿令吉解决水电",
            bm_text="Belanjawan Sabah Dibentang 4 Disember Peruntukan RM8 bilion",
            fact_ids=["FACT_BUDGET_DATE"]
        )
        valid, errors = self.validator.validate_headline(headline_unanchored, canonical_facts)
        self.assertFalse(valid)
        self.assertTrue(any("unanchored monetary value" in e for e in errors))

    # -------------------------------------------------------------------------
    # 6. Narrative Context & Stylistic Transitions Validation
    # -------------------------------------------------------------------------
    def test_06_stylistic_transition_factual_injection_rejected(self):
        # Stylistic transition attempting to inject an unmapped number
        bad_transitions = StylisticTransitions(
            zh_connector="在宣布拨出50万之后，",
            bm_connector="Selepas peruntukan RM500,000 diumumkan, "
        )
        valid, err = self.validator.validate_stylistic_transitions(bad_transitions)
        self.assertFalse(valid)
        self.assertIn("Factual token (digit) detected", err)

        # Clean transition with zero digits or currency symbols
        good_transitions = StylisticTransitions(
            zh_connector="较早前，",
            bm_connector="Terdahulu, "
        )
        valid, err = self.validator.validate_stylistic_transitions(good_transitions)
        self.assertTrue(valid)
        self.assertIsNone(err)

    # -------------------------------------------------------------------------
    # 7. Phase D-3 Regression: Article 3 (KAM Rural Allocation Mismatch)
    # -------------------------------------------------------------------------
    def test_07_regression_d3_article3_rejection_and_fix(self):
        canonical_facts = {
            "FACT_KAM_STATE_TOTAL_MYR": FactItem(
                fact_id="FACT_KAM_STATE_TOTAL_MYR",
                category=FactCategory.MONETARY,
                normalized_value=NormalizedMonetaryValue(amount_myr=9000000),
                semantic_state=SemanticLifecycleState.APPROVED_ALLOCATION,
                source_evidence=self.source_ev_dummy,
                status=FactStatus.VERIFIED
            ),
            "FACT_KAM_VILLAGE_GRANT_MYR": FactItem(
                fact_id="FACT_KAM_VILLAGE_GRANT_MYR",
                category=FactCategory.MONETARY,
                normalized_value=NormalizedMonetaryValue(amount_myr=500000),
                semantic_state=SemanticLifecycleState.APPROVED_ALLOCATION,
                source_evidence=self.source_ev_dummy,
                status=FactStatus.VERIFIED
            ),
            "FACT_PERSON_MUSTAPHA": FactItem(
                fact_id="FACT_PERSON_MUSTAPHA",
                category=FactCategory.ENTITY_PERSON,
                normalized_value="mustapha_sakmud",
                semantic_state=SemanticLifecycleState.INFORMATIONAL,
                source_evidence=self.source_ev_dummy,
                status=FactStatus.VERIFIED
            ),
            "FACT_ORG_KAM": FactItem(
                fact_id="FACT_ORG_KAM",
                category=FactCategory.ENTITY_ORGANIZATION,
                normalized_value="kam",
                semantic_state=SemanticLifecycleState.INFORMATIONAL,
                source_evidence=self.source_ev_dummy,
                status=FactStatus.VERIFIED
            )
        }

        # The EXACT D-3 failure output: BM drifted to RM9.1 juta and RM900,000!
        raw_d3_failed_article = StructuredArticle(
            article_id="d3_article_3_failed",
            category="sabah_rural",
            headline=HeadlineRecord(
                zh_text="沙巴今年18村获批昌明领养甘榜计划 穆斯达法：获900万建设基础设施",
                bm_text="18 Kampung di Sabah Diluluskan Program Kampung Angkat Madani, Peruntukan RM9.1 Juta",
                fact_ids=["FACT_KAM_STATE_TOTAL_MYR", "FACT_PERSON_MUSTAPHA", "FACT_ORG_KAM"]
            ),
            core_claims=[
                ClaimRecord(
                    claim_id="CLM_01",
                    fact_ids=["FACT_KAM_STATE_TOTAL_MYR", "FACT_PERSON_MUSTAPHA", "FACT_ORG_KAM"],
                    semantic_state=SemanticLifecycleState.APPROVED_ALLOCATION,
                    zh_text="沙巴今年共有18个甘榜获批参与昌明领养甘榜计划，总拨款额达900万令吉。",
                    bm_text="Sebanyak 18 buah kampung di Sabah telah diluluskan dengan peruntukan keseluruhan berjumlah RM9.1 juta."
                ),
                ClaimRecord(
                    claim_id="CLM_02",
                    fact_ids=["FACT_KAM_VILLAGE_GRANT_MYR"],
                    semantic_state=SemanticLifecycleState.APPROVED_ALLOCATION,
                    zh_text="哥打马鲁都甘榜哥隆孔获得50万令吉拨款用于基础设施。",
                    bm_text="Kampung Golongkong di Kota Marudu menerima peruntukan RM900,000 bagi infrastruktur."
                )
            ]
        )

        res = self.validator.validate_structured_article(raw_d3_failed_article, canonical_facts)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.status, "REVIEW_REQUIRED")
        # Must detect RM9.1m drift and RM900k drift
        self.assertTrue(any("9100000" in e for e in res.errors))
        self.assertTrue(any("900000" in e for e in res.errors))

        # Assembler must return None for failed article
        assembled = self.validator.assemble_legacy_article(raw_d3_failed_article, res)
        self.assertIsNone(assembled)

        # Corrected D-3 Article 3 (Both languages locked to RM9M and RM500k)
        corrected_d3_article = StructuredArticle(
            article_id="d3_article_3_corrected",
            category="sabah_rural",
            headline=HeadlineRecord(
                zh_text="沙巴今年18村获批昌明领养甘榜计划 穆斯达法：获900万建设基础设施",
                bm_text="18 Kampung di Sabah Diluluskan Program Kampung Angkat Madani, Peruntukan RM9 Juta",
                fact_ids=["FACT_KAM_STATE_TOTAL_MYR", "FACT_PERSON_MUSTAPHA", "FACT_ORG_KAM"]
            ),
            core_claims=[
                ClaimRecord(
                    claim_id="CLM_01",
                    fact_ids=["FACT_KAM_STATE_TOTAL_MYR", "FACT_PERSON_MUSTAPHA", "FACT_ORG_KAM"],
                    semantic_state=SemanticLifecycleState.APPROVED_ALLOCATION,
                    zh_text="沙巴今年共有18个甘榜获批参与昌明领养甘榜计划，总拨款额达900万令吉。",
                    bm_text="Sebanyak 18 buah kampung di Sabah telah diluluskan dengan peruntukan keseluruhan berjumlah RM9 juta."
                ),
                ClaimRecord(
                    claim_id="CLM_02",
                    fact_ids=["FACT_KAM_VILLAGE_GRANT_MYR"],
                    semantic_state=SemanticLifecycleState.APPROVED_ALLOCATION,
                    zh_text="哥打马鲁都甘榜哥隆孔获得50万令吉拨款用于基础设施。",
                    bm_text="Kampung Golongkong di Kota Marudu menerima peruntukan RM500,000 bagi infrastruktur."
                )
            ]
        )
        res_corr = self.validator.validate_structured_article(corrected_d3_article, canonical_facts)
        self.assertTrue(res_corr.is_valid, f"Expected valid, got errors: {res_corr.errors}")
        self.assertEqual(res_corr.status, "VERIFIED")

        # Assembler succeeds on verified article
        assembled_corr = self.validator.assemble_legacy_article(corrected_d3_article, res_corr)
        self.assertIsNotNone(assembled_corr)
        self.assertEqual(assembled_corr["validation_status"], "VERIFIED")
        self.assertIn("900万令吉", assembled_corr["detail"])
        self.assertIn("RM9 juta", assembled_corr["detailBM"])

    # -------------------------------------------------------------------------
    # 8. Phase D-3 Regression: Article 1 (Sandakan SKTS Date Disambiguation)
    # -------------------------------------------------------------------------
    def test_08_regression_d3_article1_date_disambiguation(self):
        canonical_facts = {
            "FACT_SKTS_EDITION": FactItem(
                fact_id="FACT_SKTS_EDITION",
                category=FactCategory.EDITION,
                normalized_value=NormalizedEditionValue(edition=14),
                semantic_state=SemanticLifecycleState.EVENT_ONGOING,
                source_evidence=self.source_ev_dummy,
                status=FactStatus.VERIFIED
            ),
            "FACT_SKTS_ECONOMIC_IMPACT": FactItem(
                fact_id="FACT_SKTS_ECONOMIC_IMPACT",
                category=FactCategory.MONETARY,
                normalized_value=NormalizedMonetaryValue(amount_myr=2358000),
                semantic_state=SemanticLifecycleState.INFORMATIONAL,
                source_evidence=self.source_ev_dummy,
                status=FactStatus.VERIFIED
            ),
            "FACT_SKTS_OPENING_DATE": FactItem(
                fact_id="FACT_SKTS_OPENING_DATE",
                category=FactCategory.TEMPORAL_DATE,
                normalized_value=NormalizedDateValue(year=2026, month=11, day=7, weekday=5),
                semantic_state=SemanticLifecycleState.CEREMONY_CONCLUDED,
                source_evidence=self.source_ev_dummy,
                status=FactStatus.VERIFIED
            )
        }

        # D-3 Flaw: Claiming opening took place on "Jumaat, 7 November 2026" (contradiction)
        bad_article_1 = StructuredArticle(
            article_id="d3_article_1_bad_weekday",
            category="sandakan",
            headline=HeadlineRecord(
                zh_text="沙巴地政运动会山打根开幕 注入约235万8000令吉商机",
                bm_text="Sukan PBT Sabah Dirasmikan di Sandakan, Bawa Impak RM2,358,000",
                fact_ids=["FACT_SKTS_ECONOMIC_IMPACT"]
            ),
            core_claims=[
                ClaimRecord(
                    claim_id="CLM_01",
                    fact_ids=["FACT_SKTS_OPENING_DATE", "FACT_SKTS_ECONOMIC_IMPACT"],
                    semantic_state=SemanticLifecycleState.CEREMONY_CONCLUDED,
                    zh_text="第14届沙巴州地方政府运动会昨晚在山打根开幕，预计带来约235万8000令吉经济效益。",
                    bm_text="Sukan PBT Sabah Ke-14 dirasmikan pada Jumaat, 7 November 2026 di Sandakan dan dijangka membawa impak RM2,358,000."
                )
            ]
        )
        res_bad = self.validator.validate_structured_article(bad_article_1, canonical_facts)
        self.assertFalse(res_bad.is_valid)
        self.assertTrue(any("Saturday/Sabtu, not Friday/Jumaat" in e for e in res_bad.errors))

        # Corrected Article 1: Saturday 7 November 2026 ("Sabtu, 7 November 2026")
        good_article_1 = StructuredArticle(
            article_id="d3_article_1_good",
            category="sandakan",
            headline=HeadlineRecord(
                zh_text="沙巴地政运动会山打根开幕 注入约235万8000令吉商机",
                bm_text="Sukan PBT Sabah Dirasmikan di Sandakan, Bawa Impak RM2,358,000",
                fact_ids=["FACT_SKTS_ECONOMIC_IMPACT"]
            ),
            core_claims=[
                ClaimRecord(
                    claim_id="CLM_01",
                    fact_ids=["FACT_SKTS_OPENING_DATE", "FACT_SKTS_ECONOMIC_IMPACT"],
                    semantic_state=SemanticLifecycleState.CEREMONY_CONCLUDED,
                    zh_text="第14届沙巴州地方政府运动会昨晚在山打根开幕，预计带来约235万8000令吉经济效益。",
                    bm_text="Sukan PBT Sabah Ke-14 dirasmikan pada Sabtu, 7 November 2026 di Sandakan dan dijangka membawa impak RM2,358,000."
                )
            ]
        )
        res_good = self.validator.validate_structured_article(good_article_1, canonical_facts)
        self.assertTrue(res_good.is_valid, f"Expected valid, got errors: {res_good.errors}")

    # -------------------------------------------------------------------------
    # 9. Phase D-3 Regression: Article 2 (Sabah Budget 2027 Tabling)
    # -------------------------------------------------------------------------
    def test_09_regression_d3_article2_budget_pass(self):
        canonical_facts = {
            "FACT_BUDGET_TABLING_DATE": FactItem(
                fact_id="FACT_BUDGET_TABLING_DATE",
                category=FactCategory.TEMPORAL_DATE,
                normalized_value=NormalizedDateValue(year=2026, month=12, day=4, weekday=4),  # 4 Dec 2026 is Friday
                semantic_state=SemanticLifecycleState.EVENT_SCHEDULED,
                source_evidence=self.source_ev_dummy,
                status=FactStatus.VERIFIED
            ),
            "FACT_PERSON_HAJIJI": FactItem(
                fact_id="FACT_PERSON_HAJIJI",
                category=FactCategory.ENTITY_PERSON,
                normalized_value="hajiji",
                semantic_state=SemanticLifecycleState.INFORMATIONAL,
                source_evidence=self.source_ev_dummy,
                status=FactStatus.VERIFIED
            )
        }

        article_2 = StructuredArticle(
            article_id="d3_article_2_budget",
            category="sabah",
            headline=HeadlineRecord(
                zh_text="沙巴预算案12月4日提呈 哈芝芝：着重解决民生问题",
                bm_text="Belanjawan Sabah 2027 Dibentang 4 Disember, Hajiji: Tumpu Masalah Rakyat",
                fact_ids=["FACT_BUDGET_TABLING_DATE", "FACT_PERSON_HAJIJI"]
            ),
            core_claims=[
                ClaimRecord(
                    claim_id="CLM_01",
                    fact_ids=["FACT_BUDGET_TABLING_DATE", "FACT_PERSON_HAJIJI"],
                    semantic_state=SemanticLifecycleState.EVENT_SCHEDULED,
                    zh_text="首席部长哈芝芝诺表示，2027年沙巴财政预算案定于12月4日提呈，将重点解决水供与道路问题。",
                    bm_text="Ketua Menteri Datuk Seri Hajiji Noor menyatakan Belanjawan Sabah 2027 dijadualkan dibentangkan pada 4 Disember ini."
                )
            ]
        )
        res = self.validator.validate_structured_article(article_2, canonical_facts)
        self.assertTrue(res.is_valid, f"Expected valid, got errors: {res.errors}")

    # =========================================================================
    # PHASE D-7 NEW MANDATORY TESTS (Tests 10 - 21)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 10. Identical Hallucinated Monetary Values in ZH and BM (P0-1 Bypass Check)
    # -------------------------------------------------------------------------
    def test_10_identical_hallucinated_monetary_values_rejected(self):
        # Both ZH and BM assert "80亿令吉" / "RM8 bilion", BUT canonical facts only has RM9M!
        canonical_facts = {
            "FACT_VALID_9M": FactItem(
                fact_id="FACT_VALID_9M",
                category=FactCategory.MONETARY,
                normalized_value=NormalizedMonetaryValue(amount_myr=9000000),
                semantic_state=SemanticLifecycleState.APPROVED_ALLOCATION,
                source_evidence=self.source_ev_dummy,
                status=FactStatus.VERIFIED
            )
        }
        hallucinated_article = StructuredArticle(
            article_id="art_hallucinated_money",
            category="sabah",
            headline=HeadlineRecord(
                zh_text="沙巴宣布拨款80亿令吉用于基建",
                bm_text="Sabah Mengumumkan Peruntukan RM8 bilion bagi Infrastruktur",
                fact_ids=["FACT_VALID_9M"]
            ),
            core_claims=[
                ClaimRecord(
                    claim_id="CLM_01",
                    fact_ids=["FACT_VALID_9M"],
                    semantic_state=SemanticLifecycleState.APPROVED_ALLOCATION,
                    zh_text="政府宣布拨款80亿令吉推进沙巴全境基建。",
                    bm_text="Kerajaan mengumumkan peruntukan RM8 bilion untuk pembangunan Sabah."
                )
            ]
        )
        res = self.validator.validate_structured_article(hallucinated_article, canonical_facts)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("unanchored monetary value" in e for e in res.errors))

    # -------------------------------------------------------------------------
    # 11. Unsupported Named Person in Headline (P1-5)
    # -------------------------------------------------------------------------
    def test_11_unsupported_named_person_in_headline_rejected(self):
        canonical_facts = {}
        # Headline introduces "安华" / "Anwar" without declaring fact_id
        bad_headline_article = StructuredArticle(
            article_id="art_unsupported_person",
            category="national",
            headline=HeadlineRecord(
                zh_text="首相安华宣布沙巴发展计划",
                bm_text="Perdana Menteri Anwar Mengumumkan Pembangunan Sabah",
                fact_ids=[]
            ),
            core_claims=[]
        )
        res = self.validator.validate_structured_article(bad_headline_article, canonical_facts)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("unanchored named person" in e for e in res.errors))

    # -------------------------------------------------------------------------
    # 12. Unsupported Agency in Headline (P1-5)
    # -------------------------------------------------------------------------
    def test_12_unsupported_agency_in_headline_rejected(self):
        canonical_facts = {}
        # Headline introduces "山打根市议会" / "MPS" without declaring fact_id
        bad_agency_article = StructuredArticle(
            article_id="art_unsupported_agency",
            category="sandakan",
            headline=HeadlineRecord(
                zh_text="山打根市议会通告低风险商业营业执照新规",
                bm_text="MPS Mengumumkan Notis Baharu Perniagaan Berisiko Rendah",
                fact_ids=[]
            ),
            core_claims=[]
        )
        res = self.validator.validate_structured_article(bad_agency_article, canonical_facts)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("unanchored agency" in e for e in res.errors))

    # -------------------------------------------------------------------------
    # 13. Allocation Rewritten as Expenditure using Malay Passive Voice (P1-7)
    # -------------------------------------------------------------------------
    def test_13_allocation_rewritten_as_expenditure_malay_passive_rejected(self):
        canonical_facts = {
            "FACT_GRANT": FactItem(
                fact_id="FACT_GRANT",
                category=FactCategory.MONETARY,
                normalized_value=NormalizedMonetaryValue(amount_myr=500000),
                semantic_state=SemanticLifecycleState.APPROVED_ALLOCATION,
                source_evidence=self.source_ev_dummy,
                status=FactStatus.VERIFIED
            )
        }
        # Passive voice: "peruntukan RM500,000 telah disalurkan / dibelanjakan sepenuhnya"
        claim_passive = ClaimRecord(
            claim_id="CLM_PASSIVE_BM",
            fact_ids=["FACT_GRANT"],
            semantic_state=SemanticLifecycleState.APPROVED_ALLOCATION,
            zh_text="甘榜哥隆孔获得50万令吉拨款。",
            bm_text="Peruntukan RM500,000 telah disalurkan dan dibelanjakan untuk projek kampung."
        )
        valid, errors = self.validator.validate_mixed_fact_claim(claim_passive, canonical_facts)
        self.assertFalse(valid)
        self.assertTrue(any("semantic distortion" in e for e in errors))

    # -------------------------------------------------------------------------
    # 14. Allocation Rewritten as Expenditure using Chinese Passive Voice (P1-7)
    # -------------------------------------------------------------------------
    def test_14_allocation_rewritten_as_expenditure_chinese_passive_rejected(self):
        canonical_facts = {
            "FACT_GRANT": FactItem(
                fact_id="FACT_GRANT",
                category=FactCategory.MONETARY,
                normalized_value=NormalizedMonetaryValue(amount_myr=500000),
                semantic_state=SemanticLifecycleState.APPROVED_ALLOCATION,
                source_evidence=self.source_ev_dummy,
                status=FactStatus.VERIFIED
            )
        }
        # Chinese passive voice: "50万令吉拨款已被动用"
        claim_passive_zh = ClaimRecord(
            claim_id="CLM_PASSIVE_ZH",
            fact_ids=["FACT_GRANT"],
            semantic_state=SemanticLifecycleState.APPROVED_ALLOCATION,
            zh_text="甘榜哥隆孔获批50万令吉拨款已被动用于工程建设。",
            bm_text="Peruntukan RM500,000 bagi Kampung Golongkong diluluskan untuk projek asas."
        )
        valid, errors = self.validator.validate_mixed_fact_claim(claim_passive_zh, canonical_facts)
        self.assertFalse(valid)
        self.assertTrue(any("semantic distortion" in e for e in errors))

    # -------------------------------------------------------------------------
    # 15. SourceEvidence Quote Not Found in Raw Text (P0-4 Provenance)
    # -------------------------------------------------------------------------
    def test_15_source_evidence_quote_not_found_in_raw_text_rejected(self):
        raw_article_body = "首席部长拿督斯里哈芝芝诺今日说，定于下月4日提呈2027年沙巴财政预算案。"
        
        # Fact claiming a quote that does NOT exist in raw_article_body
        invented_fact = FactItem(
            fact_id="FACT_INVENTED_QUOTE",
            category=FactCategory.MONETARY,
            normalized_value=NormalizedMonetaryValue(amount_myr=9000000),
            semantic_state=SemanticLifecycleState.APPROVED_ALLOCATION,
            source_evidence=SourceEvidence(
                exact_quote="这句名言完全不在原文中出现",
                source_url="https://news.seehua.com/post/1601838/",
                publisher="诗华日报",
                retrieved_at="2026-11-09T10:00:00+08:00"
            ),
            status=FactStatus.EXTRACTED
        )
        valid, err = self.validator.validate_evidence_provenance(invented_fact, raw_article_body)
        self.assertFalse(valid)
        self.assertIn("evidence quote not found in raw source body", err)

        # Fact with exact verbatim quote MUST PASS
        verbatim_fact = FactItem(
            fact_id="FACT_VERBATIM",
            category=FactCategory.TEMPORAL_DATE,
            normalized_value=NormalizedDateValue(year=2026, month=12, day=4, weekday=4),
            semantic_state=SemanticLifecycleState.EVENT_SCHEDULED,
            source_evidence=SourceEvidence(
                exact_quote="定于下月4日提呈2027年沙巴财政预算案",
                source_url="https://news.seehua.com/post/1601838/",
                publisher="诗华日报",
                retrieved_at="2026-11-09T10:00:00+08:00"
            ),
            status=FactStatus.EXTRACTED
        )
        valid_v, err_v = self.validator.validate_evidence_provenance(verbatim_fact, raw_article_body)
        self.assertTrue(valid_v)
        self.assertIsNone(err_v)

    # -------------------------------------------------------------------------
    # 16. Track B Narrative Bypass Attempt (P0-2)
    # -------------------------------------------------------------------------
    def test_16_track_b_narrative_bypass_attempt_rejected(self):
        canonical_facts = {}
        # Track B attempting to inject an unanchored narrative claim with unverified numbers
        bypass_article = StructuredArticle(
            article_id="track_b_bypass",
            category="sabah",
            headline=HeadlineRecord(zh_text="沙巴民生改善动态", bm_text="Perkembangan Kebajikan Sabah", fact_ids=[]),
            core_claims=[],
            narrative_claims=[
                NarrativeClaimRecord(
                    claim_id="CLM_NAR_01",
                    fact_ids=["FACT_NON_EXISTENT"],
                    semantic_state=SemanticLifecycleState.INFORMATIONAL,
                    zh_text="据了解该项目涉及200万令吉资金。",
                    bm_text="Projek berkenaan membabitkan RM2 juta."
                )
            ]
        )
        res = self.validator.validate_structured_article(bypass_article, canonical_facts)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("references unknown fact_id" in e for e in res.errors))

    # -------------------------------------------------------------------------
    # 17. Utilities and Events Secondary Payload Protection (P1-6)
    # -------------------------------------------------------------------------
    def test_17_utilities_and_events_unanchored_claims_rejected(self):
        # 1. Utility card with monetary discrepancy
        bad_card = {
            "id": "W",
            "title": "水务局斗湖水管抢修",
            "issue": "抢修耗资50万令吉更换主管道。",
            "issueBM": "Pembaikan paip membabitkan kos RM900,000.",
            "source_timestamp": "2026-11-09 10:00"
        }
        v_card, errs_card = self.validator.validate_utility_card(bad_card)
        self.assertFalse(v_card)
        self.assertTrue(any("monetary discrepancy" in e for e in errs_card))

        # 2. Event with invalid calendar date
        bad_event = {
            "name": "沙巴生态科普日",
            "full_date": "2026-02-30",  # Impossible calendar date!
            "desc": "门票收费每人100令吉。",
            "descBM": "Tiket berharga RM100 seorang."
        }
        v_ev, errs_ev = self.validator.validate_future_event(bad_event)
        self.assertFalse(v_ev)
        self.assertTrue(any("invalid calendar date" in e for e in errs_ev))

    # -------------------------------------------------------------------------
    # 18. Year-Only Fact Expanded into Date Range (P1-8)
    # -------------------------------------------------------------------------
    def test_18_year_only_fact_expanded_into_date_range_rejected(self):
        year_fact = FactItem(
            fact_id="FACT_TOURISM_YEAR",
            category=FactCategory.TEMPORAL_YEAR,
            normalized_value=2027,
            semantic_state=SemanticLifecycleState.EVENT_SCHEDULED,
            source_evidence=self.source_ev_dummy,
            status=FactStatus.VERIFIED
        )
        # Attempt to inflate "2027" to "1月1日至12月31日"
        zh_inflated = "迎接2027年沙巴旅游年（1月1日至12月31日）。"
        bm_inflated = "Menyambut Tahun Melawat Sabah 2027 (1 Januari hingga 31 Disember)."

        valid, err = self.validator.validate_temporal_precision(year_fact, zh_inflated, bm_inflated)
        self.assertFalse(valid)
        self.assertIn("precision YEAR_ONLY (2027) but claim inflated it to full date range", err)

    # -------------------------------------------------------------------------
    # 19. Synthesizer Rejects Sub-12 Articles from Track A (P0-3 Threshold Unification)
    # -------------------------------------------------------------------------
    def test_19_synthesizer_rejects_sub_12_articles_from_track_a(self):
        config = {
            "system": {
                "min_headlines_threshold": 12
            }
        }
        synthesizer = NewsSynthesizer(config)
        self.assertEqual(synthesizer.min_headlines_threshold, 12)

        # Mock Track A returning 10 articles (below threshold of 12)
        mock_10_articles = [
            {"title": f"新闻{i}", "titleBM": f"Berita{i}", "detail": "内容", "detailBM": "Kandungan"}
            for i in range(10)
        ]

        with patch.object(synthesizer, "synthesize_track_a_single_batch", return_value=mock_10_articles):
            results = synthesizer.synthesize("2026-11-09", articles=[], api_key="test_key")
            # Track A with 10 articles must NOT be returned when threshold is 12; fails closed to 0 articles
            self.assertEqual(results, [])

    # -------------------------------------------------------------------------
    # 20. Both Tracks Reject the Same Invalid Structured Article (Parity Gate)
    # -------------------------------------------------------------------------
    def test_20_both_tracks_reject_same_invalid_article(self):
        config = {"system": {"min_headlines_threshold": 12}}
        synthesizer = NewsSynthesizer(config)

        # Article with monetary mismatch: ZH=900万 vs BM=RM9.1 juta
        bad_art = {
            "title": "沙巴昌明领养甘榜计划",
            "titleBM": "Program Kampung Angkat Madani",
            "detail": "拨款总额达900万令吉。",
            "detailBM": "Peruntukan berjumlah RM9.1 juta."
        }
        is_valid, errors = synthesizer.validate_article_parity(bad_art)
        self.assertFalse(is_valid)
        self.assertTrue(any("monetary" in e.lower() for e in errors))

    # -------------------------------------------------------------------------
    # 21. Every Persistence Path Requires Successful Validation
    # -------------------------------------------------------------------------
    def test_21_every_persistence_path_requires_validation(self):
        bad_article = StructuredArticle(
            article_id="bad_art",
            category="sabah",
            headline=HeadlineRecord(zh_text="错位标题", bm_text="Tajuk Salah", fact_ids=[]),
            core_claims=[
                ClaimRecord(
                    claim_id="CLM_01",
                    fact_ids=["FACT_NON_EXIST"],
                    semantic_state=SemanticLifecycleState.INFORMATIONAL,
                    zh_text="虚假声明",
                    bm_text="Kenyataan palsu"
                )
            ]
        )
        res = self.validator.validate_structured_article(bad_article, {})
        # Output assembler must return None, preventing persistence to news_data.json
        assembled = self.validator.assemble_legacy_article(bad_article, res)
        self.assertIsNone(assembled)


if __name__ == "__main__":
    unittest.main()
