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
