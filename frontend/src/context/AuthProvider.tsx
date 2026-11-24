"use client";

import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import {
  type AuthTokenSession,
  getStoredAuthSession,
  setStoredAuthSession,
  signInAnonymouslyViaAuth,
} from "@/lib/firebase";
import type { Locale } from "@/lib/utils";

export interface UserProfile {
  uid: string;
  role: "tourist" | "admin";
  display_name: string | null;
  auth_provider: "anonymous" | "google" | "email";
  preferred_language: Locale;
  created_at: string;
  last_login: string;
}

interface AuthContextValue {
  session: AuthTokenSession | null;
  user: UserProfile | null;
  loading: boolean;
  error: string | null;
  signInAsGuest: (preferredLanguage?: Locale) => Promise<void>;
  signOut: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<AuthTokenSession | null>(() => getStoredAuthSession());
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(() => Boolean(getStoredAuthSession()));
  const [error, setError] = useState<string | null>(null);

  const fetchSyncedProfile = useCallback(
    async (
      activeSession: AuthTokenSession,
      preferredLanguage: Locale = "bn",
    ): Promise<UserProfile> => {
      try {
        return await apiFetch<UserProfile>("/auth/register", {
          method: "POST",
          token: activeSession.idToken,
          body: { preferred_language: preferredLanguage },
        });
      } catch {
        // Fallback guest profile when backend/emulator is offline (Tier 0 degradation)
        return {
          uid: activeSession.uid,
          role: "tourist",
          display_name: null,
          auth_provider: activeSession.authProvider,
          preferred_language: preferredLanguage,
          created_at: new Date().toISOString(),
          last_login: new Date().toISOString(),
        };
      }
    },
    [],
  );

  useEffect(() => {
    const existing = getStoredAuthSession();
    if (!existing) {
      return;
    }
    let active = true;
    fetchSyncedProfile(existing)
      .then((profile) => {
        if (active) {
          setUser(profile);
          setError(null);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [fetchSyncedProfile]);

  const signInAsGuest = useCallback(
    async (preferredLanguage: Locale = "bn") => {
      setLoading(true);
      setError(null);
      try {
        const newSession = await signInAnonymouslyViaAuth();
        setSession(newSession);
        const profile = await fetchSyncedProfile(newSession, preferredLanguage);
        setUser(profile);
      } catch {
        // Offline local guest session fallback so UI stays usable in Tier 0
        const fallbackSession: AuthTokenSession = {
          uid: `guest_${Date.now()}`,
          idToken: "offline-guest-token",
          authProvider: "anonymous",
        };
        setStoredAuthSession(fallbackSession);
        setSession(fallbackSession);
        setUser({
          uid: fallbackSession.uid,
          role: "tourist",
          display_name: null,
          auth_provider: "anonymous",
          preferred_language: preferredLanguage,
          created_at: new Date().toISOString(),
          last_login: new Date().toISOString(),
        });
      } finally {
        setLoading(false);
      }
    },
    [fetchSyncedProfile],
  );

  const refreshProfile = useCallback(async () => {
    if (!session) return;
    try {
      const profile = await apiFetch<UserProfile>("/me", {
        token: session.idToken,
      });
      setUser(profile);
    } catch {
      // Keep existing local state on transient network error
    }
  }, [session]);

  const signOut = useCallback(() => {
    setStoredAuthSession(null);
    setSession(null);
    setUser(null);
    setError(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        session,
        user,
        loading,
        error,
        signInAsGuest,
        signOut,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
