"""BEA (Bank Enterprise Award) program analysis."""

from typing import List, Dict, Any

from cdfifund.data.schema import Award


def bea_program_analysis(awards: List[Award]) -> Dict[str, Any]:
    """Analyze Bank Enterprise Award program activity.

    BEA incentivizes banks and thrifts to increase lending in distressed communities.

    Args:
        awards: List of all awards.

    Returns:
        Dict with BEA-specific metrics: award count, total, average, state breakdown.
    """
    bea = [a for a in awards if a.program == "BEA"]
    if not bea:
        return {"award_count": 0, "total_amount": 0.0, "average_award": 0.0}

    total = sum(a.award_amount for a in bea)
    state_breakdown: Dict[str, float] = {}
    year_breakdown: Dict[int, float] = {}

    for a in bea:
        state_breakdown[a.state] = state_breakdown.get(a.state, 0.0) + a.award_amount
        year_breakdown[a.award_year] = year_breakdown.get(a.award_year, 0.0) + a.award_amount

    return {
        "award_count": len(bea),
        "total_amount": total,
        "average_award": total / len(bea),
        "state_breakdown": dict(sorted(state_breakdown.items(), key=lambda x: x[1], reverse=True)),
        "year_breakdown": dict(sorted(year_breakdown.items())),
    }


def bank_enterprise_award_breakdown(awards: List[Award]) -> Dict[str, Any]:
    """Break down BEA awards by recipient type (depository institutions only).

    Args:
        awards: List of all awards.

    Returns:
        Dict with recipient-type breakdown for BEA awardees.
    """
    bea = [a for a in awards if a.program == "BEA"]
    type_breakdown: Dict[str, Dict[str, Any]] = {}

    for a in bea:
        if a.recipient_type not in type_breakdown:
            type_breakdown[a.recipient_type] = {"count": 0, "total": 0.0}
        type_breakdown[a.recipient_type]["count"] += 1
        type_breakdown[a.recipient_type]["total"] += a.award_amount

    for t in type_breakdown:
        n = type_breakdown[t]["count"]
        type_breakdown[t]["average"] = type_breakdown[t]["total"] / n if n else 0.0

    return {
        "by_recipient_type": type_breakdown,
        "total_bea_count": len(bea),
        "total_bea_amount": sum(a.award_amount for a in bea),
    }
