import dayjs from "dayjs";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useT } from "@/lib/i18n";

export default function CalendarGrid({ month, onMonthChange, logsByDate, estimate, selected, onSelect }) {
  const { t, lang } = useT();
  const weekdays = Array.from({ length: 7 }, (_, i) => dayjs().locale(lang).day((i + 1) % 7).format("ddd"));
  const start = month.startOf("month");
  const offset = (start.day() + 6) % 7;
  const days = Array.from({ length: offset + month.daysInMonth() }, (_, i) => (i < offset ? null : start.add(i - offset, "day")));
  const today = dayjs().format("YYYY-MM-DD");
  const est = estimate?.enabled ? estimate.next_period_estimate : null;
  const inEst = (d) => est && d.format("YYYY-MM-DD") >= est.earliest && d.format("YYYY-MM-DD") <= est.latest;
  const describe = (day, log, inEstimate) => {
    const parts = [day.locale(lang).format("dddd D MMMM")];
    if (log?.period) parts.push(`${t("cal.legend.period")}, ${t(`opt.${log.flow}`)}`);
    if (log?.symptoms?.length) parts.push(`${log.symptoms.length} ${t("cal.legend.symptoms")}`);
    if (log?.moods?.length) parts.push(`${t("log.mood")}: ${log.moods.map((m) => t(`opt.${m}`)).join(", ")}`);
    if (log?.medications_taken?.length) parts.push(t("cal.legend.meds"));
    if (log?.notes) parts.push(t("cal.legend.note"));
    if (inEstimate) parts.push(t("cal.legend.est"));
    return parts.join(", ");
  };

  return (
    <section className="fh-card p-5 sm:p-7" aria-labelledby="calendar-heading" data-testid="calendar">
      <div className="flex items-center justify-between">
        <h2 id="calendar-heading" className="font-display text-2xl sm:text-3xl font-semibold" aria-live="polite">{month.locale(lang).format("MMMM YYYY")}</h2>
        <div className="flex gap-1">
          <Button variant="ghost" size="icon" className="rounded-full" onClick={() => onMonthChange(month.subtract(1, "month"))} aria-label={t("cal.prev")} data-testid="calendar-prev-month"><ChevronLeft strokeWidth={1.5} /></Button>
          <Button variant="ghost" size="sm" className="rounded-full" onClick={() => onMonthChange(dayjs())} data-testid="calendar-today">{t("cal.today")}</Button>
          <Button variant="ghost" size="icon" className="rounded-full" onClick={() => onMonthChange(month.add(1, "month"))} aria-label={t("cal.next")} data-testid="calendar-next-month"><ChevronRight strokeWidth={1.5} /></Button>
        </div>
      </div>
      <div role="grid" aria-label={month.locale(lang).format("MMMM YYYY")} className="mt-5">
        <div role="row" className="grid grid-cols-7 text-center fh-eyebrow">
          {weekdays.map((w) => <div key={w} role="columnheader" className="py-1">{w}</div>)}
        </div>
        <div className="grid grid-cols-7 gap-1 sm:gap-2 mt-2">
          {days.map((d, i) => {
            if (!d) return <div key={`e${i}`} aria-hidden />;
            const key = d.format("YYYY-MM-DD");
            const log = logsByDate[key];
            const isSel = selected === key;
            const isToday = key === today;
            const isFuture = key > today;
            const estimated = inEst(d);
            return (
              <button key={key} type="button" role="gridcell" aria-selected={isSel} aria-current={isToday ? "date" : undefined}
                aria-label={describe(d, log, estimated)} onClick={() => onSelect(key)} data-testid={`calendar-day-${key}`}
                className={`relative flex aspect-square flex-col items-center justify-start rounded-2xl border p-1 text-sm transition-colors duration-200 sm:p-2
                  ${log?.period ? "bg-primary text-primary-foreground border-primary" : estimated ? "border-dashed border-primary/60 bg-secondary/30" : "border-border bg-white hover:bg-secondary/40"}
                  ${isSel ? "ring-2 ring-primary ring-offset-2" : ""} ${isFuture && !estimated ? "text-muted-foreground" : ""}`}>
                <span className={`font-semibold ${isToday ? "underline decoration-2 underline-offset-4" : ""}`}>{d.date()}</span>
                {estimated && !log?.period && <span className="mt-auto text-[9px] font-semibold uppercase tracking-wide text-primary">{t("cal.est")}</span>}
                <span className="mt-auto flex gap-0.5" aria-hidden>
                  {log?.symptoms?.length > 0 && <span className={`h-1.5 w-1.5 rounded-full ${log.period ? "bg-white" : "bg-accent"}`} />}
                  {log?.medications_taken?.length > 0 && <span className={`h-1.5 w-1.5 rounded-full ${log.period ? "bg-white/70" : "bg-foreground/60"}`} />}
                  {log?.notes && <span className={`h-1.5 w-1.5 rounded-full ${log.period ? "bg-white/50" : "bg-secondary"}`} />}
                </span>
              </button>
            );
          })}
        </div>
      </div>
      <ul className="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted-foreground" aria-label="Legend">
        <li className="flex items-center gap-2"><span className="h-3 w-3 rounded-md bg-primary" aria-hidden /> {t("cal.legend.period")}</li>
        <li className="flex items-center gap-2"><span className="h-3 w-3 rounded-md border border-dashed border-primary/60 bg-secondary/40" aria-hidden /> {t("cal.legend.est")}</li>
        <li className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-accent" aria-hidden /> {t("cal.legend.symptoms")}</li>
        <li className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-foreground/60" aria-hidden /> {t("cal.legend.meds")}</li>
        <li className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-secondary" aria-hidden /> {t("cal.legend.note")}</li>
      </ul>
    </section>
  );
}
