"use client";

import { useEffect, useMemo, useState } from "react";
import { Flag, MessageSquarePlus } from "lucide-react";
import { HotelCard } from "@/components/hotels/HotelCard";
import { HotelFilters, type HotelFilterState } from "@/components/hotels/HotelFilters";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthProvider";
import { useLocale } from "@/context/LocaleProvider";
import { apiFetch } from "@/lib/api";
import { type StaticHotel, loadTier0Json } from "@/lib/staticData";
import { formatBdt, formatLocaleNumber, pickLocalized } from "@/lib/utils";

interface BackendHotelItem {
  hotel_id: string;
  name: string;
  name_bilingual: { bn: string; en: string };
  area: "kolatoli" | "sugandha" | "laboni";
  description: string | null;
  description_bilingual: { bn: string; en: string } | null;
  address: string | null;
  address_bilingual: { bn: string; en: string } | null;
  price_min_bdt: number;
  price_max_bdt: number;
  amenities: string[];
  rating: number;
  phone: string | null;
  lat: number;
  lon: number;
  image_url: string;
  data_source: string;
  is_verified: boolean;
  last_updated: string;
  match_score: number;
}

interface BackendHotelResponse {
  items: BackendHotelItem[];
  total: number;
}

const DEFAULT_FILTERS: HotelFilterState = {
  area: "",
  maxPriceBdt: 6000,
  amenities: [],
  sort: "match",
};

function computeLocalScore(hotel: StaticHotel, filters: HotelFilterState): number {
  const budgetScore =
    filters.maxPriceBdt <= 0
      ? 1.0
      : hotel.price_min_bdt <= filters.maxPriceBdt
        ? 1.0 - (filters.maxPriceBdt - hotel.price_min_bdt) / filters.maxPriceBdt
        : 0.0;
  const areaScore = !filters.area || hotel.area === filters.area ? 1.0 : 0.0;
  const amenityScore =
    filters.amenities.length === 0
      ? 1.0
      : filters.amenities.filter((a) => hotel.amenities.includes(a)).length /
        filters.amenities.length;
  const ratingScore = hotel.rating > 0 ? Math.min(hotel.rating / 5.0, 1.0) : 0.5;
  return Number(
    (budgetScore * 0.3 + areaScore * 0.25 + amenityScore * 0.25 + ratingScore * 0.2).toFixed(3),
  );
}

