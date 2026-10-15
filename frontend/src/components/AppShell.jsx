import { useCallback, useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { CalendarDays, Pill, BellRing, FileText, MessageCircleHeart, BookOpen, Settings as SettingsIcon, Lock, LogOut, Cloud, CloudOff, ShieldCheck } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useSync } from "@/context/SyncContext";
import { Button } from "@/components/ui/button";
import LockScreen from "@/components/LockScreen";
import ConsentDialog from "@/components/ConsentDialog";
import { useT } from "@/lib/i18n";

const NAV = [
  { to: "/app", key: "nav.calendar", icon: CalendarDays, end: true, id: "nav-calendar" },
  { to: "/app/medications", key: "nav.medications", icon: Pill, id: "nav-medications" },
  { to: "/app/reminders", key: "nav.reminders", icon: BellRing, id: "nav-reminders" },
  { to: "/app/reports", key: "nav.reports", icon: FileText, id: "nav-reports" },
  { to: "/app/chat", key: "nav.chat", icon: MessageCircleHeart, id: "nav-chat" },
  { to: "/app/resources", key: "nav.resources", icon: BookOpen, id: "nav-resources" },
  { to: "/app/settings", key: "nav.settings", icon: SettingsIcon, id: "nav-settings" },
];

function useAppLock(user) {
  const enabled = !!user?.settings?.lock_enabled;
  const timeoutMin = user?.settings?.lock_timeout_min || 5;
  const [locked, setLocked] = useState(() => enabled && sessionStorage.getItem("forher:unlocked") !== "1");

  useEffect(() => { if (!enabled) setLocked(false); }, [enabled]);

  useEffect(() => {
    if (!enabled || locked) return;
    let timer;
    const arm = () => {
      clearTimeout(timer);
      timer = setTimeout(() => { sessionStorage.removeItem("forher:unlocked"); setLocked(true); }, timeoutMin * 60_000);
    };
    const events = ["mousemove", "keydown", "touchstart", "click", "scroll"];
    events.forEach((e) => window.addEventListener(e, arm, { passive: true }));
    arm();
    return () => { clearTimeout(timer); events.forEach((e) => window.removeEventListener(e, arm)); };
  }, [enabled, locked, timeoutMin]);

  const lockNow = useCallback(() => { sessionStorage.removeItem("forher:unlocked"); setLocked(true); }, []);
  const unlock = useCallback(() => { sessionStorage.setItem("forher:unlocked", "1"); setLocked(false); }, []);
  return { enabled, locked, lockNow, unlock };
}

export default function AppShell() {
  const { user, logout } = useAuth();
  const { online, status, pending } = useSync();
  const navigate = useNavigate();
  const lock = useAppLock(user);
  const { t, lang } = useT();

  useEffect(() => {
    document.documentElement.classList.toggle("reduce-motion", !!user?.settings?.reduced_motion);
  }, [user?.settings?.reduced_motion]);
  useEffect(() => { document.documentElement.lang = lang; }, [lang]);

  const handleLogout = async () => { await logout(); navigate("/"); };

  if (lock.locked) return <LockScreen onUnlock={lock.unlock} onLogout={handleLogout} />;

  const syncLabel = !online ? t("sync.offline") : status === "saving" ? t("sync.saving") : status === "error" ? t("sync.error") : pending > 0 ? t("sync.pending", { n: pending }) : t("sync.synced");

  return (
    <div className="min-h-screen md:grid md:grid-cols-[240px_1fr]">
      <a href="#main" className="sr-only-focusable fixed left-4 top-4 z-50 rounded-full bg-primary px-4 py-2 text-primary-foreground">{t("shell.skip")}</a>
      <aside className="hidden md:flex flex-col border-r border-border bg-white/70 backdrop-blur-xl px-5 py-8" aria-label="Primary">
        <NavLink to="/app" className="flex items-center gap-2 px-2" data-testid="brand-link">
          <span aria-hidden className="h-8 w-8 rounded-full bg-primary grid place-items-center"><span className="h-4 w-4 rounded-full bg-background translate-x-[3px]" /></span>
          <span className="font-display text-2xl font-semibold tracking-tight">ForHer</span>
        </NavLink>
        <nav className="mt-10 flex flex-col gap-1">
          {NAV.map(({ to, key, icon: Icon, end, id }) => (
            <NavLink key={to} to={to} end={end} data-testid={id}
              className={({ isActive }) => `flex items-center gap-3 rounded-full px-4 py-2.5 text-sm font-medium transition-colors duration-200 ${isActive ? "bg-primary text-primary-foreground" : "text-foreground hover:bg-secondary/50"}`}>
              <Icon size={18} strokeWidth={1.5} aria-hidden /> {t(key)}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto space-y-3 text-xs text-muted-foreground">
          <p className="flex items-center gap-2" data-testid="sync-status" aria-live="polite">
            {online ? <Cloud size={14} aria-hidden /> : <CloudOff size={14} aria-hidden />} {syncLabel}
          </p>
          <p className="flex items-start gap-2"><ShieldCheck size={14} className="mt-0.5 shrink-0" aria-hidden /> {t("shell.privacy")}</p>
        </div>
      </aside>

      <div className="flex min-h-screen flex-col">
        <header className="sticky top-0 z-30 flex items-center justify-between border-b border-border bg-white/80 px-4 py-3 backdrop-blur-xl md:px-8">
          <div className="flex items-center gap-3 md:hidden">
            <span className="font-display text-xl font-semibold">ForHer</span>
            <span className="text-xs text-muted-foreground" data-testid="sync-status-mobile">{syncLabel}</span>
          </div>
          <p className="hidden md:block text-sm text-muted-foreground">{t("shell.hello", { name: user?.name?.split(" ")[0] || "" })}</p>
          <div className="flex items-center gap-2">
            {lock.enabled && (
              <Button variant="ghost" size="sm" className="rounded-full" onClick={lock.lockNow} data-testid="lock-now-button" aria-label={t("shell.lock")}>
                <Lock size={16} strokeWidth={1.5} aria-hidden /> <span className="hidden sm:inline">{t("shell.lock")}</span>
              </Button>
            )}
            <Button variant="ghost" size="sm" className="rounded-full" onClick={handleLogout} data-testid="logout-button">
              <LogOut size={16} strokeWidth={1.5} aria-hidden /> <span className="hidden sm:inline">{t("shell.signout")}</span>
            </Button>
          </div>
        </header>

        <main id="main" className="flex-1 px-4 py-6 pb-28 md:px-10 md:py-10 md:pb-16" tabIndex={-1}>
          <Outlet />
        </main>

        <footer className="hidden md:block border-t border-border px-10 py-4 text-xs text-muted-foreground" data-testid="privacy-footer">
          {t("shell.footer")}
        </footer>

        <nav className="fixed bottom-0 inset-x-0 z-30 grid grid-cols-7 border-t border-border bg-white/90 backdrop-blur-xl md:hidden" aria-label="Primary mobile">
          {NAV.map(({ to, key, icon: Icon, end, id }) => (
            <NavLink key={to} to={to} end={end} data-testid={`${id}-mobile`}
              className={({ isActive }) => `flex flex-col items-center gap-1 py-2.5 text-[10px] font-medium ${isActive ? "text-primary" : "text-muted-foreground"}`}>
              <Icon size={20} strokeWidth={1.5} aria-hidden /> {t(key)}
            </NavLink>
          ))}
        </nav>
      </div>
      {user && !user.consent && <ConsentDialog />}
    </div>
  );
}
