"""Tests for award aggregation functions."""

import pytest
from cdfifund.analysis.aggregations import (
    by_program,
    by_state,
    by_year,
    by_recipient_type,
    top_recipients,
    geographic_distribution,
    cumulative_awards_over_time,
)


class TestByProgram:
    def test_returns_dict(self, sample_awards):
        result = by_program(sample_awards)
        assert isinstance(result, dict)

    def test_all_programs_represented(self, sample_awards):
        result = by_program(sample_awards)
        assert len(result) >= 5

    def test_count_and_total_positive(self, sample_awards):
        result = by_program(sample_awards)
        for prog, data in result.items():
            assert data["count"] > 0
            assert data["total_amount"] > 0

    def test_average_award_correct(self, sample_awards):
        result = by_program(sample_awards)
        for prog, data in result.items():
            assert abs(data["average_award"] - data["total_amount"] / data["count"]) < 0.01


class TestByState:
    def test_sorted_by_total_descending(self, sample_awards):
        result = by_state(sample_awards)
        totals = [v["total_amount"] for v in result.values()]
        assert totals == sorted(totals, reverse=True)

    def test_multiple_states(self, sample_awards):
        result = by_state(sample_awards)
        assert len(result) >= 5

    def test_all_amounts_positive(self, sample_awards):
        result = by_state(sample_awards)
        for st, data in result.items():
            assert data["total_amount"] > 0


class TestByYear:
    def test_sorted_by_year_ascending(self, sample_awards):
        result = by_year(sample_awards)
        years = list(result.keys())
        assert years == sorted(years)

    def test_multiple_years(self, sample_awards):
        result = by_year(sample_awards)
        assert len(result) >= 3

    def test_totals_positive(self, sample_awards):
        result = by_year(sample_awards)
        for yr, data in result.items():
            assert data["total_amount"] > 0


class TestByRecipientType:
    def test_returns_dict(self, sample_awards):
        result = by_recipient_type(sample_awards)
        assert isinstance(result, dict)

    def test_loan_fund_present(self, sample_awards):
        result = by_recipient_type(sample_awards)
        assert "loan_fund" in result

    def test_all_counts_positive(self, sample_awards):
        result = by_recipient_type(sample_awards)
        for rt, data in result.items():
            assert data["count"] > 0


class TestTopRecipients:
    def test_returns_list(self, sample_awards):
        result = top_recipients(sample_awards)
        assert isinstance(result, list)

    def test_sorted_by_total_descending(self, sample_awards):
        result = top_recipients(sample_awards, n=5)
        totals = [r["total_amount"] for r in result]
        assert totals == sorted(totals, reverse=True)

    def test_n_parameter(self, sample_awards):
        result = top_recipients(sample_awards, n=3)
        assert len(result) <= 3

    def test_keys_present(self, sample_awards):
        result = top_recipients(sample_awards)
        for r in result:
            for k in ("recipient_name", "total_amount", "award_count", "programs"):
                assert k in r

    def test_programs_is_list(self, sample_awards):
        result = top_recipients(sample_awards)
        for r in result:
            assert isinstance(r["programs"], list)


class TestGeographicDistribution:
    def test_keys_present(self, sample_awards):
        result = geographic_distribution(sample_awards)
        for k in ("unique_states", "herfindahl_index", "state_shares"):
            assert k in result

    def test_hhi_between_0_and_1(self, sample_awards):
        result = geographic_distribution(sample_awards)
        assert 0.0 <= result["herfindahl_index"] <= 1.0

    def test_state_shares_sum_to_one(self, sample_awards):
        result = geographic_distribution(sample_awards)
        total_share = sum(result["state_shares"].values())
        assert abs(total_share - 1.0) < 1e-9

    def test_top_state_present(self, sample_awards):
        result = geographic_distribution(sample_awards)
        assert result["top_state"] in result["state_shares"]

    def test_empty_list(self):
        result = geographic_distribution([])
        assert result["unique_states"] == 0


class TestCumulativeAwardsOverTime:
    def test_returns_list(self, sample_awards):
        result = cumulative_awards_over_time(sample_awards)
        assert isinstance(result, list)

    def test_sorted_by_year(self, sample_awards):
        result = cumulative_awards_over_time(sample_awards)
        years = [r["year"] for r in result]
        assert years == sorted(years)

    def test_cumulative_increases_monotonically(self, sample_awards):
        result = cumulative_awards_over_time(sample_awards)
        cumulatives = [r["cumulative_amount"] for r in result]
        for i in range(1, len(cumulatives)):
            assert cumulatives[i] >= cumulatives[i - 1]

    def test_keys_present(self, sample_awards):
        result = cumulative_awards_over_time(sample_awards)
        for row in result:
            for k in ("year", "annual_amount", "annual_count", "cumulative_amount"):
                assert k in row
