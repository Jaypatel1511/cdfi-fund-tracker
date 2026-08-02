# Changelog

All notable changes to cdfi-fund-tracker are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **If you used `load_from_cdfi_fund_url()` in 0.1.0, read the 0.1.0 entry
> before trusting anything it told you.** It returned 24 synthetic awards from
> every path, including on HTTP success, with no error and no signal. Anything
> derived from it needs rechecking, and this file exists so you can find that
> out without reading the source.

---

## [0.2.0] — unreleased

Prepared but **not published**. Version 0.2.0 is set in `pyproject.toml`,
`setup.py`, and `cdfifund/__init__.py`; no tag has been pushed and no artifact
uploaded.

A fail-loud correction release. The rule: **a function that cannot succeed must
not have a success-shaped return.**

### Changed — BREAKING

- **`load_from_cdfi_fund_url()` now always raises `CDFIFundDownloadError`.**
  It previously returned a `List[Award]`. It now raises for every input,
  including `url=None`, including a reachable URL that returns HTTP 200.

  There is no CDFI Fund parser in this package and never was, so there is no
  input for which the function can legitimately succeed. Returning fixtures
  from a "fetch" function is the defect; a `None` default that quietly hands
  back the same fixtures is that defect with a smaller blast radius, so the
  `None` path raises too.

  The raised message names the alternative explicitly. The synthetic fixtures
  remain reachable through `load_sample_awards()` — the function that says in
  its name what it returns. That separation is the whole correction.

  **Migration:** if you were calling `load_from_cdfi_fund_url()` and using the
  result, you were analyzing invented data. There is no drop-in replacement.
  Build `Award` objects from a source you control. If you genuinely wanted the
  fixtures, call `load_sample_awards()` directly.

- **`ComplianceRecord.is_at_risk` no longer returns `True` for records whose
  deadline has already passed.** 0.1.0 shipped two incompatible definitions of
  "at risk" under the same name:

  | Implementation | 0.1.0 condition | Included overdue records? |
  |---|---|---|
  | `ComplianceRecord.is_at_risk` | `days_remaining <= 180` | **yes** |
  | `at_risk_recipients()` | `0 <= days_remaining <= days_window` | no |

  `ComplianceTracker.at_risk()` delegates to the property, so a single record
  with a past deadline and low deployment was counted in **both**
  `at_risk_count` and `overdue_count` in `ComplianceTracker.summary()`.

  0.2.0 adopts the **forward-looking** semantic everywhere — at-risk means
  below 50% deployed with a deadline that is still ahead and no more than 180
  days out. A blown deadline is not a risk of being missed; it has been missed,
  and `is_overdue` already reported exactly that. The two sets are now
  **disjoint** and `summary()` no longer double-counts.

  **Migration:** to recover the old, broader set, use
  `r.is_at_risk or r.is_overdue`.

### Added

- **`cdfifund/exceptions.py`** — `CDFIFundTrackerError` (base) and
  `CDFIFundDownloadError` (subclass). Both exported from the package root and
  listed in `__all__`. The package previously had no exception module.
- **`.github/workflows/ci.yml`** — install and test on Python 3.9–3.12 for
  every push and PR to `main`. Never publishes, never requests `id-token`.
- **`.github/workflows/release.yml`** — tag-triggered five-job release
  pipeline: `verify-version` → `build` → `test-wheel` → `twine-check` →
  `publish`. All actions SHA-pinned; publishing via PyPI Trusted Publisher
  (OIDC, environment `pypi`), no API token.

  The version guard checks the git tag against all three version sources
  (`pyproject.toml` via `tomllib`, `setup.py` and `cdfifund/__init__.py` via
  `ast` — nothing string-scraped, nothing executed). The wheel-test job installs
  the built wheel into a fresh venv and runs the suite from a **copied
  directory that does not contain `./cdfifund`**, then asserts the resolved
  module path contains `/site-packages/`. Without that, `python -c` puts the
  cwd on `sys.path` and the check silently verifies the source tree instead of
  the wheel.
