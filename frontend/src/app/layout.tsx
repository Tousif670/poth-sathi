import type { Metadata } from "next";
import { Hind_Siliguri, Noto_Sans_Bengali } from "next/font/google";
import "./globals.css";
import { LocaleProvider } from "@/context/LocaleProvider";
import { AuthProvider } from "@/context/AuthProvider";
import { Navbar } from "@/components/layout/Navbar";
import { BottomTabs } from "@/components/layout/BottomTabs";
import { Footer } from "@/components/layout/Footer";

const hindSiliguri = Hind_Siliguri({
  variable: "--font-hind-siliguri",
  subsets: ["bengali", "latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const notoSansBengali = Noto_Sans_Bengali({
  variable: "--font-noto-sans-bengali",
  subsets: ["bengali", "latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "PothSathi — পথসাথী | Cox's Bazar Bilingual AI Travel Companion",
  description: "Bilingual (Bengali & English) AI travel companion for Cox's Bazar, Bangladesh",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="bn"
      className={`${hindSiliguri.variable} ${notoSansBengali.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col font-sans">
        <LocaleProvider>
          <AuthProvider>
            <Navbar />
            <div className="flex-1">{children}</div>
            <Footer />
            <BottomTabs />
          </AuthProvider>
        </LocaleProvider>
      </body>
    </html>
  );
}
