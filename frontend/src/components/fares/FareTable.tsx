"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useLocale } from "@/context/LocaleProvider";
import type { StaticTransportRoute } from "@/lib/staticData";
import { formatBdt, formatLocaleNumber, pickLocalized } from "@/lib/utils";

interface FareTableProps {
  routes: StaticTransportRoute[];
}

const VEHICLE_LABELS: Record<string, { bn: string; en: string }> = {
  cng_auto: { bn: "সিএনজি অটো (CNG Auto)", en: "CNG Auto" },
  tomtom: { bn: "টমটম / ইজিবাইক (Tomtom)", en: "Tomtom (Easy-bike)" },
  rickshaw: { bn: "ব্যাটারি রিকশা (Rickshaw)", en: "Battery Rickshaw" },
};

export function FareTable({ routes }: FareTableProps) {
  const { locale, messages, t } = useLocale();

  return (
    <Card className="border-feature-fares-border">
      <CardHeader className="border-b border-feature-fares-border/60 bg-feature-fares-tint/40">
        <CardTitle className="text-foreground">
          {t("স্থানীয় যাতায়াত ভাড়ার তালিকা", "Local Transport Fare Table")}
        </CardTitle>
        <CardDescription>
          {t(
            "কলাতলী, সুগন্ধা ও লাবণী রুটের নির্ধারিত ভাড়ার পরিসর (D22)",
            "Reference fare ranges across Kolatoli, Sugandha, and Laboni routes (D22)",
          )}
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        <div className="overflow-x-auto rounded-xl border border-feature-fares-border/70">
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-feature-fares-border bg-feature-fares-tint text-xs font-bold uppercase text-feature-fares dark:text-amber-300">
                <th className="py-3 pl-4 pr-3">{t("রুট (শুরু → গন্তব্য)", "Route (Origin → Destination)")}</th>
                <th className="py-3 px-3">{t("যানবাহন", "Vehicle")}</th>
                <th className="py-3 px-3">{t("ভাড়ার ধরন", "Fare Basis")}</th>
                <th className="py-3 px-3">{t("ভাড়ার পরিসর", "Fare Range")}</th>
                <th className="py-3 pl-3 pr-4">{t("স্ট্যাটাস", "Status")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {routes.map((route) => {
                const vehicleLabel = VEHICLE_LABELS[route.vehicle_type]
                  ? pickLocalized(VEHICLE_LABELS[route.vehicle_type], locale)
                  : route.vehicle_type;
                return (
                  <tr key={route.route_id} className="transition-colors hover:bg-feature-fares-tint/40">
                    <td className="py-3 pl-4 pr-3">
                      <p className="font-semibold text-foreground">
                        {pickLocalized(route.origin, locale)} →{" "}
                        {pickLocalized(route.destination, locale)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {pickLocalized(route.notes, locale)} (
                        {formatLocaleNumber(route.distance_km, locale)} km)
                      </p>
                    </td>
                    <td className="py-3 px-3 text-xs font-medium text-foreground">{vehicleLabel}</td>
                    <td className="py-3 px-3 text-xs">
                      <span className="rounded-md border border-feature-fares-border bg-feature-fares-tint px-2.5 py-0.5 font-semibold text-feature-fares dark:text-amber-300">
                        {route.fare_basis === "per_person"
                          ? t("জনপ্রতি (Per Person)", "Per Person")
                          : t("পুরো গাড়ি (Per Vehicle)", "Per Vehicle")}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-bold text-feature-fares dark:text-amber-300">
                      {formatBdt(route.fare_min_bdt, locale)} –{" "}
                      {formatBdt(route.fare_max_bdt, locale)}
                    </td>
                    <td className="py-3 pl-3 pr-4 text-xs">
                      <span className="rounded-full border border-feature-fares-border bg-feature-fares-tint px-2.5 py-0.5 text-[11px] font-semibold text-feature-fares dark:text-amber-200">
                        {route.is_verified ? messages.badges.verified : messages.badges.sample}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
