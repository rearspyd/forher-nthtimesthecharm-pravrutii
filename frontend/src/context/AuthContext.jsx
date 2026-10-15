import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
      return data;
    } catch {
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // If returning from OAuth, AuthCallback exchanges the session_id first.
    if (window.location.hash?.includes("session_id=")) {
      setLoading(false);
      return;
    }
    refresh();
  }, [refresh]);

  const logout = useCallback(async () => {
    await api.post("/auth/logout");
    sessionStorage.removeItem("forher:unlocked");
    setUser(null);
  }, []);

  return <AuthContext.Provider value={{ user, setUser, loading, refresh, logout }}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
