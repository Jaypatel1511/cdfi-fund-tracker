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

The dataclasses validate on construction and raise `ValueError` on anything outside these sets. All three tables are importable from `cdfifund`.

### `CDFI_PROGRAMS` — valid `Award.program`

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

### Other constructor constraints

| Field | Rule |
|---|---|
| `Award.status` | must be `active`, `closed`, or `pending` (default `active`) |
| `Award.award_amount` | must be `> 0` |
| `ComplianceRecord.deployment_pct` | must be `0.0 <= pct <= 1.0` — a **fraction**, not a percent. `50` raises; use `0.50` |
| `ComplianceRecord.status` | must be in `COMPLIANCE_STATUS_CODES` |
| `Recipient.certification_status` | must be `certified`, `applicant`, or `formerly_certified` |
| `Recipient.total_awards` | must be `>= 0` |

`ComplianceRecord.deadline` and `last_reporting_date` are **not** validated at construction. A malformed date is accepted and only surfaces later — see below.

## Compliance semantics and caveats

### Everything is relative to `date.today()`

`is_at_risk`, `is_overdue`, `ComplianceTracker.at_risk()`, `.overdue()`, `.summary()`, `check_deadlines()`, and `at_risk_recipients()` all evaluate against the current date. **The same unchanged records return different results on different days.** Nothing is cached, and there is no way to pin an as-of date. If you need a reproducible report, record the run date alongside the output.

### Malformed deadlines are silently dropped

`ComplianceRecord` accepts any string as `deadline`. Downstream, every consumer catches the resulting `ValueError` and skips the record:

- `is_at_risk` and `is_overdue` return `False`
- `check_deadlines()` omits it from **both** `upcoming_deadlines` and `overdue`
- `at_risk_recipients()` omits it entirely

A record with `deadline="09/15/2024"` (not ISO `YYYY-MM-DD`) vanishes from every compliance report with no error and no count. **Validate your dates before constructing records.** Counts in `summary()` will silently under-report.

### "At risk" is forward-looking (changed in 0.2.0)

0.1.0 shipped two incompatible definitions under the same name. `ComplianceRecord.is_at_risk` used `days_remaining <= 180`, which swept in records whose deadline had *already passed*; `at_risk_recipients()` used `0 <= days_remaining <= days_window`, which excluded them. `ComplianceTracker.at_risk()` delegated to the first, so a single overdue record was counted in **both** `at_risk_count` and `overdue_count` in `summary()`.

**0.2.0 adopts the forward-looking definition everywhere:** at-risk means below 50% deployed with a deadline that is still ahead and no more than 180 days out. A deadline that has already passed is not at risk of being missed — it *has been* missed, and is reported by `is_overdue` / `.overdue()` instead.

`is_at_risk` and `is_overdue` are now **disjoint**, and `summary()` no longer double-counts. If you relied on the old, broader set, use `r.is_at_risk or r.is_overdue`.

`is_at_risk` hardcodes the 50% / 180-day thresholds; `at_risk_recipients()` takes them as `threshold_pct` and `days_window` arguments, defaulting to the same values.

### `program_effectiveness_metrics()` does not measure effectiveness

It measures **award patterns** — geographic reach, average award size, recipient concentration. It has no access to outcome data: no jobs created, no units financed, no capital deployed to end borrowers, no community impact of any kind. Nothing it returns supports a claim that one program works better than another. Treat it as a descriptive profile of how a program *distributes* money, not of what that money *accomplishes*.

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

157 tests, all passing. The suite includes tests that execute this README's
quickstart end to end and check the claims on this page — including this count.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT © Jay Patel
