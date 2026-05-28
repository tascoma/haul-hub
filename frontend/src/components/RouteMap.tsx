import { useEffect } from "react";
import {
  APIProvider,
  AdvancedMarker,
  Map,
  Pin,
  useMap,
  useMapsLibrary,
} from "@vis.gl/react-google-maps";
import { GOOGLE_MAPS_API_KEY, GOOGLE_MAP_ID, type LatLng } from "../lib/maps";

interface RouteMapProps {
  pickup: LatLng | null;
  dropoff: LatLng | null;
  height?: number;
}

/** Draws the driving route between two points and auto-fits the viewport to it. */
function Directions({ pickup, dropoff }: { pickup: LatLng; dropoff: LatLng }) {
  const map = useMap();
  const routesLib = useMapsLibrary("routes");

  useEffect(() => {
    if (!routesLib || !map) return;
    const renderer = new routesLib.DirectionsRenderer({
      map,
      suppressMarkers: true, // we draw our own pickup/dropoff pins
      polylineOptions: { strokeColor: "#FF5C28", strokeWeight: 4, strokeOpacity: 0.9 },
    });
    const service = new routesLib.DirectionsService();
    service
      .route({
        origin: pickup,
        destination: dropoff,
        travelMode: google.maps.TravelMode.DRIVING,
      })
      .then((res) => renderer.setDirections(res))
      .catch(() => {
        // Directions can fail (no route, quota); the markers + fitBounds still show context.
      });
    return () => renderer.setMap(null);
    // Depend on the coordinate values, not the objects — callers pass a fresh
    // coordOf(...) object each render, which would otherwise re-request directions endlessly.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [routesLib, map, pickup.lat, pickup.lng, dropoff.lat, dropoff.lng]);

  return null;
}

export function RouteMap({ pickup, dropoff, height = 220 }: RouteMapProps) {
  if (!GOOGLE_MAPS_API_KEY || !pickup || !dropoff) {
    return (
      <div className="map-fallback" style={{ height }}>
        Map unavailable — route not yet located.
      </div>
    );
  }

  const center = {
    lat: (pickup.lat + dropoff.lat) / 2,
    lng: (pickup.lng + dropoff.lng) / 2,
  };

  return (
    <div className="route-map" style={{ height, borderRadius: 12, overflow: "hidden" }}>
      <APIProvider apiKey={GOOGLE_MAPS_API_KEY}>
        <Map
          mapId={GOOGLE_MAP_ID}
          defaultCenter={center}
          defaultZoom={9}
          gestureHandling="cooperative"
          disableDefaultUI
          style={{ width: "100%", height: "100%" }}
        >
          <AdvancedMarker position={pickup}>
            <Pin background="#334155" borderColor="#1e293b" glyphColor="#fff" />
          </AdvancedMarker>
          <AdvancedMarker position={dropoff}>
            <Pin background="#FF5C28" borderColor="#c2410c" glyphColor="#fff" />
          </AdvancedMarker>
          <Directions pickup={pickup} dropoff={dropoff} />
        </Map>
      </APIProvider>
    </div>
  );
}
