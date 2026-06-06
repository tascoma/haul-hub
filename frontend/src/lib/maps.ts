import type { Address } from "./types";

// Browser key for the Maps JavaScript API. When unset, map components render a
// graceful fallback instead of a broken map.
export const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY ?? "";

// A Map ID is required for AdvancedMarker. "DEMO_MAP_ID" works for development;
// set a real one in the Google Cloud console for production styling.
export const GOOGLE_MAP_ID = "DEMO_MAP_ID";

export interface LatLng {
  lat: number;
  lng: number;
}

/** Parse an Address's decimal-string lat/lng into numbers, or null if unusable. */
export function coordOf(ref?: Address | null): LatLng | null {
  if (!ref || ref.lat == null || ref.lng == null) return null;
  const lat = parseFloat(ref.lat);
  const lng = parseFloat(ref.lng);
  if (Number.isNaN(lat) || Number.isNaN(lng)) return null;
  return { lat, lng };
}
