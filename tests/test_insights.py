"""Tests for award insight analysis."""

import pytest
from cdfifund.analysis.insights import (
    award_concentration_analysis,
    recipient_lifecycle_analysis,
    program_effectiveness_metrics,
)


class TestAwardConcentrationAnalysis:
    def test_keys_present(self, sample_awards):
        result = award_concentration_analysis(sample_awards)
        for k in ("top_10_pct_of_total", "single_recipient_max_pct", "recipient_hhi",
                  "program_hhi", "gini_coefficient", "unique_recipients"):
            assert k in result

    def test_top_10_pct_between_0_and_1(self, sample_awards):
        result = award_concentration_analysis(sample_awards)
        assert 0.0 <= result["top_10_pct_of_total"] <= 1.0

    def test_max_share_between_0_and_1(self, sample_awards):
        result = award_concentration_analysis(sample_awards)
        assert 0.0 <= result["single_recipient_max_pct"] <= 1.0

    def test_hhi_between_0_and_1(self, sample_awards):
        result = award_concentration_analysis(sample_awards)
        assert 0.0 <= result["recipient_hhi"] <= 1.0

    def test_gini_between_0_and_1(self, sample_awards):
        result = award_concentration_analysis(sample_awards)
        assert 0.0 <= result["gini_coefficient"] <= 1.0

    def test_empty_list(self):
        result = award_concentration_analysis([])
        assert result["top_10_pct_of_total"] == 0.0


class TestRecipientLifecycleAnalysis:
    def test_keys_present(self, sample_awards):
        result = recipient_lifecycle_analysis(sample_awards)
        for k in ("unique_recipients", "first_time_recipients", "multi_program_recipients",
                  "repeat_recipients", "average_awards_per_recipient"):
            assert k in result

    def test_unique_recipients_positive(self, sample_awards):
        result = recipient_lifecycle_analysis(sample_awards)
        assert result["unique_recipients"] > 0

    def test_first_time_lte_unique(self, sample_awards):
        result = recipient_lifecycle_analysis(sample_awards)
        assert result["first_time_recipients"] <= result["unique_recipients"]

    def test_average_awards_per_recipient_gte_1(self, sample_awards):
        result = recipient_lifecycle_analysis(sample_awards)
        assert result["average_awards_per_recipient"] >= 1.0

    def test_empty_list(self):
        result = recipient_lifecycle_analysis([])
        assert result["first_time_recipients"] == 0

    def test_program_diversity_distribution(self, sample_awards):
        result = recipient_lifecycle_analysis(sample_awards)
        assert "program_diversity_distribution" in result
        assert all(k >= 1 for k in result["program_diversity_distribution"].keys())


class TestProgramEffectivenessMetrics:
    def test_returns_dict(self, sample_awards):
        result = program_effectiveness_metrics(sample_awards)
        assert isinstance(result, dict)

    def test_program_keys_in_result(self, sample_awards):
        result = program_effectiveness_metrics(sample_awards)
        assert "CDFI_FA" in result
        assert "BGP" in result

    def test_metric_keys_per_program(self, sample_awards):
        result = program_effectiveness_metrics(sample_awards)
        for prog, data in result.items():
            for k in ("full_name", "award_count", "total_amount", "average_award",
                      "geographic_reach_states", "unique_recipients", "top_recipient_share"):
                assert k in data, f"Missing key {k} for program {prog}"

    def test_top_recipient_share_between_0_and_1(self, sample_awards):
        result = program_effectiveness_metrics(sample_awards)
        for prog, data in result.items():
            assert 0.0 <= data["top_recipient_share"] <= 1.0

    def test_geographic_reach_positive(self, sample_awards):
        result = program_effectiveness_metrics(sample_awards)
        for prog, data in result.items():
            assert data["geographic_reach_states"] >= 1
