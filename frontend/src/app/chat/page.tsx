"use client";

import { ChatPanel } from "@/components/chat/ChatPanel";
import { useLocale } from "@/context/LocaleProvider";

export default function ChatPage() {
  const { t } = useLocale();

  return (
    <main className="mx-auto max-w-4xl space-y-6 px-4 py-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
          {t("দ্বিভাষিক এআই ভ্রমণ চ্যাট", "Bilingual AI Travel Chat")}
        </h1>
        <p className="text-sm text-muted-foreground">
          {t(
            "জরুরি নিরাপত্তা নিয়ম, হোটেল অনুসন্ধান, ভাড়া হিসাব এবং যাচাইকৃত কক্সবাজার নলেজ বেস",
            "Powered by pre-LLM safety rules, verified Cox's Bazar tools, and grounded sources",
          )}
        </p>
      </div>

      <ChatPanel />
    </main>
  );
}
