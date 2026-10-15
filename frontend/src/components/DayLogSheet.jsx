import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Trash2 } from "lucide-react";
import { api, SYMPTOMS, MOODS, FLOWS, readDraft, writeDraft, clearDraft } from "@/lib/api";
import { useSync } from "@/context/SyncContext";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { useT } from "@/lib/i18n";

const EMPTY = { period: false, flow: "none", moods: [], symptoms: [], medications_taken: [], notes: "" };

function Chips({ label, options, values, onToggle, testPrefix, labelOf }) {
  return (
    <fieldset>
      <legend className="fh-eyebrow mb-2">{label}</legend>
      <div className="flex flex-wrap gap-2">
        {options.map((o) => (
          <button key={o} type="button" className="fh-chip" aria-pressed={values.includes(o)} onClick={() => onToggle(o)} data-testid={`${testPrefix}-${o.toLowerCase().replace(/\s+/g, "-")}`}>{labelOf(o)}</button>
        ))}
      </div>
    </fieldset>
  );
}

export default function DayLogSheet({ date, existing, medications, preset, onClose, onSaved }) {
  const { t, tOpt, d } = useT();
  const { online, setStatus, refreshPending } = useSync();
  const [form, setForm] = useState(EMPTY);
  const [draftRestored, setDraftRestored] = useState(false);
  const [conflict, setConflict] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [busy, setBusy] = useState(false);
  const isMobile = typeof window !== "undefined" && window.innerWidth < 768;

  useEffect(() => {
    if (!date) return;
    const draft = readDraft(date);
    const base = existing?.id ? { ...EMPTY, ...existing } : EMPTY;
    if (draft) { setForm({ ...base, ...draft }); setDraftRestored(true); } else { setForm({ ...base, ...(preset || {}) }); setDraftRestored(false); }
    setConflict(null);
  }, [date, existing, preset]);

  const update = (patch) => {
    const next = { ...form, ...patch };
    if (patch.period === false) next.flow = "none";
    if (patch.flow && patch.flow !== "none") next.period = true;
    setForm(next);
    writeDraft(date, { period: next.period, flow: next.flow, moods: next.moods, symptoms: next.symptoms, medications_taken: next.medications_taken, notes: next.notes });
    refreshPending();
  };
  const toggle = (key, v) => update({ [key]: form[key].includes(v) ? form[key].filter((x) => x !== v) : [...form[key], v] });

  const save = async (force = false) => {
    if (!online) { toast.message("You're offline. This draft is saved on your device and will sync when you reconnect."); onClose(); return; }
    setBusy(true); setStatus("saving");
    try {
      const { data } = await api.put(`/logs/${date}`, { period: form.period, flow: form.flow, moods: form.moods, symptoms: form.symptoms, medications_taken: form.medications_taken, notes: form.notes, base_version: existing?.version ?? null, force });
      clearDraft(date); refreshPending(); setStatus("synced");
      toast.success("Day saved"); onSaved(data); onClose();
    } catch (err) {
      if (err?.response?.status === 409) { setConflict(err.response.data.detail.server); setStatus("idle"); }
      else { setStatus("error"); toast.error("Couldn't save. Your draft is kept on this device."); }
    } finally { setBusy(false); }
  };

  const remove = async () => {
    try {
      const { data } = await api.delete(`/logs/${date}`);
      clearDraft(date); refreshPending();
      toast.success(`Day cleared. You can restore it from Settings for ${data.recoverable_days} days.`);
      onSaved(null); onClose();
    } catch { toast.error("Couldn't delete right now."); }
  };

  return (
    <>
      <Sheet open={!!date} onOpenChange={(o) => !o && onClose()}>
        <SheetContent side={isMobile ? "bottom" : "right"} className={`${isMobile ? "max-h-[92vh] rounded-t-3xl" : "w-full sm:max-w-md"} overflow-y-auto bg-white/95 backdrop-blur-xl`} data-testid="day-log-sheet">
          <SheetHeader className="text-left">
            <SheetTitle className="font-display text-3xl">{date && d(date).format("dddd, D MMMM")}</SheetTitle>
            <SheetDescription>{t("log.subtitle")}</SheetDescription>
          </SheetHeader>
          {draftRestored && (
            <div role="status" className="mt-3 flex items-center justify-between rounded-2xl bg-secondary/40 px-4 py-2 text-sm" data-testid="draft-restored-banner">
              <span>{t("log.draft")}</span>
              <button type="button" className="underline" onClick={() => { clearDraft(date); refreshPending(); setForm(existing?.id ? { ...EMPTY, ...existing } : EMPTY); setDraftRestored(false); }} data-testid="discard-draft-button">{t("log.discard")}</button>
            </div>
          )}
          <form className="mt-5 space-y-6" onSubmit={(e) => { e.preventDefault(); save(); }}>
            <div className="flex items-center justify-between rounded-2xl border border-border p-4">
              <Label htmlFor="period-switch" className="text-base">{t("log.period")}</Label>
              <Switch id="period-switch" checked={form.period} onCheckedChange={(v) => update({ period: v })} data-testid="period-switch" />
            </div>
            <fieldset>
              <legend className="fh-eyebrow mb-2">{t("log.flow")}</legend>
              <div className="flex flex-wrap gap-2" role="radiogroup" aria-label={t("log.flow")}>
                {FLOWS.map((f) => (
                  <button key={f.value} type="button" role="radio" aria-checked={form.flow === f.value} className="fh-chip" aria-pressed={form.flow === f.value} onClick={() => update({ flow: f.value })} data-testid={`flow-${f.value}`}>{t(`opt.${f.value}`)}</button>
                ))}
              </div>
            </fieldset>
            <Chips label={t("log.mood")} options={MOODS} values={form.moods} onToggle={(v) => toggle("moods", v)} testPrefix="mood" labelOf={tOpt} />
            <Chips label={t("log.symptoms")} options={SYMPTOMS} values={form.symptoms} onToggle={(v) => toggle("symptoms", v)} testPrefix="symptom" labelOf={tOpt} />
            {medications.length > 0 && (
              <fieldset>
                <legend className="fh-eyebrow mb-2">{t("log.meds")}</legend>
                <div className="space-y-2">
                  {medications.map((m) => (
                    <label key={m.id} className="flex items-center gap-3 text-sm">
                      <Checkbox checked={form.medications_taken.includes(m.id)} onCheckedChange={() => toggle("medications_taken", m.id)} data-testid={`med-taken-${m.id}`} />
                      <span>{m.name}{m.dose ? ` · ${m.dose}` : ""}</span>
                    </label>
                  ))}
                </div>
              </fieldset>
            )}
            <div>
              <Label htmlFor="notes" className="fh-eyebrow">{t("log.notes")}</Label>
              <Textarea id="notes" value={form.notes} maxLength={2000} onChange={(e) => update({ notes: e.target.value })} className="mt-2 rounded-2xl" rows={3} placeholder={t("log.notesPlaceholder")} data-testid="notes-input" />
            </div>
            <div className="flex items-center justify-between gap-3 pt-2">
              {existing?.id ? (
                <Button type="button" variant="ghost" className="rounded-full text-destructive" onClick={() => setConfirmDelete(true)} data-testid="delete-log-button"><Trash2 size={16} strokeWidth={1.5} aria-hidden /> {t("log.clear")}</Button>
              ) : <span />}
              <Button type="submit" className="rounded-full px-6" disabled={busy} data-testid="save-log-button">{busy ? t("log.saving") : t("log.save")}</Button>
            </div>
          </form>
        </SheetContent>
      </Sheet>

      <AlertDialog open={!!conflict} onOpenChange={(o) => !o && setConflict(null)}>
        <AlertDialogContent className="rounded-3xl" data-testid="conflict-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle className="font-display text-2xl">This day changed on another device</AlertDialogTitle>
            <AlertDialogDescription className="text-left">
              Server version: {conflict?.period ? `period, ${conflict.flow} flow` : "no period"}; {conflict?.symptoms?.length || 0} symptoms; {conflict?.notes ? "has notes" : "no notes"}. Choose which version to keep — nothing is overwritten silently.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-full" onClick={() => { clearDraft(date); refreshPending(); onSaved(conflict); onClose(); }} data-testid="conflict-use-server">Use server version</AlertDialogCancel>
            <AlertDialogAction className="rounded-full" onClick={() => save(true)} data-testid="conflict-keep-mine">Keep my version</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <AlertDialogContent className="rounded-3xl" data-testid="delete-confirm-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle className="font-display text-2xl">Clear this day?</AlertDialogTitle>
            <AlertDialogDescription className="text-left">It moves to Recently deleted in Settings, where you can restore it for 30 days.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-full" data-testid="delete-cancel">Keep it</AlertDialogCancel>
            <AlertDialogAction className="rounded-full bg-destructive hover:bg-destructive/90" onClick={remove} data-testid="delete-confirm">Clear day</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
