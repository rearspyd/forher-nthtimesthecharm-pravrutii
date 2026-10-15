import { useState } from "react";
import dayjs from "dayjs";
import { Link } from "react-router-dom";
import { Moon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useT } from "@/lib/i18n";

const key = (start) => `forher:checkin:${start}`;

export default function PeriodCheckIn({ estimate, todayLog, onLogPeriod }) {
  const { t } = useT();
  const today = dayjs().format("YYYY-MM-DD");
  const win = estimate?.enabled ? estimate.next_period_estimate : null;
  const [, bump] = useState(0);
  const dismissedOn = win ? localStorage.getItem(key(win.earliest)) : null;
  if (!win || today < win.earliest || today > win.latest || todayLog?.period || dismissedOn === today) return null;

  const notYet = () => { localStorage.setItem(key(win.earliest), today); bump((n) => n + 1); };

  return (
    <section className="fh-card border-primary/30 bg-secondary/20 p-6 fh-reveal" aria-labelledby="checkin-heading" role="region" data-testid="period-checkin">
      <p className="fh-eyebrow flex items-center gap-2"><Moon size={14} strokeWidth={1.5} aria-hidden /> {t("checkin.eyebrow")}</p>
      <h2 id="checkin-heading" className="mt-2 font-display text-2xl font-semibold leading-tight">{t("checkin.title")}</h2>
      <p className="mt-1 text-sm text-muted-foreground">{t("checkin.body")}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button className="rounded-full" onClick={onLogPeriod} data-testid="checkin-yes-button">{t("checkin.yes")}</Button>
        <Button variant="outline" className="rounded-full" onClick={notYet} data-testid="checkin-not-yet-button">{t("checkin.notYet")}</Button>
        <Button asChild variant="ghost" className="rounded-full"><Link to="/app/settings" data-testid="checkin-context-link">{t("checkin.context")}</Link></Button>
      </div>
    </section>
  );
}
