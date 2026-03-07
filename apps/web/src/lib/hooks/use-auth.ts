"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { getToken, getUser, setAuth, clearAuth } from "@/lib/auth";
import { login as apiLogin, register as apiRegister } from "@/lib/api";
import type { AuthUser } from "@/lib/auth";

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setUser(getUser());
    setLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await apiLogin(email, password);
    const authUser: AuthUser = { user_id: res.user_id, email: res.email };
    setAuth(res.access_token, authUser);
    setUser(authUser);
  }, []);

  const register = useCallback(
    async (email: string, password: string, displayName?: string) => {
      const res = await apiRegister(email, password, displayName);
      const authUser: AuthUser = { user_id: res.user_id, email: res.email };
      setAuth(res.access_token, authUser);
      setUser(authUser);
    },
    [],
  );

  const logout = useCallback(() => {
    clearAuth();
    setUser(null);
  }, []);

  const isAuthenticated = !!getToken() && !!user;

  return { user, loading, isAuthenticated, login, register, logout };
}

export function useRequireAuth() {
  const auth = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!auth.loading && !auth.isAuthenticated) {
      router.replace("/login");
    }
  }, [auth.loading, auth.isAuthenticated, router]);

  return auth;
}
