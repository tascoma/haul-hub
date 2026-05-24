import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { api, getToken, setToken } from "./api";
import type { Me, TokenResponse } from "./types";

interface AuthState {
  me: Me | null;
  loading: boolean;
  signup: (email: string, password: string, fullName: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState<boolean>(getToken() !== null);

  const refresh = useCallback(async () => {
    if (!getToken()) {
      setMe(null);
      setLoading(false);
      return;
    }
    try {
      const data = await api.get<Me>("/me");
      setMe(data);
    } catch {
      setToken(null);
      setMe(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const signup = useCallback(
    async (email: string, password: string, fullName: string) => {
      const res = await api.post<TokenResponse>(
        "/auth/signup",
        { email, password, full_name: fullName },
        { skipAuth: true },
      );
      setToken(res.access_token);
      setLoading(true);
      await refresh();
    },
    [refresh],
  );

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await api.post<TokenResponse>(
        "/auth/login",
        { email, password },
        { skipAuth: true },
      );
      setToken(res.access_token);
      setLoading(true);
      await refresh();
    },
    [refresh],
  );

  const logout = useCallback(() => {
    setToken(null);
    setMe(null);
  }, []);

  return (
    <AuthContext.Provider value={{ me, loading, signup, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside <AuthProvider>");
  return ctx;
}
