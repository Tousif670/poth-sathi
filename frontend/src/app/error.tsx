"use client";

import Link from "next/link";
import { AlertTriangle, PhoneCall, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="mx-auto flex min-h-[60vh] max-w-xl flex-col items-center justify-center space-y-4 px-4 text-center">
      <AlertTriangle className="h-12 w-12 text-amber-600" />
      <h1 className="text-2xl font-bold">
        একটি অপ্রত্যাশিত সমস্যা হয়েছে / Something went wrong
      </h1>
      <p className="text-sm text-muted-foreground">
        পৃষ্ঠাটি লোড করতে সমস্যা হয়েছে। জরুরি সেবার জন্য নিচের বাটন ব্যবহার করুন।
      </p>
      <div className="flex flex-wrap justify-center gap-3">
        <Button type="button" onClick={reset} className="gap-1.5">
          <RefreshCw className="h-4 w-4" />
          <span>আবার চেষ্টা করুন / Try Again</span>
        </Button>
        <Link href="/emergency">
          <Button type="button" variant="destructive" className="gap-1.5">
            <PhoneCall className="h-4 w-4" />
            <span>জরুরি ৯৯৯ / Emergency 999</span>
          </Button>
        </Link>
      </div>
    </main>
  );
}
