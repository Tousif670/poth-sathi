"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Compass, Hotel, MapPin, MessageSquare, ShieldAlert, TrainFront } from "lucide-react";
import { useLocale } from "@/context/LocaleProvider";

export function BottomTabs() {
  const pathname = usePathname();
  const { messages } = useLocale();

  const tabs = [
    { href: "/", label: messages.nav.home, icon: Compass },
    { href: "/hotels", label: messages.nav.hotels, icon: Hotel },
    { href: "/nearby", label: messages.nav.nearby, icon: MapPin },
    { href: "/fares", label: messages.nav.fares, icon: TrainFront },
    { href: "/safety", label: messages.nav.safety, icon: ShieldAlert },
    { href: "/chat", label: messages.nav.chat, icon: MessageSquare },
  ];

  return (
    <nav
      aria-label="Mobile bottom navigation"
      className="fixed bottom-0 left-0 right-0 z-40 flex h-16 items-center justify-around border-t bg-background/95 px-2 backdrop-blur md:hidden"
    >
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = pathname === tab.href;
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`flex flex-col items-center justify-center gap-0.5 px-2 py-1 text-xs font-medium transition-colors ${
              isActive ? "text-primary font-semibold" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Icon className="h-5 w-5" />
            <span className="truncate max-w-[64px]">{tab.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
