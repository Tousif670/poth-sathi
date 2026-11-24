"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ApiError, apiFetch } from "@/lib/api";

interface HealthResponse {
  status: string;
  app_env: string;
  firestore: string;
}

type HealthState =
  | { status: "loading" }
  | { status: "ok"; data: HealthResponse }
  | { status: "error"; messageEn: string; messageBn: string };

export default function HomePage() {
  const [health, setHealth] = useState<HealthState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    apiFetch<HealthResponse>("/health", { signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted) {
          setHealth({ status: "ok", data });
        }
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) {
          return;
        }
        if (err instanceof ApiError) {
          setHealth({
            status: "error",
            messageEn: err.messageEn,
            messageBn: err.messageBn,
          });
        } else {
          setHealth({
            status: "error",
            messageEn: "Could not connect to the backend right now.",
            messageBn: "এই মুহূর্তে ব্যাকএন্ডের সাথে সংযোগ করা সম্ভব হয়নি।",
          });
        }
      });

    return () => controller.abort();
  }, [attempt]);

  const handleRecheck = () => {
    setHealth({ status: "loading" });
    setAttempt((n) => n + 1);
  };

  return (
    <main className="flex flex-1 flex-col items-center justify-center px-4 py-10">
      <div className="w-full max-w-md space-y-6">
        <header className="space-y-1 text-center">
          <h1 className="text-3xl font-bold tracking-tight">PothSathi</h1>
          <p className="text-sm text-muted-foreground">
            পথসাথী — Cox&apos;s Bazar AI Travel Companion
          </p>
        </header>

        <Card>
          <CardHeader>
            <CardTitle>System Status</CardTitle>
            <CardDescription>
              Checking connection to the FastAPI backend
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {health.status === "loading" && (
              <p className="text-sm text-muted-foreground">
                Checking backend status...
              </p>
            )}

            {health.status === "ok" && (
              <div className="space-y-2 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-950 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-100">
                <p className="font-semibold">Backend: {health.data.status}</p>
                <p>
                  Environment:{" "}
                  <span className="font-mono">{health.data.app_env}</span>
                </p>
                <p>
                  Firestore:{" "}
                  <span className="font-mono">{health.data.firestore}</span>
                </p>
              </div>
            )}

            {health.status === "error" && (
              <div
                role="alert"
                className="space-y-2 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive"
              >
                <p className="font-semibold">Backend unavailable</p>
                <p>{health.messageEn}</p>
                <p>{health.messageBn}</p>
              </div>
            )}

            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={handleRecheck}
              disabled={health.status === "loading"}
            >
              Recheck Status
            </Button>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
