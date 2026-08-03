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

- **Constructor validation is now exhaustive.** Every field of every dataclass
  is either validated or documented as unvalidated in the README's constraints
  table; there is no third category. Newly enforced, all raising `ValueError`:

  | Field | Rule | Previously |
  |---|---|---|
  | `Recipient.type` | must be in `RECIPIENT_TYPES` | accepted anything, incl. `None`, `42`, `''` |
  | `Recipient.programs_received` | every element in `CDFI_PROGRAMS` | accepted anything |
  | `ComplianceRecord.program` | must be in `CDFI_PROGRAMS` | accepted anything |
  | `Award.state` | must be in `US_STATES_AND_TERRITORIES` | accepted `il`, `Illinois`, `" IL"`, `ZZ` |
  | `Award.award_date` | strict `YYYY-MM-DD`, real calendar date | accepted anything |
  | `ComplianceRecord.deadline` | strict `YYYY-MM-DD`, real calendar date | accepted anything |
  | `ComplianceRecord.last_reporting_date` | strict `YYYY-MM-DD`, real calendar date | accepted anything |
  | `Award.award_year` | `int >= 1994` | accepted `1776`, `"2024"`, `None` |
  | `Award.award_amount` | must be **finite** | `nan` passed, because `nan <= 0` is False |
  | `Recipient.total_awards` | must be **finite** | `nan` passed, because `nan < 0` is False |

  **Migration:** records your code builds today may now raise. Every message
  names the field, the rule, and the offending value. If a date raises, it was
  never being counted correctly — see the `deadline` note below.

- **Malformed `deadline` values are rejected at construction instead of being
  silently dropped from every compliance report.** Previously a record with
  `deadline="09/15/2024"` was constructible and then vanished: `is_at_risk` and
  `is_overdue` returned `False`, `check_deadlines()` omitted it from both
  `upcoming_deadlines` and `overdue`, and `at_risk_recipients()` dropped it —
  while `summary()`'s `total_records` still counted it. Six records in, three
  malformed, and `summary()` reported an at-risk rate of 1/6 = 16.7% where the
  truth was 2/6 = 33.3%. A short numerator over a full denominator, with no
  error and no count of what was dropped.

  The four `except ValueError` handlers that implemented the skip were
  **removed rather than kept as defensive depth.** They were not dead code:
  these dataclasses are mutable, so `record.deadline = "garbage"` after
  construction still reaches them. The question was what they should *do* when
  reached, and silently reporting a record as "not at risk" because its date
  could not be read is the under-counting this release exists to remove. They
  now raise.

- **The date guard is version-stable.** `date.fromisoformat` accepts only
  `YYYY-MM-DD` on Python 3.9/3.10 but also accepts `20240915` and ISO week
  dates like `2024-W37-1` on 3.11+. With a 3.9–3.12 support matrix that would
  make the same record valid on one interpreter and invalid on another. The new
  `parse_iso_date()` helper matches `^\d{4}-\d{2}-\d{2}$` and then constructs a
  `date`, so `2024-02-29` is accepted and `2024-02-30` is rejected identically
  on every supported version. It is used at construction *and* at every parsing
  site, so validation and parsing cannot diverge.

  Non-string input (`None`, a real `datetime.date`) now raises `ValueError` at
  construction rather than a bare `TypeError` from inside a property.

### Added

- **`US_STATES_AND_TERRITORIES`** — the 50 states, DC, and 5 territories (56
  codes), exported from the package root and published in the README.
- **`parse_iso_date()`** — the package's single date gate, exported so callers
  can validate with exactly the same rule before constructing records.
