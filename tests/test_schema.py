"""Tests for CDFI Fund tracker data schema."""

import pytest
from cdfifund.data.schema import (
    Award,
    Recipient,
    ComplianceRecord,
    CDFI_PROGRAMS,
    RECIPIENT_TYPES,
    COMPLIANCE_STATUS_CODES,
)


class TestAward:
    def test_basic_creation(self, cdfi_fa_award):
        assert cdfi_fa_award.program == "CDFI_FA"
        assert cdfi_fa_award.award_amount == 1_500_000

    def test_invalid_amount(self):
        with pytest.raises(ValueError, match="award_amount"):
            Award("X", "CDFI", "loan_fund", "CDFI_FA", -1, "2024-01-01", 2024, "IL", None, "test")

    def test_invalid_recipient_type(self):
        with pytest.raises(ValueError, match="recipient_type"):
            Award("X", "CDFI", "university", "CDFI_FA", 1_000, "2024-01-01", 2024, "IL", None, "test")

    def test_invalid_program(self):
        with pytest.raises(ValueError, match="program"):
            Award("X", "CDFI", "loan_fund", "FAKE_PROG", 1_000, "2024-01-01", 2024, "IL", None, "test")

    def test_invalid_status(self):
        with pytest.raises(ValueError, match="status"):
            Award("X", "CDFI", "loan_fund", "CDFI_FA", 1_000, "2024-01-01", 2024, "IL", None, "test", "canceled")

    def test_default_status_active(self, cdfi_fa_award):
        assert cdfi_fa_award.status == "active"


class TestRecipient:
    def test_basic_creation(self):
        r = Recipient("R001", "Test CDFI", "loan_fund", "certified", 5_000_000, ["CDFI_FA"], ["IL"])
        assert r.name == "Test CDFI"

    def test_invalid_certification_status(self):
        with pytest.raises(ValueError, match="certification_status"):
            Recipient("R001", "Test", "loan_fund", "unknown", 0, [], [])

    def test_negative_total_awards_raises(self):
        with pytest.raises(ValueError, match="total_awards"):
            Recipient("R001", "Test", "loan_fund", "certified", -100, [], [])


class TestComplianceRecord:
    def test_basic_creation(self, compliance_records):
        r = compliance_records[0]
        assert r.deployment_pct == 0.80

    def test_invalid_deployment_pct(self):
        with pytest.raises(ValueError, match="deployment_pct"):
            ComplianceRecord("R001", "CDFI_FA", 1.5, "2025-01-01", "on_track", "2024-01-01")

    def test_invalid_status(self):
        with pytest.raises(ValueError, match="status"):
            ComplianceRecord("R001", "CDFI_FA", 0.5, "2025-01-01", "unknown_status", "2024-01-01")

    def test_is_at_risk_property(self, compliance_records):
        at_risk = [r for r in compliance_records if r.is_at_risk]
        assert len(at_risk) >= 1

    def test_is_overdue_property(self, compliance_records):
        overdue = [r for r in compliance_records if r.is_overdue]
        assert len(overdue) >= 1

    def test_completed_not_overdue(self, compliance_records):
        completed = next(r for r in compliance_records if r.deployment_pct == 1.0)
        assert not completed.is_overdue


class TestConstants:
    def test_eight_cdfi_programs(self):
        assert len(CDFI_PROGRAMS) == 8

    def test_all_expected_programs_present(self):
        for prog in ("CDFI_FA", "CDFI_TA", "BEA", "NACA", "BGP", "CMF", "RAPID", "NATIVE_AMERICAN"):
            assert prog in CDFI_PROGRAMS

    def test_five_recipient_types(self):
        assert len(RECIPIENT_TYPES) == 5

    def test_compliance_status_codes_present(self):
        for code in ("on_track", "at_risk", "in_default", "completed"):
            assert code in COMPLIANCE_STATUS_CODES


