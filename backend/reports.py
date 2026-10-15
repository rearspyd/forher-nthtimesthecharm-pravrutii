from collections import Counter
from datetime import date, timedelta
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from cycles import estimate, group_periods

PINK = colors.HexColor("#A05A65")
LIGHT = colors.HexColor("#F0E1E3")


def build_summary(logs: list[dict], meds: list[dict], user: dict, start: str, end: str, mode: str) -> dict:
    period_days = [l["date"] for l in logs if l.get("period")]
    flows = Counter(l.get("flow", "none") for l in logs if l.get("period"))
    symptoms = Counter(s for l in logs for s in l.get("symptoms", []))
    moods = Counter(m for l in logs for m in l.get("moods", []))
    med_names = {m["id"]: m["name"] for m in meds}
    med_counts = Counter(med_names.get(mid, "Unknown") for l in logs for mid in l.get("medications_taken", []))
    periods = group_periods(period_days)
    ctx = user.get("settings", {}).get("cycle_context", "unknown")
    all_periods = [l["date"] for l in logs if l.get("period")]
    est = estimate(all_periods, ctx)
    symptom_by_phase = _symptoms_by_phase(logs, periods)
    notes = [{"date": l["date"], "notes": l["notes"]} for l in logs if l.get("notes")]
    return {
        "mode": mode, "range": {"from": start, "to": end}, "generated_for": user.get("name") if mode == "personal" else "Shared summary",
        "cycle_context": ctx, "days_logged": len(logs), "period_days": len(period_days),
        "periods": [{"start": p["start"].isoformat(), "end": p["end"].isoformat(), "length": p["length"]} for p in periods],
        "flow_distribution": dict(flows), "top_symptoms": symptoms.most_common(10), "top_moods": moods.most_common(8),
        "medications": med_counts.most_common(20), "symptoms_by_phase": symptom_by_phase,
        "symptom_trends": symptom_trends(logs, periods, est),
        "mood_trends": symptom_trends(logs, periods, est, field="moods"),
        "cycle_history": cycle_history(period_days),
        "estimate": est, "notes": notes if mode == "personal" else notes[:10],
        "limitations": [
            "All data is self-reported by the user and may be incomplete.",
            "Cycle estimates are statistical guesses from logged dates, not clinical predictions.",
            "This summary does not diagnose any condition and is not a substitute for clinical evaluation.",
            f"Logged under cycle context: {ctx}. Estimates may be unreliable or disabled for this context.",
        ],
    }


def _symptoms_by_phase(logs, periods):
    phases = {"menstrual": Counter(), "other": Counter()}
    period_set = {d for p in periods for d in _days(p)}
    for l in logs:
        bucket = "menstrual" if l["date"] in period_set else "other"
        for s in l.get("symptoms", []):
            phases[bucket][s] += 1
    return {k: v.most_common(6) for k, v in phases.items()}


PHASES = ["menstrual", "follicular", "ovulatory", "luteal"]


def symptom_trends(logs: list[dict], periods: list[dict], est: dict, field: str = "symptoms") -> dict:
    """Counts each symptom/mood per estimated cycle phase. Phases are estimates derived from logged period starts."""
    period_set = {d for p in periods for d in _days(p)}
    starts = [p["start"] for p in periods]
    avg_len = est.get("average_cycle_length") if est.get("enabled") else None
    detailed = bool(avg_len) and len(starts) >= 1
    counts: dict[str, Counter] = {}
    days_in_phase = Counter()
    for l in logs:
        d = date.fromisoformat(l["date"])
        if l["date"] in period_set:
            phase = "menstrual"
        elif not detailed:
            phase = "other"
        else:
            prior = [s for s in starts if s <= d]
            if not prior:
                continue
            start = prior[-1]
            nxt = [s for s in starts if s > start]
            length = (nxt[0] - start).days if nxt else avg_len
            cycle_day = (d - start).days + 1
            if cycle_day > length + 7:
                continue
            mid = round(length / 2)
            phase = "follicular" if cycle_day < mid - 2 else "ovulatory" if cycle_day <= mid + 2 else "luteal"
        days_in_phase[phase] += 1
        for s in l.get(field, []):
            counts.setdefault(s, Counter())[phase] += 1
    phases = PHASES if detailed else ["menstrual", "other"]
    ranked = sorted(counts.items(), key=lambda kv: -sum(kv[1].values()))[:8]
    label = "symptoms" if field == "symptoms" else "moods"
    return {
        "method": "estimated_phases" if detailed else "period_vs_other",
        "phases": phases, "days_in_phase": {p: days_in_phase.get(p, 0) for p in phases},
        "symptoms": [{"name": name, "counts": {p: c.get(p, 0) for p in phases}, "total": sum(c.values())} for name, c in ranked],
        "note": ("Phases are estimated from your logged period start dates and average cycle length (ovulatory ≈ mid-cycle ±2 days). They are approximations, not measurements."
                 if detailed else f"Not enough cycle data (or estimates are paused for your context), so {label} are grouped as during-period vs other days."),
    }