- **`MANIFEST.in`** — the 0.2.0 sdist shipped `tests/test_*.py` without
  `conftest.py` (setuptools' legacy default matches only `tests/test*.py`), so
  `pip install <sdist> && pytest` gave 72 passed / 85 errors: every
  fixture-dependent test failing at setup. `CHANGELOG.md` was absent too, which
  made the README's relative link 404 on the PyPI project page. Third instance
  of this defect in the portfolio after sbic-tracker and oz-tracker.
- **`release.yml` job `test-sdist`** — unpacks the built sdist, installs it, and
  runs **its own** shipped suite from a directory that contains neither the
  checkout nor `./cdfifund`. The existing `test-wheel` job copies `tests/` from
  the git checkout, so it structurally cannot detect a broken sdist; `twine
  check --strict` passed on the broken artifact. A gate must consume the
  artifact it certifies. Verified to fail when `recursive-include` is removed.
- **`cdfifund/exceptions.py`** — `CDFIFundTrackerError` (base) and
  `CDFIFundDownloadError` (subclass). Both exported from the package root and
  listed in `__all__`. The package previously had no exception module.
- **`.github/workflows/ci.yml`** — install and test on Python 3.9–3.12 for
  every push and PR to `main`. Never publishes, never requests `id-token`.
- **`.github/workflows/release.yml`** — tag-triggered six-job release
  pipeline: `verify-version` → `build` → (`test-wheel`, `test-sdist`) →
  `twine-check` → `publish`. All actions SHA-pinned; publishing via PyPI Trusted Publisher
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
  against the package: the stated test count, that the constraints table names
  **every** field of every dataclass, and — for each documented vocabulary —
  that an invalid value actually raises while every valid code is accepted.
  The last of these replaces a test that only checked whether the codes
  appeared in the markdown, which is why `Recipient.type` shipped documented as
  validated while validating nothing.

- **All four GitHub-owned actions moved off the deprecated `node20` runtime.**
  `actions/checkout` v4.3.1 → v7.0.1, `actions/setup-python` v5.6.0 → v7.0.0,
  `actions/upload-artifact` v4.6.2 → v7.0.1, `actions/download-artifact` v4.3.0
  → v8.0.1 — all now `node24`, each re-pinned to a commit SHA resolved against
  the GitHub API. `pypa/gh-action-pypi-publish` is a composite action, is
  unaffected, and keeps its existing pin, which is correctly the *dereferenced*
  commit of annotated tag v1.14.0 rather than the tag object.

  The matrix jobs now pin `runs-on: ubuntu-24.04` instead of `ubuntu-latest`.
  `actions/python-versions` ships no Python 3.9 build for ubuntu-26.04, and 3.9
  is this package's declared floor, so `ubuntu-latest` would break the release
  gate whenever the runner image rolls forward.
- **`CHANGELOG.md`** — this file.

### Fixed

- **Numeric fields accept every finite real number, not just `int` and
  `float`.** The type gate was `isinstance(value, (int, float))`, which let
  `numpy.float64` through only because that type happens to subclass `float`,
  and refused `numpy.int64`, `numpy.int32`, `numpy.float32`, `decimal.Decimal`
  and `fractions.Fraction` with `award_amount must be a number` — an assertion
  that is false about a finite number, and about the exact value the README's
  own constraints table said the field required.

  It was reachable from this package's only documented workflow. A plain
  integer dollar column read through pandas yields `numpy.int64` from `.iloc`,
  `.at`, `.loc`, `Series.iloc` and `.sum()`, while `to_dict("records")` and
  `itertuples()` coerce to Python `int` and survived — so whether a caller's
  data loaded at all depended on which access pattern they reached for.
  `deployment_pct=numpy.int64(1)`, a fully deployed record, was refused too.

  The gate is now `numbers.Real` or `Decimal`, with `bool` excluded explicitly
  (it is both `Real` and `Integral`, so without that clause
  `Award(award_amount=True)` would construct as a $1.00 award). `Decimal` is
  named separately because it is deliberately not registered as `numbers.Real`
  — an ABC check alone would still have refused what is arguably the most
  correct type for a currency field. `award_year` uses `numbers.Integral`: a
  fractional year is not a year.

  **Accepted values are coerced to built-ins** — `float` for the three
  dollar/fraction fields, `int` for `award_year`. This extends existing
  behaviour rather than introducing it; the fields have been reassigned through
  `float()` since the validator existed, so `award_amount=1_500_000` has always
  read back as `1500000.0`. Coercion rather than store-as-given because
  `Decimal + float` raises `TypeError`, and every aggregation here sums these
  fields — one `Decimal` award in a portfolio of floats would have aborted
  `by_program()`, a failure that did not previously exist. Secondarily, `numpy`
  scalars and `Decimal` are not JSON-serializable and `numpy.int64` is rejected
  as a dict *key*, which is how `by_year()` returns `award_year`; nothing in
  this package serializes, so storing them as passed would have failed in the
  caller's code instead of here. The cost is that an exact
  `Decimal("1500000.07")` stops being exact — unavoidable, since every
  downstream computation is float arithmetic.

  All four bounds checks still apply to the newly accepted types, and
  `nan`, `inf`, `Decimal('NaN')`, `Decimal('Infinity')`, strings, `None`,
  `complex` and `bool` are still rejected.

- **A magnitude too large to represent as a float no longer escapes as
  `OverflowError`.** `math.isfinite(10**400)` raises rather than returning
  `False`, so `Award(award_amount=10**400)` left the constructor with an
  `OverflowError` — not a `ValueError` at all, breaking this package's stated
  convention that every constructor violation is a `ValueError`.
  `Decimal('sNaN')` raised a `ValueError` that named no field. Both now raise
  `ValueError` naming the field.

- **`Recipient.programs_received` type-checks the container before iterating
  it.** `None` — what a null CSV cell becomes — raised `TypeError`
  (`'NoneType' object is not iterable`) from the loop, contradicting the
  convention `parse_iso_date`'s docstring states outright: non-string input
  raises `ValueError` precisely so a null cell surfaces "as the same error type
  as every other constructor violation". A bare string `"CDFI_FA"` is iterable,
  so it was rejected — but character by character, and the message reported the
  offending value as `'C'`, a value the caller never wrote. `list`, `tuple` and
  `set` are accepted; anything else raises `ValueError` naming the actual value.

- **Batch compliance aborts now name the offending record.** Removing the
  `except ValueError` handlers was right — the dataclasses are mutable, so
  `record.deadline = "garbage"` still reaches the parse sites, and silently
  reporting that record as "not at risk" is the under-counting this release
  exists to remove. But the abort said only
  `deadline must be YYYY-MM-DD, got 'garbage'`. With one bad record at index
  347 of 500, `summary()`, `.at_risk()`, `.overdue()`, `check_deadlines()` and
  `at_risk_recipients()` all aborted with that same text — no index, no
  `recipient_id` — and with a placeholder repeated across a portfolio it could
  not identify which record to fix. All four parse sites now carry the
  identity: `deadline (recipient_id='R-0347') must be YYYY-MM-DD, got
  'garbage'`. The batch still aborts on the first offender. Construction-time
  messages are unchanged, where the caller has the record in hand.

- **An inaccurate claim about commit `e438251` in `tests/test_schema.py`.** The
  block comment said every test below it failed against the 0.2.0 build. It did
  not: 14 of those 92 tests are positive controls that pass on both sides by
  design, so that a guard cannot be satisfied by rejecting everything. Measured
  by running that file's `db24cfc` state against an `e438251` checkout of
  `cdfifund/`: **78 failed / 14 passed**, identically on 3.9.12 and 3.12.13.
  The whole suite against the same checkout is **82 failed / 172 passed**, also
  identical on both. A figure of 79 that circulated in an interim report
  reproduces by no method and is off by one from the 78 above; it appears
  nowhere in this repository and so required no correction here.

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
  `RECIPIENT_TYPES` (5), `COMPLIANCE_STATUS_CODES` (6),
  `US_STATES_AND_TERRITORIES` (56), the `Award.status` set, the
  `Recipient.certification_status` set, and the `deployment_pct` 0.0–1.0 range
  all raise `ValueError` on violation and none appeared in the README. Users
  learned them by crashing.

  **Correction.** An earlier draft of this entry claimed all five
  `RECIPIENT_TYPES` raised `ValueError` on violation. For `Recipient.type` that
  was false when written: the field was documented as validated here and in the
  README and validated nothing. It is validated now. The test that was supposed
  to catch this only checked whether the codes appeared in the README's
  markdown; it has been rewritten to construct an invalid value and require a
  raise for every documented vocabulary, and verified to fail when the
  validation is reverted.
- **`program_effectiveness_metrics()` now carries a caveat.** Its own docstring
  says it measures award patterns, not outcomes; the README targeted "policy
  analysts" with no such warning. It has no access to jobs created, units
  financed, or any impact data, and supports no claim that one program works
  better than another.
- **Date-relativity is now disclosed.** All compliance results are relative to
  `date.today()` and change day to day for unchanged inputs.

  The silent-data-loss disclosure that accompanied this entry described records
  with a malformed `deadline` being skipped by `is_at_risk`, `is_overdue`,
  `check_deadlines()` and `at_risk_recipients()`. That behaviour no longer
  exists — such records are now rejected at construction — so the README
  subsection describing it has been rewritten rather than left documenting an
  impossible failure mode.

- **Known limitations are now disclosed rather than latent.** The README has a
  Limitations section covering recipient-level aggregation keying on
  `recipient_name` rather than `recipient_id` (two institutions sharing a name
  merge silently), `first_time_recipients` counting single-award recipients *in
  the supplied dataset* rather than first-time-ever, and validation errors being
  `ValueError` rather than `CDFIFundTrackerError`. All three are deferred to
  0.3.0 as design changes, not patches.

- **`exceptions.py` no longer claims a family it does not have.** Its docstring
  said "all exceptions raised deliberately by this package derive from
  `CDFIFundTrackerError`". The schema layer raises bare `ValueError`, which does
  not, so a single `except CDFIFundTrackerError` never caught validation
  failures. The docstring now states the actual scope and points at the deferred
  migration.

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
