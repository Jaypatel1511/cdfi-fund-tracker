"""Synthetic sample data loader.

This package ships no CDFI Fund ingestion path. :func:`load_sample_awards`
returns synthetic fixtures for prototyping and testing;
:func:`load_from_cdfi_fund_url` always raises.
"""

from typing import List, Optional

from cdfifund.data.schema import Award
from cdfifund.exceptions import CDFIFundDownloadError


def load_sample_awards() -> List[Award]:
    """Return 24 SYNTHETIC sample awards for testing, demos, and prototyping.

    These awards are invented. The recipient names, award IDs, dollar amounts,
    dates, states, and congressional districts are all fabricated. They are
    shaped to resemble historical CDFI Fund award patterns so that downstream
    analytics have something plausible to chew on, but no row corresponds to a
    real CDFI Fund award and none was sourced from the CDFI Fund.

    Do not use this data for analysis, reporting, or any purpose where the
    numbers are taken to mean something. To analyze real CDFI Fund awards,
    construct :class:`~cdfifund.data.schema.Award` objects from a source you
    control -- this package has no ingestion path of its own.

    Returns:
        List of 24 synthetic Award objects covering all eight programs,
        award years 2018-2024, and 24 states.
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


_NO_INGESTION_PATH = (
    "cdfi-fund-tracker has no CDFI Fund ingestion path. No parser for any CDFI "
    "Fund award format (CSV, XLSX, or API) was ever implemented in this package, "
    "so load_from_cdfi_fund_url() cannot succeed for any URL and always raises.\n"
    "\n"
    "In version 0.1.0 this function returned sample data -- 24 synthetic sample "
    "awards -- instead of raising, on every path, including when the HTTP fetch "
    "SUCCEEDED. "
    "Callers who passed a real CDFI Fund URL received invented awards presented "
    "as real data, with no error and no signal, and those awards then flowed "
    "into by_program(), by_state(), top_recipients(), "
    "award_concentration_analysis(), and program_effectiveness_metrics(). "
    "Any 0.1.0 result derived from this function should be discarded.\n"
    "\n"
    "The sample awards are still available, but only from the function that "
    "says what they are: load_sample_awards(). They are synthetic and "
    "illustrative -- not real CDFI Fund award records -- and must not be used "
    "as a data source for analysis or reporting.\n"
    "\n"
    "To analyze real CDFI Fund data, build Award objects yourself from a source "
    "you control and pass them to this package's analysis functions."
)


def load_from_cdfi_fund_url(url: Optional[str] = None) -> List[Award]:
    """Always raises: this package has no CDFI Fund ingestion path.

    No parser for the CDFI Fund's published award formats was ever implemented,
    so there is no input for which this function can legitimately succeed. It
    raises unconditionally rather than silently substituting synthetic data --
    including when ``url`` is None, and including when an HTTP fetch succeeds.

    Args:
        url: Ignored. Present only to preserve the 0.1.0 call signature so that
            existing callers raise instead of failing with a TypeError.

    Raises:
        CDFIFundDownloadError: Always, unconditionally.

    See Also:
        load_sample_awards: The only path to the synthetic sample fixtures.
    """
    raise CDFIFundDownloadError(_NO_INGESTION_PATH)
