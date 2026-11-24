import type { BilingualText } from "./utils";

export interface ReferenceMetadata {
  data_source: string;
  is_verified: boolean;
  last_updated: string;
}

export interface StaticHotel extends ReferenceMetadata {
  id: string;
  hotel_id: string;
  name: BilingualText;
  area: "kolatoli" | "sugandha" | "laboni";
  description: BilingualText;
  price_min_bdt: number;
  price_max_bdt: number;
  amenities: string[];
  rating: number;
  address: BilingualText;
  phone: string;
  lat: number;
  lon: number;
  geohash?: string;
  image_url?: string;
  match_score?: number;
}

export interface StaticPlace extends ReferenceMetadata {
  id: string;
  place_id: string;
  name: BilingualText;
  category: "hospital" | "pharmacy" | "police" | "atm" | "mosque" | "other";
  description: BilingualText;
  address: BilingualText;
  phone: string;
  opening_hours: string;
  lat: number;
  lon: number;
  geohash?: string;
  distance_km?: number;
}

export interface StaticTransportRoute extends ReferenceMetadata {
  id: string;
  route_id: string;
  origin: BilingualText;
  destination: BilingualText;
  vehicle_type: "cng_auto" | "tomtom" | "rickshaw";
  fare_basis: "per_vehicle" | "per_person";
  fare_min_bdt: number;
  fare_max_bdt: number;
  distance_km: number;
  notes: BilingualText;
}

export interface StaticBeachStatus extends ReferenceMetadata {
  id: string;
  zone_id: "kolatoli" | "sugandha" | "laboni";
  zone_name: BilingualText;
  flag_colour: "green" | "yellow" | "red";
  note: BilingualText;
  set_by: string;
  is_outdated?: boolean;
}

export interface StaticEmergencyContact {
  id: string;
  service: BilingualText;
  number: string;
  status: string;
}

export async function loadTier0Json<T>(filename: string): Promise<T[]> {
  try {
    const response = await fetch(`/static/${filename}`);
    if (!response.ok) {
      return [];
    }
    const data: unknown = await response.json();
    return Array.isArray(data) ? (data as T[]) : [];
  } catch {
    return [];
  }
}
