"use client";

import { useState } from "react";
import { Flag, RefreshCw, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/context/AuthProvider";
import { useLocale } from "@/context/LocaleProvider";
import { apiFetch } from "@/lib/api";

export default function AdminPage() {
  const { t } = useLocale();
  const { session, user } = useAuth();
  const [zoneId, setZoneId] = useState<"kolatoli" | "sugandha" | "laboni">("kolatoli");
  const [flag, setFlag] = useState<"green" | "yellow" | "red">("yellow");
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const handleUpdateFlag = async () => {
    try {
      const res = await apiFetch<{ zone_id: string; flag: string; last_updated: string }>(
        `/admin/beach-status/${zoneId}`,
        {
          method: "PUT",
          token: session?.idToken,
          body: { flag },
        },
      );
      setStatusMsg(
        t(
          `সফলভাবে ${res.zone_id} সৈকতের পতাকা '${res.flag.toUpperCase()}' এ আপডেট হয়েছে।`,
          `Updated ${res.zone_id} beach flag to ${res.flag.toUpperCase()} (${res.last_updated}).`,
        ),
      );
    } catch {
      setStatusMsg(
        t(
          "অ্যাডমিন অনুমতি প্রয়োজন (scripts/make_admin.py দিয়ে অ্যাডমিন রোল দিন)।",
          "Admin role required (promote user via scripts/make_admin.py).",
        ),
      );
    }
  };

  const handleRefreshCache = async () => {
    try {
      const res = await apiFetch<{ status: string; timestamp: string }>("/admin/cache/refresh", {
        method: "POST",
        token: session?.idToken,
        body: { scope: "all" },
      });
      setStatusMsg(
        t(
          `ক্যাশ ও নলেজ বেস রিফ্রেশ হয়েছে (${res.timestamp})।`,
          `In-memory cache and RAG index reloaded (${res.timestamp}).`,
        ),
      );
    } catch {
      setStatusMsg(
        t(
          "অ্যাডমিন অনুমতি প্রয়োজন।",
          "Admin role required to refresh server cache.",
        ),
      );
    }
  };

  return (
    <main className="mx-auto max-w-4xl space-y-6 px-4 py-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            {t("অ্যাডমিন কন্ট্রোল প্যানেল (P1)", "Admin Control Panel (P1)")}
          </h1>
          <p className="text-sm text-muted-foreground">
            {t(
              "সৈকত নিরাপত্তা পতাকা পরিবর্তন ও ইন-মেমরি ক্যাশ রিফ্রেশ",
              "Update beach safety flags across 3 zones and refresh backend cache",
            )}
          </p>
        </div>

        <span className="inline-flex items-center gap-1.5 rounded-full bg-secondary px-3 py-1 text-xs font-semibold">
          <ShieldCheck className="h-4 w-4 text-primary" />
          <span>{user?.role === "admin" ? "Admin Active" : "Tourist View"}</span>
        </span>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Flag className="h-5 w-5 text-primary" />
              <span>{t("সৈকতের পতাকা আপডেট (D23)", "Update Beach Hazard Flag (D23)")}</span>
            </CardTitle>
            <CardDescription>
              {t(
                "কলাতলী, সুগন্ধা বা লাবণী পয়েন্টের পতাকা তাৎক্ষণিক পরিবর্তন করুন",
                "Set Green, Yellow, or Red flag for Kolatoli, Sugandha, or Laboni",
              )}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="admin-zone" className="text-xs font-semibold">
                {t("সৈকত জোন", "Beach Zone")}
              </label>
              <select
                id="admin-zone"
                value={zoneId}
                onChange={(e) => setZoneId(e.target.value as typeof zoneId)}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              >
                <option value="kolatoli">{t("কলাতলী সৈকত", "Kolatoli Beach")}</option>
                <option value="sugandha">{t("সুগন্ধা সৈকত", "Sugandha Beach")}</option>
                <option value="laboni">{t("লাবণী সৈকত", "Laboni Beach")}</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="admin-flag" className="text-xs font-semibold">
                {t("পতাকার রঙ", "Flag Colour")}
              </label>
              <select
                id="admin-flag"
                value={flag}
                onChange={(e) => setFlag(e.target.value as typeof flag)}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              >
                <option value="green">{t("সবুজ (নিরাপদ)", "Green (Low Hazard)")}</option>
                <option value="yellow">{t("হলুদ (সতর্কতা)", "Yellow (Medium Hazard)")}</option>
                <option value="red">{t("লাল (সমুদ্রে নামা নিষেধ)", "Red (High Hazard)")}</option>
              </select>
            </div>

            <Button type="button" onClick={handleUpdateFlag} className="w-full">
              {t("পতাকা আপডেট করুন", "Save Beach Flag")}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <RefreshCw className="h-5 w-5 text-primary" />
              <span>{t("ক্যাশ ও নলেজ বেস রিফ্রেশ", "Cache & RAG Index Refresh")}</span>
            </CardTitle>
            <CardDescription>
              {t(
                "ফায়ারস্টোর ডেটা পরিবর্তনের পর ব্যাকএন্ডের ইন-মেমরি ক্যাশ রিলোড করুন",
                "Invalidate backend TTL cache and rebuild in-memory RAG index",
              )}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              type="button"
              variant="outline"
              onClick={handleRefreshCache}
              className="w-full gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              <span>{t("সব ক্যাশ রিফ্রেশ করুন", "Refresh All Caches")}</span>
            </Button>

            {statusMsg && (
              <div className="rounded-lg border bg-muted/50 p-3 text-xs font-medium">
                {statusMsg}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
