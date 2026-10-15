import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";

const PHASE_STYLE = {
  menstrual: { label: "Menstrual", color: "#A05A65" },
  follicular: { label: "Follicular (est.)", color: "#E5D0D3" },
  ovulatory: { label: "Ovulatory (est.)", color: "#C57B71" },
  luteal: { label: "Luteal (est.)", color: "#5C4B4D" },
  other: { label: "Other days", color: "#C9B7BA" },
};

export default function SymptomTrends({ trends, title = "Symptoms across cycle phases", testId = "symptom-trends", labelOf = (x) => x }) {
  if (!trends) return null;
  const data = trends.symptoms.map((s) => ({ name: labelOf(s.name), ...s.counts }));
  const describe = trends.symptoms.map((s) => `${labelOf(s.name)}: ${trends.phases.map((p) => `${s.counts[p]} ${PHASE_STYLE[p].label}`).join(", ")}`).join("; ");

  return (
    <section className="fh-card p-6" aria-labelledby={`${testId}-heading`} data-testid={testId}>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id={`${testId}-heading`} className="font-display text-2xl font-semibold">{title}</h2>
        <span className="fh-eyebrow" data-testid={`${testId}-method`}>{trends.method === "estimated_phases" ? "Estimated phases" : "Period vs other days"}</span>
      </div>
      <p className="mt-1 text-sm text-muted-foreground">{trends.note}</p>
      {data.length === 0 ? (
        <p className="mt-4 text-sm text-muted-foreground" data-testid={`${testId}-empty`}>Nothing logged in this range yet. Log a few days to see how things cluster across your cycle.</p>
      ) : (
        <>
          <div className="mt-5 h-72" role="img" aria-label={`Symptom days per phase. ${describe}`}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ left: 0, right: 8, top: 8 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#5C4B4D" }} interval={0} angle={-20} textAnchor="end" height={56} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "#5C4B4D" }} width={28} />
                <Tooltip cursor={{ fill: "rgba(160,90,101,0.08)" }} itemStyle={{ color: "#312325" }} formatter={(v, k) => [`${v} day${v === 1 ? "" : "s"}`, PHASE_STYLE[k].label]} />
                <Legend formatter={(k) => <span style={{ color: "#312325" }}>{PHASE_STYLE[k].label}</span>} wrapperStyle={{ fontSize: 12 }} />
                {trends.phases.map((p) => <Bar key={p} dataKey={p} stackId="a" fill={PHASE_STYLE[p].color} stroke="#8A4C55" strokeWidth={0.5} />)}
              </BarChart>
            </ResponsiveContainer>
          </div>
          <table className="mt-4 w-full text-sm" data-testid={`${testId}-table`}>
            <caption className="sr-only">{title}</caption>
            <thead><tr className="text-left text-xs uppercase tracking-wider text-muted-foreground"><th scope="col" className="py-1 pr-2 font-semibold">Name</th>{trends.phases.map((p) => <th key={p} scope="col" className="py-1 px-2 font-semibold">{PHASE_STYLE[p].label}</th>)}</tr></thead>
            <tbody>
              {trends.symptoms.map((s) => (
                <tr key={s.name} className="border-t border-border"><th scope="row" className="py-1.5 pr-2 text-left font-medium">{labelOf(s.name)}</th>{trends.phases.map((p) => <td key={p} className="py-1.5 px-2 tabular-nums">{s.counts[p]}</td>)}</tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 text-xs text-muted-foreground">Days logged per phase: {trends.phases.map((p) => `${PHASE_STYLE[p].label} ${trends.days_in_phase[p]}`).join(" · ")}</p>
        </>
      )}
    </section>
  );
}
