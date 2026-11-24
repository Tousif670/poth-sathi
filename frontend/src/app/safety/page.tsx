"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { PhoneCall, ShieldAlert } from "lucide-react";
import { BeachFlag } from "@/components/safety/BeachFlag";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useLocale } from "@/context/LocaleProvider";
import { apiFetch } from "@/lib/api";
import { type StaticBeachStatus, loadTier0Json } from "@/lib/staticData";

interface BackendZoneItem {
  zone_id: "kolatoli" | "sugandha" | "laboni";
  zone_name: string;
  zone_name_bilingual: { bn: string; en: string };
  flag: "green" | "yellow" | "red";
  flag_colour: "green" | "yellow" | "red";
  flag_meaning: string;
  note: string | null;
  note_bilingual: { bn: string; en: string } | null;
  updated_by: string;
  data_source: string;
  is_verified: boolean;
  last_updated: string;
  is_outdated: boolean;
}

interface BackendBeachStatusResponse {
  zones: BackendZoneItem[];
}

interface BackendAdvisoryItem {
  chunk_id: string;
  text: string;
}

export default function SafetyPage() {
  const { locale, messages, t } = useLocale();
  const [zones, setZones] = useState<StaticBeachStatus[]>([]);
  const [advisories, setAdvisories] = useState<BackendAdvisoryItem[]>([]);
  const [isTier0Fallback, setIsTier0Fallback] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    apiFetch<BackendBeachStatusResponse>(`/safety/beach-status?lang=${locale}`, {
      signal: controller.signal,
    })
      .then((res) => {
        if (controller.signal.aborted) return;
        const mapped: StaticBeachStatus[] = res.zones.map((z) => ({
          id: z.zone_id,
          zone_id: z.zone_id,
          zone_name: z.zone_name_bilingual,
          flag_colour: z.flag_colour,
          note: z.note_bilingual ?? { bn: z.flag_meaning, en: z.flag_meaning },
          set_by: z.updated_by,
          data_source: z.data_source,
          is_verified: z.is_verified,
          last_updated: z.last_updated,
          is_outdated: z.is_outdated,
        }));
        setZones(mapped);
        setIsTier0Fallback(false);
      })
      .catch(async () => {
        if (controller.signal.aborted) return;
        const staticZones = await loadTier0Json<StaticBeachStatus>("beach_status.json");
        const nowMs = Date.now();
        setZones(
          staticZones.map((z) => {
            const ageHours = (nowMs - Date.parse(z.last_updated)) / (1000 * 3600);
            return { ...z, is_outdated: isNaN(ageHours) || ageHours > 6 };
          }),
        );
        setIsTier0Fallback(true);
      });

    apiFetch<{ items: BackendAdvisoryItem[] }>(`/safety/advisories?lang=${locale}`, {
      signal: controller.signal,
    })
      .then((res) => {
        if (!controller.signal.aborted) {
          setAdvisories(res.items);
        }
      })
      .catch(() => {
        // Advisories fallback handled gracefully below
      });

    return () => controller.abort();
  }, [locale]);

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-8" data-feature="safety">
      {/* Feature Header Banner — Sky Cyan (#0284C7) & Soft Tint (#F0F9FF) */}
      <section className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-feature-safety-border bg-feature-safety-tint p-5 shadow-2xs sm:p-6">
        <div className="flex items-start gap-3.5">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-feature-safety text-white shadow-xs">
            <ShieldAlert className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <span className="inline-flex items-center rounded-full border border-feature-safety-border bg-card px-2.5 py-0.5 text-[11px] font-bold text-feature-safety dark:text-sky-300">
              {t("সৈকত নিরাপত্তা ও পতাকা", "Beach Safety & Flags")}
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
              {t("সমুদ্র সৈকত নিরাপত্তা ও পতাকা স্ট্যাটাস", "Beach Safety Flags & Advisories")}
            </h1>
            <p className="text-sm text-muted-foreground">
              {t(
                "কলাতলী, সুগন্ধা ও লাবণী পয়েন্টের সর্বশেষ সতর্কতা পতাকা (৬ ঘণ্টার বেশি পুরনো হলে সতর্কবার্তা দেখাবে)",
                "Live hazard flags for Kolatoli, Sugandha, and Laboni beaches (>6h old status marked as may be outdated)",
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          {isTier0Fallback && (
            <span className="rounded-full border border-feature-fares-border bg-feature-fares-tint px-3 py-1 text-xs font-semibold text-feature-fares dark:text-amber-300">
              {messages.badges.tier0Fallback}
            </span>
          )}
          <Link href="/emergency">
            <Button
              variant="destructive"
              size="sm"
              className="gap-1.5 bg-feature-emergency text-white hover:bg-feature-emergency-hover shadow-xs"
            >
              <PhoneCall className="h-4 w-4" />
              <span>{t("জরুরি SOS (৯৯৯)", "Emergency SOS (999)")}</span>
            </Button>
          </Link>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-3">
        {zones.map((zone) => (
          <BeachFlag key={zone.zone_id} zone={zone} />
        ))}
      </div>

      <Card className="border-feature-safety-border">
        <CardHeader className="border-b border-feature-safety-border/60 bg-feature-safety-tint/60">
          <CardTitle className="flex items-center gap-2 text-lg text-feature-safety dark:text-sky-300">
            <ShieldAlert className="h-5 w-5" />
            <span>{t("সমুদ্র সৈকত নিরাপত্তা নির্দেশিকা", "Essential Beach Safety Guidelines")}</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 pt-4 text-sm">
          {advisories.length > 0 ? (
            advisories.map((adv) => (
              <div
                key={adv.chunk_id}
                className="rounded-xl border border-feature-safety-border/70 bg-feature-safety-tint/40 p-3.5 text-foreground"
              >
                {adv.text}
              </div>
            ))
          ) : (
            <div className="space-y-2.5">
              <div className="rounded-xl border border-feature-safety-border/70 bg-feature-safety-tint/40 p-3.5 text-foreground">
                {t(
                  "লাল পতাকা উত্তোলিত থাকলে কোনো অবস্থাতেই সমুদ্রে নামবেন না। ভাটার সময় সাঁতার কাটা থেকে বিরত থাকুন।",
                  "Never enter the sea when a red flag is hoisted. Avoid swimming during ebb tide (low tide pull).",
                )}
              </div>
              <div className="rounded-xl border border-feature-safety-border/70 bg-feature-safety-tint/40 p-3.5 text-foreground">
                {t(
                  "রিপ কারেন্টে (উল্টো স্রোত) পড়লে আতঙ্কিত না হয়ে তীরের সমান্তরালে সাঁতার কেটে স্রোত থেকে বের হয়ে আসুন।",
                  "If caught in a rip current, stay calm and swim parallel to the shoreline until free of the current.",
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
