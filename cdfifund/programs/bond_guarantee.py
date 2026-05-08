"""CDFI Bond Guarantee Program (BGP) analysis."""

from typing import List, Dict, Any

from cdfifund.data.schema import Award


def bond_guarantee_analysis(awards: List[Award]) -> Dict[str, Any]:
    """Analyze CDFI Bond Guarantee Program awards.

    BGP awards are structurally different — they are guaranteed bond issuances,
    not grants. Amounts reflect bond principal guaranteed.

    Args:
        awards: List of all awards.

    Returns:
        Dict with BGP-specific metrics: total guaranteed, average size,
        state distribution, and year-by-year totals.
    """
    bgp = [a for a in awards if a.program == "BGP"]
    if not bgp:
        return {
            "award_count": 0,
            "total_guaranteed": 0.0,
            "average_bond_size": 0.0,
            "state_breakdown": {},
            "year_breakdown": {},
        }

    total = sum(a.award_amount for a in bgp)
    state_breakdown: Dict[str, float] = {}
    year_breakdown: Dict[int, float] = {}
    size_dist = {"under_200m": 0, "200m_to_500m": 0, "over_500m": 0}

    for a in bgp:
        state_breakdown[a.state] = state_breakdown.get(a.state, 0.0) + a.award_amount
        year_breakdown[a.award_year] = year_breakdown.get(a.award_year, 0.0) + a.award_amount
        if a.award_amount < 200_000_000:
            size_dist["under_200m"] += 1
        elif a.award_amount <= 500_000_000:
            size_dist["200m_to_500m"] += 1
        else:
            size_dist["over_500m"] += 1

    return {
        "award_count": len(bgp),
        "total_guaranteed": total,
        "average_bond_size": total / len(bgp),
        "state_breakdown": dict(sorted(state_breakdown.items(), key=lambda x: x[1], reverse=True)),
        "year_breakdown": dict(sorted(year_breakdown.items())),
        "size_distribution": size_dist,
    }
