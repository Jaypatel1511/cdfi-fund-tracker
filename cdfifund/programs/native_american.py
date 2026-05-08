"""Native American CDFI Assistance (NACA) program analysis."""

from typing import List, Dict, Any

from cdfifund.data.schema import Award

NATIVE_AMERICAN_PROGRAMS = {"NACA", "NATIVE_AMERICAN"}


def native_american_analysis(awards: List[Award]) -> Dict[str, Any]:
    """Analyze all Native American-focused CDFI Fund awards (NACA + NATIVE_AMERICAN TA).

    Args:
        awards: List of all awards.

    Returns:
        Dict with combined NACA metrics, state distribution, and year trend.
    """
    na = [a for a in awards if a.program in NATIVE_AMERICAN_PROGRAMS]
    if not na:
        return {"award_count": 0, "total_amount": 0.0, "average_award": 0.0}

    total = sum(a.award_amount for a in na)
    state_breakdown: Dict[str, float] = {}
    year_breakdown: Dict[int, float] = {}

    for a in na:
        state_breakdown[a.state] = state_breakdown.get(a.state, 0.0) + a.award_amount
        year_breakdown[a.award_year] = year_breakdown.get(a.award_year, 0.0) + a.award_amount

    return {
        "award_count": len(na),
        "total_amount": total,
        "average_award": total / len(na),
        "state_breakdown": dict(sorted(state_breakdown.items(), key=lambda x: x[1], reverse=True)),
        "year_breakdown": dict(sorted(year_breakdown.items())),
        "programs_included": sorted(NATIVE_AMERICAN_PROGRAMS),
    }


def naca_breakdown(awards: List[Award]) -> Dict[str, Any]:
    """Break down NACA awards between FA and TA tracks.

    Args:
        awards: List of all awards.

    Returns:
        Dict with NACA FA vs NACA TA counts, totals, and top states.
    """
    naca_fa = [a for a in awards if a.program == "NACA"]
    naca_ta = [a for a in awards if a.program == "NATIVE_AMERICAN"]

    fa_total = sum(a.award_amount for a in naca_fa)
    ta_total = sum(a.award_amount for a in naca_ta)

    # Top states by NACA FA volume
    state_vol: Dict[str, float] = {}
    for a in naca_fa + naca_ta:
        state_vol[a.state] = state_vol.get(a.state, 0.0) + a.award_amount
    top_states = sorted(state_vol.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "naca_fa_count": len(naca_fa),
        "naca_fa_total": fa_total,
        "naca_ta_count": len(naca_ta),
        "naca_ta_total": ta_total,
        "top_5_states": [{"state": s, "total": t} for s, t in top_states],
    }