# ---------------------------------------------------------------------------
# 0.2.0 fix-cycle regression tests.
#
# These are written against BEHAVIOUR -- construct an invalid value, require a
# raise -- not against the presence of a string in a docstring or a markdown
# table. The test that missed B1 was a string-presence test: it asserted
# `loan_fund` appeared in README.md and never once passed a bad value.
#
# This block is NOT uniformly a set of tests that fail against the 0.2.0 build.
# It deliberately mixes two kinds:
#
#   - Regression tests, which fail against commit e438251 and pass after.
#   - Positive controls, which pass on BOTH sides on purpose -- "every valid
#     type is accepted", "a leap day is accepted", "-inf was already rejected".
#     They exist so a guard cannot be satisfied by rejecting everything, so
#     they must not fail beforehand, and a claim that they do would be wrong.
#
# Measured, not asserted: running this file's db24cfc state against an e438251
# checkout of `cdfifund/` gives 78 failed / 14 passed of the 92 tests below
# this comment, identically on 3.9.12 and 3.12.13. An earlier revision of this
# comment claimed *every* test below it failed, which was false for the 14
# controls; a figure of 79 that appeared in an interim report does not
# reproduce by any method and is off by one from the 78 measured here.
# ---------------------------------------------------------------------------


def _award(**kw):
    """An otherwise-valid Award, with overrides."""
    d = dict(
        award_id="A1", recipient_name="X", recipient_type="loan_fund",
        program="CDFI_FA", award_amount=1_000.0, award_date="2024-09-15",
        award_year=2024, state="IL", congressional_district=1,
        intended_use="u", status="active",
    )
    d.update(kw)
    return lambda: Award(**d)


def _recipient(**kw):
    """An otherwise-valid Recipient, with overrides."""
    d = dict(
        recipient_id="R1", name="X", type="loan_fund",
        certification_status="certified", total_awards=1.0,
        programs_received=["CDFI_FA"], geographic_areas=["IL"],
    )
    d.update(kw)
    return lambda: Recipient(**d)


def _record(**kw):
    """An otherwise-valid ComplianceRecord, with overrides."""
    d = dict(
        recipient_id="R1", program="CDFI_FA", deployment_pct=0.5,
        deadline="2026-12-01", status="on_track",
        last_reporting_date="2025-01-01",
    )
    d.update(kw)
    return lambda: ComplianceRecord(**d)


class TestB1RecipientValidation:
    """B1: Recipient.type and .programs_received were documented as validated
    and were not. All three pre-existing Recipient tests passed a valid
    "loan_fund", which is why 157 green tests missed it."""

    @pytest.mark.parametrize("bad", ["NOT_A_TYPE", "Loan Fund", "", None, 42, "LOAN_FUND"])
    def test_invalid_type_raises(self, bad):
        with pytest.raises(ValueError, match="type must be one of"):
            _recipient(type=bad)()

    def test_display_label_is_rejected(self):
        """"Loan Fund" is the label the README prints directly beside the code.
        Accepting it carried a bad type into the caller's own rollups."""
        assert RECIPIENT_TYPES["loan_fund"] == "Loan Fund"
        with pytest.raises(ValueError):
            _recipient(type="Loan Fund")()

    def test_every_valid_type_is_accepted(self):
        for code in RECIPIENT_TYPES:
            _recipient(type=code)()

    @pytest.mark.parametrize("bad", [["NOT_A_PROGRAM"], ["CDFI_FA", "FAKE"], [""], [None]])
    def test_invalid_programs_received_raises(self, bad):
        with pytest.raises(ValueError, match="programs_received"):
            _recipient(programs_received=bad)()

    def test_every_valid_program_accepted_in_programs_received(self):
        _recipient(programs_received=list(CDFI_PROGRAMS))()

    def test_empty_programs_received_is_allowed(self):
        _recipient(programs_received=[])()


