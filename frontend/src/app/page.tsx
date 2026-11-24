"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Hotel, MapPin, MessageSquare, PhoneCall, ShieldAlert, TrainFront } from "lucide-react";
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
      desc: t("বাংলা বা ইংরেজিতে প্রশ্ন করুন", "Ask questions in Bengali or English"),
      icon: MessageSquare,
      primary: true,
    },
    {
      href: "/hotels",
      title: messages.nav.hotels,
      desc: t("কলাতলী, সুগন্ধা ও লাবণীর হোটেল খুঁজুন", "Browse verified hotels by area & budget"),
      icon: Hotel,
    },
    {
      href: "/fares",
      title: messages.nav.fares,
      desc: t("সিএনজি, টমটম ও রিকশার ন্যায্য ভাড়া", "CNG, Tomtom & Rickshaw fare guide"),
      icon: TrainFront,
    },
    {
      href: "/nearby",
      title: messages.nav.nearby,
      desc: t("হাসপাতাল, ফার্মেসি, পুলিশ ও এটিএম ম্যাপ", "Hospitals, pharmacies, police & ATMs"),
      icon: MapPin,
    },
    {
      href: "/safety",
      title: messages.nav.safety,
      desc: t("সৈকতের পতাকা ও জোয়ারের সতর্কতা", "Live beach flag status & tide warnings"),
      icon: ShieldAlert,
    },
    {
      href: "/emergency",
      title: messages.nav.emergency,
      desc: t("জাতীয় জরুরি সেবা ৯৯৯ ও ট্যুরিস্ট পুলিশ", "Emergency 999 & Tourist Police SOS"),
      icon: PhoneCall,
      urgent: true,
    },
  ];

  return (
    <main className="mx-auto max-w-6xl space-y-8 px-4 py-8">
      <section className="rounded-2xl border bg-gradient-to-br from-sky-50 via-background to-emerald-50 p-6 sm:p-8 dark:from-sky-950/30 dark:to-emerald-950/20">
        <div className="max-w-2xl space-y-3">
          <span className="inline-flex items-center rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
            {t("কক্সবাজার পর্যটন গাইড", "Cox's Bazar Tourism Guide")}
          </span>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
            {messages.app.name} — {messages.app.tagline}
          </h1>
          <p className="text-sm text-muted-foreground sm:text-base">
            {t(
              "যাচাইকৃত হোটেল ভাড়া, লোকাল ট্রান্সপোর্ট গাইড, সৈকত নিরাপত্তা পতাকা এবং জরুরি সেবার নির্ভরযোগ্য তথ্য।",
              "Verified hotel tariffs, local transport fare calculator, beach safety flags, and instant emergency contacts.",
            )}
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link href="/chat">
              <Button size="lg" className="gap-2">
                <MessageSquare className="h-4 w-4" />
                <span>{t("এআই চ্যাট শুরু করুন", "Start AI Chat")}</span>
              </Button>
            </Link>
            <Link href="/emergency">
              <Button size="lg" variant="destructive" className="gap-2">
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

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {quickActions.map((item) => {
          const Icon = item.icon;
          return (
            <Link key={item.href} href={item.href} className="group block">
              <Card className="h-full transition-shadow group-hover:shadow-md">
                <CardHeader className="flex flex-row items-center gap-3 pb-2">
                  <div
                    className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                      item.urgent
                        ? "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300"
                        : item.primary
                          ? "bg-primary text-primary-foreground"
                          : "bg-secondary text-secondary-foreground"
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <CardTitle className="text-base">{item.title}</CardTitle>
                    <CardDescription className="text-xs">{item.desc}</CardDescription>
                  </div>
                </CardHeader>
              </Card>
            </Link>
          );
        })}
      </section>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{t("সৈকত নিরাপত্তা সংক্ষেপ (Tier 0)", "Beach Status Snapshot (Tier 0)")}</CardTitle>
            <CardDescription>
              {t("কলাতলী, সুগন্ধা ও লাবণী সৈকতের সর্বশেষ পতাকা", "Latest flags for Kolatoli, Sugandha & Laboni")}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {tier0Beaches.map((zone) => (
              <div
                key={zone.zone_id}
                className="flex items-center justify-between rounded-lg border p-3 text-sm"
              >
                <div>
                  <p className="font-semibold">{pickLocalized(zone.zone_name, locale)}</p>
                  <p className="text-xs text-muted-foreground">{pickLocalized(zone.note, locale)}</p>
                </div>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-bold uppercase ${
                    zone.flag_colour === "green"
                      ? "bg-emerald-100 text-emerald-800"
                      : zone.flag_colour === "yellow"
                        ? "bg-amber-100 text-amber-800"
                        : "bg-red-100 text-red-800"
                  }`}
                >
                  {zone.flag_colour}
                </span>
              </div>
            ))}
            {tier0Contacts.length > 0 && (
              <p className="text-xs text-muted-foreground">
                {t("জরুরি হটলাইন:", "Emergency Hotline:")}{" "}
                <strong>
                  {locale === "bn" ? toBengaliDigits(tier0Contacts[0].number) : tier0Contacts[0].number}
                </strong>{" "}
                ({messages.badges.sample})
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("সিস্টেম সংযোগ স্ট্যাটাস", "System Connection Status")}</CardTitle>
            <CardDescription>
              {t("ফাস্টএপিআই ব্যাকএন্ড ও ফায়ারস্টোর সংযোগ পরীক্ষা", "Checking connection to FastAPI backend")}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {health.status === "loading" && (
              <p className="text-sm text-muted-foreground">
                {t("ব্যাকএন্ড স্ট্যাটাস পরীক্ষা করা হচ্ছে...", "Checking backend status...")}
              </p>
            )}

            {health.status === "ok" && (
              <div className="space-y-2 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-950 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-100">
                <p className="font-semibold">Backend: {health.data.status}</p>
                <p>
                  Environment: <span className="font-mono">{health.data.app_env}</span>
                </p>
                <p>
                  Firestore: <span className="font-mono">{health.data.firestore}</span>
                </p>
              </div>
            )}

            {health.status === "error" && (
              <div
                role="alert"
                className="space-y-2 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-100"
              >
                <p className="font-semibold">{messages.badges.tier0Fallback}</p>
                <p>{locale === "bn" ? health.messageBn : health.messageEn}</p>
              </div>
            )}

            <Button
              type="button"
              variant="outline"
              className="w-full"
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
