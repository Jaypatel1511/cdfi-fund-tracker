"""
cdfi-fund-tracker: CDFI Fund award analysis & compliance tracking.

Analysis and compliance tooling for CDFI Program FA/TA, BEA, NACA, Native
American TA, RAPID, Capital Magnet Fund, and CDFI Bond Guarantee Program
awards.

BRING YOUR OWN DATA. This package has no CDFI Fund ingestion path -- no CSV,
XLSX, or API reader exists anywhere in it, and ``dependencies = []``. You
construct :class:`Award` objects yourself and pass them to the analysis
functions. :func:`load_from_cdfi_fund_url` always raises
:class:`CDFIFundDownloadError`; :func:`load_sample_awards` returns 24
SYNTHETIC fixtures for prototyping only.
"""

from cdfifund.exceptions import CDFIFundTrackerError, CDFIFundDownloadError
from cdfifund.data.schema import (
    Award,
    Recipient,
    ComplianceRecord,
    CDFI_PROGRAMS,
    RECIPIENT_TYPES,
    COMPLIANCE_STATUS_CODES,
    US_STATES_AND_TERRITORIES,
    parse_iso_date,
)
from cdfifund.data.loader import load_sample_awards, load_from_cdfi_fund_url
from cdfifund.programs.cdfi_program import cdfi_program_analysis, fa_vs_ta_breakdown
from cdfifund.programs.bea import bea_program_analysis, bank_enterprise_award_breakdown
from cdfifund.programs.native_american import native_american_analysis, naca_breakdown
from cdfifund.programs.bond_guarantee import bond_guarantee_analysis
from cdfifund.compliance.tracker import (
    ComplianceTracker,
    track_deployment,
    check_deadlines,
    at_risk_recipients,
)
from cdfifund.analysis.aggregations import (
    by_program,
    by_state,
    by_year,
    by_recipient_type,
    top_recipients,
    geographic_distribution,
    cumulative_awards_over_time,
)
from cdfifund.analysis.insights import (
    award_concentration_analysis,
    recipient_lifecycle_analysis,
    program_effectiveness_metrics,
)

__version__ = "0.2.0"

__all__ = [
    # Exceptions
    "CDFIFundTrackerError",
    "CDFIFundDownloadError",
    # Data
    "Award",
    "Recipient",
    "ComplianceRecord",
    "CDFI_PROGRAMS",
    "RECIPIENT_TYPES",
    "COMPLIANCE_STATUS_CODES",
    "US_STATES_AND_TERRITORIES",
    "parse_iso_date",
    # Loader
    "load_sample_awards",
    "load_from_cdfi_fund_url",
    # Programs
    "cdfi_program_analysis",
    "fa_vs_ta_breakdown",
    "bea_program_analysis",
    "bank_enterprise_award_breakdown",
    "native_american_analysis",
    "naca_breakdown",
    "bond_guarantee_analysis",
    # Compliance
    "ComplianceTracker",
    "track_deployment",
    "check_deadlines",
    "at_risk_recipients",
    # Aggregations
    "by_program",
    "by_state",
    "by_year",
    "by_recipient_type",
    "top_recipients",
    "geographic_distribution",
    "cumulative_awards_over_time",
    # Insights
    "award_concentration_analysis",
    "recipient_lifecycle_analysis",
    "program_effectiveness_metrics",
]
