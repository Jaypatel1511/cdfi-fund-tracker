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


class TestAtRiskSemanticReconciliation:
    """0.1.0 shipped two incompatible definitions of "at risk".

    ComplianceRecord.is_at_risk used ``days_remaining <= 180``, which swept in
    records whose deadline had ALREADY PASSED. at_risk_recipients() used
    ``0 <= days_remaining <= days_window``, which excluded them. Same words,
    different sets, and ComplianceTracker.at_risk() delegated to the first --
    so summary() counted an overdue record in both at_risk_count and
    overdue_count.

    0.2.0 adopts the forward-looking semantic everywhere: at-risk means there
    is still time left on the clock. A blown deadline is `is_overdue`, a
    distinct and already-realized state. The two sets are now disjoint.
    """

    @staticmethod
    def _record(days_offset, pct=0.10, status="at_risk"):
        from datetime import date, timedelta

        from cdfifund.data.schema import ComplianceRecord

        deadline = (date.today() + timedelta(days=days_offset)).isoformat()
        return ComplianceRecord("R-X", "CDFI_FA", pct, deadline, status, "2025-01-01")

    def test_past_deadline_is_not_at_risk(self):
        """THE case the two implementations disagreed on. 0.1.0: True."""
        assert self._record(-30).is_at_risk is False

    def test_past_deadline_is_overdue(self):
        assert self._record(-30).is_overdue is True

    def test_at_risk_and_overdue_are_disjoint(self):
        for offset in (-400, -180, -30, -1, 0, 1, 30, 180, 181, 400):
            r = self._record(offset)
            assert not (r.is_at_risk and r.is_overdue), (
                f"offset {offset} landed in both buckets"
            )

    def test_summary_does_not_double_count_an_overdue_record(self):
        """0.1.0: at_risk_count=1 AND overdue_count=1 for a single record."""
        tracker = ComplianceTracker([self._record(-30)])
        summary = tracker.summary()
        assert summary["total_records"] == 1
        assert summary["at_risk_count"] == 0
        assert summary["overdue_count"] == 1

    def test_property_and_function_agree_on_past_deadline(self):
        """The reconciliation: both implementations now return the same set."""
        records = [self._record(-30)]
        assert len(ComplianceTracker(records).at_risk()) == len(
            at_risk_recipients(records)
        ) == 0

    def test_property_and_function_agree_across_the_deadline_range(self):
        for offset in (-400, -180, -30, -1, 0, 1, 30, 179, 180, 181, 400):
            records = [self._record(offset)]
            via_property = len(ComplianceTracker(records).at_risk())
            via_function = len(at_risk_recipients(records))
            assert via_property == via_function, (
                f"offset {offset}: property={via_property} function={via_function}"
            )

    def test_deadline_today_is_at_risk(self):
        assert self._record(0).is_at_risk is True

    def test_deadline_inside_window_is_at_risk(self):
        assert self._record(179).is_at_risk is True

    def test_deadline_at_window_boundary_is_at_risk(self):
        assert self._record(180).is_at_risk is True

    def test_deadline_beyond_window_is_not_at_risk(self):
        assert self._record(181).is_at_risk is False

    def test_well_deployed_record_inside_window_is_not_at_risk(self):
        assert self._record(30, pct=0.80).is_at_risk is False

    def test_malformed_deadline_is_rejected_at_construction(self):
        """0.2.0 replaced silent-skip with a construction-time raise.

        Through the fix release this record was constructible and then vanished
        from every compliance report: is_at_risk and is_overdue both returned
        False, check_deadlines() omitted it from both lists, and
        at_risk_recipients() dropped it -- while summary()'s total_records
        still counted it, producing a short numerator over a full denominator.
        """
        from cdfifund.data.schema import ComplianceRecord

        with pytest.raises(ValueError, match="deadline must be YYYY-MM-DD"):
            ComplianceRecord(
                "R-BAD", "CDFI_FA", 0.10, "not-a-date", "at_risk", "2025-01-01"
            )
