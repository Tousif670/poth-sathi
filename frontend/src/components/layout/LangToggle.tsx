"use client";

import { Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useLocale } from "@/context/LocaleProvider";

export function LangToggle() {
  const { locale, toggleLocale } = useLocale();

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      onClick={toggleLocale}
      aria-label={locale === "bn" ? "Switch to English" : "বাংলায় পরিবর্তন করুন"}
      data-testid="lang-toggle"
      className="gap-1.5 font-medium"
    >
      <Globe className="h-4 w-4" />
      <span>{locale === "bn" ? "English" : "বাংলা"}</span>
    </Button>
  );
}
