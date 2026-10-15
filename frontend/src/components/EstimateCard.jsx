import { Info, Moon } from "lucide-react";
import { useT } from "@/lib/i18n";

export default function EstimateCard({ estimate }) {
  const { t, d } = useT();
  if (!estimate) return null;
  const next = estimate.next_period_estimate;
  return (
    <section className="fh-card p-6 sm:p-7" aria-labelledby="estimate-heading" data-testid="estimate-card">
      <p className="fh-eyebrow flex items-center gap-2"><Moon size={14} strokeWidth={1.5} aria-hidden /> {t("est.eyebrow")}</p>
      {estimate.enabled ? (
        <>
          <h2 id="estimate-heading" className="mt-2 font-display text-3xl font-semibold leading-tight">
            {t("est.nextAround")} <span className="text-primary">{d(next.start).format("D MMM")}</span>
          </h2>
          <p className="mt-1 text-sm text-muted-foreground" data-testid="estimate-window">
            {t("est.window")}: {d(next.earliest).format("D MMM")} – {d(next.latest).format("D MMM")} · {t(`conf.${estimate.confidence}`)}
          </p>
          <dl className="mt-5 grid grid-cols-3 gap-3 text-sm">
            <div><dt className="text-muted-foreground">{t("est.cycleDay")}</dt><dd className="text-xl font-semibold" data-testid="estimate-cycle-day">{estimate.current_cycle_day ?? "—"}</dd></div>
            <div><dt className="text-muted-foreground">{t("est.avgCycle")}</dt><dd className="text-xl font-semibold">{estimate.average_cycle_length} d</dd></div>
            <div><dt className="text-muted-foreground">{t("est.avgPeriod")}</dt><dd className="text-xl font-semibold">{estimate.average_period_length} d</dd></div>
          </dl>
          <p className="mt-4 flex gap-2 text-xs leading-relaxed text-muted-foreground"><Info size={14} className="mt-0.5 shrink-0" aria-hidden /> {estimate.confidence_note} {t("est.basedOn", { n: estimate.cycles_counted })}</p>
        </>
      ) : (
        <>
          <h2 id="estimate-heading" className="mt-2 font-display text-3xl font-semibold leading-tight">{t("est.none")}</h2>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground" data-testid="estimate-reason">{estimate.reason}</p>
          {estimate.last_period_start && <p className="mt-3 text-sm">{t("est.lastPeriod")}: <strong>{d(estimate.last_period_start).format("D MMM YYYY")}</strong>{estimate.current_cycle_day ? ` · ${t("est.cycleDay")} ${estimate.current_cycle_day}` : ""}</p>}
        </>
      )}
    </section>
  );
}
