"""Compliance tracking for CDFI Fund award deployment obligations."""

from datetime import date
from typing import List, Dict, Any, Optional

from cdfifund.data.schema import (
    Award,
    ComplianceRecord,
    COMPLIANCE_STATUS_CODES,
    parse_iso_date,
)


class ComplianceTracker:
    """Tracks deployment compliance across a set of CDFI Fund awards.

    Usage:
        tracker = ComplianceTracker(records)
        at_risk = tracker.at_risk()
        overdue = tracker.overdue()
    """

    def __init__(self, records: List[ComplianceRecord]) -> None:
        self.records = records

    def at_risk(self) -> List[ComplianceRecord]:
        """Return records at risk of non-compliance: behind pace, deadline ahead.

        Delegates to :attr:`ComplianceRecord.is_at_risk` -- forward-looking,
        below 50% deployed, deadline within the next 180 days. Disjoint from
        :meth:`overdue`.

        .. versionchanged:: 0.2.0
            No longer includes records whose deadline has already passed;
            those are returned by :meth:`overdue`. See
            :attr:`ComplianceRecord.is_at_risk`.
        """
        return [r for r in self.records if r.is_at_risk]

    def overdue(self) -> List[ComplianceRecord]:
        """Return records past deadline with incomplete deployment.

        Disjoint from :meth:`at_risk`.
        """
        return [r for r in self.records if r.is_overdue]

    def on_track(self) -> List[ComplianceRecord]:
        """Return records with status 'on_track' or 'completed'."""
        return [r for r in self.records if r.status in ("on_track", "completed")]

    def summary(self) -> Dict[str, Any]:
        """Return a portfolio-level compliance summary.

        ``at_risk_count`` and ``overdue_count`` are disjoint as of 0.2.0; in
        0.1.0 a record with a past deadline and low deployment was counted in
        both. Both counts are relative to ``date.today()``.
        """
        total = len(self.records)
        at_risk = self.at_risk()
        overdue = self.overdue()
        avg_deployment = (
            sum(r.deployment_pct for r in self.records) / total if total else 0.0
        )
        return {
            "total_records": total,
            "at_risk_count": len(at_risk),
            "overdue_count": len(overdue),
            "on_track_count": len(self.on_track()),
            "average_deployment_pct": avg_deployment,
            "fully_deployed_count": sum(1 for r in self.records if r.deployment_pct >= 1.0),
        }


def track_deployment(
    records: List[ComplianceRecord],
) -> Dict[str, Any]:
    """Compute deployment statistics across a set of compliance records.

    Args:
        records: List of ComplianceRecord objects.

    Returns:
        Dict with total_records, average_deployment_pct, fully_deployed,
        below_50_pct, and by_status breakdown.
    """
    if not records:
        return {
            "total_records": 0,
            "average_deployment_pct": 0.0,
            "fully_deployed": 0,
            "below_50_pct": 0,
            "by_status": {},
        }

    avg_pct = sum(r.deployment_pct for r in records) / len(records)
    fully_deployed = sum(1 for r in records if r.deployment_pct >= 1.0)
    below_50 = sum(1 for r in records if r.deployment_pct < 0.50)

    by_status: Dict[str, int] = {}
    for r in records:
        by_status[r.status] = by_status.get(r.status, 0) + 1

    return {
        "total_records": len(records),
        "average_deployment_pct": avg_pct,
        "fully_deployed": fully_deployed,
        "below_50_pct": below_50,
        "by_status": by_status,
    }


def check_deadlines(
    records: List[ComplianceRecord],
    horizon_days: int = 180,
) -> Dict[str, Any]:
    """Identify records with deadlines falling within a forward-looking window.

    Evaluated against ``date.today()``, so results change over time for an
    unchanged input.

    Every record is accounted for: a record appears in ``upcoming_deadlines``,
    in ``overdue``, or in neither because it is fully deployed or its deadline
    is beyond the horizon. No record is dropped for being unparseable.

    Args:
        records: List of ComplianceRecord objects.
        horizon_days: Number of days ahead to check (default 180).

    Returns:
        Dict with upcoming_deadlines list and counts.

    Raises:
        ValueError: If any record's ``deadline`` is not a valid ``YYYY-MM-DD``
            string. Unreachable for records constructed normally, since
            :class:`~cdfifund.data.schema.ComplianceRecord` validates it.

    .. versionchanged:: 0.2.0
        Records with a malformed ``deadline`` used to be silently skipped,
        appearing in neither list while still counting toward the denominator
        elsewhere. Deadlines are now validated at construction, and this
        function raises rather than dropping.
    """
    today = date.today()
    upcoming = []
    overdue = []

    for r in records:
        dl = parse_iso_date(r.deadline, "deadline")
        days_remaining = (dl - today).days
        if days_remaining < 0 and r.deployment_pct < 1.0:
            overdue.append({
                "recipient_id": r.recipient_id,
                "program": r.program,
                "deadline": r.deadline,
                "deployment_pct": r.deployment_pct,
                "days_overdue": abs(days_remaining),
            })
        elif 0 <= days_remaining <= horizon_days and r.deployment_pct < 1.0:
            upcoming.append({
                "recipient_id": r.recipient_id,
                "program": r.program,
                "deadline": r.deadline,
                "deployment_pct": r.deployment_pct,
                "days_remaining": days_remaining,
            })

    return {
        "upcoming_deadlines": sorted(upcoming, key=lambda x: x["days_remaining"]),
        "overdue": overdue,
        "upcoming_count": len(upcoming),
        "overdue_count": len(overdue),
        "horizon_days": horizon_days,
    }


def at_risk_recipients(
    records: List[ComplianceRecord],
    threshold_pct: float = 0.50,
    days_window: int = 180,
) -> List[Dict[str, Any]]:
    """Return recipient IDs and details for at-risk deployment records.

    "At risk" is forward-looking: below ``threshold_pct`` deployed with a
    deadline that is still ahead but no more than ``days_window`` days out.
    Records whose deadline has already passed are NOT returned here -- they are
    overdue, a distinct state, reported by :func:`check_deadlines` under the
    ``overdue`` key and by :attr:`ComplianceRecord.is_overdue`. This matches
    :attr:`ComplianceRecord.is_at_risk` as of 0.2.0.

    Evaluated against ``date.today()``, so results change over time for an
    unchanged input. No record is dropped for being unparseable.

    Args:
        records: List of ComplianceRecord objects.
        threshold_pct: Deployment percentage below which a record is "at risk".
        days_window: Deadline must be within this many days to count as at-risk.

    Returns:
        List of dicts with recipient_id, program, deployment_pct, deadline,
        and days_remaining, sorted by days_remaining ascending.

    Raises:
        ValueError: If any record's ``deadline`` is not a valid ``YYYY-MM-DD``
            string. See :func:`check_deadlines`.

    .. versionchanged:: 0.2.0
        Records with a malformed ``deadline`` used to be silently skipped.
    """
    today = date.today()
    results = []

    for r in records:
        dl = parse_iso_date(r.deadline, "deadline")
        days_remaining = (dl - today).days
        if r.deployment_pct < threshold_pct and 0 <= days_remaining <= days_window:
            results.append({
                "recipient_id": r.recipient_id,
                "program": r.program,
                "deployment_pct": r.deployment_pct,
                "deadline": r.deadline,
                "days_remaining": days_remaining,
                "shortfall_pct": threshold_pct - r.deployment_pct,
            })

    return sorted(results, key=lambda x: x["days_remaining"])
