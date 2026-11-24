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
    <Card>
      <CardHeader>
        <CardTitle>{t("স্থানীয় যাতায়াত ভাড়ার তালিকা", "Local Transport Fare Table")}</CardTitle>
        <CardDescription>
          {t(
            "কলাতলী, সুগন্ধা ও লাবণী রুটের নির্ধারিত ভাড়ার পরিসর (D22)",
            "Reference fare ranges across Kolatoli, Sugandha, and Laboni routes (D22)",
          )}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr className="border-b text-xs uppercase text-muted-foreground">
                <th className="py-2.5 pr-3">{t("রুট (শুরু → গন্তব্য)", "Route (Origin → Destination)")}</th>
                <th className="py-2.5 px-3">{t("যানবাহন", "Vehicle")}</th>
                <th className="py-2.5 px-3">{t("ভাড়ার ধরন", "Fare Basis")}</th>
                <th className="py-2.5 px-3">{t("ভাড়ার পরিসর", "Fare Range")}</th>
                <th className="py-2.5 pl-3">{t("স্ট্যাটাস", "Status")}</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {routes.map((route) => {
                const vehicleLabel = VEHICLE_LABELS[route.vehicle_type]
                  ? pickLocalized(VEHICLE_LABELS[route.vehicle_type], locale)
                  : route.vehicle_type;
                return (
                  <tr key={route.route_id} className="hover:bg-muted/40">
                    <td className="py-3 pr-3">
                      <p className="font-semibold">
                        {pickLocalized(route.origin, locale)} →{" "}
                        {pickLocalized(route.destination, locale)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {pickLocalized(route.notes, locale)} (
                        {formatLocaleNumber(route.distance_km, locale)} km)
                      </p>
                    </td>
                    <td className="py-3 px-3 text-xs font-medium">{vehicleLabel}</td>
                    <td className="py-3 px-3 text-xs">
                      <span className="rounded-md bg-secondary px-2 py-0.5 font-medium">
                        {route.fare_basis === "per_person"
                          ? t("জনপ্রতি (Per Person)", "Per Person")
                          : t("পুরো গাড়ি (Per Vehicle)", "Per Vehicle")}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-bold text-primary">
                      {formatBdt(route.fare_min_bdt, locale)} –{" "}
                      {formatBdt(route.fare_max_bdt, locale)}
                    </td>
                    <td className="py-3 pl-3 text-xs">
                      <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-[11px] font-semibold text-amber-900">
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
