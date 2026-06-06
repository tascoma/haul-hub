import CoreLocation
import MapKit
import SwiftUI

/// Real MapKit map showing a load's pickup and dropoff with the driving route between them.
///
/// Coordinates come from the backend (`AddressRef.latitude/longitude`) when available;
/// otherwise the address strings are forward-geocoded on-device (same approach as
/// `RouteDistance`). The route is fetched via `MKDirections`. Any failure falls back to a
/// neutral placeholder so the surrounding card still reads cleanly.
struct HHRouteMapView: View {
    let pickupCoordinate: CLLocationCoordinate2D?
    let dropoffCoordinate: CLLocationCoordinate2D?
    let pickupAddress: String
    let dropoffAddress: String

    @State private var pickup: CLLocationCoordinate2D?
    @State private var dropoff: CLLocationCoordinate2D?
    @State private var route: MKRoute?
    @State private var failed = false

    var body: some View {
        Group {
            if let pickup, let dropoff {
                Map {
                    Marker("Pickup", systemImage: "shippingbox.fill", coordinate: pickup)
                        .tint(HHColor.ink900)
                    Marker("Dropoff", systemImage: "flag.checkered", coordinate: dropoff)
                        .tint(HHColor.accent)
                    if let route {
                        MapPolyline(route)
                            .stroke(HHColor.accent, lineWidth: 4)
                    }
                }
                .mapControlVisibility(.hidden)
            } else if failed {
                placeholder
            } else {
                ZStack {
                    HHColor.ink100
                    ProgressView()
                }
            }
        }
        .task { await resolve() }
    }

    private var placeholder: some View {
        ZStack {
            HHColor.ink100
            VStack(spacing: 6) {
                Image(systemName: "map")
                    .font(.system(size: 22, weight: .semibold))
                    .foregroundStyle(HHColor.ink400)
                Text("Map unavailable")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(HHColor.ink500)
            }
        }
    }

    /// Resolve both endpoints (backend coords first, geocoding fallback) then the route.
    private func resolve() async {
        guard pickup == nil || dropoff == nil else { return }
        let geocoder = CLGeocoder()
        // CLGeocoder serves one request at a time, so resolve sequentially.
        var p = pickupCoordinate
        if p == nil { p = try? await coordinate(for: pickupAddress, using: geocoder) }
        var d = dropoffCoordinate
        if d == nil { d = try? await coordinate(for: dropoffAddress, using: geocoder) }
        guard let p, let d else {
            failed = true
            return
        }
        pickup = p
        dropoff = d
        route = try? await drivingRoute(from: p, to: d)
    }

    private func coordinate(
        for address: String,
        using geocoder: CLGeocoder
    ) async throws -> CLLocationCoordinate2D? {
        let placemarks = try await geocoder.geocodeAddressString(address)
        return placemarks.first?.location?.coordinate
    }

    private func drivingRoute(
        from source: CLLocationCoordinate2D,
        to destination: CLLocationCoordinate2D
    ) async throws -> MKRoute? {
        let request = MKDirections.Request()
        request.source = MKMapItem(placemark: MKPlacemark(coordinate: source))
        request.destination = MKMapItem(placemark: MKPlacemark(coordinate: destination))
        request.transportType = .automobile
        let response = try await MKDirections(request: request).calculate()
        return response.routes.first
    }
}

extension AddressRef {
    /// Backend-supplied coordinate, or nil if the address hasn't been geocoded.
    var coordinate: CLLocationCoordinate2D? {
        guard let latitude, let longitude else { return nil }
        return CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }
}

extension HHRouteMapView {
    /// Build the map straight from a load, preferring backend coordinates and falling
    /// back to geocoding the flat address strings.
    init(load: APILoad) {
        self.init(
            pickupCoordinate: load.pickupAddressRef?.coordinate,
            dropoffCoordinate: load.dropoffAddressRef?.coordinate,
            pickupAddress: "\(load.pickupAddress), \(load.pickupCity), \(load.pickupState) \(load.pickupZip)",
            dropoffAddress: "\(load.dropoffAddress), \(load.dropoffCity), \(load.dropoffState) \(load.dropoffZip)"
        )
    }
}