class TestProgramsReceivedContainerType:
    """programs_received was type-checked only by iterating it.

    Two consequences, both fixed in 0.2.0:

    ``None`` -- what a null CSV cell becomes -- raised TypeError
    ('NoneType' object is not iterable) from the loop, not ValueError. That
    contradicts the convention parse_iso_date's docstring states explicitly:
    non-string input raises ValueError so a null cell surfaces "as the same
    error type as every other constructor violation". This field broke that
    promise.

    A bare string ``"CDFI_FA"`` is iterable, so it was rejected -- but
    character by character, and the message reported the offending value as
    ``'C'``. A caller who forgot the brackets got an error naming a value they
    never wrote.
    """

    @pytest.mark.parametrize(
        "bad", [None, 42, 3.5, True, object()],
        ids=["None", "int", "float", "bool", "object"],
    )
    def test_non_container_raises_valueerror_not_typeerror(self, bad):
        with pytest.raises(ValueError, match="programs_received"):
            _recipient(programs_received=bad)()

    def test_bare_string_names_the_whole_value_not_a_character(self):
        with pytest.raises(ValueError) as exc:
            _recipient(programs_received="CDFI_FA")()
        msg = str(exc.value)
        assert "'CDFI_FA'" in msg, msg
        assert "'C'" not in msg, msg

    def test_bare_string_is_rejected_even_when_it_is_a_valid_program(self):
        """The string spells a real program code; it is still not a list."""
        assert "CDFI_FA" in CDFI_PROGRAMS
        with pytest.raises(ValueError, match="programs_received"):
            _recipient(programs_received="CDFI_FA")()

    @pytest.mark.parametrize(
        "good", [["CDFI_FA"], ("CDFI_FA",), {"CDFI_FA"}, [], (), set()],
        ids=["list", "tuple", "set", "empty_list", "empty_tuple", "empty_set"],
    )
    def test_list_tuple_and_set_are_all_accepted(self, good):
        _recipient(programs_received=good)()


class TestB2DateValidation:
    """B2: three date-shaped fields were unvalidated; only `deadline` was
    parsed, so only it caused visible harm -- silently, by dropping records
    from every compliance report while summary() still counted them."""

    DATE_FIELDS = [
        (_record, "deadline"),
        (_record, "last_reporting_date"),
        (_award, "award_date"),
    ]

    @pytest.mark.parametrize("factory,field", DATE_FIELDS)
    @pytest.mark.parametrize(
        "bad", ["09/01/2026", "2024-9-5", "not-a-date", "", "2024-02-30", "2024-13-01"]
    )
    def test_malformed_date_raises(self, factory, field, bad):
        with pytest.raises(ValueError, match=field):
            factory(**{field: bad})()

    @pytest.mark.parametrize("factory,field", DATE_FIELDS)
    def test_error_message_names_field_and_value(self, factory, field):
        with pytest.raises(ValueError) as exc:
            factory(**{field: "09/01/2026"})()
        msg = str(exc.value)
        assert field in msg, msg
        assert "YYYY-MM-DD" in msg, msg
        assert "09/01/2026" in msg, msg

    @pytest.mark.parametrize("factory,field", DATE_FIELDS)
    @pytest.mark.parametrize("bad", [None, 20240915])
    def test_non_string_raises_valueerror_not_typeerror(self, factory, field, bad):
        """deadline=None (a null CSV field) used to raise a bare TypeError out
        of a property, outside the family exceptions.py describes."""
        with pytest.raises(ValueError, match=field):
            factory(**{field: bad})()

    @pytest.mark.parametrize("factory,field", DATE_FIELDS)
    def test_real_date_object_raises_valueerror_not_typeerror(self, factory, field):
        """Passing a real datetime.date is a natural mistake, not a crash."""
        import datetime
        with pytest.raises(ValueError, match=field):
            factory(**{field: datetime.date(2024, 9, 15)})()

    @pytest.mark.parametrize("factory,field", DATE_FIELDS)
    def test_leap_day_is_accepted(self, factory, field):
        factory(**{field: "2024-02-29"})()

    @pytest.mark.parametrize("factory,field", DATE_FIELDS)
    def test_non_leap_feb_29_is_rejected(self, factory, field):
        with pytest.raises(ValueError, match="real calendar date"):
            factory(**{field: "2023-02-29"})()


