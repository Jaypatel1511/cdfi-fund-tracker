"""Tests for award data loader."""

import pytest
from cdfifund.data.loader import load_sample_awards, load_from_cdfi_fund_url
from cdfifund.data.schema import Award


class TestLoadSampleAwards:
    def test_returns_list(self):
        awards = load_sample_awards()
        assert isinstance(awards, list)

    def test_non_empty(self):
        awards = load_sample_awards()
        assert len(awards) >= 10

    def test_all_are_awards(self):
        for a in load_sample_awards():
            assert isinstance(a, Award)

    def test_multiple_programs_represented(self):
        awards = load_sample_awards()
        programs = {a.program for a in awards}
        assert len(programs) >= 5

    def test_multiple_years(self):
        awards = load_sample_awards()
        years = {a.award_year for a in awards}
        assert len(years) >= 3

    def test_multiple_states(self):
        awards = load_sample_awards()
        states = {a.state for a in awards}
        assert len(states) >= 5

    def test_bgp_award_large(self):
        awards = load_sample_awards()
        bgp = [a for a in awards if a.program == "BGP"]
        assert len(bgp) > 0
        assert all(a.award_amount >= 100_000_000 for a in bgp)

    def test_positive_amounts(self):
        for a in load_sample_awards():
            assert a.award_amount > 0


class TestLoadFromCDFIFundUrl:
    def test_none_url_returns_sample_data(self):
        awards = load_from_cdfi_fund_url(None)
        assert len(awards) > 0

    def test_invalid_url_falls_back(self):
        awards = load_from_cdfi_fund_url("http://invalid.nonexistent.url/data.json")
        assert isinstance(awards, list)
        assert len(awards) > 0
