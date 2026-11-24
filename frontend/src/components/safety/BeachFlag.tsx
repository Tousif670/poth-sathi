"use client";

import { AlertTriangle, CheckCircle2, Clock, Flag } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useLocale } from "@/context/LocaleProvider";
import type { StaticBeachStatus } from "@/lib/staticData";
import { pickLocalized } from "@/lib/utils";

interface BeachFlagProps {
  zone: StaticBeachStatus;
}

const FLAG_STYLES = {
  green: {
    badge: "bg-emerald-100 text-emerald-900 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-200",
    dot: "bg-emerald-500",
    label: { bn: "সবুজ পতাকা (নিরাপদ)", en: "Green Flag (Low Hazard)" },
  },
  yellow: {
    badge: "bg-amber-100 text-amber-900 border-amber-300 dark:bg-amber-950 dark:text-amber-200",
    dot: "bg-amber-500",
    label: { bn: "হলুদ পতাকা (সতর্কতা)", en: "Yellow Flag (Medium Caution)" },
  },
  red: {
    badge: "bg-red-100 text-red-900 border-red-300 dark:bg-red-950 dark:text-red-200",
    dot: "bg-red-600",
    label: { bn: "লাল পতাকা (সমুদ্রে নামা নিষেধ)", en: "Red Flag (Do Not Swim)" },
  },
} as const;

export function BeachFlag({ zone }: BeachFlagProps) {
  const { locale, messages, t } = useLocale();
  const style = FLAG_STYLES[zone.flag_colour] ?? FLAG_STYLES.yellow;

  return (
    <Card
      className="flex flex-col justify-between border-feature-safety-border transition-shadow hover:shadow-md"
      data-testid={`beach-zone-${zone.zone_id}`}
    >
      <CardHeader className="space-y-2.5 pb-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span
            className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-bold ${style.badge}`}
          >
            <span className={`h-2.5 w-2.5 rounded-full ${style.dot}`} />
            <Flag className="h-3.5 w-3.5" />
            <span>{pickLocalized(style.label, locale)}</span>
          </span>

          {zone.is_outdated && (
            <span className="inline-flex items-center gap-1 rounded-full border border-feature-fares-border bg-feature-fares-tint px-2.5 py-0.5 text-[11px] font-semibold text-feature-fares dark:text-amber-200">
              <AlertTriangle className="h-3 w-3" />
              <span>{messages.badges.outdated}</span>
            </span>
          )}
        </div>

        <CardTitle className="text-lg font-bold text-foreground">
          {pickLocalized(zone.zone_name, locale)}
        </CardTitle>
        <CardDescription className="text-xs leading-relaxed">
          {pickLocalized(zone.note, locale)}
        </CardDescription>
      </CardHeader>

      <CardContent className="border-t border-feature-safety-border/60 bg-feature-safety-tint/30 pt-3 text-xs text-muted-foreground space-y-1">
        <div className="flex items-center justify-between">
          <span className="inline-flex items-center gap-1">
            <Clock className="h-3.5 w-3.5 text-feature-safety dark:text-sky-300" />
            <span>
              {t("সর্বশেষ আপডেট:", "Last updated:")} {zone.last_updated}
            </span>
          </span>
          <span className="inline-flex items-center gap-1 font-medium text-feature-safety dark:text-sky-300">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>{zone.is_verified ? messages.badges.verified : messages.badges.sample}</span>
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
