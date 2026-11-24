import { describe, expect, it } from "vitest";
import {
  formatBdt,
  formatLocaleNumber,
  fromBengaliDigits,
  parseBengaliNumber,
  pickLocalized,
  toBengaliDigits,
} from "./utils";

describe("Bengali digits & i18n utilities", () => {
  it("converts English digits to Bengali digits accurately", () => {
    expect(toBengaliDigits(2026)).toBe("২০২৬");
    expect(toBengaliDigits("999")).toBe("৯৯৯");
    expect(toBengaliDigits("৳1,250")).toBe("৳১,২৫০");
  });

  it("converts Bengali digits back to English and parses numbers", () => {
    expect(fromBengaliDigits("৩৫০০")).toBe("3500");
    expect(parseBengaliNumber("৩,৫০০")).toBe(3500);
    expect(parseBengaliNumber("120")).toBe(120);
  });

  it("formats BDT and numbers by locale", () => {
    expect(formatLocaleNumber(450, "bn")).toBe("৪৫০");
    expect(formatLocaleNumber(450, "en")).toBe("450");
    expect(formatBdt(120, "bn")).toBe("৳১২০");
    expect(formatBdt(120, "en")).toBe("৳120");
  });

  it("picks localized string from BilingualText", () => {
    const label = { bn: "কলাতলী", en: "Kolatoli" };
    expect(pickLocalized(label, "bn")).toBe("কলাতলী");
    expect(pickLocalized(label, "en")).toBe("Kolatoli");
    expect(pickLocalized(null, "bn")).toBe("");
  });
});
