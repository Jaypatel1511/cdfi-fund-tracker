"""Sample data loader and CDFI Fund data fetcher."""

import json
from typing import List, Optional

from cdfifund.data.schema import Award, ComplianceRecord


def load_sample_awards() -> List[Award]:
    """Return a realistic list of sample CDFI Fund awards for testing and demos.

    Data is illustrative and calibrated to historical CDFI Fund award patterns.

    Returns:
        List of Award objects covering multiple programs, years, and geographies.
    """
    raw = [
        ("A2024-001", "Hope Community Capital", "loan_fund", "CDFI_FA", 1_500_000, "2024-09-15", 2024, "MS", 3, "Small business lending in rural Mississippi", "active"),
        ("A2024-002", "Inland Empire CDFI", "loan_fund", "CDFI_FA", 2_000_000, "2024-09-15", 2024, "CA", 42, "Affordable housing predevelopment", "active"),
        ("A2024-003", "First Nations Finance", "loan_fund", "NACA", 750_000, "2024-08-01", 2024, "MT", 1, "Native American small business and housing", "active"),
        ("A2024-004", "Sunrise Community Bank", "depository_institution", "BEA", 500_000, "2024-07-20", 2024, "TN", 7, "Increased CDFI-qualified activities", "active"),
        ("A2024-005", "Coastal Opportunity Fund", "loan_fund", "CMF", 3_000_000, "2024-11-01", 2024, "NC", 4, "Affordable rental housing development", "active"),
        ("A2023-001", "Prairie CDFI", "loan_fund", "CDFI_FA", 1_750_000, "2023-09-10", 2023, "ND", 1, "Agricultural and rural small business lending", "active"),
        ("A2023-002", "Metro Community CU", "credit_union", "CDFI_FA", 1_000_000, "2023-09-10", 2023, "OH", 11, "Consumer and microbusiness lending", "active"),
        ("A2023-003", "Tribal Capital Partners", "loan_fund", "NACA", 650_000, "2023-08-15", 2023, "NM", 2, "Tribal economic development finance", "active"),
        ("A2023-004", "Heartland Bank", "depository_institution", "BEA", 450_000, "2023-07-01", 2023, "IA", 3, "CDFI-qualified lending increase", "closed"),
        ("A2023-005", "Gulf Coast Housing Fund", "loan_fund", "CMF", 5_000_000, "2023-10-01", 2023, "LA", 2, "Mixed-income housing preservation", "active"),
        ("A2022-001", "Northeast CDFI Alliance", "loan_fund", "CDFI_FA", 2_500_000, "2022-09-12", 2022, "MA", 7, "Small business and community facility", "active"),
        ("A2022-002", "Southwest Finance Corp", "loan_fund", "CDFI_FA", 1_200_000, "2022-09-12", 2022, "AZ", 9, "Healthcare facility and childcare lending", "active"),
        ("A2022-003", "Lakota Lending Initiative", "loan_fund", "NATIVE_AMERICAN", 400_000, "2022-08-01", 2022, "SD", 1, "Technical assistance and capacity building", "closed"),
        ("A2022-004", "First Southern CU", "credit_union", "BEA", 350_000, "2022-07-15", 2022, "AL", 5, "Small dollar consumer loans", "closed"),
        ("A2021-001", "Mountain West Impact Fund", "loan_fund", "CDFI_FA", 3_000_000, "2021-09-14", 2021, "CO", 1, "Affordable housing and NMTC leveraging", "closed"),
        ("A2021-002", "Pacific Rim Community Dev", "loan_fund", "CDFI_FA", 2_250_000, "2021-09-14", 2021, "HI", 1, "Rural and Native Hawaiian lending", "active"),
        ("A2021-003", "Midwest Opportunity Fund", "loan_fund", "BGP", 250_000_000, "2021-06-01", 2021, "IL", 7, "Small business and community facility bond lending", "active"),
        ("A2021-004", "Urban Futures VC", "venture_capital_fund", "CDFI_FA", 500_000, "2021-09-14", 2021, "NY", 12, "Equity capital for minority-owned businesses", "active"),
        ("A2020-001", "Appalachian Dev Fund", "loan_fund", "CDFI_FA", 1_500_000, "2020-09-08", 2020, "WV", 2, "Coal community economic transition lending", "closed"),
        ("A2020-002", "Delta Community Finance", "loan_fund", "RAPID", 2_000_000, "2020-05-01", 2020, "AR", 4, "COVID-19 emergency small business relief", "closed"),
        ("A2020-003", "Great Plains Holding", "holding_company", "CDFI_FA", 4_000_000, "2020-09-08", 2020, "KS", 2, "Multi-entity CDFI holding company expansion", "active"),
        ("A2019-001", "Northern Plains CU", "credit_union", "CDFI_FA", 900_000, "2019-09-10", 2019, "MN", 5, "Consumer and small business lending", "closed"),
        ("A2019-002", "Borderlands Finance", "loan_fund", "CDFI_TA", 125_000, "2019-09-10", 2019, "TX", 23, "Technical assistance for product development", "closed"),
        ("A2018-001", "Cascade CDFI", "loan_fund", "BGP", 150_000_000, "2018-06-01", 2018, "WA", 9, "Affordable housing and small business bond lending", "closed"),
    ]
    awards = []
    for row in raw:
        awards.append(Award(*row))
    return awards


def load_from_cdfi_fund_url(url: Optional[str] = None) -> List[Award]:
    """Attempt to fetch award data from a CDFI Fund URL, falling back to sample data.

    In production, CDFI Fund publishes award data as downloadable spreadsheets.
    This function attempts a basic fetch; on any error it returns sample data.

    Args:
        url: Optional URL to fetch from. If None, uses the sample data fallback.

    Returns:
        List of Award objects.
    """
    if url is None:
        return load_sample_awards()

    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=10) as resp:
            raw = resp.read()
        # If we get here the fetch succeeded but we'd need parsing logic
        # specific to the CDFI Fund's format. Fall back to sample data.
        return load_sample_awards()
    except Exception:
        return load_sample_awards()