export default function HotelsPage() {
  const { locale, messages, t } = useLocale();
  const { session } = useAuth();
  const [filters, setFilters] = useState<HotelFilterState>(DEFAULT_FILTERS);
  const [hotels, setHotels] = useState<StaticHotel[]>([]);
  const [isTier0Fallback, setIsTier0Fallback] = useState(false);
  const [selectedHotel, setSelectedHotel] = useState<StaticHotel | null>(null);
  const [reviewComment, setReviewComment] = useState("");
  const [reviewRating, setReviewRating] = useState(5);
  const [feedbackNotice, setFeedbackNotice] = useState<string | null>(null);

  const handleReportWrongInfo = async (hotel: StaticHotel) => {
    try {
      const res = await apiFetch<{ message_bn: string; message_en: string }>("/reports", {
        method: "POST",
        token: session?.idToken,
        body: {
          entity_type: "hotel",
          entity_id: hotel.hotel_id,
          issue_description: "User flagged hotel tariff or details for verification.",
        },
      });
      setFeedbackNotice(locale === "bn" ? res.message_bn : res.message_en);
    } catch {
      setFeedbackNotice(
        t(
          "ধন্যবাদ। আপনার প্রতিবেদনটি পর্যালোচনার জন্য নোট করা হয়েছে।",
          "Thank you. Your report has been noted for review.",
        ),
      );
    }
  };

  const handleSubmitReview = async (hotel: StaticHotel) => {
    if (!reviewComment.trim()) return;
    try {
      const res = await apiFetch<{ sentiment: { overall: string } }>(
        `/hotels/${hotel.hotel_id}/reviews`,
        {
          method: "POST",
          token: session?.idToken,
          body: {
            rating: reviewRating,
            comment: reviewComment.trim(),
            lang: locale,
          },
        },
      );
      setReviewComment("");
      setFeedbackNotice(
        t(
          `রিভিউ জমা হয়েছে! সেন্টিমেন্ট: ${res.sentiment.overall}`,
          `Review submitted! Detected sentiment: ${res.sentiment.overall}`,
        ),
      );
    } catch {
      setFeedbackNotice(
        t(
          "রিভিউ জমা দিতে উপরে 'অতিথি হিসেবে শুরু করুন' বাটনে ক্লিক করুন।",
          "Please click 'Continue as Guest' in the top bar before posting a review.",
        ),
      );
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams();
    if (filters.area) params.set("area", filters.area);
    if (filters.maxPriceBdt) params.set("max_price_bdt", String(filters.maxPriceBdt));
    if (filters.amenities.length > 0) params.set("amenities", filters.amenities.join(","));
    params.set("sort", filters.sort);
    params.set("lang", locale);

    apiFetch<BackendHotelResponse>(`/hotels?${params.toString()}`, {
      signal: controller.signal,
    })
      .then((res) => {
        if (controller.signal.aborted) return;
        const mapped: StaticHotel[] = res.items.map((item) => ({
          id: item.hotel_id,
          hotel_id: item.hotel_id,
          name: item.name_bilingual,
          area: item.area,
          description: item.description_bilingual ?? { bn: item.name, en: item.name },
          address: item.address_bilingual ?? { bn: "", en: "" },
          price_min_bdt: item.price_min_bdt,
          price_max_bdt: item.price_max_bdt,
          amenities: item.amenities,
          rating: item.rating,
          phone: item.phone ?? "EXAMPLE_PHONE",
          lat: item.lat,
          lon: item.lon,
          image_url: item.image_url,
          data_source: item.data_source,
          is_verified: item.is_verified,
          last_updated: item.last_updated,
          match_score: item.match_score,
        }));
        setHotels(mapped);
        setIsTier0Fallback(false);
      })
      .catch(async () => {
        if (controller.signal.aborted) return;
        const staticHotels = await loadTier0Json<StaticHotel>("hotels.json");
        setHotels(staticHotels);
        setIsTier0Fallback(true);
      });

    return () => controller.abort();
  }, [filters, locale]);

  const displayedHotels = useMemo(() => {
    if (!isTier0Fallback) return hotels;
    return hotels
      .filter((h) => (!filters.area || h.area === filters.area) && h.price_min_bdt <= filters.maxPriceBdt)
      .map((h) => ({ ...h, match_score: computeLocalScore(h, filters) }))
      .sort((a, b) => {
        if (filters.sort === "price_asc") return a.price_min_bdt - b.price_min_bdt;
        if (filters.sort === "price_desc") return b.price_min_bdt - a.price_min_bdt;
        if (filters.sort === "rating") return b.rating - a.rating;
        return (b.match_score ?? 0) - (a.match_score ?? 0);
      });
  }, [hotels, isTier0Fallback, filters]);

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            {t("কক্সবাজার হোটেল এক্সপ্লোরার ও রেকমেন্ডার", "Cox's Bazar Hotel Explorer & Recommender")}
          </h1>
          <p className="text-sm text-muted-foreground">
            {t(
              "এলাকা, বাজেট ও সুবিধার ভিত্তিতে সেরা ম্যাচ স্কোরসহ হোটেল খুঁজুন",
              "Find verified and sample hotels ranked by area, budget, and amenity match score",
            )}
          </p>
        </div>

        {isTier0Fallback && (
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-900">
            {messages.badges.tier0Fallback}
          </span>
        )}
      </div>

      <HotelFilters
        filters={filters}
        onChange={setFilters}
        onReset={() => setFilters(DEFAULT_FILTERS)}
      />

      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>
          {t("মোট ফলাফল:", "Showing results:")}{" "}
          <strong>{formatLocaleNumber(displayedHotels.length, locale)}</strong>
        </span>
      </div>

      {displayedHotels.length === 0 ? (
        <div className="rounded-xl border border-dashed p-10 text-center space-y-2">
          <p className="font-medium">
            {t("এই বাজেট বা ফিল্টারে কোনো হোটেল পাওয়া যায়নি।", "No hotels match the selected filters.")}
          </p>
          <Button type="button" variant="outline" size="sm" onClick={() => setFilters(DEFAULT_FILTERS)}>
            {t("সব হোটেল দেখুন", "Show All Hotels")}
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {displayedHotels.map((hotel) => (
            <HotelCard key={hotel.hotel_id} hotel={hotel} onSelect={setSelectedHotel} />
          ))}
        </div>
      )}

      {selectedHotel && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
        >
          <div className="w-full max-w-lg rounded-2xl border bg-background p-6 space-y-4 shadow-xl">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-xl font-bold">{pickLocalized(selectedHotel.name, locale)}</h2>
                <p className="text-xs text-muted-foreground">
                  {pickLocalized(selectedHotel.address, locale)}
                </p>
              </div>
              <Button type="button" variant="ghost" size="sm" onClick={() => setSelectedHotel(null)}>
                ✕
              </Button>
            </div>

            <p className="text-sm">{pickLocalized(selectedHotel.description, locale)}</p>

            <div className="rounded-lg bg-muted/50 p-3 text-sm space-y-1">
              <p>
                <strong>{t("ভাড়ার সীমা:", "Tariff Range:")}</strong>{" "}
                {formatBdt(selectedHotel.price_min_bdt, locale)} –{" "}
                {formatBdt(selectedHotel.price_max_bdt, locale)}
              </p>
              <p>
                <strong>{t("ফোন:", "Phone:")}</strong> {selectedHotel.phone}
              </p>
              <p className="text-xs text-muted-foreground">
                {t("তথ্যসূত্র:", "Source:")} {selectedHotel.data_source} •{" "}
                {t("সর্বশেষ আপডেট:", "Last Updated:")} {selectedHotel.last_updated}
              </p>
            </div>

            <div className="space-y-2 border-t pt-3">
              <p className="text-xs font-semibold flex items-center gap-1.5">
                <MessageSquarePlus className="h-3.5 w-3.5" />
                <span>{t("রিভিউ ও সেন্টিমেন্ট যোগ করুন (P1)", "Write a Review with Sentiment Analysis (P1)")}</span>
              </p>
              <div className="flex gap-2">
                <select
                  aria-label="Rating"
                  value={reviewRating}
                  onChange={(e) => setReviewRating(Number(e.target.value))}
                  className="rounded-md border bg-background px-2 py-1.5 text-xs"
                >
                  {[5, 4, 3, 2, 1].map((r) => (
                    <option key={r} value={r}>
                      {r} ★
                    </option>
                  ))}
                </select>
                <input
                  type="text"
                  value={reviewComment}
                  onChange={(e) => setReviewComment(e.target.value)}
                  placeholder={t("যেমন: ঘর পরিষ্কার এবং সুন্দর...", "e.g. Room was clean and great...")}
                  className="flex-1 rounded-md border bg-background px-3 py-1.5 text-xs"
                />
                <Button type="button" size="sm" onClick={() => handleSubmitReview(selectedHotel)}>
                  {t("জমা দিন", "Post")}
                </Button>
              </div>
            </div>

            {feedbackNotice && (
              <p className="rounded-md bg-emerald-50 p-2 text-xs font-medium text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200">
                {feedbackNotice}
              </p>
            )}

            <div className="flex items-center justify-between pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => handleReportWrongInfo(selectedHotel)}
                className="gap-1.5 text-xs"
              >
                <Flag className="h-3.5 w-3.5 text-amber-600" />
                <span>{t("ভুল তথ্য রিপোর্ট করুন", "Report Wrong Info")}</span>
              </Button>
              <Button
                type="button"
                onClick={() => {
                  setSelectedHotel(null);
                  setFeedbackNotice(null);
                }}
              >
                {t("বন্ধ করুন", "Close")}
              </Button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
