"""Exception types for cdfi-fund-tracker.

All exceptions raised deliberately by this package derive from
:class:`CDFIFundTrackerError`, so callers can catch the whole family with a
single ``except`` clause.
"""


class CDFIFundTrackerError(Exception):
    """Base class for all cdfi-fund-tracker errors."""


class CDFIFundDownloadError(CDFIFundTrackerError):
    """Raised when CDFI Fund award data cannot be downloaded or parsed.

    This package ships no CDFI Fund ingestion path, so
    :func:`cdfifund.data.loader.load_from_cdfi_fund_url` raises this
    unconditionally rather than substituting synthetic sample data.
    """


__all__ = ["CDFIFundTrackerError", "CDFIFundDownloadError"]
