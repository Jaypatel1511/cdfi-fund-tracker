"""Data structures and constants for CDFI Fund award tracking."""

import math
import numbers
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Any


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_iso_date(value: Any, field_name: str) -> date:
    """Parse a strict ``YYYY-MM-DD`` string into a :class:`datetime.date`.

    This is the single date gate for the package: every date field is validated
    with it at construction, and every consumer that needs the parsed value
    calls it again rather than parsing independently. Validation and parsing
    therefore cannot drift apart.

    **Deliberately not ``date.fromisoformat``.** This is a stricter rule than
    the stdlib's, on purpose. On every version this package supports (3.11+),
    ``fromisoformat`` accepts the full ISO 8601 date grammar: the compact form
    ``20240915`` and ISO week dates such as ``2024-W37-1``. The package's
    contract is ``YYYY-MM-DD`` and nothing else, and the week-date form is the
    reason that matters -- ``2024-W37-1`` parses without complaint to
    ``2024-09-09``, a *different date* than any reader scanning that string
    would expect. A date field that silently means something other than it
    reads is worse than one that raises. The regex below admits exactly one
    form, and the ``date()`` construction that follows rejects impossible
    calendar dates (``2024-02-30``) while accepting real ones (``2024-02-29``).

    Args:
        value: The value to validate. Must be a ``str``.
        field_name: Field name, used in the error message.

    Returns:
        The parsed :class:`datetime.date`.

    Raises:
        ValueError: If ``value`` is not a string, does not match ``YYYY-MM-DD``,
            or is not a real calendar date. Non-string input raises ValueError
            (not TypeError) so that a null CSV cell or a real ``date`` object --
            both natural mistakes -- surface as the same error type as every
            other constructor violation.
    """
    if not isinstance(value, str):
        raise ValueError(
            f"{field_name} must be a YYYY-MM-DD string, got "
            f"{type(value).__name__} {value!r}"
        )
    if not _ISO_DATE_RE.match(value):
        raise ValueError(f"{field_name} must be YYYY-MM-DD, got {value!r}")
    try:
        return date(int(value[0:4]), int(value[5:7]), int(value[8:10]))
    except ValueError:
        raise ValueError(
            f"{field_name} must be a real calendar date in YYYY-MM-DD form, "
            f"got {value!r}"
        ) from None


def _validate_finite(value: Any, field_name: str) -> float:
    """Return ``value`` as a ``float``, rejecting non-numeric and non-finite input.

    ``float('nan')`` defeats every ordinary bounds check by returning False from
    *both* sides of a comparison: ``nan <= 0`` is False, so ``if x <= 0: raise``
    never fires, and a NaN flows into sums, ranks, and ratios. It is exactly
    what an empty numeric cell becomes when read through pandas, and this
    package's documented workflow is for callers to build records from their own
    source. ``inf`` is rejected for the same reason.

    **The type gate is an ABC check, not a concrete-type check.** Through the
    0.2.0 build this read ``isinstance(value, (int, float))``, which accepted
    ``numpy.float64`` only because that type happens to subclass ``float``, and
    refused ``numpy.int64``, ``numpy.int32``, ``numpy.float32``,
    ``decimal.Decimal`` and ``fractions.Fraction`` -- every one of them a finite
    number -- with the message "must be a number". A plain integer dollar column
    read through pandas produces ``numpy.int64`` from ``.iloc``, ``.at``,
    ``.loc``, ``Series.iloc`` and ``.sum()``, so the package's own documented
    workflow hit it, and which access pattern the caller reached for decided
    whether their data loaded at all.

    ``numbers.Real`` covers the numpy scalars and ``Fraction``. ``Decimal`` is
    checked separately because it is deliberately NOT registered as
    ``numbers.Real`` -- and it is arguably the most correct type for a currency
    field, so an ABC check alone would still have refused it.

    Booleans are rejected explicitly, and must stay that way: ``bool`` is both
    ``numbers.Real`` and ``numbers.Integral``, so without this clause
    ``Award(award_amount=True)`` would construct as a $1.00 award.

    The return value is a built-in ``float``, so accepted foreign types are
    COERCED rather than stored as given. See :class:`Award` for why.
    """
    if isinstance(value, bool) or not isinstance(value, (numbers.Real, Decimal)):
        raise ValueError(
            f"{field_name} must be a number, got {type(value).__name__} {value!r}"
        )
    try:
        finite = math.isfinite(value)
    except (ValueError, OverflowError):
        # math.isfinite does not always answer the question for a value that
        # passed the type gate. Decimal('sNaN') raises ValueError, and an int or
        # Fraction too large to convert to float raises OverflowError -- which
        # is not a ValueError at all, so `Award(award_amount=10**400)` escaped
        # this package's convention that every constructor violation is a
        # ValueError. Both mean "not a usable finite number", which is what the
        # caller needs to be told, with the field named.
        finite = False
    if not finite:
        raise ValueError(f"{field_name} must be a finite number, got {value!r}")
    return float(value)


