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
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            {t("সমুদ্র সৈকত নিরাপত্তা ও পতাকা স্ট্যাটাস", "Beach Safety Flags & Advisories")}
          </h1>
          <p className="text-sm text-muted-foreground">
            {t(
              "কলাতলী, সুগন্ধা ও লাবণী পয়েন্টের সর্বশেষ সতর্কতা পতাকা (৬ ঘণ্টার বেশি পুরনো হলে সতর্কবার্তা দেখাবে)",
              "Live hazard flags for Kolatoli, Sugandha, and Laboni beaches (>6h old status marked as may be outdated)",
            )}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {isTier0Fallback && (
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-900">
              {messages.badges.tier0Fallback}
            </span>
          )}
          <Link href="/emergency">
            <Button variant="destructive" size="sm" className="gap-1.5">
              <PhoneCall className="h-4 w-4" />
              <span>{t("জরুরি SOS (৯৯৯)", "Emergency SOS (999)")}</span>
            </Button>
          </Link>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {zones.map((zone) => (
          <BeachFlag key={zone.zone_id} zone={zone} />
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <ShieldAlert className="h-5 w-5 text-amber-600" />
            <span>{t("সমুদ্র সৈকত নিরাপত্তা নির্দেশিকা", "Essential Beach Safety Guidelines")}</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {advisories.length > 0 ? (
            advisories.map((adv) => (
              <div key={adv.chunk_id} className="rounded-lg border bg-muted/40 p-3">
                {adv.text}
              </div>
            ))
          ) : (
            <div className="space-y-2">
              <div className="rounded-lg border bg-muted/40 p-3">
                {t(
                  "লাল পতাকা উত্তোলিত থাকলে কোনো অবস্থাতেই সমুদ্রে নামবেন না। ভাটার সময় সাঁতার কাটা থেকে বিরত থাকুন।",
                  "Never enter the sea when a red flag is hoisted. Avoid swimming during ebb tide (low tide pull).",
                )}
              </div>
              <div className="rounded-lg border bg-muted/40 p-3">
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
