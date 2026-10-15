import { useState } from "react";
import { Lock } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function LockScreen({ onUnlock, onLogout }) {
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      await api.post("/me/lock/verify", { pin });
      onUnlock();
    } catch (err) {
      setError(err?.response?.status === 403 ? "That PIN doesn't match. Try again." : "Couldn't verify right now. Check your connection.");
      setPin("");
    } finally { setBusy(false); }
  };

  return (
    <main className="min-h-screen grid place-items-center bg-background p-6" data-testid="lock-screen">
      <form onSubmit={submit} className="fh-card w-full max-w-sm p-8 fh-reveal" aria-labelledby="lock-title">
        <div className="mx-auto h-12 w-12 rounded-full bg-secondary/60 grid place-items-center"><Lock className="text-primary" strokeWidth={1.5} aria-hidden /></div>
        <h1 id="lock-title" className="mt-4 text-center text-3xl font-semibold">ForHer is locked</h1>
        <p className="mt-1 text-center text-sm text-muted-foreground">Enter your PIN to continue. Nothing is shown until you do.</p>
        <Label htmlFor="lock-pin" className="mt-6 block">PIN</Label>
        <Input id="lock-pin" type="password" inputMode="numeric" autoComplete="off" pattern="\d*" maxLength={8} value={pin} onChange={(e) => setPin(e.target.value.replace(/\D/g, ""))}
          className="mt-1 rounded-xl text-center text-lg tracking-[0.5em]" autoFocus data-testid="lock-pin-input" aria-describedby={error ? "lock-error" : undefined} />
        {error && <p id="lock-error" role="alert" className="mt-2 text-sm text-destructive" data-testid="lock-error">{error}</p>}
        <Button type="submit" className="mt-4 w-full rounded-full" disabled={pin.length < 4 || busy} data-testid="lock-unlock-button">Unlock</Button>
        <button type="button" onClick={onLogout} className="mt-4 w-full text-sm text-muted-foreground underline" data-testid="lock-signout-button">Sign out instead</button>
      </form>
    </main>
  );
}