def _validate_integral(value: Any, field_name: str) -> int:
    """Return ``value`` as a built-in ``int``, rejecting non-integral input.

    The integer counterpart of :func:`_validate_finite`, and it exists for the
    same reason: the check it replaced was ``isinstance(value, int)``, which
    refused ``numpy.int64`` -- what a plain integer year column yields from
    pandas -- while reporting that the value was not an int.

    ``numbers.Integral`` rather than ``numbers.Real``: this gates a year, and a
    fractional year is not a valid input. That also excludes ``Decimal``, which
    :func:`_validate_finite` accepts; a year is a count, not a currency amount,
    so there is no exactness argument for it. ``bool`` is excluded explicitly
    for the same reason as in :func:`_validate_finite`.

    Every ``numbers.Integral`` is finite by construction -- there is no integral
    NaN or infinity -- so there is no finiteness check here.
    """
    if isinstance(value, bool) or not isinstance(value, numbers.Integral):
        raise ValueError(
            f"{field_name} must be an int, got {type(value).__name__} {value!r}"
        )
    return int(value)


@dataclass
class Award:
    """Represents a single CDFI Fund award.

    **Numeric fields are coerced to built-ins at construction.** ``award_amount``
    is stored as a ``float`` and ``award_year`` as an ``int``, whatever numeric
    type you pass -- ``numpy.int64``, ``numpy.float32``, ``decimal.Decimal`` and
    ``fractions.Fraction`` are all accepted and all converted. This is not new
    in kind: the field has been reassigned through a ``float()`` since the
    validator was introduced, so ``award_amount=1_500_000`` has always read back
    as ``1500000.0``. 0.2.0 widens which types get in, not what happens to them
    afterwards.

    Coercion rather than store-as-given, deliberately:

    * ``Decimal + float`` raises TypeError. Every aggregation in this package
      sums this field, so one ``Decimal`` award in a portfolio of floats would
      abort :func:`~cdfifund.analysis.aggregations.by_program` -- a failure that
      does not exist today and that accepting the type without converting it
      would have introduced.
    * ``numpy`` scalars and ``Decimal`` are not JSON-serializable, and
      ``numpy.int64`` is rejected as a dict *key* too, which is how
      :func:`~cdfifund.analysis.aggregations.by_year` returns ``award_year``.
      Nothing in this package serializes, so storing them as given would not
      fail here -- it would fail in the caller's code, one layer removed from
      the constructor that let the value in.

    The cost is that an exact ``Decimal("1500000.07")`` becomes a float and
    stops being exact. That trade is forced: the field is annotated ``float``
    and every downstream computation is float arithmetic, so the exactness
    would not survive the first division regardless.

    Attributes:
        award_id: Unique identifier for the award.
        recipient_name: Legal name of the awardee.
        recipient_type: Category of institution (see RECIPIENT_TYPES).
        program: CDFI Fund program name (see CDFI_PROGRAMS keys).
        award_amount: Dollar amount awarded. Any finite real number or
            ``Decimal``; stored as ``float``.
        award_date: Award announcement date (YYYY-MM-DD string). Validated.
        award_year: Fiscal year of the award. Any integral type >= 1994, stored
            as ``int``; see :meth:`__post_init__` for why it is NOT
            cross-checked against ``award_date``.
        state: Two-letter USPS code for a state, DC, or a US territory (see
            US_STATES_AND_TERRITORIES). Uppercase, exact.
        congressional_district: Congressional district number or None. NOT
            validated -- district numbering is state-dependent and changes with
            redistricting, and nothing in this package consumes the value.
        intended_use: Description of how funds will be used. NOT validated;
            free text by design.
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
        # Rejects NaN and inf before the bounds check: `nan <= 0` is False, so a
        # bare `if self.award_amount <= 0` accepts NaN and lets it poison every
        # downstream sum, rank and ratio.
        self.award_amount = _validate_finite(self.award_amount, "award_amount")
        if self.award_amount <= 0:
            raise ValueError(
                f"award_amount must be positive, got {self.award_amount!r}"
            )
        if self.recipient_type not in RECIPIENT_TYPES:
            raise ValueError(
                f"recipient_type must be one of {list(RECIPIENT_TYPES)}, "
                f"got {self.recipient_type!r}"
            )
        if self.program not in CDFI_PROGRAMS:
            raise ValueError(
                f"program must be one of {list(CDFI_PROGRAMS)}, got {self.program!r}"
            )
        if self.status not in ("active", "closed", "pending"):
            raise ValueError(
                f"status must be 'active', 'closed', or 'pending', "
                f"got {self.status!r}"
            )
        # Un-normalized state codes are the single most likely input error in a
        # bring-your-own-data package, and geographic_distribution() is the
        # metric that would otherwise report six Illinois awards as six states.
        if self.state not in US_STATES_AND_TERRITORIES:
            raise ValueError(
                f"state must be an uppercase two-letter USPS code for a state, "
                f"DC, or a US territory, got {self.state!r}"
            )
        parse_iso_date(self.award_date, "award_date")
        # award_year is NOT cross-checked against award_date. It is documented
        # as the FISCAL year, and the federal fiscal year runs October-September:
        # an award announced 2023-11-15 legitimately belongs to FY2024. A
        # calendar-year equality check would reject correct data. Only the floor
        # is enforced -- the CDFI Fund was created by the Riegle Act in 1994, so
        # no award predates it. There is no upper bound, deliberately: a ceiling
        # tied to the current date would make construction date-relative, the
        # exact hazard this package already warns about for compliance results.
        self.award_year = _validate_integral(self.award_year, "award_year")
        if self.award_year < 1994:
            raise ValueError(
                f"award_year must be >= 1994 (the CDFI Fund was created in "
                f"1994), got {self.award_year!r}"
            )


@dataclass
class Recipient:
    """Represents a CDFI Fund award recipient.

    Attributes:
        recipient_id: Unique identifier. NOT validated, and nothing in this
            package consumes it -- recipient-level aggregation keys on the
            award's ``recipient_name`` string instead. See the README's
            Limitations section.
        name: Legal name. NOT validated.
        type: Institution type (see RECIPIENT_TYPES). Validated -- pass the
            CODE (``loan_fund``), not the display label (``Loan Fund``).
        certification_status: 'certified', 'applicant', 'formerly_certified'.
        total_awards: Total lifetime award dollars received.
        programs_received: List of CDFI Fund programs participated in. Every
            element must be a CDFI_PROGRAMS key.
        geographic_areas: States or regions served. NOT validated -- the field
            is documented as states *or regions*, so it is not a state-code
            vocabulary and nothing in this package consumes it.
    """

    recipient_id: str
    name: str
    type: str
    certification_status: str
    total_awards: float
    programs_received: List[str]
    geographic_areas: List[str]

    def __post_init__(self) -> None:
        # NaN defeats `< 0` the same way it defeats `<= 0` on Award.
        self.total_awards = _validate_finite(self.total_awards, "total_awards")
        if self.total_awards < 0:
            raise ValueError(
                f"total_awards cannot be negative, got {self.total_awards!r}"
            )
        valid_cert = {"certified", "applicant", "formerly_certified"}
        if self.certification_status not in valid_cert:
            raise ValueError(
                f"certification_status must be one of {sorted(valid_cert)}, "
                f"got {self.certification_status!r}"
            )
        # Added in 0.2.0. Through the 0.2.0 build these two fields were
        # accepted unvalidated while Award.recipient_type and Award.program --
        # the same two vocabularies, on the sibling dataclass -- were enforced,
        # and the README claimed all of them were. A caller writing
        # type="Loan Fund" (the display label the README prints beside the code)
        # got no error and carried a bad type into their own rollups.
        if self.type not in RECIPIENT_TYPES:
            raise ValueError(
                f"type must be one of {list(RECIPIENT_TYPES)}, got {self.type!r}"
            )
        # Type-gate the container before iterating it. Two things went wrong
        # when the loop was the only check:
        #
        # `None` -- what a null CSV cell becomes -- raised TypeError
        # ("'NoneType' object is not iterable") from the loop rather than
        # ValueError, contradicting the convention parse_iso_date's docstring
        # states outright: a null cell should surface "as the same error type as
        # every other constructor violation".
        #
        # A bare string "CDFI_FA" is iterable, so it was rejected -- but
        # character by character, and the message named the offending value as
        # 'C'. A caller who forgot the brackets got an error quoting a value
        # they never wrote. str is excluded from the accepted types on purpose:
        # it is a sequence, but not a sequence of program codes.
        if not isinstance(self.programs_received, (list, tuple, set)):
            raise ValueError(
                f"programs_received must be a list, tuple, or set of program "
                f"codes, got {type(self.programs_received).__name__} "
                f"{self.programs_received!r}"
            )
        for prog in self.programs_received:
            if prog not in CDFI_PROGRAMS:
                raise ValueError(
                    f"programs_received entries must each be one of "
                    f"{list(CDFI_PROGRAMS)}, got {prog!r}"
                )


@dataclass
class ComplianceRecord:
    """Tracks deployment and compliance for a specific award/program.

    Attributes:
        recipient_id: Links to Recipient. NOT validated -- an opaque caller-side
            key; this package never resolves it.
        program: CDFI Fund program (see CDFI_PROGRAMS keys).
        deployment_pct: Percentage of award funds deployed (0.0-1.0) -- a
            FRACTION, not a percent. ``50`` raises; use ``0.50``.
        deadline: Deployment deadline (YYYY-MM-DD string). Validated.
        status: Compliance status code (see COMPLIANCE_STATUS_CODES).
        last_reporting_date: Date of most recent compliance report
            (YYYY-MM-DD string). Validated.
    """

    recipient_id: str
    program: str
    deployment_pct: float
    deadline: str
    status: str
    last_reporting_date: str

    def __post_init__(self) -> None:
        # The `not 0.0 <= x <= 1.0` form already rejected NaN by accident --
        # both comparisons are False for NaN, so `not False` fired. Made
        # explicit here so the guard no longer depends on which side of the
        # comparison the `not` happens to sit on.
        self.deployment_pct = _validate_finite(self.deployment_pct, "deployment_pct")
        if not 0.0 <= self.deployment_pct <= 1.0:
            raise ValueError(
                f"deployment_pct must be between 0 and 1 (a fraction, not a "
                f"percent -- use 0.50, not 50), got {self.deployment_pct!r}"
            )
        if self.status not in COMPLIANCE_STATUS_CODES:
            raise ValueError(
                f"status must be one of {list(COMPLIANCE_STATUS_CODES)}, "
                f"got {self.status!r}"
            )
        # Added in 0.2.0: Award.program was validated against CDFI_PROGRAMS and
        # this one was not, for no reason a reader could discover.
        if self.program not in CDFI_PROGRAMS:
            raise ValueError(
                f"program must be one of {list(CDFI_PROGRAMS)}, got {self.program!r}"
            )
        # Both date fields, not just the one that happens to be parsed today.
        # Validating only `deadline` would leave `last_reporting_date` as an
        # arbitrary exception a reader would trip over.
        parse_iso_date(self.deadline, "deadline")
        parse_iso_date(self.last_reporting_date, "last_reporting_date")

    def _deadline_field_name(self) -> str:
        """Field name for deadline parse errors, carrying this record's identity.

        Batch entry points evaluate every record in a portfolio, so an abort
        must say WHICH record caused it. Without the identity, one bad deadline
        at index 347 of 500 aborts :meth:`ComplianceTracker.summary`,
        :meth:`~cdfifund.compliance.tracker.ComplianceTracker.at_risk`,
        :meth:`~cdfifund.compliance.tracker.ComplianceTracker.overdue`,
        :func:`~cdfifund.compliance.tracker.check_deadlines` and
        :func:`~cdfifund.compliance.tracker.at_risk_recipients` with the same
        text -- and if the bad value is a placeholder repeated across the
        portfolio, the message cannot distinguish the offenders.

        Deliberately NOT used by :meth:`__post_init__`. At construction the
        caller has the record in hand and the traceback points at their own
        call site; the identity only earns its noise in a batch.
        """
        return f"deadline (recipient_id={self.recipient_id!r})"

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
        an unchanged record.

        Raises:
            ValueError: If ``deadline`` is not a valid ``YYYY-MM-DD`` string.
                Unreachable for a record that was constructed normally --
                ``__post_init__`` validates it -- but reachable by assigning to
                ``deadline`` after construction, which a mutable dataclass
                permits. It raises rather than returning False; see the module
                note on why the old silent-skip behaviour was removed.

        .. versionchanged:: 0.2.0
            In 0.1.0 this used ``days_remaining <= 180`` with no lower bound,
            so records with already-past deadlines returned True here while
            ``at_risk_recipients()`` excluded them. Overdue records now return
            False. To recover the old set, use ``r.is_at_risk or r.is_overdue``.

        .. versionchanged:: 0.2.0
            A malformed ``deadline`` used to return False. It now raises: the
            deadline is validated at construction, so the only way to reach a
            malformed one is to assign it afterwards, and silently reporting
            such a record as "not at risk" is the under-counting this release
            exists to remove.
        """
        dl = parse_iso_date(self.deadline, self._deadline_field_name())
        days_remaining = (dl - date.today()).days
        return self.deployment_pct < 0.50 and 0 <= days_remaining <= 180

    @property
    def is_overdue(self) -> bool:
        """True if the deadline has passed and deployment is incomplete.

        Disjoint from :attr:`is_at_risk`. Evaluated against ``date.today()``.

        Raises:
            ValueError: If ``deadline`` is not a valid ``YYYY-MM-DD`` string.
                See :attr:`is_at_risk`.

        .. versionchanged:: 0.2.0
            A malformed ``deadline`` used to return False; it now raises.
        """
        dl = parse_iso_date(self.deadline, self._deadline_field_name())
        return dl < date.today() and self.deployment_pct < 1.0


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

