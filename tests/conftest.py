"""Shared fixtures for cdfi-fund-tracker tests."""

import pytest
from datetime import date, timedelta
from cdfifund.data.schema import Award, ComplianceRecord
from cdfifund.data.loader import load_sample_awards


@pytest.fixture
def sample_awards():
    return load_sample_awards()


@pytest.fixture
def cdfi_fa_award():
    return Award(
        award_id="T001",
        recipient_name="Test CDFI",
        recipient_type="loan_fund",
        program="CDFI_FA",
        award_amount=1_500_000,
        award_date="2024-09-15",
        award_year=2024,
        state="IL",
        congressional_district=7,
        intended_use="Small business lending",
    )


@pytest.fixture
def bgp_award():
    return Award(
        award_id="T002",
        recipient_name="Big CDFI",
        recipient_type="loan_fund",
        program="BGP",
        award_amount=200_000_000,
        award_date="2023-06-01",
        award_year=2023,
        state="NY",
        congressional_district=12,
        intended_use="Bond issuance for affordable housing",
    )


@pytest.fixture
def compliance_records():
    future_deadline = (date.today() + timedelta(days=90)).isoformat()
    far_future = (date.today() + timedelta(days=400)).isoformat()
    past_deadline = (date.today() - timedelta(days=30)).isoformat()
    return [
        ComplianceRecord("R001", "CDFI_FA", 0.80, far_future, "on_track", "2024-06-01"),
        ComplianceRecord("R002", "BEA", 0.30, future_deadline, "at_risk", "2024-03-01"),
        ComplianceRecord("R003", "CDFI_FA", 0.20, future_deadline, "at_risk", "2024-01-15"),
        ComplianceRecord("R004", "CMF", 0.60, far_future, "on_track", "2024-09-01"),
        ComplianceRecord("R005", "BGP", 0.10, past_deadline, "in_default", "2023-12-01"),
        ComplianceRecord("R006", "NACA", 1.0, far_future, "completed", "2024-08-01"),
    ]
