import { useEffect } from "react";
import { APIProvider, AdvancedMarker, Map, Pin, useMap } from "@vis.gl/react-google-maps";
import type { Load } from "../lib/types";
import { GOOGLE_MAPS_API_KEY, GOOGLE_MAP_ID, coordOf, type LatLng } from "../lib/maps";

interface PickupsMapProps {
  loads: Load[];
  onSelect: (id: string) => void;
  height?: number | string;
}

interface Pickup {
  id: string;
  title: string;
  pos: LatLng;
}

/** Keeps the viewport fitted to all visible pickup pins as the list changes. */
function FitBounds({ points }: { points: LatLng[] }) {
  const map = useMap();
  useEffect(() => {
    if (!map || points.length === 0) return;
    if (points.length === 1) {
      map.setCenter(points[0]);
      map.setZoom(11);
      return;
    }
    const bounds = new google.maps.LatLngBounds();
    points.forEach((p) => bounds.extend(p));
    map.fitBounds(bounds, 48);
  }, [map, points]);
  return null;
}

export function PickupsMap({ loads, onSelect, height = 280 }: PickupsMapProps) {
  const pickups: Pickup[] = loads
    .map((l) => {
      const pos = coordOf(l.pickup_address_ref);
      return pos ? { id: l.id, title: l.title, pos } : null;
    })
    .filter((p): p is Pickup => p !== null);

  if (!GOOGLE_MAPS_API_KEY || pickups.length === 0) {
    return (
      <div className="map-fallback" style={{ height }}>
        {GOOGLE_MAPS_API_KEY
          ? "No mapped pickups yet for these loads."
          : "Map unavailable — set VITE_GOOGLE_MAPS_API_KEY."}
      </div>
    );
  }

  return (
    <div className="pickups-map" style={{ height, borderRadius: 12, overflow: "hidden" }}>
      <APIProvider apiKey={GOOGLE_MAPS_API_KEY}>
        <Map
          mapId={GOOGLE_MAP_ID}
          defaultCenter={pickups[0].pos}
          defaultZoom={9}
          gestureHandling="cooperative"
          disableDefaultUI
          style={{ width: "100%", height: "100%" }}
        >
          {pickups.map((p) => (
            <AdvancedMarker
              key={p.id}
              position={p.pos}
              title={p.title}
              onClick={() => onSelect(p.id)}
            >
              <Pin background="#FF5C28" borderColor="#c2410c" glyphColor="#fff" />
            </AdvancedMarker>
          ))}
          <FitBounds points={pickups.map((p) => p.pos)} />
        </Map>
      </APIProvider>
    </div>
  );
}
