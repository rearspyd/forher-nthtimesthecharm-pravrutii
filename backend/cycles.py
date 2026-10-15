from datetime import date, timedelta
from statistics import mean, pstdev

NO_ESTIMATE_CONTEXTS = {
    "pregnancy": "Estimates are paused during pregnancy because cycles do not follow the usual pattern.",
    "postpartum": "Estimates are paused postpartum; cycles often take months to settle and can be unpredictable.",
    "menopause": "Estimates are paused around menopause because cycle timing changes and may stop.",
    "not_applicable": "You marked cycle estimates as not applicable, so ForHer does not predict dates.",
}


def group_periods(period_dates: list[str]) -> list[dict]:
    days = sorted({date.fromisoformat(d) for d in period_dates})
    periods = []
    for d in days:
        if periods and (d - periods[-1]["end"]).days <= 2:
            periods[-1]["end"] = d
        else:
            periods.append({"start": d, "end": d})
    for p in periods:
        p["length"] = (p["end"] - p["start"]).days + 1
    return periods


def estimate(period_dates: list[str], cycle_context: str, today: date | None = None) -> dict:
    today = today or date.today()
    periods = group_periods(period_dates)
    base = {
        "is_estimate": True, "enabled": True, "periods_logged": len(periods),
        "cycle_context": cycle_context, "disclaimer": "These are estimates based only on what you have logged. They are not medical predictions.",
    }
    if cycle_context in NO_ESTIMATE_CONTEXTS:
        return {**base, "enabled": False, "reason": NO_ESTIMATE_CONTEXTS[cycle_context]}
    if not periods:
        return {**base, "enabled": False, "reason": "Log your period days to see estimates here."}
    last = periods[-1]
    cycle_day = (today - last["start"]).days + 1
    result = {**base, "last_period_start": last["start"].isoformat(), "current_cycle_day": cycle_day if cycle_day > 0 else None,
              "average_period_length": round(mean(p["length"] for p in periods), 1)}
    if len(periods) < 2:
        return {**result, "enabled": False, "reason": "At least two logged periods are needed to estimate cycle length."}
    lengths = [(periods[i + 1]["start"] - periods[i]["start"]).days for i in range(len(periods) - 1)]
    lengths = [l for l in lengths if 15 <= l <= 90] or lengths
    avg = mean(lengths)
    spread = pstdev(lengths) if len(lengths) > 1 else 4.0
    if len(lengths) >= 3 and spread <= 3:
        confidence = "moderate"
    elif len(lengths) >= 2 and spread <= 7:
        confidence = "low"
    else:
        confidence = "very_low"
    if cycle_context in ("irregular", "unknown") and confidence == "moderate":
        confidence = "low"
    window = max(2, round(spread))
    next_start = last["start"] + timedelta(days=round(avg))
    while next_start + timedelta(days=window) < today:
        next_start += timedelta(days=round(avg))
    return {
        **result, "enabled": True, "average_cycle_length": round(avg, 1), "cycle_length_range": [min(lengths), max(lengths)],
        "cycles_counted": len(lengths), "confidence": confidence,
        "next_period_estimate": {"start": next_start.isoformat(), "earliest": (next_start - timedelta(days=window)).isoformat(),
                                  "latest": (next_start + timedelta(days=window)).isoformat()},
        "confidence_note": {
            "moderate": "Your logged cycles have been fairly consistent, but timing can still shift with stress, travel, illness or life changes.",
            "low": "Your logged cycles vary, so this window is wide. Treat it as a rough guide only.",
            "very_low": "There is not enough consistent data for a reliable estimate. Keep logging and treat this as a very rough guide.",
        }[confidence],
    }
