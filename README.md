# cdfi-fund-tracker

![PyPI](https://img.shields.io/pypi/v/cdfi-fund-tracker)
![Python](https://img.shields.io/pypi/pyversions/cdfi-fund-tracker)
![License](https://img.shields.io/pypi/l/cdfi-fund-tracker)

**CDFI Fund award & compliance tracker** — load, analyze, and monitor awards across all eight CDFI Fund programs: CDFI Program FA/TA, BEA, NACA, Native American TA, RAPID, Capital Magnet Fund, and CDFI Bond Guarantee Program. Track deployment deadlines, identify at-risk recipients, and run portfolio analytics.

## Why

The CDFI Fund administers eight distinct programs with different award types, deployment requirements, and compliance timelines. Tracking them all in spreadsheets means missed deadlines, duplicated analysis, and no single view of portfolio concentration. This library gives you a clean Python API for any of it: from a one-liner to pull all BEA awards by state to a compliance sweep that flags recipients overdue on deployment.

## Installation

```bash
pip install cdfi-fund-tracker
```

## Quickstart

```python
from cdfifund import (
    Award,
    ComplianceRecord,
    CDFI_PROGRAMS,
    load_sample_awards,
    cdfi_program_analysis,
    fa_vs_ta_breakdown,
    bea_program_analysis,
    bank_enterprise_award_breakdown,
    native_american_analysis,
    naca_breakdown,
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

# Load sample awards (or substitute your own list)
awards = load_sample_awards()
print(f"Loaded {len(awards)} awards across {len({a.program for a in awards})} programs")

# CDFI Program (FA + TA) summary
cdfi = cdfi_program_analysis(awards)
print(f"CDFI Program: {cdfi['award_count']} awards totaling ${cdfi['total_amount']:,.0f}")

# FA vs TA breakdown
breakdown = fa_vs_ta_breakdown(awards)
print(f"FA/TA ratio: {breakdown['fa_ta_dollar_ratio']:.1f}x")

# BEA analysis
bea = bea_program_analysis(awards)
print(f"BEA: {bea['award_count']} awards, avg ${bea['average_award']:,.0f}")

# Native American programs
na = native_american_analysis(awards)
print(f"Native American: {na['award_count']} awards in {len(na['state_breakdown'])} states")

# BGP analysis
bgp = bond_guarantee_analysis(awards)
print(f"BGP: {bgp['award_count']} issuances totaling ${bgp['total_guaranteed']:,.0f}")

# Aggregations
prog_agg = by_program(awards)
state_agg = by_state(awards)
year_agg = by_year(awards)
top10 = top_recipients(awards, n=10)
print(f"Top recipient: {top10[0]['recipient_name']} (${top10[0]['total_amount']:,.0f})")

geo = geographic_distribution(awards)
print(f"States reached: {geo['unique_states']}  HHI: {geo['herfindahl_index']:.3f}")

ts = cumulative_awards_over_time(awards)
print(f"Cumulative through {ts[-1]['year']}: ${ts[-1]['cumulative_amount']:,.0f}")

# Compliance tracking
from datetime import date, timedelta
records = [
    ComplianceRecord("R001", "CDFI_FA", 0.75, "2026-12-01", "on_track", "2025-06-01"),
    ComplianceRecord("R002", "BEA",     0.30, (date.today() + timedelta(days=60)).isoformat(),
                     "at_risk", "2025-01-01"),
    ComplianceRecord("R003", "CMF",     1.00, "2025-06-01", "completed", "2025-04-01"),
]
tracker = ComplianceTracker(records)
print(tracker.summary())

deadlines = check_deadlines(records, horizon_days=180)
print(f"Upcoming deadlines: {deadlines['upcoming_count']}  Overdue: {deadlines['overdue_count']}")

at_risk = at_risk_recipients(records)
for r in at_risk:
    print(f"  {r['recipient_id']} ({r['program']}): {r['deployment_pct']:.0%} deployed, "
          f"{r['days_remaining']} days remaining")

# Insights
conc = award_concentration_analysis(awards)
print(f"Top-10 recipients hold {conc['top_10_pct_of_total']:.0%} of total dollars")
print(f"Gini coefficient: {conc['gini_coefficient']:.3f}")

lifecycle = recipient_lifecycle_analysis(awards)
print(f"Multi-program recipients: {lifecycle['multi_program_recipients']}")

effectiveness = program_effectiveness_metrics(awards)
for prog, data in effectiveness.items():
    print(f"{prog}: {data['geographic_reach_states']} states, avg ${data['average_award']:,.0f}")
```

## Key Features

- **All 8 CDFI Fund programs** — CDFI FA, CDFI TA, BEA, NACA, Native American TA, RAPID, Capital Magnet Fund, Bond Guarantee Program
- **Compliance tracker** — `ComplianceTracker` class with `at_risk()`, `overdue()`, `on_track()`, and `summary()`
- **Deadline monitoring** — `check_deadlines()` with configurable horizon; flags both upcoming and overdue records
- **Aggregations** — slice awards by program, state, year, or recipient type in one call
- **Concentration metrics** — HHI, Gini coefficient, top-10 share for both recipients and programs
- **Recipient lifecycle** — first-time vs. repeat vs. multi-program participation analysis
- **Geographic distribution** — state-level shares, HHI, top/bottom states
- **Cumulative time series** — year-by-year and running total
- **Sample data** — 24 realistic awards across all programs, years, and geographies for instant prototyping

## Use Cases

- **CDFI fund managers** monitoring deployment deadlines across a compliance portfolio
- **Researchers** analyzing CDFI Fund award patterns and geographic concentration
- **Grant writers** quickly summarizing award history for applications
- **Policy analysts** comparing program activity over time
- **CDFIs** tracking their own award history and peer benchmarking

## License

MIT © Jay Patel
