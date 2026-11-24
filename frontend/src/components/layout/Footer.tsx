"use client";

import Link from "next/link";
import { useLocale } from "@/context/LocaleProvider";

export function Footer() {
  const { messages, t } = useLocale();

  return (
    <footer className="border-t border-border bg-card py-6 pb-20 lg:pb-6">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 text-center text-xs text-muted-foreground sm:flex-row sm:text-left">
        <div className="space-y-1">
          <p className="font-semibold text-foreground">
            <span className="text-primary dark:text-teal-400">পথসাথী | PothSathi</span> — {messages.app.tagline}
          </p>
          <p>{messages.app.disclaimer}</p>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/emergency"
            className="inline-flex items-center gap-1 rounded-full border border-feature-emergency-border bg-feature-emergency-tint px-3 py-1 font-semibold text-feature-emergency hover:bg-feature-emergency hover:text-white transition-colors"
          >
            {t("জরুরি সেবা ৯৯৯", "Emergency 999")}
          </Link>
          <span>•</span>
          <span>© OpenStreetMap contributors</span>
        </div>
      </div>
    </footer>
  );
}
