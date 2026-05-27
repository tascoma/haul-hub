import CoreLocation
import MapKit

enum RouteDistanceError: Error, LocalizedError {
    case geocodingFailed
    case noRoute

    var errorDescription: String? {
        switch self {
        case .geocodingFailed: return "Couldn't find one of these addresses"
        case .noRoute: return "No drivable route between these addresses"
        }
    }
}

/// Driving-distance lookup backed by MapKit. Forward-geocodes both addresses
/// (no location permission required) then asks MKDirections for a car route.
enum RouteDistance {
    private static let metersPerMile = 1609.344

    /// Driving distance in miles between two free-form address strings.
    static func miles(from pickup: String, to dropoff: String) async throws -> Double {
        let geocoder = CLGeocoder()
        // CLGeocoder handles one request at a time, so geocode sequentially.
        let source = try await coordinate(for: pickup, using: geocoder)
        let destination = try await coordinate(for: dropoff, using: geocoder)

        let request = MKDirections.Request()
        request.source = MKMapItem(placemark: MKPlacemark(coordinate: source))
        request.destination = MKMapItem(placemark: MKPlacemark(coordinate: destination))
        request.transportType = .automobile

        let response = try await MKDirections(request: request).calculate()
        guard let route = response.routes.first else { throw RouteDistanceError.noRoute }
        return route.distance / metersPerMile
    }

    private static func coordinate(
        for address: String,
        using geocoder: CLGeocoder
    ) async throws -> CLLocationCoordinate2D {
        let placemarks = try await geocoder.geocodeAddressString(address)
        guard let coordinate = placemarks.first?.location?.coordinate else {
            throw RouteDistanceError.geocodingFailed
        }
        return coordinate
    }
}
