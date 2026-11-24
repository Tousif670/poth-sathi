"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  Compass,
  Hotel,
  MapPin,
  MessageSquare,
  PhoneCall,
  ShieldAlert,
  TrainFront,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ApiError, apiFetch } from "@/lib/api";
import { useLocale } from "@/context/LocaleProvider";
import {
  type StaticBeachStatus,
  type StaticEmergencyContact,
  loadTier0Json,
} from "@/lib/staticData";
import { pickLocalized, toBengaliDigits } from "@/lib/utils";

interface HealthResponse {
  status: string;
  app_env: string;
  firestore: string;
}

type HealthState =
  | { status: "loading" }
  | { status: "ok"; data: HealthResponse }
  | { status: "error"; messageEn: string; messageBn: string };

export default function HomePage() {
  const { locale, messages, t } = useLocale();
  const [health, setHealth] = useState<HealthState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [tier0Beaches, setTier0Beaches] = useState<StaticBeachStatus[]>([]);
  const [tier0Contacts, setTier0Contacts] = useState<StaticEmergencyContact[]>([]);

  useEffect(() => {
    loadTier0Json<StaticBeachStatus>("beach_status.json").then(setTier0Beaches);
    loadTier0Json<StaticEmergencyContact>("emergency.json").then(setTier0Contacts);
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    apiFetch<HealthResponse>("/health", { signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted) {
          setHealth({ status: "ok", data });
        }
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) {
          return;
        }
        if (err instanceof ApiError) {
          setHealth({
            status: "error",
            messageEn: err.messageEn,
            messageBn: err.messageBn,
          });
        } else {
          setHealth({
            status: "error",
            messageEn: "Could not connect to the backend right now.",
            messageBn: "এই মুহূর্তে ব্যাকএন্ডের সাথে সংযোগ করা সম্ভব হয়নি।",
          });
        }
      });

    return () => controller.abort();
  }, [attempt]);

  const handleRecheck = () => {
    setHealth({ status: "loading" });
    setAttempt((n) => n + 1);
  };

  const quickActions = [
    {
      href: "/chat",
      title: t("এআই ভ্রমণ সহকারী", "AI Travel Assistant"),
      badge: t("এআই চ্যাট", "AI Chat"),
      desc: t("বাংলা বা ইংরেজিতে প্রশ্ন করুন", "Ask questions in Bengali or English"),
      icon: MessageSquare,
      iconBg: "bg-feature-chat text-white",
      cardBorder: "border-feature-chat-border hover:border-feature-chat",
      tintBg: "bg-feature-chat-tint/70",
      badgeStyle: "bg-feature-chat-tint text-feature-chat border-feature-chat-border dark:text-violet-300",
      accentText: "text-feature-chat dark:text-violet-300",
    },
    {
      href: "/hotels",
      title: messages.nav.hotels,
      badge: t("হোটেল গাইড", "Hotels Guide"),
      desc: t("কলাতলী, সুগন্ধা ও লাবণীর হোটেল খুঁজুন", "Browse verified hotels by area & budget"),
      icon: Hotel,
      iconBg: "bg-feature-hotels text-white",
      cardBorder: "border-feature-hotels-border hover:border-feature-hotels",
      tintBg: "bg-feature-hotels-tint/70",
      badgeStyle: "bg-feature-hotels-tint text-feature-hotels border-feature-hotels-border dark:text-indigo-300",
      accentText: "text-feature-hotels dark:text-indigo-300",
    },
    {
      href: "/nearby",
      title: messages.nav.nearby,
      badge: t("কাছাকাছি স্থান", "Nearby Places"),
      desc: t("হাসপাতাল, ফার্মেসি, পুলিশ ও এটিএম ম্যাপ", "Hospitals, pharmacies, police & ATMs"),
      icon: MapPin,
      iconBg: "bg-feature-nearby text-white",
      cardBorder: "border-feature-nearby-border hover:border-feature-nearby",
      tintBg: "bg-feature-nearby-tint/70",
      badgeStyle: "bg-feature-nearby-tint text-feature-nearby border-feature-nearby-border dark:text-emerald-300",
      accentText: "text-feature-nearby dark:text-emerald-300",
    },
    {
      href: "/fares",
      title: messages.nav.fares,
      badge: t("ভাড়া ও ক্যালকুলেটর", "Transport Fares"),
      desc: t("সিএনজি, টমটম ও রিকশার ন্যায্য ভাড়া", "CNG, Tomtom & Rickshaw fare guide"),
      icon: TrainFront,
      iconBg: "bg-feature-fares text-white",
      cardBorder: "border-feature-fares-border hover:border-feature-fares",
      tintBg: "bg-feature-fares-tint/70",
      badgeStyle: "bg-feature-fares-tint text-feature-fares border-feature-fares-border dark:text-amber-300",
      accentText: "text-feature-fares dark:text-amber-300",
    },
    {
      href: "/safety",
      title: messages.nav.safety,
      badge: t("সৈকত নিরাপত্তা", "Beach Safety"),
      desc: t("সৈকতের পতাকা ও জোয়ারের সতর্কতা", "Live beach flag status & tide warnings"),
      icon: ShieldAlert,
      iconBg: "bg-feature-safety text-white",
      cardBorder: "border-feature-safety-border hover:border-feature-safety",
      tintBg: "bg-feature-safety-tint/70",
      badgeStyle: "bg-feature-safety-tint text-feature-safety border-feature-safety-border dark:text-sky-300",
      accentText: "text-feature-safety dark:text-sky-300",
    },
    {
      href: "/emergency",
      title: messages.nav.emergency,
      badge: t("জরুরি SOS", "Emergency 999"),
      desc: t("জাতীয় জরুরি সেবা ৯৯৯ ও ট্যুরিস্ট পুলিশ", "Emergency 999 & Tourist Police SOS"),
      icon: PhoneCall,
      iconBg: "bg-feature-emergency text-white",
      cardBorder: "border-feature-emergency-border hover:border-feature-emergency",
      tintBg: "bg-feature-emergency-tint/80",
      badgeStyle: "bg-feature-emergency-tint text-feature-emergency border-feature-emergency-border dark:text-red-300",
      accentText: "text-feature-emergency dark:text-red-300",
    },
  ];

  return (
    <main className="mx-auto max-w-6xl space-y-8 px-4 py-8" data-feature="home">
      {/* Hero Banner — Ocean Teal (#0F766E) & Soft Tint (#F0FDFA) */}
      <section className="relative overflow-hidden rounded-2xl border border-feature-home-border bg-feature-home-tint p-6 shadow-sm sm:p-8">
        <div className="max-w-2xl space-y-4">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-feature-home-border bg-card px-3.5 py-1 text-xs font-bold text-feature-home shadow-2xs dark:text-teal-300">
            <Compass className="h-3.5 w-3.5" />
            <span>{t("কক্সবাজার পর্যটন গাইড", "Cox's Bazar Tourism Guide")}</span>
          </span>
          <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            {messages.app.name} — {messages.app.tagline}
          </h1>
          <p className="text-sm leading-relaxed text-muted-foreground sm:text-base">
            {t(
              "যাচাইকৃত হোটেল ভাড়া, লোকাল ট্রান্সপোর্ট গাইড, সৈকত নিরাপত্তা পতাকা এবং জরুরি সেবার নির্ভরযোগ্য তথ্য।",
              "Verified hotel tariffs, local transport fare calculator, beach safety flags, and instant emergency contacts.",
            )}
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link href="/chat">
              <Button
                size="lg"
                className="gap-2 bg-feature-home text-white shadow-xs hover:bg-feature-home-hover px-5 py-2.5 h-10"
              >
                <MessageSquare className="h-4 w-4" />
                <span>{t("এআই চ্যাট শুরু করুন", "Start AI Chat")}</span>
              </Button>
            </Link>
            <Link href="/emergency">
              <Button
                size="lg"
                variant="destructive"
                className="gap-2 bg-feature-emergency text-white shadow-xs hover:bg-feature-emergency-hover px-5 py-2.5 h-10"
              >
                <PhoneCall className="h-4 w-4" />
                <span>
                  {t(
                    `জরুরি কল (${toBengaliDigits("999")})`,
                    "Emergency SOS (999)",
                  )}
                </span>
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Feature-Coded Dashboard Cards */}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {quickActions.map((item) => {
          const Icon = item.icon;
          return (
            <Link key={item.href} href={item.href} className="group block">
              <Card
                className={`h-full border transition-all duration-200 group-hover:-translate-y-0.5 group-hover:shadow-md ${item.cardBorder}`}
              >
                <CardHeader className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div
                      className={`flex h-11 w-11 items-center justify-center rounded-xl shadow-xs ${item.iconBg}`}
                    >
                      <Icon className="h-5 w-5" />
                    </div>
                    <span
                      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${item.badgeStyle}`}
                    >
                      {item.badge}
                    </span>
                  </div>
                  <div className="space-y-1">
                    <CardTitle className="flex items-center justify-between text-base font-bold">
                      <span>{item.title}</span>
                      <ArrowRight
                        className={`h-4 w-4 transition-transform group-hover:translate-x-1 ${item.accentText}`}
                      />
                    </CardTitle>
                    <CardDescription className="text-xs leading-relaxed">
                      {item.desc}
                    </CardDescription>
                  </div>
                </CardHeader>
              </Card>
            </Link>
          );
        })}
      </section>

      {/* Tier 0 Beach Snapshot (Sky Cyan) & System Connection Status (Ocean Teal) */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-feature-safety-border">
          <CardHeader className="border-b border-feature-safety-border/60 bg-feature-safety-tint/60">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-feature-safety dark:text-sky-300">
                <ShieldAlert className="h-5 w-5" />
                <span>{t("সৈকত নিরাপত্তা সংক্ষেপ (Tier 0)", "Beach Status Snapshot (Tier 0)")}</span>
              </CardTitle>
              <Link
                href="/safety"
                className="text-xs font-semibold text-feature-safety hover:underline dark:text-sky-300"
              >
                {t("বিস্তারিত →", "View All →")}
              </Link>
            </div>
            <CardDescription>
              {t("কলাতলী, সুগন্ধা ও লাবণী সৈকতের সর্বশেষ পতাকা", "Latest flags for Kolatoli, Sugandha & Laboni")}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 pt-4">
            {tier0Beaches.map((zone) => (
              <div
                key={zone.zone_id}
                className="flex items-center justify-between rounded-xl border border-border bg-background/60 p-3 text-sm"
              >
                <div>
                  <p className="font-semibold text-foreground">{pickLocalized(zone.zone_name, locale)}</p>
                  <p className="text-xs text-muted-foreground">{pickLocalized(zone.note, locale)}</p>
                </div>
                <span
                  className={`rounded-full px-3 py-0.5 text-xs font-bold uppercase ${
                    zone.flag_colour === "green"
                      ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200"
                      : zone.flag_colour === "yellow"
                        ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200"
                        : "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200"
                  }`}
                >
                  {zone.flag_colour}
                </span>
              </div>
            ))}
            {tier0Contacts.length > 0 && (
              <p className="text-xs text-muted-foreground pt-1">
                {t("জরুরি হটলাইন:", "Emergency Hotline:")}{" "}
                <strong className="text-feature-emergency">
                  {locale === "bn" ? toBengaliDigits(tier0Contacts[0].number) : tier0Contacts[0].number}
                </strong>{" "}
                ({messages.badges.sample})
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="border-feature-home-border">
          <CardHeader className="border-b border-feature-home-border/60 bg-feature-home-tint/60">
            <CardTitle className="text-feature-home dark:text-teal-300">
              {t("সিস্টেম সংযোগ স্ট্যাটাস", "System Connection Status")}
            </CardTitle>
            <CardDescription>
              {t("ফাস্টএপিআই ব্যাকএন্ড ও ফায়ারস্টোর সংযোগ পরীক্ষা", "Checking connection to FastAPI backend")}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 pt-4">
            {health.status === "loading" && (
              <p className="text-sm text-muted-foreground">
                {t("ব্যাকএন্ড স্ট্যাটাস পরীক্ষা করা হচ্ছে...", "Checking backend status...")}
              </p>
            )}

            {health.status === "ok" && (
              <div className="space-y-2 rounded-xl border border-feature-home-border bg-feature-home-tint p-3.5 text-sm text-foreground">
                <p className="font-semibold text-feature-home dark:text-teal-300">
                  Backend: {health.data.status}
                </p>
                <p>
                  Environment: <span className="font-mono font-medium">{health.data.app_env}</span>
                </p>
                <p>
                  Firestore: <span className="font-mono font-medium">{health.data.firestore}</span>
                </p>
              </div>
            )}

            {health.status === "error" && (
              <div
                role="alert"
                className="space-y-2 rounded-xl border border-feature-fares-border bg-feature-fares-tint p-3.5 text-sm text-foreground"
              >
                <p className="font-semibold text-feature-fares dark:text-amber-300">
                  {messages.badges.tier0Fallback}
                </p>
                <p className="text-muted-foreground">
                  {locale === "bn" ? health.messageBn : health.messageEn}
                </p>
              </div>
            )}

            <Button
              type="button"
              variant="outline"
              className="w-full border-feature-home-border text-feature-home hover:bg-feature-home-tint dark:text-teal-300"
              onClick={handleRecheck}
              disabled={health.status === "loading"}
            >
              {t("পুনরায় পরীক্ষা করুন", "Recheck Status")}
            </Button>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
