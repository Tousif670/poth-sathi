"use client";

import Link from "next/link";
import { useState } from "react";
import { AlertTriangle, Bot, CheckCircle2, Send, ShieldAlert, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/context/AuthProvider";
import { useLocale } from "@/context/LocaleProvider";
import { ApiError } from "@/lib/api";
import { formatLocaleNumber } from "@/lib/utils";

export interface ChatCardPayload {
  type: "hotel" | "place" | "fare" | "beach_status";
  data: Record<string, unknown>;
}

export interface ChatSourcePayload {
  label: string;
  source_id: string;
  is_verified: boolean;
}

export interface ChatApiPayload {
  answer_text: string;
  language: "bn" | "en";
  session_id?: string | null;
  cards: ChatCardPayload[];
  sources: ChatSourcePayload[];
  severity?: "info" | "warning" | "error" | null;
  tool_calls_used: string[];
  fallback_used: boolean;
  safety_triggered: boolean;
  is_ai_resting: boolean;
}

interface ConversationMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  meta?: ChatApiPayload;
}

export function ChatPanel() {
  const { locale, t } = useLocale();
  const { session } = useAuth();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [remainingLimit, setRemainingLimit] = useState<number>(50);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);

  const samplePrompts = [
    t("কলাতলী থেকে লাবণী বিচে যেতে কত ভাড়া?", "What is the fare from Kolatoli to Laboni Beach?"),
    t("বাজেট ৩০০০ টাকার নিচে কলাতলীর হোটেল দেখান", "Hotels in Kolatoli under 3000 BDT with WiFi"),
    t("আজ সমুদ্র সৈকত কি নিরাপদ?", "Is the beach safe for swimming today?"),
    t("কাছের ফার্মেসি বা হাসপাতাল কোথায়?", "Where is the nearest pharmacy or hospital?"),
  ];

  const sendMessage = async (textToSend: string) => {
    const trimmed = textToSend.trim();
    if (!trimmed || loading) return;

    setMessages((prev) => [
      ...prev,
      {
        id: `u_${prev.length + 1}`,
        role: "user",
        text: trimmed,
      },
    ]);
    setInput("");
    setLoading(true);
    setErrorBanner(null);

    try {
      const apiBase = (process.env.NEXT_PUBLIC_API_URL?.trim() || "http://localhost:8000").replace(
        /\/+$/,
        "",
      );
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        Accept: "application/json",
      };
      if (session?.idToken) {
        headers["Authorization"] = `Bearer ${session.idToken}`;
      }

      const resp = await fetch(`${apiBase}/api/v1/chat/messages`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          message: trimmed,
          language: locale,
        }),
      });

      const remHeader = resp.headers.get("X-RateLimit-Remaining");
      if (remHeader && !isNaN(Number(remHeader))) {
        setRemainingLimit(Number(remHeader));
      }

      const data = await resp.json();
      if (!resp.ok) {
        const msg =
          locale === "bn"
            ? data?.error?.message_bn || "অনুরোধ ব্যর্থ হয়েছে।"
            : data?.error?.message_en || "Request failed.";
        throw new ApiError({
          code: data?.error?.code || "CHAT_ERROR",
          messageBn: msg,
          messageEn: msg,
          status: resp.status,
        });
      }

      const chatData = data as ChatApiPayload;
      setMessages((prev) => [
        ...prev,
        {
          id: `a_${prev.length + 1}`,
          role: "assistant",
          text: chatData.answer_text,
          meta: chatData,
        },
      ]);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorBanner(locale === "bn" ? err.messageBn : err.messageEn);
      } else {
        // Offline Tier 0 polite rest fallback
        const restMsg = t(
          "আমাদের AI সহকারী এখন বিশ্রামে আছে। নিচের তথ্যগুলো দেখুন।",
          "Our AI assistant is resting. See the information below.",
        );
        setMessages((prev) => [
          ...prev,
          {
            id: `a_${prev.length + 1}`,
            role: "assistant",
            text: restMsg,
            meta: {
              answer_text: restMsg,
              language: locale,
              cards: [],
              sources: [],
              tool_calls_used: [],
              fallback_used: true,
              safety_triggered: false,
              is_ai_resting: true,
            },
          },
        ]);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between border-b pb-4">
        <div>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Bot className="h-5 w-5 text-primary" />
            <span>{t("পথসাথী এআই ভ্রমণ সহকারী", "PothSathi AI Travel Companion")}</span>
          </CardTitle>
          <CardDescription className="text-xs">
            {t(
              "যাচাইকৃত তথ্যের ভিত্তিতে উত্তর দেয়। ব্যক্তিগত তথ্য (নাম, ফোন, ইমেইল) পাঠাবেন না।",
              "Grounded in verified local data. Do not share personal info (name, email, phone).",
            )}
          </CardDescription>
        </div>

        <span
          className="rounded-full bg-secondary px-3 py-1 text-xs font-semibold"
          data-testid="daily-limit-badge"
        >
          {t("বাকি মেসেজ:", "Daily Remaining:")} {formatLocaleNumber(remainingLimit, locale)}/
          {formatLocaleNumber(50, locale)}
        </span>
      </CardHeader>

      <CardContent className="space-y-4 pt-4">
        {messages.length === 0 && (
          <div className="space-y-3 rounded-xl bg-muted/40 p-4">
            <p className="text-xs font-semibold text-muted-foreground">
              {t("দ্রুত প্রশ্ন নির্বাচন করুন:", "Try asking a common question:")}
            </p>
            <div className="flex flex-wrap gap-2">
              {samplePrompts.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => sendMessage(prompt)}
                  className="rounded-lg border bg-background px-3 py-1.5 text-left text-xs hover:bg-secondary"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="max-h-[460px] space-y-4 overflow-y-auto pr-1">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col gap-2 ${
                msg.role === "user" ? "items-end" : "items-start"
              }`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : msg.meta?.safety_triggered
                      ? "border-2 border-red-600 bg-red-50 text-red-950 dark:bg-red-950/40 dark:text-red-100"
                      : "border bg-muted/50 text-foreground"
                }`}
              >
                <div className="mb-1 flex items-center gap-1.5 text-[11px] font-semibold opacity-80">
                  {msg.role === "user" ? (
                    <>
                      <User className="h-3 w-3" />
                      <span>{t("আপনি", "You")}</span>
                    </>
                  ) : msg.meta?.safety_triggered ? (
                    <>
                      <ShieldAlert className="h-3.5 w-3.5 text-red-600" />
                      <span>{t("জরুরি নিরাপত্তা সতর্কবার্তা", "Emergency Safety Response")}</span>
                    </>
                  ) : (
                    <>
                      <Bot className="h-3.5 w-3.5" />
                      <span>{t("পথসাথী এআই", "PothSathi AI")}</span>
                    </>
                  )}
                </div>

                <p className="whitespace-pre-line">{msg.text}</p>

                {msg.meta && msg.meta.cards.length > 0 && (
                  <div className="mt-3 grid gap-2">
                    {msg.meta.cards.map((card, idx) => (
                      <div
                        key={`${card.type}-${idx}`}
                        className="rounded-lg border bg-background p-2.5 text-xs text-foreground"
                      >
                        <span className="font-bold uppercase text-primary">{card.type}: </span>
                        <span>{String(card.data.name || card.data.zone_name || card.data.origin || "")}</span>
                        {card.data.price_min_bdt !== undefined && (
                          <span className="ml-2 font-semibold">
                            ৳{String(card.data.price_min_bdt)}
                          </span>
                        )}
                        {card.data.min_fare_bdt !== undefined && (
                          <span className="ml-2 font-semibold">
                            ৳{String(card.data.min_fare_bdt)}–৳{String(card.data.max_fare_bdt)}
                          </span>
                        )}
                        {card.data.flag !== undefined && (
                          <span className="ml-2 rounded bg-amber-100 px-1.5 py-0.5 font-bold uppercase text-amber-900">
                            {String(card.data.flag)}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {msg.meta && msg.meta.sources.length > 0 && (
                  <div className="mt-2.5 flex flex-wrap gap-1.5 border-t pt-2">
                    {msg.meta.sources.map((src) => (
                      <span
                        key={src.source_id}
                        className="inline-flex items-center gap-1 rounded-full bg-background/90 px-2.5 py-0.5 text-[11px] font-medium text-muted-foreground shadow-2xs"
                      >
                        <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                        <span>
                          {src.label} ({src.source_id})
                        </span>
                      </span>
                    ))}
                  </div>
                )}

                {msg.meta?.is_ai_resting && (
                  <div className="mt-3 flex flex-wrap gap-2 border-t pt-2 text-xs">
                    <Link href="/hotels" className="underline font-semibold">
                      {t("হোটেল তালিকা", "Hotels")}
                    </Link>
                    <span>•</span>
                    <Link href="/fares" className="underline font-semibold">
                      {t("ভাড়া ক্যালকুলেটর", "Fares")}
                    </Link>
                    <span>•</span>
                    <Link href="/safety" className="underline font-semibold">
                      {t("সৈকত পতাকা", "Beach Flags")}
                    </Link>
                    <span>•</span>
                    <Link href="/emergency" className="underline font-semibold text-red-600">
                      {t("জরুরি ৯৯৯", "Emergency 999")}
                    </Link>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <p className="text-xs italic text-muted-foreground">
              {t("পথসাথী উত্তর প্রস্তুত করছে...", "PothSathi is thinking...")}
            </p>
          )}
        </div>

        {errorBanner && (
          <div
            role="alert"
            className="flex items-center gap-2 rounded-lg border border-red-300 bg-red-50 p-3 text-xs text-red-900"
          >
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{errorBanner}</span>
          </div>
        )}

        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage(input);
          }}
          className="flex gap-2 pt-2"
        >
          <input
            type="text"
            maxLength={2000}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t(
              "বাংলা বা ইংরেজিতে আপনার প্রশ্ন লিখুন (সর্বোচ্চ ২০০০ অক্ষর)...",
              "Ask about Cox's Bazar hotels, fares, safety, or nearby places...",
            )}
            className="flex-1 rounded-xl border bg-background px-4 py-2.5 text-sm"
            data-testid="chat-input"
          />
          <Button type="submit" disabled={loading || !input.trim()} className="gap-1.5">
            <Send className="h-4 w-4" />
            <span>{t("পাঠান", "Send")}</span>
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
