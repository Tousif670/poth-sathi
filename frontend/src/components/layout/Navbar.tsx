"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  Compass,
  Hotel,
  MapPin,
  MessageSquare,
  Moon,
  PhoneCall,
  ShieldAlert,
  Sun,
  TrainFront,
  UserCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { LangToggle } from "./LangToggle";
import { useLocale } from "@/context/LocaleProvider";
import { useAuth } from "@/context/AuthProvider";

function isRouteActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Navbar() {
  const pathname = usePathname();
  const { messages, locale, t } = useLocale();
  const { user, loading, signInAsGuest, signOut } = useAuth();
  const [darkMode, setDarkMode] = useState(false);

  const toggleDarkMode = () => {
    if (typeof document === "undefined") return;
    const next = !document.documentElement.classList.contains("dark");
    document.documentElement.classList.toggle("dark", next);
    setDarkMode(next);
  };

  const navItems = [
    {
      href: "/",
      label: messages.nav.home,
      icon: Compass,
      activeClass:
        "bg-feature-home-tint text-feature-home border-feature-home-border font-semibold shadow-2xs dark:text-teal-300",
    },
    {
      href: "/hotels",
      label: messages.nav.hotels,
      icon: Hotel,
      activeClass:
        "bg-feature-hotels-tint text-feature-hotels border-feature-hotels-border font-semibold shadow-2xs dark:text-indigo-300",
    },
    {
      href: "/nearby",
      label: messages.nav.nearby,
      icon: MapPin,
      activeClass:
        "bg-feature-nearby-tint text-feature-nearby border-feature-nearby-border font-semibold shadow-2xs dark:text-emerald-300",
    },
    {
      href: "/fares",
      label: messages.nav.fares,
      icon: TrainFront,
      activeClass:
        "bg-feature-fares-tint text-feature-fares border-feature-fares-border font-semibold shadow-2xs dark:text-amber-300",
    },
    {
      href: "/safety",
      label: messages.nav.safety,
      icon: ShieldAlert,
      activeClass:
        "bg-feature-safety-tint text-feature-safety border-feature-safety-border font-semibold shadow-2xs dark:text-sky-300",
    },
    {
      href: "/emergency",
      label: messages.nav.emergency,
      icon: PhoneCall,
      urgent: true,
      activeClass:
        "bg-feature-emergency text-white ring-2 ring-feature-emergency/30 font-semibold shadow-xs",
    },
    {
      href: "/chat",
      label: messages.nav.chat,
      icon: MessageSquare,
      activeClass:
        "bg-feature-chat-tint text-feature-chat border-feature-chat-border font-semibold shadow-2xs dark:text-violet-300",
    },
  ];

  if (user?.role === "admin") {
    navItems.push({
      href: "/admin",
      label: messages.nav.admin,
      icon: UserCheck,
      activeClass:
        "bg-feature-home-tint text-feature-home border-feature-home-border font-semibold shadow-2xs dark:text-teal-300",
    });
  }

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/85 shadow-2xs">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
        <div className="flex items-center gap-5">
          <Link
            href="/"
            className="group flex items-center gap-2.5 text-base font-bold tracking-tight text-foreground sm:text-lg"
            aria-label="পথসাথী | PothSathi Home"
          >
            <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-xs transition-colors group-hover:bg-primary-hover">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-5 w-5"
                aria-hidden="true"
              >
                <path d="M12 2a5 5 0 0 0-5 5c0 3.5 5 9 5 9s5-5.5 5-9a5 5 0 0 0-5-5Z" />
                <circle cx="12" cy="7" r="1.75" />
                <path d="M2 19.5c1.5-1 3.5-1 5 0s3.5 1 5 0 3.5-1 5 0 3.5 1 5 0" />
              </svg>
            </span>
            <span className="flex items-center gap-1.5 whitespace-nowrap">
              <span className="text-primary dark:text-teal-400">পথসাথী</span>
              <span className="text-muted-foreground/50 font-normal">|</span>
              <span>PothSathi</span>
            </span>
          </Link>

          <nav className="hidden lg:flex items-center gap-1" aria-label="Main navigation">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = isRouteActive(pathname, item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={isActive ? "page" : undefined}
                  className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium transition-all ${
                    item.urgent
                      ? isActive
                        ? item.activeClass
                        : "border-transparent bg-feature-emergency text-white shadow-xs hover:bg-feature-emergency-hover"
                      : isActive
                        ? item.activeClass
                        : "border-transparent text-muted-foreground hover:bg-muted hover:text-foreground"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="icon-sm"
            onClick={toggleDarkMode}
            aria-label={t("থিম পরিবর্তন করুন", "Toggle color theme")}
            title={t("থিম পরিবর্তন করুন", "Toggle color theme")}
          >
            {darkMode ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-muted-foreground" />}
          </Button>

          <LangToggle />

          {user ? (
            <div className="flex items-center gap-2">
              <span className="hidden sm:inline-flex items-center gap-1.5 rounded-full border border-feature-home-border bg-feature-home-tint px-3 py-1 text-xs font-semibold text-feature-home dark:text-teal-300">
                <UserCheck className="h-3.5 w-3.5" />
                <span>{user.display_name || messages.auth.guest}</span>
                {user.role === "admin" && (
                  <span className="ml-1 rounded bg-feature-fares-tint px-1.5 py-0.5 text-[10px] font-bold text-feature-fares">
                    {messages.auth.adminBadge}
                  </span>
                )}
              </span>
              <Button type="button" variant="ghost" size="sm" onClick={signOut}>
                {messages.auth.signOut}
              </Button>
            </div>
          ) : (
            <Button
              type="button"
              size="sm"
              disabled={loading}
              onClick={() => signInAsGuest(locale)}
              data-testid="guest-login-btn"
              className="bg-primary text-primary-foreground hover:bg-primary-hover"
            >
              {messages.auth.signInGuest}
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
