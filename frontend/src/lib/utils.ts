import { cn } from "cn";

export { cn };

const EN_TO_BN_DIGITS: Record<string, string> = {
  "0": "০",
  "1": "১",
  "2": "২",
  "3": "৩",
  "4": "৪",
  "5": "৫",
  "6": "৬",
  "7": "৭",
  "8": "৮",
  "9": "৯",
};

const BN_TO_EN_DIGITS: Record<string, string> = {
  "০": "0",
  "১": "1",
  "২": "2",
  "৩": "3",
  "৪": "4",
  "৫": "5",
  "৬": "6",
  "৭": "7",
  "৮": "8",
  "৯": "9",
};

export type Locale = "bn" | "en";

export interface BilingualText {
  bn: string;
  en: string;
}

/**
 * Converts Western Arabic digits (0-9) to Bengali digits (০-৯).
 */
export function toBengaliDigits(value: string | number): string {
  return String(value).replace(/[0-9]/g, (digit) => EN_TO_BN_DIGITS[digit] ?? digit);
}

/**
 * Converts Bengali digits (০-৯) to Western Arabic digits (0-9).
 */
export function fromBengaliDigits(value: string): string {
  return value.replace(/[০-৯]/g, (digit) => BN_TO_EN_DIGITS[digit] ?? digit);
}

/**
 * Parses a numeric input that may contain Bengali or English digits.
 */
export function parseBengaliNumber(value: string): number {
  const normalized = fromBengaliDigits(value.trim()).replace(/,/g, "");
  return Number(normalized);
}

/**
 * Formats a number according to the current locale ('bn' uses Bengali digits).
 */
export function formatLocaleNumber(value: number | string, locale: Locale): string {
  const str = typeof value === "number" ? value.toLocaleString("en-IN") : String(value);
  return locale === "bn" ? toBengaliDigits(str) : str;
}

/**
 * Formats an amount in BDT with the ৳ symbol and locale-appropriate digits.
 */
export function formatBdt(amount: number, locale: Locale): string {
  return `৳${formatLocaleNumber(amount, locale)}`;
}

/**
 * Selects the localized string from a BilingualText object.
 */
export function pickLocalized(text: BilingualText | undefined | null, locale: Locale): string {
  if (!text) return "";
  return text[locale] || text.en || text.bn || "";
}
