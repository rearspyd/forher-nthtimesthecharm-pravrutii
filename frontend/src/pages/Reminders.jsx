import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { BellRing, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const KINDS = [{ value: "medication", label: "Medication" }, { value: "period", label: "Period check-in" }, { value: "custom", label: "Custom" }];
const INIT = { label: "", kind: "custom", time: "09:00", days: [0, 1, 2, 3, 4, 5, 6], date: "" };

export default function Reminders() {
  const qc = useQueryClient();
  const remQ = useQuery({ queryKey: ["reminders"], queryFn: () => api.get("/reminders").then((r) => r.data) });
  const [form, setForm] = useState(INIT);
  const refresh = () => { qc.invalidateQueries({ queryKey: ["reminders"] }); qc.invalidateQueries({ queryKey: ["reminders-today"] }); };

  const add = async (e) => {
    e.preventDefault();
    try {
      await api.post("/reminders", { ...form, date: form.date || null, active: true });
      setForm(INIT); refresh(); toast.success("Reminder added");
    } catch { toast.error("Couldn't add reminder"); }
  };
  const toggle = async (r) => { await api.put(`/reminders/${r.id}`, { label: r.label, kind: r.kind, time: r.time, days: r.days, date: r.date, active: !r.active }); refresh(); };
  const remove = async (r) => {
    if (!window.confirm(`Remove "${r.label}"? Restorable from Settings for 30 days.`)) return;
    await api.delete(`/reminders/${r.id}`); refresh(); toast.success("Moved to Recently deleted");
  };
  const toggleDay = (i) => setForm({ ...form, days: form.days.includes(i) ? form.days.filter((d) => d !== i) : [...form.days, i].sort() });

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div>
        <p className="fh-eyebrow">Reminders</p>
        <h1 className="mt-1 text-4xl font-semibold tracking-tight sm:text-5xl">Gentle nudges</h1>
        <p className="mt-2 max-w-xl text-sm text-muted-foreground">Reminders appear inside ForHer on your calendar page — never as device notifications — so nothing sensitive shows on a shared screen.</p>
      </div>
      <form onSubmit={add} className="fh-card space-y-5 p-6" aria-label="Add reminder">
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="sm:col-span-2"><Label htmlFor="rem-label">Label (keep it discreet)</Label><Input id="rem-label" required maxLength={120} value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} className="mt-1 rounded-xl" placeholder="e.g. Morning tablet" data-testid="rem-label-input" /></div>
          <div>
            <Label htmlFor="rem-kind">Type</Label>
            <Select value={form.kind} onValueChange={(v) => setForm({ ...form, kind: v })}>
              <SelectTrigger id="rem-kind" className="mt-1 rounded-xl" data-testid="rem-kind-select"><SelectValue /></SelectTrigger>
              <SelectContent>{KINDS.map((k) => <SelectItem key={k.value} value={k.value}>{k.label}</SelectItem>)}</SelectContent>
            </Select>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          <div><Label htmlFor="rem-time">Time</Label><Input id="rem-time" type="time" required value={form.time} onChange={(e) => setForm({ ...form, time: e.target.value })} className="mt-1 rounded-xl" data-testid="rem-time-input" /></div>
          <div className="sm:col-span-2">
            <Label htmlFor="rem-date">One-off date (optional — leave blank to repeat on chosen days)</Label>
            <Input id="rem-date" type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} className="mt-1 rounded-xl" data-testid="rem-date-input" />
          </div>
        </div>
        {!form.date && (
          <fieldset>
            <legend className="fh-eyebrow mb-2">Repeat on</legend>
            <div className="flex flex-wrap gap-2">
              {DAYS.map((d, i) => <button type="button" key={d} className="fh-chip" aria-pressed={form.days.includes(i)} onClick={() => toggleDay(i)} data-testid={`rem-day-${d.toLowerCase()}`}>{d}</button>)}
            </div>
          </fieldset>
        )}
        <Button type="submit" className="rounded-full" data-testid="rem-add-button">Add reminder</Button>
      </form>
      <ul className="space-y-3" aria-label="Your reminders" data-testid="rem-list">
        {(remQ.data || []).map((r) => (
          <li key={r.id} className="fh-card flex flex-wrap items-center justify-between gap-4 p-5" data-testid={`rem-item-${r.id}`}>
            <div className="flex items-center gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-full bg-secondary/50 text-primary"><BellRing size={18} strokeWidth={1.5} aria-hidden /></span>
              <div>
                <p className="font-semibold">{r.time} · {r.label}</p>
                <p className="text-sm text-muted-foreground">{KINDS.find((k) => k.value === r.kind)?.label} · {r.date ? `once on ${r.date}` : r.days.length === 7 ? "every day" : r.days.map((d) => DAYS[d]).join(", ")}</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm"><Switch checked={r.active} onCheckedChange={() => toggle(r)} data-testid={`rem-active-${r.id}`} /> {r.active ? "On" : "Off"}</label>
              <Button variant="ghost" size="icon" className="rounded-full text-destructive" onClick={() => remove(r)} aria-label={`Remove reminder ${r.label}`} data-testid={`rem-delete-${r.id}`}><Trash2 size={16} strokeWidth={1.5} /></Button>
            </div>
          </li>
        ))}
        {remQ.data?.length === 0 && <li className="text-sm text-muted-foreground" data-testid="rem-empty">No reminders yet.</li>}
      </ul>
    </div>
  );
}
