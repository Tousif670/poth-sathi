"use client";

import { useEffect, useMemo, useState } from "react";
import { Clock, MapPin, Phone } from "lucide-react";
import { CategoryChips, type NearbyCategoryFilter } from "@/components/nearby/CategoryChips";
import { NearbyMap } from "@/components/nearby/NearbyMap";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useLocale } from "@/context/LocaleProvider";
import { apiFetch } from "@/lib/api";
import { type StaticPlace, loadTier0Json } from "@/lib/staticData";
import { formatLocaleNumber, pickLocalized } from "@/lib/utils";

interface BackendPlaceItem {
  place_id: string;
  name: string;
  name_bilingual: { bn: string; en: string };
  category: StaticPlace["category"];
  description: string | null;
  description_bilingual: { bn: string; en: string } | null;
  address: string | null;
  address_bilingual: { bn: string; en: string } | null;
  phone: string | null;
  opening_hours: string | null;
  lat: number;
  lon: number;
  distance_km: number | null;
  data_source: string;
  is_verified: boolean;
  last_updated: string;
}

interface BackendNearbyResponse {
  items: BackendPlaceItem[];
  count: number;
}

export default function NearbyPage() {
  const { locale, messages, t } = useLocale();
  const [category, setCategory] = useState<NearbyCategoryFilter>("all");
  const [places, setPlaces] = useState<StaticPlace[]>([]);
  const [isTier0Fallback, setIsTier0Fallback] = useState(false);
  const [selectedPlace, setSelectedPlace] = useState<StaticPlace | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({
      category,
      lat: "21.4250",
      lng: "91.9750",
      radius_km: "10",
      lang: locale,
    });

    apiFetch<BackendNearbyResponse>(`/nearby?${params.toString()}`, {
      signal: controller.signal,
    })
      .then((res) => {
        if (controller.signal.aborted) return;
        const mapped: StaticPlace[] = res.items.map((item) => ({
          id: item.place_id,
          place_id: item.place_id,
          name: item.name_bilingual,
          category: item.category,
          description: item.description_bilingual ?? { bn: item.name, en: item.name },
          address: item.address_bilingual ?? { bn: "", en: "" },
          phone: item.phone ?? "EXAMPLE_PHONE",
          opening_hours: item.opening_hours ?? "24/7",
          lat: item.lat,
          lon: item.lon,
          distance_km: item.distance_km ?? undefined,
          data_source: item.data_source,
          is_verified: item.is_verified,
          last_updated: item.last_updated,
        }));
        setPlaces(mapped);
        setSelectedPlace(mapped[0] ?? null);
        setIsTier0Fallback(false);
      })
      .catch(async () => {
        if (controller.signal.aborted) return;
        const staticPlaces = await loadTier0Json<StaticPlace>("places.json");
        setPlaces(staticPlaces);
        setSelectedPlace(staticPlaces[0] ?? null);
        setIsTier0Fallback(true);
      });

    return () => controller.abort();
  }, [category, locale]);

  const filteredPlaces = useMemo(() => {
    if (!isTier0Fallback || category === "all") return places;
    return places.filter((p) => p.category === category);
  }, [places, isTier0Fallback, category]);

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            {t("কাছাকাছি জরুরি সেবা ও ম্যাপ", "Nearby Essentials Map")}
          </h1>
          <p className="text-sm text-muted-foreground">
            {t(
              "ওপেনস্ট্রিটম্যাপে হাসপাতাল, ফার্মেসি, ট্যুরিস্ট পুলিশ, এটিএম ও মসজিদ খুঁজুন",
              "Locate hospitals, pharmacies, Tourist Police, ATMs, and mosques on OpenStreetMap",
            )}
          </p>
        </div>

        {isTier0Fallback && (
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-900">
            {messages.badges.tier0Fallback}
          </span>
        )}
      </div>

      <CategoryChips selected={category} onSelect={setCategory} />

      <NearbyMap
        places={filteredPlaces}
        selectedPlace={selectedPlace}
        onSelectPlace={setSelectedPlace}
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filteredPlaces.map((place) => (
          <Card
            key={place.place_id}
            className="cursor-pointer transition-shadow hover:shadow-md"
            onClick={() => setSelectedPlace(place)}
          >
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span className="uppercase font-semibold">{place.category}</span>
                <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-medium text-amber-900">
                  {place.is_verified ? messages.badges.verified : messages.badges.sample}
                </span>
              </div>
              <CardTitle className="text-base">{pickLocalized(place.name, locale)}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-xs text-muted-foreground">
              <p className="inline-flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5 shrink-0" />
                <span>{pickLocalized(place.address, locale)}</span>
              </p>
              <div className="flex flex-wrap items-center justify-between gap-2 border-t pt-2">
                <span className="inline-flex items-center gap-1">
                  <Phone className="h-3.5 w-3.5" />
                  <span>{place.phone}</span>
                </span>
                <span className="inline-flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5" />
                  <span>{place.opening_hours}</span>
                </span>
                {place.distance_km !== undefined && (
                  <span className="font-semibold text-primary">
                    {formatLocaleNumber(place.distance_km, locale)} km
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </main>
  );
}
