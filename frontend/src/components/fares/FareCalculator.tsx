"use client";

import { useState } from "react";
import { Calculator } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useLocale } from "@/context/LocaleProvider";
import { apiFetch } from "@/lib/api";
import type { StaticTransportRoute } from "@/lib/staticData";
import { formatBdt, formatLocaleNumber, pickLocalized } from "@/lib/utils";

interface FareCalculatorProps {
  routes: StaticTransportRoute[];
}

interface CalcResult {
  origin: string;
  destination: string;
  mode: string;
  passengers: number;
  fare_basis: "per_person" | "per_vehicle";
  min_fare_bdt: number;
  max_fare_bdt: number;
  notes?: string;
}

export function FareCalculator({ routes }: FareCalculatorProps) {
  const { locale, t } = useLocale();
  const [selectedRouteId, setSelectedRouteId] = useState<string>(routes[0]?.route_id || "EXAMPLE_route_001");
  const [passengers, setPassengers] = useState<number>(2);
  const [result, setResult] = useState<CalcResult | null>(null);

  const handleCalculate = async () => {
    const route = routes.find((r) => r.route_id === selectedRouteId) ?? routes[0];
    if (!route) return;

    try {
      const params = new URLSearchParams({
        origin: route.origin.en,
        destination: route.destination.en,
        mode: route.vehicle_type,
        passengers: String(passengers),
        lang: locale,
      });
      const res = await apiFetch<CalcResult>(`/transport/calculate?${params.toString()}`);
      setResult(res);
    } catch {
      // Offline Tier 0 local calculation following D22 rules
      const multiplier = route.fare_basis === "per_person" ? passengers : 1;
      setResult({
        origin: pickLocalized(route.origin, locale),
        destination: pickLocalized(route.destination, locale),
        mode: route.vehicle_type,
        passengers,
        fare_basis: route.fare_basis,
        min_fare_bdt: route.fare_min_bdt * multiplier,
        max_fare_bdt: route.fare_max_bdt * multiplier,
        notes: pickLocalized(route.notes, locale),
      });
    }
  };

  return (
    <Card className="border-feature-fares-border">
      <CardHeader className="border-b border-feature-fares-border/60 bg-feature-fares-tint/60">
        <CardTitle className="flex items-center gap-2 text-feature-fares dark:text-amber-300">
          <Calculator className="h-5 w-5" />
          <span>{t("ভাড়া ক্যালকুলেটর (D22)", "Trip Fare Calculator (D22)")}</span>
        </CardTitle>
        <CardDescription>
          {t(
            "রুট ও যাত্রী সংখ্যা নির্বাচন করে মোট আনুমানিক ভাড়া হিসাব করুন",
            "Select a route and passenger count to calculate total estimated fare",
          )}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 pt-4">
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="space-y-1.5 sm:col-span-2">
            <label htmlFor="route-select" className="text-xs font-semibold text-foreground">
              {t("রুট ও যানবাহন", "Route & Vehicle Mode")}
            </label>
            <select
              id="route-select"
              value={selectedRouteId}
              onChange={(e) => setSelectedRouteId(e.target.value)}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:border-feature-fares focus:outline-none"
            >
              {routes.map((r) => (
                <option key={r.route_id} value={r.route_id}>
                  {pickLocalized(r.origin, locale)} → {pickLocalized(r.destination, locale)} ({r.vehicle_type})
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label htmlFor="passengers-input" className="text-xs font-semibold text-foreground">
              {t("যাত্রী সংখ্যা", "Passengers")}
            </label>
            <input
              id="passengers-input"
              type="number"
              min={1}
              max={10}
              value={passengers}
              onChange={(e) => setPassengers(Math.max(1, Number(e.target.value) || 1))}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:border-feature-fares focus:outline-none"
            />
          </div>
        </div>

        <Button
          type="button"
          onClick={handleCalculate}
          className="w-full sm:w-auto bg-feature-fares text-white hover:bg-feature-fares-hover shadow-xs"
        >
          {t("মোট ভাড়া হিসাব করুন", "Calculate Estimated Fare")}
        </Button>

        {result && (
          <div className="rounded-xl border border-feature-fares-border bg-feature-fares-tint p-4 space-y-1">
            <p className="text-xs text-muted-foreground">
              {result.origin} → {result.destination} •{" "}
              {formatLocaleNumber(result.passengers, locale)}{" "}
              {t("জন যাত্রী", "passenger(s)")}
            </p>
            <p className="text-2xl font-bold text-feature-fares dark:text-amber-300">
              {formatBdt(result.min_fare_bdt, locale)} – {formatBdt(result.max_fare_bdt, locale)}
            </p>
            <p className="text-xs text-muted-foreground">
              {result.fare_basis === "per_person"
                ? t(
                    "ভাড়ার ধরন: জনপ্রতি (যাত্রী সংখ্যা দিয়ে গুণ করা হয়েছে)",
                    "Fare basis: Per person (multiplied by passenger count)",
                  )
                : t(
                    "ভাড়ার ধরন: পুরো গাড়ি রিজার্ভ (যাত্রী সংখ্যায় ভাড়া পরিবর্তিত হয় না)",
                    "Fare basis: Per vehicle (flat vehicle rate regardless of passengers)",
                  )}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