class TestB2VersionStability:
    """The date guard must not depend on the interpreter.

    date.fromisoformat is strict YYYY-MM-DD on 3.9/3.10 but on 3.11+ also
    accepts the compact form and ISO week dates. The CI matrix is 3.9-3.12, so
    using it would make the same record valid on 3.12 and invalid on 3.9.
    """

    @pytest.mark.parametrize("form", ["20240915", "2024-W37-1", "2024-W37"])
    def test_forms_python_311_plus_would_accept_are_rejected(self, form):
        from cdfifund.data.schema import parse_iso_date
        with pytest.raises(ValueError, match="must be YYYY-MM-DD"):
            parse_iso_date(form, "deadline")

    def test_guard_does_not_delegate_to_fromisoformat(self):
        """Mutation guard: if parse_iso_date is ever reimplemented on top of
        date.fromisoformat, the compact form starts passing on 3.11+ and this
        test fails there while still passing on 3.9 -- which is the whole
        problem. Asserting the rejection directly keeps that from landing."""
        import datetime
        from cdfifund.data.schema import parse_iso_date
        assert parse_iso_date("2024-09-15", "d") == datetime.date(2024, 9, 15)
        with pytest.raises(ValueError):
            parse_iso_date("20240915", "d")


class TestB3StateValidation:
    """B3: Award.state was unvalidated, and geographic_distribution -- a
    headline feature -- reported six spellings of Illinois as six states."""

    @pytest.mark.parametrize("bad", ["il", "Illinois", " IL", "", "ZZ", "I", "ILL", None, 17])
    def test_invalid_state_raises(self, bad):
        with pytest.raises(ValueError, match="state must be"):
            _award(state=bad)()

    def test_all_fifty_states_plus_dc_and_territories_accepted(self):
        from cdfifund.data.schema import US_STATES_AND_TERRITORIES
        assert len(US_STATES_AND_TERRITORIES) == 56
        for code in US_STATES_AND_TERRITORIES:
            _award(state=code)()

    def test_dc_and_territories_present(self):
        from cdfifund.data.schema import US_STATES_AND_TERRITORIES
        for code in ("DC", "PR", "VI", "GU", "AS", "MP"):
            assert code in US_STATES_AND_TERRITORIES

    def test_military_and_freely_associated_codes_excluded(self):
        from cdfifund.data.schema import US_STATES_AND_TERRITORIES
        for code in ("AA", "AE", "AP", "FM", "MH", "PW"):
            assert code not in US_STATES_AND_TERRITORIES

    def test_geographic_distribution_no_longer_splits_one_state(self):
        """The reproduction: six Illinois awards must not read as six states."""
        from cdfifund.analysis.aggregations import geographic_distribution
        awards = [
            Award(f"A{i}", f"L{i}", "loan_fund", "CDFI_FA", 1_000_000.0,
                  "2024-09-15", 2024, "IL", 1, "u", "active")
            for i in range(6)
        ]
        geo = geographic_distribution(awards)
        assert geo["unique_states"] == 1
        assert geo["herfindahl_index"] == pytest.approx(1.0)


class TestB3AwardYear:
    def test_absurd_year_rejected(self):
        with pytest.raises(ValueError, match="award_year"):
            _award(award_year=1776)()

    def test_cdfi_fund_founding_year_is_the_floor(self):
        _award(award_year=1994)()
        with pytest.raises(ValueError, match="award_year"):
            _award(award_year=1993)()

    @pytest.mark.parametrize("bad", ["2024", None, 2024.0, True])
    def test_non_int_year_rejected(self, bad):
        with pytest.raises(ValueError, match="award_year"):
            _award(award_year=bad)()

    def test_year_is_deliberately_not_cross_checked_against_award_date(self):
        """award_year is the FISCAL year; the federal FY runs Oct-Sep, so an
        award announced 2023-11-15 legitimately belongs to FY2024. A
        calendar-year equality check would reject correct data. Documented in
        the README constraints table rather than enforced."""
        _award(award_date="2023-11-15", award_year=2024)()


