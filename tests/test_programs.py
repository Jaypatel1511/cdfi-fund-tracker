"""Tests for program-specific analysis modules."""

import pytest
from cdfifund.programs.cdfi_program import cdfi_program_analysis, fa_vs_ta_breakdown
from cdfifund.programs.bea import bea_program_analysis, bank_enterprise_award_breakdown
from cdfifund.programs.native_american import native_american_analysis, naca_breakdown
from cdfifund.programs.bond_guarantee import bond_guarantee_analysis


class TestCDFIProgramAnalysis:
    def test_returns_dict(self, sample_awards):
        result = cdfi_program_analysis(sample_awards)
        assert isinstance(result, dict)

    def test_keys_present(self, sample_awards):
        result = cdfi_program_analysis(sample_awards)
        for k in ("award_count", "total_amount", "average_award", "state_breakdown", "year_breakdown"):
            assert k in result

    def test_count_positive(self, sample_awards):
        result = cdfi_program_analysis(sample_awards)
        assert result["award_count"] > 0

    def test_average_makes_sense(self, sample_awards):
        result = cdfi_program_analysis(sample_awards)
        assert result["average_award"] > 0
        assert result["average_award"] <= result["total_amount"]

    def test_empty_list_returns_zero(self):
        result = cdfi_program_analysis([])
        assert result["award_count"] == 0


class TestFAVsTABreakdown:
    def test_returns_dict(self, sample_awards):
        result = fa_vs_ta_breakdown(sample_awards)
        assert isinstance(result, dict)

    def test_keys_present(self, sample_awards):
        result = fa_vs_ta_breakdown(sample_awards)
        for k in ("fa_count", "ta_count", "fa_total", "ta_total", "fa_pct_of_cdfi_program"):
            assert k in result

    def test_fa_count_positive(self, sample_awards):
        result = fa_vs_ta_breakdown(sample_awards)
        assert result["fa_count"] > 0

    def test_fa_pct_between_0_and_1(self, sample_awards):
        result = fa_vs_ta_breakdown(sample_awards)
        assert 0.0 <= result["fa_pct_of_cdfi_program"] <= 1.0


class TestBEAProgramAnalysis:
    def test_returns_dict(self, sample_awards):
        result = bea_program_analysis(sample_awards)
        assert isinstance(result, dict)

    def test_count_positive(self, sample_awards):
        result = bea_program_analysis(sample_awards)
        assert result["award_count"] > 0

    def test_empty_returns_zero(self):
        result = bea_program_analysis([])
        assert result["award_count"] == 0

    def test_bank_enterprise_breakdown_keys(self, sample_awards):
        result = bank_enterprise_award_breakdown(sample_awards)
        for k in ("by_recipient_type", "total_bea_count", "total_bea_amount"):
            assert k in result


class TestNativeAmericanAnalysis:
    def test_returns_dict(self, sample_awards):
        result = native_american_analysis(sample_awards)
        assert isinstance(result, dict)

    def test_count_positive(self, sample_awards):
        result = native_american_analysis(sample_awards)
        assert result["award_count"] > 0

    def test_naca_breakdown_keys(self, sample_awards):
        result = naca_breakdown(sample_awards)
        for k in ("naca_fa_count", "naca_ta_count", "naca_fa_total", "top_5_states"):
            assert k in result

    def test_top_5_states_list(self, sample_awards):
        result = naca_breakdown(sample_awards)
        assert isinstance(result["top_5_states"], list)
        assert len(result["top_5_states"]) <= 5


class TestBondGuaranteeAnalysis:
    def test_returns_dict(self, sample_awards):
        result = bond_guarantee_analysis(sample_awards)
        assert isinstance(result, dict)

    def test_count_positive(self, sample_awards):
        result = bond_guarantee_analysis(sample_awards)
        assert result["award_count"] > 0

    def test_large_average_size(self, sample_awards):
        result = bond_guarantee_analysis(sample_awards)
        assert result["average_bond_size"] >= 100_000_000

    def test_size_distribution_keys(self, sample_awards):
        result = bond_guarantee_analysis(sample_awards)
        assert "size_distribution" in result
        for k in ("under_200m", "200m_to_500m", "over_500m"):
            assert k in result["size_distribution"]

    def test_empty_returns_zero(self):
        result = bond_guarantee_analysis([])
        assert result["award_count"] == 0
