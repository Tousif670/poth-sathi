"use client";

import { ExternalLink, MapPin, Phone } from "lucide-react";
import { useLocale } from "@/context/LocaleProvider";
import type { StaticPlace } from "@/lib/staticData";
import { formatLocaleNumber, pickLocalized } from "@/lib/utils";

interface NearbyMapProps {
  places: StaticPlace[];
  selectedPlace: StaticPlace | null;
  onSelectPlace: (place: StaticPlace) => void;
}

export function NearbyMap({ places, selectedPlace, onSelectPlace }: NearbyMapProps) {
  const { locale, t } = useLocale();
  const focusLat = selectedPlace?.lat ?? 21.4272;
  const focusLon = selectedPlace?.lon ?? 91.9765;
  const bbox = `${(focusLon - 0.015).toFixed(4)}%2C${(focusLat - 0.012).toFixed(4)}%2C${(
    focusLon + 0.015
  ).toFixed(4)}%2C${(focusLat + 0.012).toFixed(4)}`;
  const osmEmbedUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${focusLat}%2C${focusLon}`;

  return (
    <div className="overflow-hidden rounded-2xl border border-feature-nearby-border bg-card shadow-sm">
      <div className="relative h-80 w-full bg-muted sm:h-96">
        <iframe
          title="Cox's Bazar OpenStreetMap"
          src={osmEmbedUrl}
          className="h-full w-full border-0"
          loading="lazy"
        />
        <div className="absolute bottom-2 right-2 rounded bg-card/90 px-2 py-0.5 text-[11px] text-muted-foreground shadow">
          ©{" "}
          <a
            href="https://www.openstreetmap.org/copyright"
            target="_blank"
            rel="noreferrer"
            className="underline"
          >
            OpenStreetMap
          </a>{" "}
          contributors
        </div>
      </div>

      <div className="border-t border-feature-nearby-border/60 p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs font-semibold text-muted-foreground">
            {t("ম্যাপে স্থান নির্বাচন করতে নিচের পিনে ক্লিক করুন:", "Tap a pin below to focus on OpenStreetMap:")}
          </p>
          {selectedPlace && (
            <a
              href={`https://www.openstreetmap.org/?mlat=${selectedPlace.lat}&mlon=${selectedPlace.lon}#map=16/${selectedPlace.lat}/${selectedPlace.lon}`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 rounded-full border border-feature-nearby-border bg-feature-nearby-tint px-2.5 py-0.5 text-xs font-semibold text-feature-nearby hover:bg-feature-nearby hover:text-white transition-colors dark:text-emerald-300"
            >
              <span>{t("পূর্ণ ম্যাপে খুলুন", "Open in OSM")}</span>
              <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          {places.map((p) => {
            const isSelected = selectedPlace?.place_id === p.place_id;
            return (
              <button
                key={p.place_id}
                type="button"
                onClick={() => onSelectPlace(p)}
                className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs transition-colors ${
                  isSelected
                    ? "border-feature-nearby bg-feature-nearby text-white font-semibold shadow-2xs"
                    : "border-border bg-background text-foreground hover:border-feature-nearby-border hover:bg-feature-nearby-tint hover:text-feature-nearby"
                }`}
              >
                <MapPin className="h-3.5 w-3.5 shrink-0" />
                <span>{pickLocalized(p.name, locale)}</span>
                {p.distance_km !== undefined && (
                  <span className={`text-[11px] ${isSelected ? "text-white/90" : "text-muted-foreground"}`}>
                    ({formatLocaleNumber(p.distance_km, locale)} km)
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {selectedPlace && (
          <div className="rounded-xl border border-feature-nearby-border bg-feature-nearby-tint/70 p-3.5 text-xs space-y-1">
            <p className="font-bold text-sm text-feature-nearby dark:text-emerald-300">
              {pickLocalized(selectedPlace.name, locale)}
            </p>
            <p className="text-muted-foreground">{pickLocalized(selectedPlace.address, locale)}</p>
            <div className="flex flex-wrap items-center gap-4 pt-1 text-foreground">
              <span className="inline-flex items-center gap-1 font-medium">
                <Phone className="h-3 w-3 text-feature-nearby dark:text-emerald-300" />
                <span>{selectedPlace.phone}</span>
              </span>
              <span>
                {t("সময়সূচী:", "Hours:")} <strong>{selectedPlace.opening_hours}</strong>
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
