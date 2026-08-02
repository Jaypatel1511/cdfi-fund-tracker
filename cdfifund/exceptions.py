"""Exception types for cdfi-fund-tracker.

Scope, stated precisely: :class:`CDFIFundTrackerError` is the base for the
package's *operational* errors -- currently only
:class:`CDFIFundDownloadError`. It is **not** yet the base for everything this
package raises. The schema layer
(:mod:`cdfifund.data.schema`) raises bare :class:`ValueError` on every
constructor violation, and :class:`ValueError` does not derive from
:class:`CDFIFundTrackerError`, so a single ``except CDFIFundTrackerError`` does
NOT catch validation failures. Catch ``(CDFIFundTrackerError, ValueError)``
to cover both.

Migrating the schema layer to a ``CDFIFundValidationError`` subclass is
deferred to 0.3.0 -- it is a breaking change for anyone currently catching
``ValueError``, and doing half of it would leave the family harder to reason
about than leaving it alone.

.. versionchanged:: 0.2.0
    This docstring previously claimed that "all exceptions raised deliberately
    by this package derive from CDFIFundTrackerError". That was never true --
    the schema layer's ``ValueError``\\ s are raised deliberately and do not.
    The claim is corrected here rather than made true, because making it true
    is the deferred breaking change described above.
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
