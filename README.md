# cdfi-fund-tracker

![PyPI](https://img.shields.io/pypi/v/cdfi-fund-tracker)
![Python](https://img.shields.io/pypi/pyversions/cdfi-fund-tracker)
![License](https://img.shields.io/pypi/l/cdfi-fund-tracker)

**Analysis and compliance tooling for CDFI Fund awards** — aggregations, concentration metrics, deployment-deadline tracking, and per-program analyses across all eight CDFI Fund programs: CDFI Program FA/TA, BEA, NACA, Native American TA, RAPID, Capital Magnet Fund, and CDFI Bond Guarantee Program.

## Read this first: bring your own data

**This package does not load CDFI Fund data.** There is no CSV reader, no XLSX reader, no API client, and no scraper anywhere in it. `dependencies = []` — it ships nothing that could fetch or parse a spreadsheet.

What it gives you is the layer *above* ingestion: you construct `Award` and `ComplianceRecord` objects from a source you control, and this package aggregates, ranks, concentrates, and compliance-checks them. That layer is tested and works. The ingestion layer was never built.

Two functions are easy to mistake for a data source. They are not:

| Function | What it does |
|---|---|
| `load_from_cdfi_fund_url()` | **Always raises `CDFIFundDownloadError`.** No URL succeeds. |
| `load_sample_awards()` | Returns **24 synthetic, invented awards**. Not real CDFI Fund records. Prototyping only. |

### If you used 0.1.0, read this

In 0.1.0, `load_from_cdfi_fund_url()` returned the 24 synthetic sample awards from **every** path — including when the HTTP fetch **succeeded**, and including when `url` was `None` (where it never attempted a fetch at all). Every exception was swallowed. A caller who passed a real CDFI Fund URL got invented awards back, presented as real data, with no error and no warning. Those awards then flowed into `by_program()`, `by_state()`, `top_recipients()`, `award_concentration_analysis()`, and `program_effectiveness_metrics()`.

**Any 0.1.0 output derived from `load_from_cdfi_fund_url()` should be discarded.** As of 0.2.0 the function raises unconditionally; the synthetic fixtures are reachable only through `load_sample_awards()`, which says in its name what it is.

Implementing real CDFI Fund ingestion is out of scope for 0.2.0 and is not currently planned.

## Installation

```bash
pip install cdfi-fund-tracker
```

## Quickstart

```python
from cdfifund import (
    Award,
    Recipient,
    ComplianceRecord,
    CDFI_PROGRAMS,
    RECIPIENT_TYPES,
    COMPLIANCE_STATUS_CODES,
    US_STATES_AND_TERRITORIES,
    parse_iso_date,
    CDFIFundDownloadError,
    load_sample_awards,
    load_from_cdfi_fund_url,
    cdfi_program_analysis,
    fa_vs_ta_breakdown,
    bea_program_analysis,
    native_american_analysis,
    bond_guarantee_analysis,
    ComplianceTracker,
    track_deployment,
    check_deadlines,
    at_risk_recipients,
    by_program,
    by_state,
    by_year,
    by_recipient_type,
    top_recipients,
    geographic_distribution,
    cumulative_awards_over_time,
    award_concentration_analysis,
    recipient_lifecycle_analysis,
    program_effectiveness_metrics,
)

# ---------------------------------------------------------------------------
# There is no ingestion path. This is what asking for one gets you:
# ---------------------------------------------------------------------------
try:
    load_from_cdfi_fund_url("https://www.cdfifund.gov/some/awards.csv")
except CDFIFundDownloadError as exc:
    print(f"As designed — no parser exists: {str(exc).splitlines()[0]}")

# In real use you build Award objects yourself, from a source you control:
my_award = Award(
    award_id="A2024-100",
    recipient_name="Example Community Lender",
    recipient_type="loan_fund",        # must be in RECIPIENT_TYPES
    program="CDFI_FA",                 # must be in CDFI_PROGRAMS
    award_amount=1_250_000,
    award_date="2024-09-15",
    award_year=2024,
    state="IL",
    congressional_district=7,
    intended_use="Small business lending",
    status="active",                   # 'active' | 'closed' | 'pending'
)

# Everything the constraints table claims is enforced, is enforced. Each of
# these raises ValueError naming the field, the rule, and the value you passed:
for bad_kwargs in (
    {"recipient_type": "Loan Fund"},   # display label, not the code
    {"program": "NOT_A_PROGRAM"},      # not in CDFI_PROGRAMS
    {"state": "Illinois"},             # not in US_STATES_AND_TERRITORIES
    {"state": "il"},                   # right place, wrong case
    {"award_date": "09/15/2024"},      # not YYYY-MM-DD
    {"award_date": "2024-02-30"},      # well-formed but not a real date
    {"award_amount": float("nan")},    # nan <= 0 is False; the guard used to miss it
    {"award_year": 1776},              # before the CDFI Fund existed
):
    fields = {**my_award.__dict__, **bad_kwargs}
    try:
        Award(**fields)
        raise AssertionError(f"expected ValueError for {bad_kwargs}")
    except ValueError as exc:
        print(f"rejected {bad_kwargs}: {exc}"[:96])

print(f"{len(US_STATES_AND_TERRITORIES)} valid state/territory codes; "
      f"IL is {US_STATES_AND_TERRITORIES['IL']}")
print(f"parse_iso_date is the single date gate: {parse_iso_date('2024-09-15', 'award_date')}")

# For the rest of this quickstart we use the SYNTHETIC sample set, so the
# numbers below are illustrative and mean nothing about real CDFI Fund awards.
awards = load_sample_awards()
print(f"{len(awards)} synthetic awards across {len({a.program for a in awards})} programs")

# Per-program analyses
cdfi = cdfi_program_analysis(awards)
print(f"CDFI Program: {cdfi['award_count']} awards totaling ${cdfi['total_amount']:,.0f}")
print(f"FA/TA ratio: {fa_vs_ta_breakdown(awards)['fa_ta_dollar_ratio']:.1f}x")

bea = bea_program_analysis(awards)
print(f"BEA: {bea['award_count']} awards, avg ${bea['average_award']:,.0f}")

na = native_american_analysis(awards)
print(f"Native American: {na['award_count']} awards in {len(na['state_breakdown'])} states")

bgp = bond_guarantee_analysis(awards)
print(f"BGP: {bgp['award_count']} issuances totaling ${bgp['total_guaranteed']:,.0f}")

# Aggregations
print(f"Programs: {len(by_program(awards))}  States: {len(by_state(awards))}  "
      f"Years: {len(by_year(awards))}")
for rtype, data in by_recipient_type(awards).items():
    print(f"  {RECIPIENT_TYPES[rtype]}: {data['count']} awards, "
          f"${data['total_amount']:,.0f}")

top10 = top_recipients(awards, n=10)
print(f"Top recipient: {top10[0]['recipient_name']} (${top10[0]['total_amount']:,.0f})")

geo = geographic_distribution(awards)
print(f"States reached: {geo['unique_states']}  HHI: {geo['herfindahl_index']:.3f}")

ts = cumulative_awards_over_time(awards)
print(f"Cumulative through {ts[-1]['year']}: ${ts[-1]['cumulative_amount']:,.0f}")

# ---------------------------------------------------------------------------
# Compliance tracking. NOTE: every result below is relative to date.today().
# ---------------------------------------------------------------------------
from datetime import date, timedelta

records = [
    ComplianceRecord("R001", "CDFI_FA", 0.75, (date.today() + timedelta(days=400)).isoformat(),
                     "on_track", "2025-06-01"),
    ComplianceRecord("R002", "BEA", 0.30, (date.today() + timedelta(days=60)).isoformat(),
                     "at_risk", "2025-01-01"),
    ComplianceRecord("R003", "BGP", 0.10, (date.today() - timedelta(days=30)).isoformat(),
                     "in_default", "2024-12-01"),
    ComplianceRecord("R004", "CMF", 1.00, (date.today() - timedelta(days=90)).isoformat(),
                     "completed", "2025-04-01"),
]

tracker = ComplianceTracker(records)
summary = tracker.summary()
print(f"at_risk={summary['at_risk_count']}  overdue={summary['overdue_count']}  "
      f"on_track={summary['on_track_count']}  (disjoint as of 0.2.0)")

stats = track_deployment(records)
print(f"Average deployment: {stats['average_deployment_pct']:.0%}  "
      f"below 50%: {stats['below_50_pct']}  by status: {stats['by_status']}")

deadlines = check_deadlines(records, horizon_days=180)
print(f"Upcoming: {deadlines['upcoming_count']}  Overdue: {deadlines['overdue_count']}")

for r in at_risk_recipients(records):
    print(f"  AT RISK {r['recipient_id']} ({r['program']}): {r['deployment_pct']:.0%} "
          f"deployed, {r['days_remaining']} days left")

for r in tracker.overdue():
    print(f"  OVERDUE {r.recipient_id} ({r.program}): {r.deployment_pct:.0%} deployed, "
          f"deadline {r.deadline}")

# Recipient is a standalone record type for institution-level rollups. Nothing
# in this package builds one for you — construct them yourself.
recipient = Recipient(
    recipient_id="R001",
    name="Example Community Lender",
    type="loan_fund",                  # must be in RECIPIENT_TYPES
    certification_status="certified",  # 'certified' | 'applicant' | 'formerly_certified'
    total_awards=3_750_000,
    programs_received=["CDFI_FA", "CMF"],
    geographic_areas=["IL", "IN"],
)
print(f"{recipient.name}: ${recipient.total_awards:,.0f} across "
      f"{len(recipient.programs_received)} programs")

# Insights
conc = award_concentration_analysis(awards)
print(f"Top-10 recipients hold {conc['top_10_pct_of_total']:.0%} of dollars; "
      f"Gini {conc['gini_coefficient']:.3f}")
print(f"Multi-program recipients: {recipient_lifecycle_analysis(awards)['multi_program_recipients']}")

# NOTE: these are award-pattern proxies, not outcome measures. See caveat below.
for prog, data in program_effectiveness_metrics(awards).items():
    print(f"{prog}: {data['geographic_reach_states']} states, avg ${data['average_award']:,.0f}")

print(f"Status codes: {', '.join(COMPLIANCE_STATUS_CODES)}")
print(f"Programs: {', '.join(CDFI_PROGRAMS)}")
```

## Validated vocabularies

The dataclasses validate on construction and raise `ValueError` on anything outside these sets. All four tables are importable from `cdfifund`.

Every claim in this section is executed by the test suite: for each vocabulary, an invalid value must raise **and** every valid code must be accepted. Through 0.2.0's build that test only checked whether the codes appeared in this markdown — which is how `Recipient.type`, named in the heading two subsections down, shipped documented-as-validated and validating nothing.

### `CDFI_PROGRAMS` — valid `Award.program`, `ComplianceRecord.program`, and every element of `Recipient.programs_received`

| Code | Program |
|---|---|
| `CDFI_FA` | CDFI Program Financial Assistance |
| `CDFI_TA` | CDFI Program Technical Assistance |
| `BEA` | Bank Enterprise Award Program |
| `NACA` | Native American CDFI Assistance Program |
| `NATIVE_AMERICAN` | Native American CDFI Assistance — TA |
| `RAPID` | CDFI Rapid Response Program |
| `BGP` | CDFI Bond Guarantee Program |
| `CMF` | Capital Magnet Fund |

### `RECIPIENT_TYPES` — valid `Award.recipient_type` and `Recipient.type`

Pass the **code**, not the display label: `type="loan_fund"`, not `type="Loan Fund"`.

| Code | Type |
|---|---|
| `loan_fund` | Loan Fund |
| `depository_institution` | Depository Institution |
| `credit_union` | Credit Union |
| `venture_capital_fund` | Venture Capital Fund |
| `holding_company` | Holding Company |

### `COMPLIANCE_STATUS_CODES` — valid `ComplianceRecord.status`

| Code | Meaning |
|---|---|
| `on_track` | On track — meeting deployment milestones |
| `at_risk` | At risk — below milestone pace |
| `in_default` | In default — past deadline with material shortfall |
| `completed` | Completed — fully deployed and closed |
| `extended` | Extended — deadline extended by CDFI Fund |
| `pending_review` | Pending review — awaiting CDFI Fund determination |

### `US_STATES_AND_TERRITORIES` — valid `Award.state`

The 50 states, `DC`, and five territories: `AS`, `GU`, `MP`, `PR`, `VI`. Uppercase USPS codes, matched exactly — 56 in all, importable from `cdfifund`.

`il`, `Illinois`, `" IL"` and `ZZ` all raise. They are the same place under four spellings, and accepting them made `geographic_distribution()` report one state as four. Military codes (`AA`/`AE`/`AP`) and the Freely Associated States (`FM`/`MH`/`PW`) are excluded — they are not CDFI Fund award jurisdictions.

### Every constructor constraint

Exhaustive: every field of every dataclass, validated or not. Anything marked *not validated* is accepted as-is and never checked, so check it yourself before you rely on it.

**`Award`**

| Field | Rule |
|---|---|
| `Award.award_id` | **not validated** — an opaque caller-side key; uniqueness is not enforced |
| `Award.recipient_name` | **not validated** — free text, and the key aggregation groups on (see Limitations) |
| `Award.recipient_type` | must be in `RECIPIENT_TYPES` |
| `Award.program` | must be in `CDFI_PROGRAMS` |
| `Award.award_amount` | must be a **finite** number `> 0`. Any real numeric type — `int`, `float`, `numpy` scalars, `Decimal`, `Fraction` — **stored as `float`** (see below). `nan`, `inf`, `Decimal('NaN')` raise; so does a string or a bool |
| `Award.award_date` | must be `YYYY-MM-DD` and a real calendar date |
| `Award.award_year` | must be an integer `>= 1994` — `int` or any `numbers.Integral` such as `numpy.int64`, **stored as `int`**. A fractional year raises, and so does `Decimal`. **Not** cross-checked against `award_date` — see below |
| `Award.state` | must be in `US_STATES_AND_TERRITORIES` |
| `Award.congressional_district` | **not validated** — `int` or `None`; numbering is state-dependent and changes with redistricting, and nothing here consumes it |
| `Award.intended_use` | **not validated** — free text by design |
| `Award.status` | must be `active`, `closed`, or `pending` (default `active`) |

**`Recipient`**

| Field | Rule |
|---|---|
| `Recipient.recipient_id` | **not validated** — an opaque caller-side key. Nothing in this package consumes it (see Limitations) |
| `Recipient.name` | **not validated** — free text |
| `Recipient.type` | must be in `RECIPIENT_TYPES` |
| `Recipient.certification_status` | must be `certified`, `applicant`, or `formerly_certified` |
| `Recipient.total_awards` | must be a **finite** number `>= 0`, same accepted types as `Award.award_amount`, **stored as `float`**. `nan` and `inf` raise |
| `Recipient.programs_received` | must be a `list`, `tuple`, or `set` — a bare string raises, even one spelling a valid code — and every element must be in `CDFI_PROGRAMS`. An empty container is allowed |
| `Recipient.geographic_areas` | **not validated** — documented as states *or regions*, so it is not a state-code vocabulary |

**`ComplianceRecord`**

| Field | Rule |
|---|---|
| `ComplianceRecord.recipient_id` | **not validated** — an opaque caller-side key; this package never resolves it against a `Recipient` |
| `ComplianceRecord.program` | must be in `CDFI_PROGRAMS` |
| `ComplianceRecord.deployment_pct` | must be a **finite** number `0.0 <= pct <= 1.0` — a **fraction**, not a percent. `50` raises; use `0.50`. Same accepted types as `Award.award_amount`, **stored as `float`** |
| `ComplianceRecord.deadline` | must be `YYYY-MM-DD` and a real calendar date |
| `ComplianceRecord.status` | must be in `COMPLIANCE_STATUS_CODES` |
| `ComplianceRecord.last_reporting_date` | must be `YYYY-MM-DD` and a real calendar date |

#### Numbers: which types are accepted, and what is stored (changed in 0.2.0)

The numeric fields take **any finite real number**, not just `int` and `float`. `numpy.int64`, `numpy.int32`, `numpy.float32`, `numpy.float64`, `decimal.Decimal` and `fractions.Fraction` are all accepted. This matters because this package's whole premise is that you build records from your own source: a plain integer dollar column read through pandas hands you a `numpy.int64` from `.iloc`, `.at`, `.loc`, `Series.iloc` and `.sum()`, and through 0.2.0's build every one of those raised `award_amount must be a number` — about a value that is, plainly, a number. `df.to_dict("records")` and `itertuples()` happened to yield Python `int` and worked, so whether your data loaded depended on which access pattern you reached for.

**Accepted values are coerced to built-ins**, not stored as you passed them: the three dollar/fraction fields become `float`, and `award_year` becomes `int`.

```
a = Award(..., award_amount=Decimal("1500000"), award_year=numpy.int64(2024), ...)
type(a.award_amount)   # <class 'float'>  — not Decimal
type(a.award_year)     # <class 'int'>    — not numpy.int64
```

This is not new in kind — the field has been reassigned through a `float()` since the validator existed, so `award_amount=1_500_000` has always read back as `1500000.0`. 0.2.0 widens which types get in, not what happens to them after. Two reasons it coerces rather than storing what you passed:

- **`Decimal + float` raises `TypeError`.** Every aggregation here sums these fields, so a single `Decimal` award in a portfolio of floats would abort `by_program()`. Accepting the type without converting it would have introduced a failure that did not previously exist.
- **`numpy` scalars and `Decimal` are not JSON-serializable**, and `numpy.int64` is rejected as a dict *key* too — which is exactly how `by_year()` returns `award_year`. Nothing in this package serializes, so storing them as given would not fail *here*; it would fail in your code, one layer away from the constructor that admitted the value.

The cost, stated plainly: an exact `Decimal("1500000.07")` becomes a float and stops being exact. If you need decimal exactness end to end, this package cannot give it to you — every downstream computation is float arithmetic, so the exactness would not survive the first division either way.

`bool` is still rejected everywhere (`True` is an `int` in Python, and a `True` award is not a $1.00 award), as are `nan`, `inf`, `Decimal('NaN')`, `Decimal('Infinity')`, strings, and `None`. A value too large to represent as a float — `10**400` — raises `ValueError` naming the field, where it previously escaped as an `OverflowError`.

#### Dates: what "valid" means, and why not `date.fromisoformat`

All three date fields are checked at construction against a strict `YYYY-MM-DD` pattern, then confirmed to be a real calendar date. `2024-02-29` is accepted; `2024-02-30` raises. `09/01/2026`, `2024-9-5`, `""`, `None`, and a real `datetime.date` object all raise `ValueError` naming the field, the expected format, and the value you passed:

```
ValueError: deadline must be YYYY-MM-DD, got '09/01/2026'
```

The check is **not** `date.fromisoformat`, deliberately. On Python 3.9/3.10 that function accepts only `YYYY-MM-DD`; on 3.11+ it also accepts the compact form `20240915` and ISO week dates like `2024-W37-1`. This package supports 3.9 through 3.12, so using it would make the same record valid on one interpreter and invalid on another. A guard whose verdict depends on the interpreter is unreproducible, which is worse than no guard.

Passing a non-string raises `ValueError`, not `TypeError`. A null CSV field and a real `date` object are both natural mistakes, and through 0.2.0's build they surfaced as a bare `TypeError` from inside a property — well away from the line that caused it.

#### `award_year` is not derived from `award_date`

They are independent, on purpose. `award_year` is the **fiscal** year, and the federal fiscal year runs October–September, so an award announced `2023-11-15` legitimately belongs to FY2024. A calendar-year equality check would reject correct data.

The consequence, stated plainly: `Award(award_date="2024-09-15", award_year=2024)` and `Award(award_date="2023-11-15", award_year=2024)` are both valid, and nothing detects a genuine mismatch between the two fields. `award_year >= 1994` (the CDFI Fund's founding year) is the only bound; there is no upper bound, because a ceiling tied to the current date would make construction date-relative — the exact hazard this package warns about for compliance results. `by_year()` reports whatever `award_year` you supply.

## Compliance semantics and caveats

### Everything is relative to `date.today()`

`is_at_risk`, `is_overdue`, `ComplianceTracker.at_risk()`, `.overdue()`, `.summary()`, `check_deadlines()`, and `at_risk_recipients()` all evaluate against the current date. **The same unchanged records return different results on different days.** Nothing is cached, and there is no way to pin an as-of date. If you need a reproducible report, record the run date alongside the output.

### Malformed deadlines now fail at construction (changed in 0.2.0)

`ComplianceRecord` used to accept any string as `deadline`, and every downstream consumer caught the resulting `ValueError` and skipped the record: `is_at_risk` and `is_overdue` returned `False`, `check_deadlines()` omitted it from **both** `upcoming_deadlines` and `overdue`, and `at_risk_recipients()` dropped it entirely — while `summary()`'s `total_records` still counted it.

That produced a short numerator over a full denominator. Six records in, three with deadlines like `"09/15/2024"`, and `summary()` reported `total_records=6, at_risk_count=1, overdue_count=1` — an at-risk rate of 1/6 = 16.7% where the truth was 2/6 = 33.3%. No error, no warning, no count of what was dropped. `track_deployment()` is deadline-independent, so two views of the same portfolio disagreed and neither said why.

**0.2.0 validates all three date fields at construction.** A malformed date can no longer enter a `ComplianceRecord`, so no report can silently drop one. Every record you successfully construct is accounted for in every compliance function.

The `except ValueError` handlers that implemented the silent skip were **removed, not kept as defensive depth.** Reasoning: dataclasses here are mutable, so assigning `record.deadline = "garbage"` after construction still reaches those code paths — they were never truly unreachable. The question was therefore not "is this dead code?" but "what should happen when it runs?", and silently reporting a record as *not at risk* because its date could not be read is the exact under-counting this release exists to remove. They now raise, naming the field and the value.

### `is_at_risk` and `is_overdue` can raise

Both properties, and `check_deadlines()` / `at_risk_recipients()`, raise `ValueError` on an unreadable `deadline`. For a normally-constructed record this cannot happen. It is reachable only by mutating `deadline` after construction, which a mutable dataclass permits and this package does not defend against beyond failing loudly.

**The error names the offending record** (added in 0.2.0). These are batch entry points: one bad deadline at index 347 of 500 aborts `summary()`, `.at_risk()`, `.overdue()`, `check_deadlines()` and `at_risk_recipients()` alike, and until 0.2.0 all five said only `deadline must be YYYY-MM-DD, got 'garbage'` — no index, no `recipient_id`. With a placeholder repeated across a portfolio, that message could not tell you which record to fix. It now reads:

```
ValueError: deadline (recipient_id='R-0347') must be YYYY-MM-DD, got 'garbage'
```

The batch still aborts on the **first** offender rather than collecting them all, so fixing a portfolio with several bad deadlines takes several passes. Construction-time errors are unchanged and do not carry the identity — there you have the record in hand and the traceback points at your own call site.

### "At risk" is forward-looking (changed in 0.2.0)

0.1.0 shipped two incompatible definitions under the same name. `ComplianceRecord.is_at_risk` used `days_remaining <= 180`, which swept in records whose deadline had *already passed*; `at_risk_recipients()` used `0 <= days_remaining <= days_window`, which excluded them. `ComplianceTracker.at_risk()` delegated to the first, so a single overdue record was counted in **both** `at_risk_count` and `overdue_count` in `summary()`.

**0.2.0 adopts the forward-looking definition everywhere:** at-risk means below 50% deployed with a deadline that is still ahead and no more than 180 days out. A deadline that has already passed is not at risk of being missed — it *has been* missed, and is reported by `is_overdue` / `.overdue()` instead.

`is_at_risk` and `is_overdue` are now **disjoint**, and `summary()` no longer double-counts. If you relied on the old, broader set, use `r.is_at_risk or r.is_overdue`.

`is_at_risk` hardcodes the 50% / 180-day thresholds; `at_risk_recipients()` takes them as `threshold_pct` and `days_window` arguments, defaulting to the same values.

### `program_effectiveness_metrics()` does not measure effectiveness

It measures **award patterns** — geographic reach, average award size, recipient concentration. It has no access to outcome data: no jobs created, no units financed, no capital deployed to end borrowers, no community impact of any kind. Nothing it returns supports a claim that one program works better than another. Treat it as a descriptive profile of how a program *distributes* money, not of what that money *accomplishes*.

## Limitations

Known, unfixed, and disclosed rather than left latent. Each is a design change rather than a patch, and each is deferred to 0.3.0.

### Aggregation keys on `recipient_name`, not `recipient_id`

Every recipient-level rollup — `top_recipients()`, `award_concentration_analysis()`, `recipient_lifecycle_analysis()`, and `program_effectiveness_metrics()`'s recipient counts — groups awards by the `recipient_name` string. **Two distinct institutions that share a name merge into one row, silently.**

Verified: two "Community Bank" awards, one in IL and one in CA, collapse to `unique_recipients=1` and `single_recipient_max_pct=1.0` — a perfectly concentrated portfolio that is actually two separate banks. The reverse also holds: one institution recorded under two spellings ("Hope Community Capital" and "Hope Community Capital, Inc.") counts as two recipients.

`Award` has no `recipient_id` field, and `Recipient.recipient_id` exists but **nothing in this package consumes it**. Deduplicate on your side before you rely on any concentration metric.

### `first_time_recipients` does not mean first-time-ever

`recipient_lifecycle_analysis()['first_time_recipients']` counts recipients holding **exactly one award in the dataset you passed in**. It has no knowledge of any award outside that list. A recipient with a twenty-year award history counts as "first time" if your slice contains one of their awards. The name outruns the definition; read it as `single_award_recipients_in_this_dataset`.

### Validation errors are `ValueError`, not `CDFIFundTrackerError`

`CDFIFundTrackerError` is the base for the package's *operational* errors — currently only `CDFIFundDownloadError`. Constructor validation raises bare `ValueError`, which does **not** derive from it. A single `except CDFIFundTrackerError` will not catch a validation failure; catch `(CDFIFundTrackerError, ValueError)` to cover both.

Migrating the schema layer to a `CDFIFundValidationError` is deferred: it is a breaking change for anyone currently catching `ValueError`, and half-migrating would leave the hierarchy harder to reason about than leaving it alone.

## Key features

- **All 8 CDFI Fund programs** — CDFI FA, CDFI TA, BEA, NACA, Native American TA, RAPID, Capital Magnet Fund, Bond Guarantee Program
- **Compliance tracker** — `ComplianceTracker` with `at_risk()`, `overdue()`, `on_track()`, `summary()`
- **Deadline monitoring** — `check_deadlines()` with configurable horizon; separates upcoming from overdue
- **Aggregations** — by program, state, year, or recipient type
- **Concentration metrics** — HHI, Gini coefficient, top-10 share
- **Recipient lifecycle** — first-time vs. repeat vs. multi-program participation
- **Geographic distribution** — state-level shares, HHI, top/bottom states
- **Cumulative time series** — year-by-year and running total
- **Synthetic sample data** — 24 invented awards spanning all programs, 2018–2024, and 24 states, for prototyping only

## Use cases

Every one of these assumes **you have already loaded award data yourself**. This package does no loading.

- **CDFI fund managers** monitoring deployment deadlines across a compliance portfolio they maintain
- **Researchers** analyzing award patterns and geographic concentration in a dataset they obtained separately
- **Grant writers** summarizing an award history they already hold
- **Policy analysts** comparing program *activity* over time — see the `program_effectiveness_metrics()` caveat above; this package measures distribution patterns, not outcomes, and supports no conclusion about program impact
- **CDFIs** tracking their own award history

## Development status

**Alpha.** The analysis, aggregation, compliance, and per-program layers are implemented and tested. The data-ingestion layer does not exist and is not planned. The API may change.

## Tests

```bash
python -m pytest
```

341 tests, all passing. The suite includes tests that execute this README's
quickstart end to end and check the claims on this page — including this count,
the exhaustiveness of the constraints table above, and, for every documented
vocabulary, that an invalid value actually raises.

Six of those exercise `numpy` scalar types and skip automatically where `numpy`
is absent — it is not a dependency of this package and CI does not install it.
The rest of the numeric-type coverage runs on stdlib `Decimal` and `Fraction`,
which exercise the same guard, so nothing about it depends on a third-party
package being present.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT © Jay Patel
