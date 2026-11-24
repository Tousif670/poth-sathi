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
    <Card className="flex flex-col justify-between transition-shadow hover:shadow-md" data-testid={`hotel-card-${hotel.hotel_id}`}>
      <CardHeader className="space-y-2 pb-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="inline-flex items-center gap-1 rounded-md bg-secondary px-2 py-0.5 text-xs font-medium">
            <MapPin className="h-3 w-3" />
            <span>{areaLabel}</span>
          </span>

          <div className="flex items-center gap-1.5">
            {matchPercent !== null && (
              <span className="rounded-full bg-sky-100 px-2.5 py-0.5 text-xs font-bold text-sky-900 dark:bg-sky-950 dark:text-sky-200">
                {formatLocaleNumber(matchPercent, locale)}% {t("মিল", "Match")}
              </span>
            )}
            {hotel.is_verified ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200">
                <CheckCircle2 className="h-3 w-3" />
                <span>{messages.badges.verified}</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-900 dark:bg-amber-950 dark:text-amber-200">
                <Info className="h-3 w-3" />
                <span>{messages.badges.sample}</span>
              </span>
            )}
          </div>
        </div>

        <CardTitle className="text-lg">{pickLocalized(hotel.name, locale)}</CardTitle>
        <CardDescription className="line-clamp-2 text-xs">
          {pickLocalized(hotel.description, locale)}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex items-baseline justify-between border-y py-2.5">
          <div>
            <p className="text-xs text-muted-foreground">{t("প্রতি রাতের ভাড়া", "Tariff per night")}</p>
            <p className="text-lg font-bold text-primary">
              {formatBdt(hotel.price_min_bdt, locale)} – {formatBdt(hotel.price_max_bdt, locale)}
            </p>
          </div>
          <div className="flex items-center gap-1 rounded-md bg-amber-50 px-2 py-1 text-sm font-semibold text-amber-800 dark:bg-amber-950/60 dark:text-amber-200">
            <Star className="h-4 w-4 fill-amber-400 text-amber-500" />
            <span>{formatLocaleNumber(hotel.rating.toFixed(1), locale)}</span>
          </div>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {hotel.amenities.map((amenity) => (
            <span
              key={amenity}
              className="rounded-md border bg-muted/50 px-2 py-0.5 text-xs capitalize text-muted-foreground"
            >
              {amenity}
            </span>
          ))}
        </div>

        <div className="flex items-center justify-between pt-1 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <Phone className="h-3.5 w-3.5" />
            <span>{hotel.phone}</span>
          </span>
          {onSelect && (
            <Button type="button" variant="outline" size="sm" onClick={() => onSelect(hotel)}>
              {t("বিস্তারিত দেখুন", "View Details")}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
