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
    <main className="mx-auto max-w-4xl space-y-6 px-4 py-8">
      <div className="rounded-2xl border-2 border-red-600 bg-red-50/90 p-6 space-y-4 dark:bg-red-950/30">
        <div className="flex items-start gap-3">
          <ShieldAlert className="h-8 w-8 shrink-0 text-red-600" />
          <div className="space-y-1">
            <h1 className="text-2xl font-bold text-red-950 dark:text-red-100">
              {t("জরুরি সাহায্য ও এসওএস (Emergency SOS)", "Emergency Assistance & SOS")}
            </h1>
            <p className="text-sm text-red-900/80 dark:text-red-200/80">
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
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-red-600 px-6 py-3.5 text-base font-bold text-white shadow-md hover:bg-red-700"
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
            className="border-red-400 font-semibold text-red-900 hover:bg-red-100 dark:text-red-100"
          >
            <AlertCircle className="mr-2 h-5 w-5" />
            <span>{t("SOS অ্যালার্ট লগ ও অবস্থান পাঠান", "Log SOS Alert & Share Location")}</span>
          </Button>

          <a
            href="https://wa.me/?text=Emergency%20help%20needed%20in%20Cox%27s%20Bazar"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-emerald-600 bg-emerald-600 px-4 py-3 text-sm font-semibold text-white hover:bg-emerald-700"
          >
            <MessageCircle className="h-4 w-4" />
            <span>{t("হোয়াটসঅ্যাপ মেসেজ", "WhatsApp Emergency Link")}</span>
          </a>
        </div>

        {coords && (
          <p className="inline-flex items-center gap-1.5 rounded-lg bg-background/80 px-3 py-1.5 text-xs font-mono">
            <MapPin className="h-3.5 w-3.5 text-red-600" />
            <span>
              {t("আপনার বর্তমান জিপিএস স্থানাঙ্ক:", "Your GPS coordinates:")} {coords.lat}, {coords.lng}
            </span>
          </p>
        )}

        {sosResult && (
          <div
            role="status"
            className="rounded-xl border border-red-300 bg-background p-4 space-y-2 text-sm"
          >
            <p className="font-bold text-red-700">
              {t("SOS রেকর্ড সম্পন্ন:", "SOS Alert Logged:")} {sosResult.sos_id}
            </p>
            <p>{sosResult.guidance}</p>
          </div>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {contacts.map((contact) => {
          const dial = contact.number.replace(/\D/g, "") || "999";
          const displayNum =
            locale === "bn" && /^\d+$/.test(contact.number)
              ? toBengaliDigits(contact.number)
              : contact.number;
          return (
            <Card key={contact.id}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">
                    {pickLocalized(contact.service, locale)}
                  </CardTitle>
                  <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-900">
                    {contact.status}
                  </span>
                </div>
                <CardDescription className="text-xs">
                  {messages.badges.sample}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex items-center justify-between pt-2">
                <span className="text-xl font-bold text-primary">{displayNum}</span>
                <a
                  href={`tel:${dial}`}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-xs font-semibold text-primary-foreground hover:opacity-90"
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
