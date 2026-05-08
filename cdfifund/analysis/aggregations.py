"""Award data aggregation functions."""

from typing import List, Dict, Any, Optional
from collections import defaultdict

from cdfifund.data.schema import Award


def by_program(awards: List[Award]) -> Dict[str, Dict[str, Any]]:
    """Aggregate awards by CDFI Fund program.

    Args:
        awards: List of awards.

    Returns:
        Dict mapping program code to {'count', 'total_amount', 'average_award'}.
    """
    result: Dict[str, Dict[str, Any]] = {}
    for a in awards:
        if a.program not in result:
            result[a.program] = {"count": 0, "total_amount": 0.0}
        result[a.program]["count"] += 1
        result[a.program]["total_amount"] += a.award_amount

    for prog in result:
        n = result[prog]["count"]
        result[prog]["average_award"] = result[prog]["total_amount"] / n if n else 0.0

    return result


def by_state(awards: List[Award]) -> Dict[str, Dict[str, Any]]:
    """Aggregate awards by state.

    Args:
        awards: List of awards.

    Returns:
        Dict mapping state abbreviation to {'count', 'total_amount', 'average_award'},
        sorted by total_amount descending.
    """
    result: Dict[str, Dict[str, Any]] = {}
    for a in awards:
        if a.state not in result:
            result[a.state] = {"count": 0, "total_amount": 0.0}
        result[a.state]["count"] += 1
        result[a.state]["total_amount"] += a.award_amount

    for st in result:
        n = result[st]["count"]
        result[st]["average_award"] = result[st]["total_amount"] / n if n else 0.0

    return dict(sorted(result.items(), key=lambda x: x[1]["total_amount"], reverse=True))


def by_year(awards: List[Award]) -> Dict[int, Dict[str, Any]]:
    """Aggregate awards by fiscal year.

    Args:
        awards: List of awards.

    Returns:
        Dict mapping year to {'count', 'total_amount', 'average_award'},
        sorted by year ascending.
    """
    result: Dict[int, Dict[str, Any]] = {}
    for a in awards:
        if a.award_year not in result:
            result[a.award_year] = {"count": 0, "total_amount": 0.0}
        result[a.award_year]["count"] += 1
        result[a.award_year]["total_amount"] += a.award_amount

    for yr in result:
        n = result[yr]["count"]
        result[yr]["average_award"] = result[yr]["total_amount"] / n if n else 0.0

    return dict(sorted(result.items()))


def by_recipient_type(awards: List[Award]) -> Dict[str, Dict[str, Any]]:
    """Aggregate awards by recipient type.

    Args:
        awards: List of awards.

    Returns:
        Dict mapping recipient type to {'count', 'total_amount', 'average_award'}.
    """
    result: Dict[str, Dict[str, Any]] = {}
    for a in awards:
        if a.recipient_type not in result:
            result[a.recipient_type] = {"count": 0, "total_amount": 0.0}
        result[a.recipient_type]["count"] += 1
        result[a.recipient_type]["total_amount"] += a.award_amount

    for rt in result:
        n = result[rt]["count"]
        result[rt]["average_award"] = result[rt]["total_amount"] / n if n else 0.0

    return result


def top_recipients(
    awards: List[Award],
    n: int = 10,
) -> List[Dict[str, Any]]:
    """Return the top N recipients by total award dollars.

    Args:
        awards: List of awards.
        n: Number of top recipients to return.

    Returns:
        List of dicts with 'recipient_name', 'total_amount', 'award_count',
        'programs', sorted by total_amount descending.
    """
    agg: Dict[str, Dict[str, Any]] = {}
    for a in awards:
        if a.recipient_name not in agg:
            agg[a.recipient_name] = {"total_amount": 0.0, "award_count": 0, "programs": set()}
        agg[a.recipient_name]["total_amount"] += a.award_amount
        agg[a.recipient_name]["award_count"] += 1
        agg[a.recipient_name]["programs"].add(a.program)

    rows = [
        {
            "recipient_name": name,
            "total_amount": data["total_amount"],
            "award_count": data["award_count"],
            "programs": sorted(data["programs"]),
        }
        for name, data in agg.items()
    ]
    return sorted(rows, key=lambda x: x["total_amount"], reverse=True)[:n]


def geographic_distribution(awards: List[Award]) -> Dict[str, Any]:
    """Compute geographic distribution metrics for a set of awards.

    Args:
        awards: List of awards.

    Returns:
        Dict with unique_states, top_state, bottom_state, herfindahl_index
        (concentration measure), and state_shares.
    """
    if not awards:
        return {"unique_states": 0, "state_shares": {}}

    state_totals: Dict[str, float] = {}
    grand_total = 0.0
    for a in awards:
        state_totals[a.state] = state_totals.get(a.state, 0.0) + a.award_amount
        grand_total += a.award_amount

    state_shares = {s: v / grand_total for s, v in state_totals.items()}
    hhi = sum(share ** 2 for share in state_shares.values())

    sorted_states = sorted(state_totals.items(), key=lambda x: x[1], reverse=True)
    return {
        "unique_states": len(state_totals),
        "top_state": sorted_states[0][0] if sorted_states else None,
        "bottom_state": sorted_states[-1][0] if sorted_states else None,
        "herfindahl_index": hhi,
        "state_shares": dict(sorted(state_shares.items(), key=lambda x: x[1], reverse=True)),
        "total_amount": grand_total,
    }


def cumulative_awards_over_time(awards: List[Award]) -> List[Dict[str, Any]]:
    """Build a cumulative award time series by year.

    Args:
        awards: List of awards.

    Returns:
        List of dicts sorted by year with 'year', 'annual_amount',
        'annual_count', and 'cumulative_amount'.
    """
    year_data: Dict[int, Dict[str, Any]] = {}
    for a in awards:
        if a.award_year not in year_data:
            year_data[a.award_year] = {"annual_amount": 0.0, "annual_count": 0}
        year_data[a.award_year]["annual_amount"] += a.award_amount
        year_data[a.award_year]["annual_count"] += 1

    cumulative = 0.0
    rows = []
    for yr in sorted(year_data.keys()):
        cumulative += year_data[yr]["annual_amount"]
        rows.append({
            "year": yr,
            "annual_amount": year_data[yr]["annual_amount"],
            "annual_count": year_data[yr]["annual_count"],
            "cumulative_amount": cumulative,
        })
    return rows