- **`Development Status :: 3 - Alpha`** classifier in both `setup.py` and
  `pyproject.toml`. `setup.py` previously declared no development status.
- **`[tool.pytest.ini_options]`** with `addopts = "--import-mode=importlib"`,
  so `import cdfifund` cannot silently resolve to the source tree when a wheel
  is under test.
- **`tests/test_readme.py`** — executes the README quickstart end to end,
  verifies every imported name is used, and checks the README's factual claims
  (test count, vocabulary coverage, disclosures) against the package.
- **`CHANGELOG.md`** — this file.

### Fixed

- **README no longer describes the sample data as "24 realistic awards."** They
  are 24 **synthetic, invented** awards. No row corresponds to a real CDFI Fund
  award and none was sourced from the CDFI Fund.
- **README no longer implies a data-ingestion path exists.** It does not.
  There is no CSV, XLSX, or API reader anywhere in the package and
  `dependencies = []`. The README now leads with "bring your own data."
- **README quickstart no longer imports `track_deployment` and
  `by_recipient_type` without using them.** Both are now demonstrated, and a
  test fails the build if any imported name goes unused.
- **`Recipient` is now documented.** It was in `__all__` and absent from the
  README.
- **Validated vocabularies are now published.** `CDFI_PROGRAMS` (8),
  `RECIPIENT_TYPES` (5), `COMPLIANCE_STATUS_CODES` (6), the `Award.status` set,
  the `Recipient.certification_status` set, and the `deployment_pct` 0.0–1.0
  range all raise `ValueError` on violation and none appeared in the README.
  Users learned them by crashing.
- **`program_effectiveness_metrics()` now carries a caveat.** Its own docstring
  says it measures award patterns, not outcomes; the README targeted "policy
  analysts" with no such warning. It has no access to jobs created, units
  financed, or any impact data, and supports no claim that one program works
  better than another.
- **Date-relativity and silent data loss are now disclosed.** All compliance
  results are relative to `date.today()` and change day to day for unchanged
  inputs. Records with a malformed (non-ISO) `deadline` are silently skipped by
  `is_at_risk`, `is_overdue`, `check_deadlines()`, and `at_risk_recipients()` —
  they appear in no bucket and no count, with no error.

### Removed

- Unused `json` and `ComplianceRecord` imports in `cdfifund/data/loader.py`.

---

## [0.1.0] — 2026-05-10 (published, superseded)

Initial release. All eight CDFI Fund programs, compliance tracking,
aggregations, and program analyses. 115 tests passing.

**Defect — fabricated data presented as real.** `load_from_cdfi_fund_url()`
returned 24 synthetic sample awards on **every** path:

- HTTP fetch **succeeded** → discarded the response body, returned samples
- HTTP fetch failed → `except Exception:` swallowed it, returned samples
- `url=None` → returned samples without attempting a fetch at all

A caller who passed a real CDFI Fund URL received invented awards presented as
real data, with no exception, no warning, and no signal of any kind. Those
awards then flowed into `by_program()`, `by_state()`, `top_recipients()`,
`award_concentration_analysis()`, and `program_effectiveness_metrics()`.

The function was exported in `__all__` and documented as a data loader.

**Any 0.1.0 result derived from `load_from_cdfi_fund_url()` should be
discarded.** Results built from `Award` objects you constructed yourself, or
from `load_sample_awards()` used knowingly as fixtures, are unaffected — the
analysis, aggregation, and compliance layers work as documented, with the
`is_at_risk` divergence noted under 0.2.0 above.

[0.2.0]: https://github.com/Jaypatel1511/cdfi-fund-tracker/releases/tag/v0.2.0
[0.1.0]: https://pypi.org/project/cdfi-fund-tracker/0.1.0/
