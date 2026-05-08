"""CDFI Program (FA and TA) analysis functions."""

from typing import List, Dict, Any

from cdfifund.data.schema import Award


def cdfi_program_analysis(awards: List[Award]) -> Dict[str, Any]:
    """Analyze CDFI Program awards (FA + TA combined).

    Args:
        awards: List of all awards to filter and analyze.

    Returns:
        Dict with total_awards, total_amount, award_count,
        average_award, state_breakdown, year_breakdown.
    """
    cdfi_awards = [a for a in awards if a.program in ("CDFI_FA", "CDFI_TA")]
    if not cdfi_awards:
        return {"award_count": 0, "total_amount": 0.0, "average_award": 0.0,
                "state_breakdown": {}, "year_breakdown": {}}

    total = sum(a.award_amount for a in cdfi_awards)
    state_breakdown: Dict[str, float] = {}
    year_breakdown: Dict[int, float] = {}

    for a in cdfi_awards:
        state_breakdown[a.state] = state_breakdown.get(a.state, 0.0) + a.award_amount
        year_breakdown[a.award_year] = year_breakdown.get(a.award_year, 0.0) + a.award_amount

    return {
        "award_count": len(cdfi_awards),
        "total_amount": total,
        "average_award": total / len(cdfi_awards),
        "state_breakdown": dict(sorted(state_breakdown.items(), key=lambda x: x[1], reverse=True)),
        "year_breakdown": dict(sorted(year_breakdown.items())),
        "programs_included": ["CDFI_FA", "CDFI_TA"],
    }


def fa_vs_ta_breakdown(awards: List[Award]) -> Dict[str, Any]:
    """Break down CDFI Program awards between Financial Assistance and Technical Assistance.

    Args:
        awards: List of all awards.

    Returns:
        Dict with separate FA and TA stats and FA/TA dollar ratio.
    """
    fa = [a for a in awards if a.program == "CDFI_FA"]
    ta = [a for a in awards if a.program == "CDFI_TA"]

    fa_total = sum(a.award_amount for a in fa)
    ta_total = sum(a.award_amount for a in ta)

    return {
        "fa_count": len(fa),
        "fa_total": fa_total,
        "fa_average": fa_total / len(fa) if fa else 0.0,
        "ta_count": len(ta),
        "ta_total": ta_total,
        "ta_average": ta_total / len(ta) if ta else 0.0,
        "fa_pct_of_cdfi_program": fa_total / (fa_total + ta_total) if (fa_total + ta_total) else 0.0,
        "fa_ta_dollar_ratio": fa_total / ta_total if ta_total else float("inf"),
    }
