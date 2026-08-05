"use client";

/** Minimal auth context: token in localStorage + user profile. */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { usePathname, useRouter } from "next/navigation";
import { api, getToken, setToken } from "@/lib/api";
import type { User } from "@/lib/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, name: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const existing = getToken();
    if (!existing) {
      setLoading(false);
      if (pathname !== "/login") router.replace("/login");
      return;
    }
    api
      .get<User>("/api/v1/auth/me")
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const resp = await api.post<{ access_token: string }>("/api/v1/auth/login", {
      email,
      password,
    });
    setToken(resp.access_token);
    setUser(await api.get<User>("/api/v1/auth/me"));
  }, []);

  const register = useCallback(
    async (email: string, name: string, password: string) => {
      const resp = await api.post<{ access_token: string }>(
        "/api/v1/auth/register",
        { email, name, password }
      );
      setToken(resp.access_token);
      setUser(await api.get<User>("/api/v1/auth/me"));
    },
    []
  );

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    router.replace("/login");
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
