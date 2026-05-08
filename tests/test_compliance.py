"""Tests for compliance tracking."""

import pytest
from cdfifund.compliance.tracker import (
    ComplianceTracker,
    track_deployment,
    check_deadlines,
    at_risk_recipients,
)


class TestComplianceTracker:
    def test_at_risk_returns_list(self, compliance_records):
        tracker = ComplianceTracker(compliance_records)
        assert isinstance(tracker.at_risk(), list)

    def test_at_risk_content(self, compliance_records):
        tracker = ComplianceTracker(compliance_records)
        at_risk = tracker.at_risk()
        for r in at_risk:
            assert r.deployment_pct < 0.50

    def test_overdue_returns_list(self, compliance_records):
        tracker = ComplianceTracker(compliance_records)
        assert len(tracker.overdue()) >= 1

    def test_summary_keys(self, compliance_records):
        tracker = ComplianceTracker(compliance_records)
        s = tracker.summary()
        for k in ("total_records", "at_risk_count", "overdue_count", "average_deployment_pct"):
            assert k in s

    def test_summary_total_correct(self, compliance_records):
        tracker = ComplianceTracker(compliance_records)
        s = tracker.summary()
        assert s["total_records"] == len(compliance_records)

    def test_on_track_returns_subset(self, compliance_records):
        tracker = ComplianceTracker(compliance_records)
        on_track = tracker.on_track()
        for r in on_track:
            assert r.status in ("on_track", "completed")


class TestTrackDeployment:
    def test_keys_present(self, compliance_records):
        result = track_deployment(compliance_records)
        for k in ("total_records", "average_deployment_pct", "fully_deployed", "below_50_pct", "by_status"):
            assert k in result

    def test_total_correct(self, compliance_records):
        result = track_deployment(compliance_records)
        assert result["total_records"] == len(compliance_records)

    def test_average_in_range(self, compliance_records):
        result = track_deployment(compliance_records)
        assert 0.0 <= result["average_deployment_pct"] <= 1.0

    def test_empty_list(self):
        result = track_deployment([])
        assert result["total_records"] == 0

    def test_fully_deployed_count(self, compliance_records):
        result = track_deployment(compliance_records)
        # One record has deployment_pct == 1.0
        assert result["fully_deployed"] >= 1


class TestCheckDeadlines:
    def test_keys_present(self, compliance_records):
        result = check_deadlines(compliance_records)
        for k in ("upcoming_deadlines", "overdue", "upcoming_count", "overdue_count"):
            assert k in result

    def test_overdue_count_positive(self, compliance_records):
        result = check_deadlines(compliance_records)
        assert result["overdue_count"] >= 1

    def test_upcoming_count_positive(self, compliance_records):
        result = check_deadlines(compliance_records, horizon_days=180)
        assert result["upcoming_count"] >= 1

    def test_upcoming_sorted_by_days_remaining(self, compliance_records):
        result = check_deadlines(compliance_records)
        days = [r["days_remaining"] for r in result["upcoming_deadlines"]]
        assert days == sorted(days)

    def test_overdue_has_days_overdue(self, compliance_records):
        result = check_deadlines(compliance_records)
        for item in result["overdue"]:
            assert "days_overdue" in item
            assert item["days_overdue"] > 0


class TestAtRiskRecipients:
    def test_returns_list(self, compliance_records):
        result = at_risk_recipients(compliance_records)
        assert isinstance(result, list)

    def test_all_below_threshold(self, compliance_records):
        result = at_risk_recipients(compliance_records, threshold_pct=0.50)
        for r in result:
            assert r["deployment_pct"] < 0.50

    def test_sorted_by_days_remaining(self, compliance_records):
        result = at_risk_recipients(compliance_records)
        days = [r["days_remaining"] for r in result]
        assert days == sorted(days)

    def test_shortfall_pct_present(self, compliance_records):
        result = at_risk_recipients(compliance_records)
        for r in result:
            assert "shortfall_pct" in r
            assert r["shortfall_pct"] > 0