class TestB5NonFiniteNumbers:
    """B5: float('nan') <= 0 is False, so the positive guard never fired."""

    def test_nan_defeats_a_naive_bounds_check(self):
        nan = float("nan")
        assert (nan <= 0) is False
        assert (nan < 0) is False

    @pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
    def test_award_amount_rejects_non_finite(self, bad):
        with pytest.raises(ValueError, match="award_amount"):
            _award(award_amount=bad)()

    @pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
    def test_total_awards_rejects_non_finite(self, bad):
        """Not in the audit report: Recipient.total_awards had the identical
        hole, since `nan < 0` is also False."""
        with pytest.raises(ValueError, match="total_awards"):
            _recipient(total_awards=bad)()

    @pytest.mark.parametrize("bad", [float("nan"), float("inf")])
    def test_deployment_pct_rejects_non_finite(self, bad):
        with pytest.raises(ValueError, match="deployment_pct"):
            _record(deployment_pct=bad)()

    @pytest.mark.parametrize("bad", ["1000", None, True])
    def test_non_numeric_raises_valueerror_not_typeerror(self, bad):
        """`"1000" <= 0` raises a bare TypeError, outside the ValueError
        contract every other constructor violation honours."""
        with pytest.raises(ValueError, match="award_amount"):
            _award(award_amount=bad)()
        with pytest.raises(ValueError, match="total_awards"):
            _recipient(total_awards=bad)()

    def test_nan_no_longer_reaches_the_rankings(self):
        """The visible harm: aggregates went loudly nan, but top_recipients
        ranked the broken row at a position set by sort stability, not by
        dollars."""
        from cdfifund.analysis.aggregations import top_recipients
        with pytest.raises(ValueError):
            _award(award_amount=float("nan"), recipient_name="Broken Fund")()
        clean = [
            Award("A1", "Alpha", "loan_fund", "CDFI_FA", 5_000_000.0, "2024-09-15", 2024, "IL", 1, "u", "active"),
            Award("A2", "Beta", "loan_fund", "CDFI_FA", 100_000.0, "2024-09-15", 2024, "CA", 1, "u", "active"),
        ]
        assert [r["recipient_name"] for r in top_recipients(clean)] == ["Alpha", "Beta"]


class TestComplianceRecordProgramValidation:
    """Not in the audit report: Award.program was validated against
    CDFI_PROGRAMS and ComplianceRecord.program was not, for no reason a reader
    could discover."""

    def test_invalid_program_raises(self):
        with pytest.raises(ValueError, match="program must be one of"):
            _record(program="NOT_A_PROGRAM")()

    def test_every_valid_program_accepted(self):
        for code in CDFI_PROGRAMS:
            _record(program=code)()


class TestValidationIsExhaustiveAcrossDataclasses:
    """Cross-cutting: the same vocabulary must be enforced everywhere it is
    used. Partial enforcement is the defect class B1 and B2 both belong to."""

    def test_recipient_types_enforced_on_both_fields_that_use_it(self):
        with pytest.raises(ValueError):
            _award(recipient_type="NOPE")()
        with pytest.raises(ValueError):
            _recipient(type="NOPE")()

    def test_cdfi_programs_enforced_on_all_three_fields_that_use_it(self):
        with pytest.raises(ValueError):
            _award(program="NOPE")()
        with pytest.raises(ValueError):
            _record(program="NOPE")()
        with pytest.raises(ValueError):
            _recipient(programs_received=["NOPE"])()

    def test_date_format_enforced_on_all_three_date_fields(self):
        for factory, field in [(_award, "award_date"), (_record, "deadline"),
                               (_record, "last_reporting_date")]:
            with pytest.raises(ValueError, match=field):
                factory(**{field: "09/01/2026"})()
