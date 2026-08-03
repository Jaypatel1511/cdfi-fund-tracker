"""Numeric type acceptance for the four validated numeric fields.

Added in 0.2.0. The guard these cover used ``isinstance(value, (int, float))``,
which refused every numeric type that is not literally ``int`` or ``float``:
``numpy.int64``, ``numpy.int32``, ``numpy.float32``, ``decimal.Decimal`` and
``fractions.Fraction`` were all rejected as "must be a number" -- a message that
asserts something false about a finite number. It was reachable from the
package's own documented workflow ("build Award objects from your own source"),
because a plain integer dollar column read through pandas yields ``numpy.int64``
from ``.iloc``, ``.at``, ``.loc``, ``Series.iloc`` and ``.sum()``.

numpy is NOT a dependency of this package (``dependencies = []``) and CI does
not install it, so the numpy legs skip when it is absent. They are not the load
-bearing coverage: ``Decimal`` and ``Fraction`` are stdlib and exercise the same
abstract-base-class gap. ``Decimal`` is not registered as ``numbers.Real`` at
all, and ``Fraction`` is ``numbers.Real`` but neither ``int`` nor ``float``, so
between them they pin both halves of the guard without any third-party package.
"""

import json
import math
from decimal import Decimal
from fractions import Fraction

import pytest

from cdfifund.data.schema import Award, ComplianceRecord, Recipient


def make_award(**kw):
    base = dict(
        award_id="A001", recipient_name="Test CDFI", recipient_type="loan_fund",
        program="CDFI_FA", award_amount=1_500_000, award_date="2024-01-01",
        award_year=2024, state="IL", congressional_district=None,
        intended_use="lending",
    )
    base.update(kw)
    return Award(**base)


def make_recipient(**kw):
    base = dict(
        recipient_id="R001", name="Test CDFI", type="loan_fund",
        certification_status="certified", total_awards=1_500_000,
        programs_received=["CDFI_FA"], geographic_areas=["IL"],
    )
    base.update(kw)
    return Recipient(**base)


def make_record(**kw):
    base = dict(
        recipient_id="R001", program="CDFI_FA", deployment_pct=0.5,
        deadline="2030-01-01", status="on_track", last_reporting_date="2024-01-01",
    )
    base.update(kw)
    return ComplianceRecord(**base)


# Values every numeric field must ACCEPT. Each is a finite number, which is
# exactly what the README's constraints table says these fields require.
ACCEPTED = [
    ("int", 1, 1.0),
    ("float", 1.0, 1.0),
    ("Decimal", Decimal("1"), 1.0),
    ("Fraction", Fraction(1, 1), 1.0),
]

# Values every numeric field must REJECT, with ValueError.
REJECTED = [
    ("bool", True),
    ("str", "5"),
    ("None", None),
    ("complex", 1 + 2j),
    ("nan", float("nan")),
    ("inf", float("inf")),
    ("Decimal_NaN", Decimal("NaN")),
    ("Decimal_Infinity", Decimal("Infinity")),
    ("Decimal_sNaN", Decimal("sNaN")),
]


def numpy_values():
    """numpy scalars, or an empty list when numpy is not installed."""
    np = pytest.importorskip("numpy")
    return [
        ("np.int64", np.int64(1), 1.0),
        ("np.int32", np.int32(1), 1.0),
        ("np.float32", np.float32(1.0), 1.0),
        ("np.float64", np.float64(1.0), 1.0),
    ]


class TestAwardAmountAccepts:
    @pytest.mark.parametrize("label,value,expected", ACCEPTED, ids=[c[0] for c in ACCEPTED])
    def test_accepts(self, label, value, expected):
        a = make_award(award_amount=value)
        assert a.award_amount == expected

    def test_accepts_numpy(self):
        for label, value, expected in numpy_values():
            a = make_award(award_amount=value)
            assert a.award_amount == expected, label

    @pytest.mark.parametrize("label,value", REJECTED, ids=[c[0] for c in REJECTED])
    def test_rejects(self, label, value):
        with pytest.raises(ValueError, match="award_amount"):
            make_award(award_amount=value)


class TestTotalAwardsAccepts:
    @pytest.mark.parametrize("label,value,expected", ACCEPTED, ids=[c[0] for c in ACCEPTED])
    def test_accepts(self, label, value, expected):
        r = make_recipient(total_awards=value)
        assert r.total_awards == expected

    def test_accepts_numpy(self):
        for label, value, expected in numpy_values():
            r = make_recipient(total_awards=value)
            assert r.total_awards == expected, label

    @pytest.mark.parametrize("label,value", REJECTED, ids=[c[0] for c in REJECTED])
    def test_rejects(self, label, value):
        with pytest.raises(ValueError, match="total_awards"):
            make_recipient(total_awards=value)


class TestDeploymentPctAccepts:
    @pytest.mark.parametrize("label,value,expected", ACCEPTED, ids=[c[0] for c in ACCEPTED])
    def test_accepts(self, label, value, expected):
        # 1 is a legitimate deployment_pct: a fully deployed record.
        rec = make_record(deployment_pct=value)
        assert rec.deployment_pct == expected

    def test_accepts_numpy(self):
        for label, value, expected in numpy_values():
            rec = make_record(deployment_pct=value)
            assert rec.deployment_pct == expected, label

    @pytest.mark.parametrize("label,value", REJECTED, ids=[c[0] for c in REJECTED])
    def test_rejects(self, label, value):
        with pytest.raises(ValueError, match="deployment_pct"):
            make_record(deployment_pct=value)


