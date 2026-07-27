import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { fetchMe, login as loginApi, logout as logoutApi } from "../api/auth";
import { csrfState } from "../api/client";
import type { UserOut } from "../types";

interface AuthContextValue {
  user: UserOut | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: UserOut) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMe()
      .then((response) => {
        csrfState.token = response.csrf_token;
        setUser(response.user);
      })
      .catch(() => {
        csrfState.token = null;
      })
      .finally(() => setLoading(false));
  }, []);

  async function login(username: string, password: string) {
    const response = await loginApi(username, password);
    csrfState.token = response.csrf_token;
    setUser(response.user);
  }

  async function logout() {
    try {
      await logoutApi();
    } finally {
      csrfState.token = null;
      setUser(null);
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, setUser }}>{children}</AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
