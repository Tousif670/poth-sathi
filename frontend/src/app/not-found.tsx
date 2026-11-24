import Link from "next/link";
import { Compass, PhoneCall } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFoundPage() {
  return (
    <main className="mx-auto flex min-h-[60vh] max-w-xl flex-col items-center justify-center space-y-4 px-4 text-center">
      <h1 className="text-3xl font-bold">৪০৪ — পৃষ্ঠাটি পাওয়া যায়নি / Page Not Found</h1>
      <p className="text-sm text-muted-foreground">
        আপনি যে পৃষ্ঠাটি খুঁজছেন তা পাওয়া যায়নি। হোম পেইজে ফিরে যান বা জরুরি নম্বর দেখুন।
      </p>
      <div className="flex flex-wrap justify-center gap-3">
        <Link href="/">
          <Button className="gap-1.5">
            <Compass className="h-4 w-4" />
            <span>হোম পেইজ / Home</span>
          </Button>
        </Link>
        <Link href="/emergency">
          <Button variant="destructive" className="gap-1.5">
            <PhoneCall className="h-4 w-4" />
            <span>জরুরি ৯৯৯ / Emergency 999</span>
          </Button>
        </Link>
      </div>
    </main>
  );
}
