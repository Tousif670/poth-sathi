"use client";

import { useLocale } from "@/context/LocaleProvider";

export type NearbyCategoryFilter = "all" | "hospital" | "pharmacy" | "police" | "atm" | "mosque";

interface CategoryChipsProps {
  selected: NearbyCategoryFilter;
  onSelect: (category: NearbyCategoryFilter) => void;
}

const CATEGORIES: Array<{ id: NearbyCategoryFilter; bn: string; en: string }> = [
  { id: "all", bn: "সবগুলো", en: "All Places" },
  { id: "hospital", bn: "হাসপাতাল", en: "Hospitals" },
  { id: "pharmacy", bn: "ফার্মেসি", en: "Pharmacies" },
  { id: "police", bn: "ট্যুরিস্ট পুলিশ / উদ্ধার", en: "Police & Rescue" },
  { id: "atm", bn: "এটিএম বুথ", en: "ATM Booths" },
  { id: "mosque", bn: "মসজিদ", en: "Mosques" },
];

export function CategoryChips({ selected, onSelect }: CategoryChipsProps) {
  const { locale } = useLocale();

  return (
    <div className="flex flex-wrap gap-2" role="tablist" aria-label="Place category filter">
      {CATEGORIES.map((cat) => {
        const isActive = selected === cat.id;
        return (
          <button
            key={cat.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => onSelect(cat.id)}
            className={`rounded-full border px-3.5 py-1.5 text-xs font-semibold transition-colors ${
              isActive
                ? "border-primary bg-primary text-primary-foreground"
                : "bg-card text-muted-foreground hover:bg-secondary hover:text-foreground"
            }`}
          >
            {locale === "bn" ? cat.bn : cat.en}
          </button>
        );
      })}
    </div>
  );
}
