"use client";

import { useEffect, useState } from "react";
import { AlertCircle, MapPin, MessageCircle, PhoneCall, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/context/AuthProvider";
import { useLocale } from "@/context/LocaleProvider";
import { apiFetch } from "@/lib/api";
import { type StaticEmergencyContact, loadTier0Json } from "@/lib/staticData";
import { pickLocalized, toBengaliDigits } from "@/lib/utils";

interface SOSResponse {
  sos_id: string;
  status: string;
  national_emergency: string;
  tourist_police: string;
  ambulance: string;
  guidance: string;
  quick_links: {
    tel: string;
    whatsapp: string;
  };
}

export default function EmergencyPage() {
  const { locale, messages, t } = useLocale();
  const { session } = useAuth();
  const [contacts, setContacts] = useState<StaticEmergencyContact[]>([]);
  const [sosResult, setSosResult] = useState<SOSResponse | null>(null);
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadTier0Json<StaticEmergencyContact>("emergency.json").then(setContacts);
  }, []);

  const handleTriggerSOS = async () => {
    setSubmitting(true);
    let currentCoords = coords;

    if (!currentCoords && typeof navigator !== "undefined" && "geolocation" in navigator) {
      try {
        const pos = await new Promise<GeolocationPosition>((resolve, reject) =>
          navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 2500 }),
        );
        currentCoords = {
          lat: Number(pos.coords.latitude.toFixed(4)),
          lng: Number(pos.coords.longitude.toFixed(4)),
        };
        setCoords(currentCoords);
      } catch {
        // Proceed without coordinates if geolocation permission denied
      }
    }

    try {
      const res = await apiFetch<SOSResponse>("/emergency/sos", {
        method: "POST",
        token: session?.idToken,
        body: {
          trigger_type: "button",
          lat: currentCoords?.lat,
          lng: currentCoords?.lng,
          lang: locale,
        },
      });
      setSosResult(res);
    } catch {
      setSosResult({
        sos_id: "OFFLINE_TIER0_SOS",
        status: "offline_fallback",
        national_emergency: "999",
        tourist_police: "TO_VERIFY",
        ambulance: "199",
        guidance: t(
          "শান্ত থাকুন। সরাসরি ৯৯৯ নম্বরে কল করুন এবং আপনার অবস্থান জানান।",
          "Stay calm. Dial 999 immediately and relay your location verbally.",
        ),
        quick_links: {
          tel: "tel:999",
          whatsapp: "https://wa.me/?text=Emergency%20SOS%20at%20Cox%27s%20Bazar",
        },
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="mx-auto max-w-4xl space-y-6 px-4 py-8" data-feature="emergency">
      {/* Feature Header & SOS Action Banner — Crimson Red (#DC2626) & Soft Tint (#FEF2F2) */}
      <section className="rounded-2xl border-2 border-feature-emergency bg-feature-emergency-tint p-6 space-y-4 shadow-sm">
        <div className="flex items-start gap-3.5">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-feature-emergency text-white shadow-xs">
            <ShieldAlert className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <span className="inline-flex items-center rounded-full border border-feature-emergency-border bg-card px-2.5 py-0.5 text-[11px] font-bold text-feature-emergency dark:text-red-300">
              {t("২৪/৭ জরুরি সহায়তা", "24/7 Emergency SOS")}
            </span>
            <h1 className="text-2xl font-bold text-foreground sm:text-3xl">
              {t("জরুরি সাহায্য ও এসওএস (Emergency SOS)", "Emergency Assistance & SOS")}
            </h1>
            <p className="text-sm text-muted-foreground">
              {t(
                "জীবন বিপন্ন হলে বা জরুরি বিপদে পড়লে নিচের বাটনে চাপ দিন অথবা সরাসরি ৯৯৯-এ কল করুন।",
                "In any life-threatening situation or emergency, tap SOS below or call 999 immediately.",
              )}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-3 pt-2">
          <a
            href="tel:999"
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-feature-emergency px-6 py-3.5 text-base font-bold text-white shadow-md transition-colors hover:bg-feature-emergency-hover"
          >
            <PhoneCall className="h-5 w-5" />
            <span>
              {t(`এখনই ৯৯৯-এ কল করুন (${toBengaliDigits("999")})`, "Call 999 Immediately")}
            </span>
          </a>

          <Button
            type="button"
            variant="outline"
            size="lg"
            disabled={submitting}
            onClick={handleTriggerSOS}
            data-testid="sos-trigger-btn"
            className="h-auto border-feature-emergency bg-card px-4 py-3 font-semibold text-feature-emergency hover:bg-feature-emergency hover:text-white dark:text-red-300"
          >
            <AlertCircle className="mr-2 h-5 w-5" />
            <span>{t("SOS অ্যালার্ট লগ ও অবস্থান পাঠান", "Log SOS Alert & Share Location")}</span>
          </Button>

          <a
            href="https://wa.me/?text=Emergency%20help%20needed%20in%20Cox%27s%20Bazar"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-feature-nearby px-4 py-3 text-sm font-semibold text-white shadow-xs transition-colors hover:bg-feature-nearby-hover"
          >
            <MessageCircle className="h-4 w-4" />
            <span>{t("হোয়াটসঅ্যাপ মেসেজ", "WhatsApp Emergency Link")}</span>
          </a>
        </div>

        {coords && (
          <p className="inline-flex items-center gap-1.5 rounded-lg border border-feature-emergency-border bg-card px-3 py-1.5 text-xs font-mono text-foreground">
            <MapPin className="h-3.5 w-3.5 text-feature-emergency" />
            <span>
              {t("আপনার বর্তমান জিপিএস স্থানাঙ্ক:", "Your GPS coordinates:")} {coords.lat}, {coords.lng}
            </span>
          </p>
        )}

        {sosResult && (
          <div
            role="status"
            className="rounded-xl border border-feature-emergency bg-card p-4 space-y-2 text-sm shadow-xs"
          >
            <p className="font-bold text-feature-emergency dark:text-red-300">
              {t("SOS রেকর্ড সম্পন্ন:", "SOS Alert Logged:")} {sosResult.sos_id}
            </p>
            <p className="text-foreground">{sosResult.guidance}</p>
          </div>
        )}
      </section>

      <div className="grid gap-4 sm:grid-cols-2">
        {contacts.map((contact) => {
          const dial = contact.number.replace(/\D/g, "") || "999";
          const displayNum =
            locale === "bn" && /^\d+$/.test(contact.number)
              ? toBengaliDigits(contact.number)
              : contact.number;
          return (
            <Card
              key={contact.id}
              className="border-feature-emergency-border transition-shadow hover:shadow-md"
            >
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-bold text-foreground">
                    {pickLocalized(contact.service, locale)}
                  </CardTitle>
                  <span className="rounded-full border border-feature-fares-border bg-feature-fares-tint px-2.5 py-0.5 text-[10px] font-semibold text-feature-fares dark:text-amber-200">
                    {contact.status}
                  </span>
                </div>
                <CardDescription className="text-xs">
                  {messages.badges.sample}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex items-center justify-between border-t border-feature-emergency-border/50 bg-feature-emergency-tint/40 pt-3">
                <span className="text-xl font-bold text-feature-emergency dark:text-red-300">
                  {displayNum}
                </span>
                <a
                  href={`tel:${dial}`}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-feature-emergency px-3.5 py-2 text-xs font-semibold text-white shadow-2xs transition-colors hover:bg-feature-emergency-hover"
                >
                  <PhoneCall className="h-3.5 w-3.5" />
                  <span>{t("কল করুন", "Dial Now")}</span>
                </a>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </main>
  );
}
