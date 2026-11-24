"use client";

import { MessageSquare } from "lucide-react";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { useLocale } from "@/context/LocaleProvider";

export default function ChatPage() {
  const { t } = useLocale();

  return (
    <main className="mx-auto max-w-4xl space-y-6 px-4 py-8" data-feature="chat">
      {/* Feature Header Banner — Electric Violet (#7C3AED) & Soft Tint (#F5F3FF) */}
      <section className="flex items-start gap-3.5 rounded-2xl border border-feature-chat-border bg-feature-chat-tint p-5 shadow-2xs sm:p-6">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-feature-chat text-white shadow-xs">
          <MessageSquare className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <span className="inline-flex items-center rounded-full border border-feature-chat-border bg-card px-2.5 py-0.5 text-[11px] font-bold text-feature-chat dark:text-violet-300">
            {t("এআই ভ্রমণ সঙ্গী", "AI Chat Companion")}
          </span>
          <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            {t("দ্বিভাষিক এআই ভ্রমণ চ্যাট", "Bilingual AI Travel Chat")}
          </h1>
          <p className="text-sm text-muted-foreground">
            {t(
              "জরুরি নিরাপত্তা নিয়ম, হোটেল অনুসন্ধান, ভাড়া হিসাব এবং যাচাইকৃত কক্সবাজার নলেজ বেস",
              "Powered by pre-LLM safety rules, verified Cox's Bazar tools, and grounded sources",
            )}
          </p>
        </div>
      </section>

      <ChatPanel />
    </main>
  );
}