class TestAwardYearAccepts:
    """award_year takes numbers.Integral, not Real: a fractional year is not a year."""

    def test_accepts_int(self):
        assert make_award(award_year=2024).award_year == 2024

    def test_accepts_numpy_integers(self):
        np = pytest.importorskip("numpy")
        for value in (np.int64(2024), np.int32(2024)):
            assert make_award(award_year=value).award_year == 2024

    @pytest.mark.parametrize(
        "value",
        [True, "2024", None, 2024.0, 2024.5, Fraction(2024, 1), Decimal("2024"),
         float("nan"), 1 + 2j],
        ids=["bool", "str", "None", "float_whole", "float_fractional",
             "Fraction", "Decimal", "nan", "complex"],
    )
    def test_rejects_non_integral(self, value):
        with pytest.raises(ValueError, match="award_year"):
            make_award(award_year=value)

    def test_numpy_integer_still_subject_to_1994_floor(self):
        np = pytest.importorskip("numpy")
        with pytest.raises(ValueError, match="1994"):
            make_award(award_year=np.int64(1993))


class TestCoercionToBuiltins:
    """Accepted foreign types are COERCED, not stored as given.

    The dataclass already coerced ``int`` -> ``float`` before 0.2.0
    (``_validate_finite`` returns ``float(value)``), so this extends an existing
    behaviour to the newly accepted types rather than introducing a new one. It
    matters because the package sums these fields: ``Decimal + float`` raises
    TypeError, so a portfolio mixing a Decimal award with a float award would
    abort inside ``by_program`` if the Decimal were stored as given.
    """

    def test_award_amount_is_exactly_float(self):
        for value in (1, Decimal("1"), Fraction(1, 1)):
            assert type(make_award(award_amount=value).award_amount) is float

    def test_award_year_is_exactly_int(self):
        assert type(make_award(award_year=2024).award_year) is int

    def test_total_awards_is_exactly_float(self):
        for value in (1, Decimal("1"), Fraction(1, 1)):
            assert type(make_recipient(total_awards=value).total_awards) is float

    def test_deployment_pct_is_exactly_float(self):
        for value in (1, Decimal("1"), Fraction(1, 1)):
            assert type(make_record(deployment_pct=value).deployment_pct) is float

    def test_numpy_coerced_to_builtins(self):
        np = pytest.importorskip("numpy")
        assert type(make_award(award_amount=np.int64(1)).award_amount) is float
        assert type(make_award(award_amount=np.float32(1)).award_amount) is float
        assert type(make_award(award_year=np.int64(2024)).award_year) is int

    def test_mixed_decimal_and_float_portfolio_sums(self):
        """The reason coercion is not optional."""
        awards = [make_award(award_amount=Decimal("1500000")),
                  make_award(award_amount=2000000.0)]
        assert sum(a.award_amount for a in awards) == 3_500_000.0

    def test_coerced_fields_are_json_serializable(self):
        a = make_award(award_amount=Decimal("1500000"), award_year=2024)
        assert json.loads(json.dumps({"amt": a.award_amount, "yr": a.award_year})) == {
            "amt": 1500000.0, "yr": 2024,
        }


class TestNonFiniteEdges:
    """The finiteness check must not leak a non-ValueError exception.

    ``math.isfinite`` raises rather than returning False for two inputs that
    pass the type gate: ``Decimal('sNaN')`` raises ValueError with a message
    that names no field, and an ``int``/``Fraction`` too large to convert to
    float raises OverflowError -- not a ValueError at all, so it escaped the
    package's stated convention that every constructor violation is a
    ValueError.
    """

    @pytest.mark.parametrize(
        "value", [10 ** 400, Fraction(10 ** 400, 1)], ids=["huge_int", "huge_Fraction"]
    )
    def test_unrepresentable_magnitude_raises_valueerror(self, value):
        with pytest.raises(ValueError, match="award_amount"):
            make_award(award_amount=value)

    def test_signaling_nan_names_the_field(self):
        with pytest.raises(ValueError, match="award_amount"):
            make_award(award_amount=Decimal("sNaN"))

    def test_widening_the_gate_did_not_admit_array_or_null_types(self):
        """The gate got wider, not open.

        A 0-d or single-element ``ndarray`` is the dangerous one: ``float()``
        accepts both, so a gate that checked convertibility instead of type
        would silently take an array as a dollar amount. ``ndarray`` is not
        registered as ``numbers.Real``, so it is refused.
        """
        np = pytest.importorskip("numpy")
        for value in (np.array([1500000]), np.array(1500000),
                      np.datetime64("2024-01-01"), np.complex128(1 + 2j)):
            with pytest.raises(ValueError, match="award_amount"):
                make_award(award_amount=value)

    def test_pandas_null_sentinels_are_rejected(self):
        pd = pytest.importorskip("pandas")
        for value in (pd.NA, pd.NaT):
            with pytest.raises(ValueError, match="award_amount"):
                make_award(award_amount=value)

    def test_bounds_checks_still_apply_to_accepted_types(self):
        with pytest.raises(ValueError, match="positive"):
            make_award(award_amount=Decimal("0"))
        with pytest.raises(ValueError, match="negative"):
            make_recipient(total_awards=Decimal("-1"))
        with pytest.raises(ValueError, match="between 0 and 1"):
            make_record(deployment_pct=Decimal("1.5"))
        with pytest.raises(ValueError, match="between 0 and 1"):
            make_record(deployment_pct=Fraction(3, 2))
