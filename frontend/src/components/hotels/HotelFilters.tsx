"use client";

import { Button } from "@/components/ui/button";
import { useLocale } from "@/context/LocaleProvider";
import { formatBdt } from "@/lib/utils";

export interface HotelFilterState {
  area: "" | "kolatoli" | "sugandha" | "laboni";
  maxPriceBdt: number;
  amenities: string[];
  sort: "match" | "price_asc" | "price_desc" | "rating";
}

interface HotelFiltersProps {
  filters: HotelFilterState;
  onChange: (next: HotelFilterState) => void;
  onReset: () => void;
}

const AVAILABLE_AMENITIES = [
  { id: "wifi", bn: "ওয়াইফাই (WiFi)", en: "WiFi" },
  { id: "ac", bn: "এসি (AC)", en: "AC" },
  { id: "pool", bn: "সুইমিং পুল", en: "Swimming Pool" },
  { id: "restaurant", bn: "রেস্তোরাঁ", en: "Restaurant" },
  { id: "parking", bn: "পার্কিং", en: "Parking" },
];

export function HotelFilters({ filters, onChange, onReset }: HotelFiltersProps) {
  const { locale, t } = useLocale();

  const toggleAmenity = (id: string) => {
    const exists = filters.amenities.includes(id);
    const nextAmenities = exists
      ? filters.amenities.filter((a) => a !== id)
      : [...filters.amenities, id];
    onChange({ ...filters, amenities: nextAmenities });
  };

  return (
    <div className="rounded-xl border bg-card p-4 space-y-4 shadow-xs">
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-1.5">
          <label htmlFor="area-select" className="text-xs font-semibold">
            {t("এলাকা নির্বাচন করুন", "Select Beach Zone")}
          </label>
          <select
            id="area-select"
            value={filters.area}
            onChange={(e) =>
              onChange({
                ...filters,
                area: e.target.value as HotelFilterState["area"],
              })
            }
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
          >
            <option value="">{t("সব এলাকা (কলাতলী, সুগন্ধা, লাবণী)", "All Zones")}</option>
            <option value="kolatoli">{t("কলাতলী (Kolatoli)", "Kolatoli")}</option>
            <option value="sugandha">{t("সুগন্ধা (Sugandha)", "Sugandha")}</option>
            <option value="laboni">{t("লাবণী (Laboni)", "Laboni")}</option>
          </select>
        </div>

        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs font-semibold">
            <label htmlFor="budget-slider">{t("সর্বোচ্চ বাজেট (সর্বনিম্ন ভাড়া)", "Max Budget (Min Tariff)")}</label>
            <span className="text-primary font-bold">{formatBdt(filters.maxPriceBdt, locale)}</span>
          </div>
          <input
            id="budget-slider"
            type="range"
            min={1000}
            max={10000}
            step={500}
            value={filters.maxPriceBdt}
            onChange={(e) =>
              onChange({
                ...filters,
                maxPriceBdt: Number(e.target.value),
              })
            }
            className="w-full accent-primary"
          />
        </div>

        <div className="space-y-1.5">
          <label htmlFor="sort-select" className="text-xs font-semibold">
            {t("সাজানোর ক্রম", "Sort By")}
          </label>
          <select
            id="sort-select"
            value={filters.sort}
            onChange={(e) =>
              onChange({
                ...filters,
                sort: e.target.value as HotelFilterState["sort"],
              })
            }
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
          >
            <option value="match">{t("রেকমেন্ডার স্কোর (সেরা মিল)", "Recommender Match Score")}</option>
            <option value="price_asc">{t("ভাড়া (কম থেকে বেশি)", "Price (Low to High)")}</option>
            <option value="price_desc">{t("ভাড়া (বেশি থেকে কম)", "Price (High to Low)")}</option>
            <option value="rating">{t("রেটিং (সর্বোচ্চ)", "Highest Rating")}</option>
          </select>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t pt-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold text-muted-foreground">
            {t("সুবিধাসমূহ:", "Amenities:")}
          </span>
          {AVAILABLE_AMENITIES.map((item) => {
            const active = filters.amenities.includes(item.id);
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => toggleAmenity(item.id)}
                className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                  active
                    ? "border-primary bg-primary text-primary-foreground"
                    : "bg-background text-muted-foreground hover:bg-secondary"
                }`}
              >
                {locale === "bn" ? item.bn : item.en}
              </button>
            );
          })}
        </div>

        <Button type="button" variant="ghost" size="sm" onClick={onReset}>
          {t("ফিল্টার রিসেট", "Reset Filters")}
        </Button>
      </div>
    </div>
  );
}
