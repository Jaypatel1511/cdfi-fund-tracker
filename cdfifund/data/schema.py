"""Data structures and constants for CDFI Fund award tracking."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class Award:
    """Represents a single CDFI Fund award.

    Attributes:
        award_id: Unique identifier for the award.
        recipient_name: Legal name of the awardee.
        recipient_type: Category of institution (see RECIPIENT_TYPES).
        program: CDFI Fund program name (see CDFI_PROGRAMS keys).
        award_amount: Dollar amount awarded.
        award_date: Award announcement date (YYYY-MM-DD string).
        award_year: Fiscal year of the award.
        state: Two-letter state abbreviation.
        congressional_district: Congressional district number or None.
        intended_use: Description of how funds will be used.
        status: Award status ('active', 'closed', 'pending').
    """

    award_id: str
    recipient_name: str
    recipient_type: str
    program: str
    award_amount: float
    award_date: str
    award_year: int
    state: str
    congressional_district: Optional[int]
    intended_use: str
    status: str = "active"

    def __post_init__(self) -> None:
        if self.award_amount <= 0:
            raise ValueError("award_amount must be positive")
        if self.recipient_type not in RECIPIENT_TYPES:
            raise ValueError(f"recipient_type must be one of {list(RECIPIENT_TYPES)}")
        if self.program not in CDFI_PROGRAMS:
            raise ValueError(f"program must be one of {list(CDFI_PROGRAMS)}")
        if self.status not in ("active", "closed", "pending"):
            raise ValueError("status must be 'active', 'closed', or 'pending'")


@dataclass
class Recipient:
    """Represents a CDFI Fund award recipient.

    Attributes:
        recipient_id: Unique identifier.
        name: Legal name.
        type: Institution type (see RECIPIENT_TYPES).
        certification_status: 'certified', 'applicant', 'formerly_certified'.
        total_awards: Total lifetime award dollars received.
        programs_received: List of CDFI Fund programs participated in.
        geographic_areas: States or regions served.
    """

    recipient_id: str
    name: str
    type: str
    certification_status: str
    total_awards: float
    programs_received: List[str]
    geographic_areas: List[str]

    def __post_init__(self) -> None:
        if self.total_awards < 0:
            raise ValueError("total_awards cannot be negative")
        valid_cert = {"certified", "applicant", "formerly_certified"}
        if self.certification_status not in valid_cert:
            raise ValueError(f"certification_status must be one of {valid_cert}")


@dataclass
class ComplianceRecord:
    """Tracks deployment and compliance for a specific award/program.

    Attributes:
        recipient_id: Links to Recipient.
        program: CDFI Fund program.
        deployment_pct: Percentage of award funds deployed (0.0-1.0).
        deadline: Deployment deadline (YYYY-MM-DD string).
        status: Compliance status code (see COMPLIANCE_STATUS_CODES).
        last_reporting_date: Date of most recent compliance report.
    """

    recipient_id: str
    program: str
    deployment_pct: float
    deadline: str
    status: str
    last_reporting_date: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.deployment_pct <= 1.0:
            raise ValueError("deployment_pct must be between 0 and 1")
        if self.status not in COMPLIANCE_STATUS_CODES:
            raise ValueError(f"status must be one of {list(COMPLIANCE_STATUS_CODES)}")

    @property
    def is_at_risk(self) -> bool:
        """True if below 50% deployed with a deadline still ahead, within 180 days.

        "At risk" is FORWARD-LOOKING: there is still time on the clock, but the
        record is behind pace. A deadline that has already passed is not at
        risk of being missed -- it has been missed, and is reported by
        :attr:`is_overdue` instead. The two properties are disjoint.

        Uses the same thresholds as
        :func:`~cdfifund.compliance.tracker.at_risk_recipients` defaults
        (``threshold_pct=0.50``, ``days_window=180``); that function takes them
        as arguments, this property does not.

        Evaluated against ``date.today()``, so the result changes over time for
        an unchanged record. A malformed ``deadline`` returns False.

        .. versionchanged:: 0.2.0
            In 0.1.0 this used ``days_remaining <= 180`` with no lower bound,
            so records with already-past deadlines returned True here while
            ``at_risk_recipients()`` excluded them. Overdue records now return
            False. To recover the old set, use ``r.is_at_risk or r.is_overdue``.
        """
        from datetime import date
        try:
            dl = date.fromisoformat(self.deadline)
            days_remaining = (dl - date.today()).days
            return self.deployment_pct < 0.50 and 0 <= days_remaining <= 180
        except ValueError:
            return False

    @property
    def is_overdue(self) -> bool:
        """True if the deadline has passed and deployment is incomplete.

        Disjoint from :attr:`is_at_risk`. Evaluated against ``date.today()``.
        A malformed ``deadline`` returns False.
        """
        from datetime import date
        try:
            dl = date.fromisoformat(self.deadline)
            return dl < date.today() and self.deployment_pct < 1.0
        except ValueError:
            return False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CDFI_PROGRAMS: Dict[str, str] = {
    "CDFI_FA": "CDFI Program Financial Assistance",
    "CDFI_TA": "CDFI Program Technical Assistance",
    "BEA": "Bank Enterprise Award Program",
    "NACA": "Native American CDFI Assistance Program",
    "NATIVE_AMERICAN": "Native American CDFI Assistance — TA",
    "RAPID": "CDFI Rapid Response Program",
    "BGP": "CDFI Bond Guarantee Program",
    "CMF": "Capital Magnet Fund",
}
"""All eight CDFI Fund programs with their full names."""

RECIPIENT_TYPES: Dict[str, str] = {
    "loan_fund": "Loan Fund",
    "depository_institution": "Depository Institution",
    "credit_union": "Credit Union",
    "venture_capital_fund": "Venture Capital Fund",
    "holding_company": "Holding Company",
}
"""CDFI Fund recipient type categories."""

COMPLIANCE_STATUS_CODES: Dict[str, str] = {
    "on_track": "On track — meeting deployment milestones",
    "at_risk": "At risk — below milestone pace",
    "in_default": "In default — past deadline with material shortfall",
    "completed": "Completed — fully deployed and closed",
    "extended": "Extended — deadline extended by CDFI Fund",
    "pending_review": "Pending review — awaiting CDFI Fund determination",
}
"""Award compliance status code definitions."""
