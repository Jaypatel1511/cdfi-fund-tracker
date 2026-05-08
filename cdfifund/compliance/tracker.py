"""Compliance tracking for CDFI Fund award deployment obligations."""

from datetime import date
from typing import List, Dict, Any, Optional

from cdfifund.data.schema import Award, ComplianceRecord, COMPLIANCE_STATUS_CODES


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
        """Return records that are at risk of non-compliance."""
        return [r for r in self.records if r.is_at_risk]

    def overdue(self) -> List[ComplianceRecord]:
        """Return records that are past deadline with incomplete deployment."""
        return [r for r in self.records if r.is_overdue]

    def on_track(self) -> List[ComplianceRecord]:
        """Return records with status 'on_track' or 'completed'."""
        return [r for r in self.records if r.status in ("on_track", "completed")]

    def summary(self) -> Dict[str, Any]:
        """Return a portfolio-level compliance summary."""
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

    Args:
        records: List of ComplianceRecord objects.
        horizon_days: Number of days ahead to check (default 180).

    Returns:
        Dict with upcoming_deadlines list and counts.
    """
    today = date.today()
    upcoming = []
    overdue = []

    for r in records:
        try:
            dl = date.fromisoformat(r.deadline)
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
        except ValueError:
            continue

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

    Args:
        records: List of ComplianceRecord objects.
        threshold_pct: Deployment percentage below which a record is "at risk".
        days_window: Deadline must be within this many days to count as at-risk.

    Returns:
        List of dicts with recipient_id, program, deployment_pct, deadline,
        and days_remaining, sorted by days_remaining ascending.
    """
    today = date.today()
    results = []

    for r in records:
        try:
            dl = date.fromisoformat(r.deadline)
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
        except ValueError:
            continue

    return sorted(results, key=lambda x: x["days_remaining"])
