import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { pendingDrafts } from "@/lib/api";

const SyncContext = createContext(null);

export function SyncProvider({ children }) {
  const [online, setOnline] = useState(navigator.onLine);
  const [status, setStatus] = useState("idle");
  const [pending, setPending] = useState(pendingDrafts().length);

  useEffect(() => {
    const up = () => setOnline(true);
    const down = () => setOnline(false);
    window.addEventListener("online", up);
    window.addEventListener("offline", down);
    return () => { window.removeEventListener("online", up); window.removeEventListener("offline", down); };
  }, []);

  const refreshPending = useCallback(() => setPending(pendingDrafts().length), []);

  return <SyncContext.Provider value={{ online, status, setStatus, pending, refreshPending }}>{children}</SyncContext.Provider>;
}

export const useSync = () => useContext(SyncContext);
