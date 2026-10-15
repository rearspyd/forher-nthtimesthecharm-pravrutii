import { useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";

export default function ConsentDialog() {
  const { refresh, logout } = useAuth();
  const [agree, setAgree] = useState(false);
  const [busy, setBusy] = useState(false);

  const accept = async () => {
    setBusy(true);
    try { await api.put("/me/consent", { accepted: true }); await refresh(); } finally { setBusy(false); }
  };

  return (
    <Dialog open>
      <DialogContent className="rounded-3xl max-w-lg [&>button]:hidden" data-testid="consent-dialog" onEscapeKeyDown={(e) => e.preventDefault()} onPointerDownOutside={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle className="font-display text-3xl">Before we begin</DialogTitle>
          <DialogDescription className="text-left text-base text-foreground/80">A few honest things about how ForHer works.</DialogDescription>
        </DialogHeader>
        <ul className="space-y-3 text-sm leading-relaxed text-left">
          <li><strong>Awareness, not diagnosis.</strong> ForHer helps you notice patterns and prepare for conversations with a clinician. It never diagnoses or prescribes.</li>
          <li><strong>Your data stays yours.</strong> Logs are encrypted in transit, stored only under your account, never sold, and you can export or permanently delete everything in Settings.</li>
          <li><strong>Estimates are estimates.</strong> Cycle predictions are statistical guesses from what you log; they can be wrong or switched off for your context.</li>
          <li><strong>Minimal analytics.</strong> No health details appear in links, notifications or tracking.</li>
        </ul>
        <label className="mt-2 flex items-start gap-3 text-sm">
          <Checkbox checked={agree} onCheckedChange={(v) => setAgree(!!v)} data-testid="consent-checkbox" className="mt-0.5" />
          <span>I understand ForHer is a tracking and awareness tool, not medical advice, and I consent to storing my logs under my account.</span>
        </label>
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button variant="ghost" className="rounded-full" onClick={logout} data-testid="consent-decline-button">Not now, sign me out</Button>
          <Button className="rounded-full" disabled={!agree || busy} onClick={accept} data-testid="consent-accept-button">Continue</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