def cycle_history(period_dates: list[str]) -> dict:
    periods = group_periods(period_dates)
    cycles = []
    for i, p in enumerate(periods):
        nxt = periods[i + 1]["start"] if i + 1 < len(periods) else None
        length = (nxt - p["start"]).days if nxt else None
        prev_len = cycles[-1]["cycle_length"] if cycles else None
        cycles.append({
            "start": p["start"].isoformat(), "period_end": p["end"].isoformat(), "period_length": p["length"],
            "cycle_length": length, "complete": nxt is not None,
            "change_from_previous": (length - prev_len) if (length is not None and prev_len is not None) else None,
        })
    lengths = [c["cycle_length"] for c in cycles if c["cycle_length"]]
    notable = [c for c in cycles if c["change_from_previous"] is not None and abs(c["change_from_previous"]) >= 7]
    return {
        "cycles": cycles, "completed_cycles": len(lengths),
        "shortest": min(lengths) if lengths else None, "longest": max(lengths) if lengths else None,
        "variation": (max(lengths) - min(lengths)) if lengths else None,
        "notable_changes": [c["start"] for c in notable],
        "note": "Cycle length is counted from the first day of one period to the first day of the next. A change of 7+ days from the previous cycle is highlighted — common and often harmless, but worth mentioning to a clinician if it keeps happening.",
    }


def _days(p):
    d = p["start"]
    while d <= p["end"]:
        yield d.isoformat()
        d += timedelta(days=1)


def render_pdf(summary: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm)
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], textColor=PINK, fontSize=20, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=PINK, fontSize=13, spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("body", parent=ss["BodyText"], fontSize=9.5, leading=13)
    small = ParagraphStyle("small", parent=body, fontSize=8.5, textColor=colors.HexColor("#5C4B4D"))
    label = "Personal cycle report" if summary["mode"] == "personal" else "Cycle summary for clinician"
    story = [Paragraph(f"ForHer — {label}", h1),
             Paragraph(f"Range: {summary['range']['from']} to {summary['range']['to']} · Prepared for: {summary['generated_for']} · Cycle context: {summary['cycle_context']}", small),
             Paragraph("Not medical advice. Self-reported awareness data only; estimates are estimates.", small), Spacer(1, 8)]

    def table(rows, widths=None):
        t = Table(rows, colWidths=widths, hAlign="LEFT")
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#312325")),
                               ("FONTSIZE", (0, 0), (-1, -1), 9), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5D0D3")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5)]))
        return t

    story += [Paragraph("Overview", h2), table([["Days logged", "Period days", "Periods in range"],
                                                [str(summary["days_logged"]), str(summary["period_days"]), str(len(summary["periods"]))]])]
    if summary["periods"]:
        story += [Paragraph("Periods", h2), table([["Start", "End", "Days"]] + [[p["start"], p["end"], str(p["length"])] for p in summary["periods"]])]
    est = summary["estimate"]
    story += [Paragraph("Cycle estimate (estimate only)", h2)]
    if est.get("enabled"):
        nxt = est["next_period_estimate"]
        story += [Paragraph(f"Average cycle length ≈ {est['average_cycle_length']} days (range {est['cycle_length_range'][0]}–{est['cycle_length_range'][1]}), "
                            f"based on {est['cycles_counted']} cycles. Confidence: {est['confidence'].replace('_', ' ')}. "
                            f"Next period estimated around {nxt['start']} (window {nxt['earliest']} to {nxt['latest']}).", body),
                  Paragraph(est["confidence_note"], small)]
    else:
        story += [Paragraph(est.get("reason", "No estimate available."), body)]
    if summary["flow_distribution"]:
        story += [Paragraph("Flow on period days", h2), table([["Flow", "Days"]] + [[k, str(v)] for k, v in summary["flow_distribution"].items()])]
    if summary["top_symptoms"]:
        story += [Paragraph("Most logged symptoms", h2), table([["Symptom", "Days"]] + [[s, str(c)] for s, c in summary["top_symptoms"]])]
    trends = summary.get("symptom_trends")
    if trends and trends["symptoms"]:
        header = ["Symptom"] + [p.capitalize() for p in trends["phases"]]
        rows = [[t["name"]] + [str(t["counts"][p]) for p in trends["phases"]] for t in trends["symptoms"]]
        story += [Paragraph("Symptoms by estimated cycle phase (days logged)", h2), table([header] + rows), Paragraph(trends["note"], small)]
    moods = summary.get("mood_trends")
    if moods and moods["symptoms"]:
        header = ["Mood"] + [p.capitalize() for p in moods["phases"]]
        rows = [[t["name"]] + [str(t["counts"][p]) for p in moods["phases"]] for t in moods["symptoms"]]
        story += [Paragraph("Moods by estimated cycle phase (days logged)", h2), table([header] + rows)]
    hist = summary.get("cycle_history")
    if hist and hist["completed_cycles"]:
        rows = [[c["start"], str(c["period_length"]), str(c["cycle_length"] or "—"), (f"{c['change_from_previous']:+d}" if c["change_from_previous"] is not None else "—")] for c in hist["cycles"]]
        story += [Paragraph("Cycle history (within range)", h2), table([["Period start", "Period days", "Cycle length", "Change"]] + rows),
                  Paragraph(f"Shortest {hist['shortest']} · longest {hist['longest']} · variation {hist['variation']} days. {hist['note']}", small)]
    if summary["top_moods"]:
        story += [Paragraph("Most logged moods", h2), table([["Mood", "Days"]] + [[m, str(c)] for m, c in summary["top_moods"]])]
    if summary["medications"]:
        story += [Paragraph("Medications marked as taken", h2), table([["Medication", "Days taken"]] + [[m, str(c)] for m, c in summary["medications"]])]
    if summary["notes"]:
        story += [Paragraph("Notes", h2)] + [Paragraph(f"<b>{n['date']}</b> — {_esc(n['notes'])}", body) for n in summary["notes"]]
    story += [Paragraph("Limitations", h2)] + [Paragraph("• " + l, small) for l in summary["limitations"]]
    doc.build(story)
    return buf.getvalue()


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
