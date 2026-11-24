"use client";

import React, { createContext, useCallback, useContext, useState } from "react";
import bnMessages from "@/messages/bn.json";
import enMessages from "@/messages/en.json";
import type { Locale } from "@/lib/utils";

type Messages = typeof enMessages;

const MESSAGE_MAP: Record<Locale, Messages> = {
  bn: bnMessages,
  en: enMessages,
};

const STORAGE_KEY = "pothsathi_locale";

interface LocaleContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  toggleLocale: () => void;
  messages: Messages;
  t: (bnText: string, enText: string) => string;
}

const LocaleContext = createContext<LocaleContextValue | undefined>(undefined);

function getInitialLocale(initialLocale: Locale): Locale {
  if (typeof window === "undefined") {
    return initialLocale;
  }
  const saved = window.localStorage.getItem(STORAGE_KEY);
  return saved === "bn" || saved === "en" ? saved : initialLocale;
}

export function LocaleProvider({
  children,
  initialLocale = "bn",
}: {
  children: React.ReactNode;
  initialLocale?: Locale;
}) {
  const [locale, setLocaleState] = useState<Locale>(() => getInitialLocale(initialLocale));

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, next);
      document.documentElement.lang = next;
    }
  }, []);

  const toggleLocale = useCallback(() => {
    setLocaleState((prev) => {
      const next: Locale = prev === "bn" ? "en" : "bn";
      if (typeof window !== "undefined") {
        window.localStorage.setItem(STORAGE_KEY, next);
        document.documentElement.lang = next;
      }
      return next;
    });
  }, []);

  const t = useCallback(
    (bnText: string, enText: string) => (locale === "bn" ? bnText : enText),
    [locale],
  );

  return (
    <LocaleContext.Provider
      value={{
        locale,
        setLocale,
        toggleLocale,
        messages: MESSAGE_MAP[locale],
        t,
      }}
    >
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale(): LocaleContextValue {
  const ctx = useContext(LocaleContext);
  if (!ctx) {
    throw new Error("useLocale must be used within a LocaleProvider");
  }
  return ctx;
}