US_STATES_AND_TERRITORIES: Dict[str, str] = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut",
    "DE": "Delaware", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
    "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan",
    "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
    "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota",
    "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
    # District of Columbia
    "DC": "District of Columbia",
    # US territories the CDFI Fund makes awards in.
    "AS": "American Samoa",
    "GU": "Guam",
    "MP": "Northern Mariana Islands",
    "PR": "Puerto Rico",
    "VI": "US Virgin Islands",
}
"""Valid ``Award.state`` codes: the 50 states, DC, and 5 US territories.

Uppercase USPS codes, matched exactly. Lowercase (``il``), full names
(``Illinois``) and padded values (``" IL"``) are rejected -- they are the same
place under three spellings, and accepting them made
:func:`~cdfifund.analysis.aggregations.geographic_distribution` report one
state as three.

Military codes (AA/AE/AP) and the Freely Associated States (FM/MH/PW) are
excluded: they are not CDFI Fund award jurisdictions.
"""

COMPLIANCE_STATUS_CODES: Dict[str, str] = {
    "on_track": "On track — meeting deployment milestones",
    "at_risk": "At risk — below milestone pace",
    "in_default": "In default — past deadline with material shortfall",
    "completed": "Completed — fully deployed and closed",
    "extended": "Extended — deadline extended by CDFI Fund",
    "pending_review": "Pending review — awaiting CDFI Fund determination",
}
"""Award compliance status code definitions."""
