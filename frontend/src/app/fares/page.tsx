"use client";

import { useEffect, useState } from "react";
import { FareCalculator } from "@/components/fares/FareCalculator";
import { FareTable } from "@/components/fares/FareTable";
import { useLocale } from "@/context/LocaleProvider";
import { apiFetch } from "@/lib/api";
import { type StaticTransportRoute, loadTier0Json } from "@/lib/staticData";

interface BackendFareItem {
  route_id: string;
  origin: string;
  origin_bilingual: { bn: string; en: string };
  destination: string;
  destination_bilingual: { bn: string; en: string };
  vehicle_type: StaticTransportRoute["vehicle_type"];
  fare_basis: StaticTransportRoute["fare_basis"];
  fare_min_bdt: number;
  fare_max_bdt: number;
  distance_km: number | null;
  notes: string | null;
  notes_bilingual: { bn: string; en: string } | null;
  data_source: string;
  is_verified: boolean;
  last_updated: string;
}

interface BackendFareListResponse {
  items: BackendFareItem[];
  count: number;
}

export default function FaresPage() {
  const { locale, messages, t } = useLocale();
  const [routes, setRoutes] = useState<StaticTransportRoute[]>([]);
  const [isTier0Fallback, setIsTier0Fallback] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    apiFetch<BackendFareListResponse>(`/transport/fares?lang=${locale}`, {
      signal: controller.signal,
    })
      .then((res) => {
        if (controller.signal.aborted) return;
        const mapped: StaticTransportRoute[] = res.items.map((item) => ({
          id: item.route_id,
          route_id: item.route_id,
          origin: item.origin_bilingual,
          destination: item.destination_bilingual,
          vehicle_type: item.vehicle_type,
          fare_basis: item.fare_basis,
          fare_min_bdt: item.fare_min_bdt,
          fare_max_bdt: item.fare_max_bdt,
          distance_km: item.distance_km ?? 2.0,
          notes: item.notes_bilingual ?? { bn: "", en: "" },
          data_source: item.data_source,
          is_verified: item.is_verified,
          last_updated: item.last_updated,
        }));
        setRoutes(mapped);
        setIsTier0Fallback(false);
      })
      .catch(async () => {
        if (controller.signal.aborted) return;
        const staticRoutes = await loadTier0Json<StaticTransportRoute>("fares.json");
        setRoutes(staticRoutes);
        setIsTier0Fallback(true);
      });

    return () => controller.abort();
  }, [locale]);

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            {t("যাতায়াত ভাড়া গাইড ও ক্যালকুলেটর", "Transport Fare Guide & Calculator")}
          </h1>
          <p className="text-sm text-muted-foreground">
            {t(
              "সিএনজি অটো, টমটম (ইজিবাইক) ও রিকশার ন্যায্য ভাড়ার তালিকা এবং হিসাব",
              "Fair fare guide and trip calculator for CNG autos, Tomtoms, and Rickshaws",
            )}
          </p>
        </div>

        {isTier0Fallback && (
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-900">
            {messages.badges.tier0Fallback}
          </span>
        )}
      </div>

      {routes.length > 0 && <FareCalculator routes={routes} />}
      <FareTable routes={routes} />
    </main>
  );
}
