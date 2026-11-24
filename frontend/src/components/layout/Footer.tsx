"use client";

import Link from "next/link";
import { useLocale } from "@/context/LocaleProvider";

export function Footer() {
  const { messages, t } = useLocale();

  return (
    <footer className="border-t bg-muted/30 py-6 pb-20 md:pb-6">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 text-center text-xs text-muted-foreground sm:flex-row sm:text-left">
        <div className="space-y-1">
          <p className="font-medium text-foreground">{messages.app.name} — {messages.app.tagline}</p>
          <p>{messages.app.disclaimer}</p>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Link href="/emergency" className="font-semibold text-red-600 hover:underline">
            {t("জরুরি সেবা ৯৯৯", "Emergency 999")}
          </Link>
          <span>•</span>
          <span>© OpenStreetMap contributors</span>
        </div>
      </div>
    </footer>
  );
}
