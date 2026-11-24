"use client";

import { CheckCircle2, Info, MapPin, Phone, Star } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useLocale } from "@/context/LocaleProvider";
import type { StaticHotel } from "@/lib/staticData";
import { formatBdt, formatLocaleNumber, pickLocalized } from "@/lib/utils";

interface HotelCardProps {
  hotel: StaticHotel;
  onSelect?: (hotel: StaticHotel) => void;
}

const AREA_LABELS = {
  kolatoli: { bn: "কলাতলী", en: "Kolatoli" },
  sugandha: { bn: "সুগন্ধা", en: "Sugandha" },
  laboni: { bn: "লাবণী", en: "Laboni" },
} as const;

export function HotelCard({ hotel, onSelect }: HotelCardProps) {
  const { locale, messages, t } = useLocale();
  const areaLabel = AREA_LABELS[hotel.area]
    ? pickLocalized(AREA_LABELS[hotel.area], locale)
    : hotel.area;

  const matchPercent =
    hotel.match_score !== undefined ? Math.round(hotel.match_score * 100) : null;

  return (
    <Card
      className="flex flex-col justify-between border-border transition-all hover:border-feature-hotels-border hover:shadow-md"
      data-testid={`hotel-card-${hotel.hotel_id}`}
    >
      <CardHeader className="space-y-2 pb-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="inline-flex items-center gap-1 rounded-md border border-feature-hotels-border bg-feature-hotels-tint px-2.5 py-0.5 text-xs font-semibold text-feature-hotels dark:text-indigo-300">
            <MapPin className="h-3 w-3" />
            <span>{areaLabel}</span>
          </span>

          <div className="flex items-center gap-1.5">
            {matchPercent !== null && (
              <span className="rounded-full bg-feature-hotels px-2.5 py-0.5 text-xs font-bold text-white shadow-2xs">
                {formatLocaleNumber(matchPercent, locale)}% {t("মিল", "Match")}
              </span>
            )}
            {hotel.is_verified ? (
              <span className="inline-flex items-center gap-1 rounded-full border border-feature-nearby-border bg-feature-nearby-tint px-2.5 py-0.5 text-xs font-semibold text-feature-nearby dark:text-emerald-200">
                <CheckCircle2 className="h-3 w-3" />
                <span>{messages.badges.verified}</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full border border-feature-fares-border bg-feature-fares-tint px-2.5 py-0.5 text-xs font-semibold text-feature-fares dark:text-amber-200">
                <Info className="h-3 w-3" />
                <span>{messages.badges.sample}</span>
              </span>
            )}
          </div>
        </div>

        <CardTitle className="text-lg font-bold text-foreground">
          {pickLocalized(hotel.name, locale)}
        </CardTitle>
        <CardDescription className="line-clamp-2 text-xs">
          {pickLocalized(hotel.description, locale)}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex items-baseline justify-between rounded-xl border border-feature-hotels-border/60 bg-feature-hotels-tint/50 px-3 py-2.5">
          <div>
            <p className="text-xs text-muted-foreground">{t("প্রতি রাতের ভাড়া", "Tariff per night")}</p>
            <p className="text-lg font-bold text-feature-hotels dark:text-indigo-300">
              {formatBdt(hotel.price_min_bdt, locale)} – {formatBdt(hotel.price_max_bdt, locale)}
            </p>
          </div>
          <div className="flex items-center gap-1 rounded-md border border-feature-fares-border bg-feature-fares-tint px-2 py-1 text-sm font-semibold text-feature-fares dark:text-amber-200">
            <Star className="h-4 w-4 fill-amber-400 text-amber-500" />
            <span>{formatLocaleNumber(hotel.rating.toFixed(1), locale)}</span>
          </div>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {hotel.amenities.map((amenity) => (
            <span
              key={amenity}
              className="rounded-md border border-border bg-muted/60 px-2 py-0.5 text-xs capitalize text-muted-foreground"
            >
              {amenity}
            </span>
          ))}
        </div>

        <div className="flex items-center justify-between pt-1 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <Phone className="h-3.5 w-3.5 text-feature-hotels dark:text-indigo-300" />
            <span>{hotel.phone}</span>
          </span>
          {onSelect && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => onSelect(hotel)}
              className="border-feature-hotels-border text-feature-hotels hover:bg-feature-hotels hover:text-white dark:text-indigo-300"
            >
              {t("বিস্তারিত দেখুন", "View Details")}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
