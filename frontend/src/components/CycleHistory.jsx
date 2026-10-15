import { useQuery } from "@tanstack/react-query";
import { LineChart, Line, XAxis, YAxis, Tooltip, ReferenceDot, ResponsiveContainer } from "recharts";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

export default function CycleHistory() {
  const { t, d } = useT();
  const q = useQuery({ queryKey: ["cycle-history"], queryFn: () => api.get("/cycles/history").then((r) => r.data) });
  const h = q.data;
  if (!h) return null;
  const complete = h.cycles.filter((c) => c.complete);
  const data = complete.map((c) => ({ start: c.start, label: d(c.start).format("D MMM"), length: c.cycle_length, change: c.change_from_previous, notable: h.notable_changes.includes(c.start) }));

  return (
    <section className="fh-card p-6" aria-labelledby="history-heading" data-testid="cycle-history">
      <h2 id="history-heading" className="font-display text-2xl font-semibold">{t("rep.history")}</h2>
      {complete.length === 0 ? (
        <p className="mt-2 text-sm text-muted-foreground" data-testid="history-empty">{t("rep.historyEmpty")}</p>
      ) : (
        <>
          <dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            {[["rep.completed", h.completed_cycles, "history-completed"], ["rep.shortest", `${h.shortest} d`, "history-shortest"], ["rep.longest", `${h.longest} d`, "history-longest"], ["rep.variation", `${h.variation} d`, "history-variation"]].map(([k, v, id]) => (
              <div key={k} className="rounded-2xl bg-secondary/30 p-3"><dt className="text-xs text-muted-foreground">{t(k)}</dt><dd className="text-xl font-semibold" data-testid={id}>{v}</dd></div>
            ))}
          </dl>
          <div className="mt-5 h-52" role="img" aria-label={`Cycle lengths over time: ${data.map((x) => `${x.label} ${x.length} days`).join(", ")}`}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ left: 0, right: 16, top: 12 }}>
                <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#5C4B4D" }} />
                <YAxis domain={["dataMin - 3", "dataMax + 3"]} tick={{ fontSize: 11, fill: "#5C4B4D" }} width={28} allowDecimals={false} />
                <Tooltip itemStyle={{ color: "#312325" }} formatter={(v) => [`${v} days`, "Cycle length"]} />
                <Line type="monotone" dataKey="length" stroke="#A05A65" strokeWidth={2} dot={{ r: 4, fill: "#A05A65" }} activeDot={{ r: 6 }} />
                {data.filter((x) => x.notable).map((x) => <ReferenceDot key={x.start} x={x.label} y={x.length} r={9} fill="none" stroke="#C57B71" strokeWidth={2} />)}
              </LineChart>
            </ResponsiveContainer>
          </div>
          <ol className="mt-4 space-y-1.5 text-sm" data-testid="history-list">
            {h.cycles.map((c) => (
              <li key={c.start} className={`flex flex-wrap items-center justify-between gap-2 rounded-2xl border px-4 py-2 ${h.notable_changes.includes(c.start) ? "border-accent/60 bg-accent/5" : "border-border"}`} data-testid={`history-cycle-${c.start}`}>
                <span>{d(c.start).format("D MMM YYYY")} · period {c.period_length} d</span>
                <span className="tabular-nums">{c.complete ? `${c.cycle_length} d` : "ongoing"}{c.change_from_previous != null && <span className={`ml-2 text-xs ${Math.abs(c.change_from_previous) >= 7 ? "font-semibold text-accent" : "text-muted-foreground"}`}>{c.change_from_previous > 0 ? "+" : ""}{c.change_from_previous} vs previous</span>}</span>
              </li>
            ))}
          </ol>
          <p className="mt-3 text-xs text-muted-foreground">{h.note}</p>
        </>
      )}
    </section>
  );
}
