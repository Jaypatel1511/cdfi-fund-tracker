"""Higher-level analytical insights: concentration, lifecycle, effectiveness."""

from typing import List, Dict, Any

from cdfifund.data.schema import Award, CDFI_PROGRAMS


def award_concentration_analysis(awards: List[Award]) -> Dict[str, Any]:
    """Measure award concentration by recipient and program.

    Args:
        awards: List of awards.

    Returns:
        Dict with:
        - 'top_10_pct_of_total': Share of dollars going to top 10 recipients.
        - 'single_recipient_max_pct': Largest single recipient's share.
        - 'program_hhi': Herfindahl index for program concentration.
        - 'recipient_hhi': Herfindahl index for recipient concentration.
        - 'gini_coefficient': Gini coefficient for award distribution.
    """
    if not awards:
        return {"top_10_pct_of_total": 0.0, "single_recipient_max_pct": 0.0}

    grand_total = sum(a.award_amount for a in awards)

    # Recipient concentration
    rec_totals: Dict[str, float] = {}
    for a in awards:
        rec_totals[a.recipient_name] = rec_totals.get(a.recipient_name, 0.0) + a.award_amount

    sorted_rec = sorted(rec_totals.values(), reverse=True)
    top10_total = sum(sorted_rec[:10])
    top10_pct = top10_total / grand_total if grand_total else 0.0
    max_pct = sorted_rec[0] / grand_total if grand_total else 0.0

    rec_shares = [v / grand_total for v in rec_totals.values()]
    rec_hhi = sum(s ** 2 for s in rec_shares)

    # Program concentration
    prog_totals: Dict[str, float] = {}
    for a in awards:
        prog_totals[a.program] = prog_totals.get(a.program, 0.0) + a.award_amount
    prog_shares = [v / grand_total for v in prog_totals.values()]
    prog_hhi = sum(s ** 2 for s in prog_shares)

    # Gini coefficient
    n = len(sorted_rec)
    if n > 0:
        sorted_asc = sorted(rec_totals.values())
        cumsum = 0.0
        gini_num = 0.0
        for i, v in enumerate(sorted_asc, 1):
            gini_num += (2 * i - n - 1) * v
        gini = gini_num / (n * sum(sorted_asc)) if sum(sorted_asc) else 0.0
    else:
        gini = 0.0

    return {
        "top_10_pct_of_total": top10_pct,
        "single_recipient_max_pct": max_pct,
        "recipient_hhi": rec_hhi,
        "program_hhi": prog_hhi,
        "gini_coefficient": gini,
        "unique_recipients": len(rec_totals),
        "total_amount": grand_total,
    }


def recipient_lifecycle_analysis(awards: List[Award]) -> Dict[str, Any]:
    """Analyze recipient engagement patterns: first award, multi-program participation.

    Args:
        awards: List of awards.

    Returns:
        Dict with:
        - 'first_time_recipients': Recipients with only one award.
        - 'multi_program_recipients': Recipients in 2+ programs.
        - 'repeat_recipients': Recipients with 2+ awards in the same program.
        - 'average_awards_per_recipient': Mean award count.
        - 'program_diversity_distribution': How many recipients participated in N programs.
    """
    if not awards:
        return {"first_time_recipients": 0, "multi_program_recipients": 0}

    rec_awards: Dict[str, List[Award]] = {}
    for a in awards:
        if a.recipient_name not in rec_awards:
            rec_awards[a.recipient_name] = []
        rec_awards[a.recipient_name].append(a)

    first_time = sum(1 for a in rec_awards.values() if len(a) == 1)
    multi_prog = sum(
        1 for a in rec_awards.values()
        if len({x.program for x in a}) >= 2
    )
    repeat = sum(
        1 for a in rec_awards.values()
        if len(a) > 1
    )

    prog_counts = [len({x.program for x in a}) for a in rec_awards.values()]
    diversity_dist: Dict[int, int] = {}
    for c in prog_counts:
        diversity_dist[c] = diversity_dist.get(c, 0) + 1

    return {
        "unique_recipients": len(rec_awards),
        "first_time_recipients": first_time,
        "multi_program_recipients": multi_prog,
        "repeat_recipients": repeat,
        "average_awards_per_recipient": len(awards) / len(rec_awards),
        "program_diversity_distribution": dict(sorted(diversity_dist.items())),
    }


def program_effectiveness_metrics(awards: List[Award]) -> Dict[str, Any]:
    """Compute program-level effectiveness proxy metrics.

    Metrics are based on observable award patterns, not impact data
    (true impact measurement requires outcome data outside the award record).

    Args:
        awards: List of awards.

    Returns:
        Dict mapping program code to metrics including geographic reach,
        average award size, and recipient concentration.
    """
    program_data: Dict[str, Dict[str, Any]] = {}

    for a in awards:
        if a.program not in program_data:
            program_data[a.program] = {
                "awards": [],
                "states": set(),
                "recipients": set(),
            }
        program_data[a.program]["awards"].append(a.award_amount)
        program_data[a.program]["states"].add(a.state)
        program_data[a.program]["recipients"].add(a.recipient_name)

    result: Dict[str, Any] = {}
    for prog, data in program_data.items():
        amounts = data["awards"]
        total = sum(amounts)
        n = len(amounts)
        rec_count = len(data["recipients"])
        # Concentration: top recipient share
        rec_totals: Dict[str, float] = {}
        for a in awards:
            if a.program == prog:
                rec_totals[a.recipient_name] = rec_totals.get(a.recipient_name, 0.0) + a.award_amount
        top_share = max(rec_totals.values()) / total if total and rec_totals else 0.0

        result[prog] = {
            "full_name": CDFI_PROGRAMS.get(prog, prog),
            "award_count": n,
            "total_amount": total,
            "average_award": total / n if n else 0.0,
            "geographic_reach_states": len(data["states"]),
            "unique_recipients": rec_count,
            "top_recipient_share": top_share,
        }

    return result
