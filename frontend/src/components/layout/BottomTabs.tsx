"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Compass, Hotel, MapPin, MessageSquare, PhoneCall, ShieldAlert, TrainFront } from "lucide-react";
import { useLocale } from "@/context/LocaleProvider";

function isRouteActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function BottomTabs() {
  const pathname = usePathname();
  const { messages } = useLocale();

  const tabs = [
    {
      href: "/",
      label: messages.nav.home,
      icon: Compass,
      activeClass: "bg-feature-home-tint text-feature-home font-semibold dark:text-teal-300",
    },
    {
      href: "/hotels",
      label: messages.nav.hotels,
      icon: Hotel,
      activeClass: "bg-feature-hotels-tint text-feature-hotels font-semibold dark:text-indigo-300",
    },
    {
      href: "/nearby",
      label: messages.nav.nearby,
      icon: MapPin,
      activeClass: "bg-feature-nearby-tint text-feature-nearby font-semibold dark:text-emerald-300",
    },
    {
      href: "/fares",
      label: messages.nav.fares,
      icon: TrainFront,
      activeClass: "bg-feature-fares-tint text-feature-fares font-semibold dark:text-amber-300",
    },
    {
      href: "/safety",
      label: messages.nav.safety,
      icon: ShieldAlert,
      activeClass: "bg-feature-safety-tint text-feature-safety font-semibold dark:text-sky-300",
    },
    {
      href: "/emergency",
      label: "SOS",
      icon: PhoneCall,
      urgent: true,
      activeClass: "bg-feature-emergency text-white font-bold",
    },
    {
      href: "/chat",
      label: messages.nav.chat,
      icon: MessageSquare,
      activeClass: "bg-feature-chat-tint text-feature-chat font-semibold dark:text-violet-300",
    },
  ];

  return (
    <nav
      aria-label="Mobile bottom navigation"
      className="fixed bottom-0 left-0 right-0 z-40 flex h-16 items-center justify-around border-t border-border bg-card/95 px-1.5 backdrop-blur lg:hidden"
    >
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = isRouteActive(pathname, tab.href);
        return (
          <Link
            key={tab.href}
            href={tab.href}
            aria-current={isActive ? "page" : undefined}
            className={`flex flex-col items-center justify-center gap-0.5 rounded-lg px-2 py-1 text-[11px] font-medium transition-colors ${
              isActive
                ? tab.activeClass
                : tab.urgent
                  ? "text-feature-emergency font-semibold hover:bg-feature-emergency-tint"
                  : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Icon className="h-4 w-4" />
            <span className="truncate max-w-[56px]">{tab.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
