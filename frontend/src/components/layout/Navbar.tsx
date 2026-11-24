"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Compass, Hotel, MapPin, MessageSquare, PhoneCall, ShieldAlert, TrainFront, UserCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LangToggle } from "./LangToggle";
import { useLocale } from "@/context/LocaleProvider";
import { useAuth } from "@/context/AuthProvider";

export function Navbar() {
  const pathname = usePathname();
  const { messages, locale } = useLocale();
  const { user, loading, signInAsGuest, signOut } = useAuth();

  const navItems = [
    { href: "/", label: messages.nav.home, icon: Compass },
    { href: "/hotels", label: messages.nav.hotels, icon: Hotel },
    { href: "/nearby", label: messages.nav.nearby, icon: MapPin },
    { href: "/fares", label: messages.nav.fares, icon: TrainFront },
    { href: "/safety", label: messages.nav.safety, icon: ShieldAlert },
    { href: "/emergency", label: messages.nav.emergency, icon: PhoneCall, urgent: true },
    { href: "/chat", label: messages.nav.chat, icon: MessageSquare },
  ];

  if (user?.role === "admin") {
    navItems.push({ href: "/admin", label: messages.nav.admin, icon: UserCheck });
  }

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2 font-bold text-lg tracking-tight">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold">
              প
            </span>
            <span>{messages.app.name}</span>
          </Link>

          <nav className="hidden md:flex items-center gap-1" aria-label="Main navigation">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                    item.urgent
                      ? "bg-red-600 text-white hover:bg-red-700"
                      : isActive
                        ? "bg-secondary text-secondary-foreground font-semibold"
                        : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
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
          <LangToggle />

          {user ? (
            <div className="flex items-center gap-2">
              <span className="hidden sm:inline-flex items-center gap-1 rounded-full bg-secondary px-2.5 py-1 text-xs font-medium">
                <UserCheck className="h-3.5 w-3.5 text-emerald-600" />
                <span>{user.display_name || messages.auth.guest}</span>
                {user.role === "admin" && (
                  <span className="ml-1 rounded bg-amber-500/20 px-1.5 py-0.5 text-[10px] font-bold text-amber-800 dark:text-amber-200">
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
            >
              {messages.auth.signInGuest}
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
