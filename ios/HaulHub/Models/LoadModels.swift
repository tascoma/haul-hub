import Foundation

// MARK: - Load status

enum LoadStatus: String, Decodable, Hashable {
    case draft
    case posted
    case accepted
    case pickedUp   = "picked_up"
    case inTransit  = "in_transit"
    case delivered
    case cancelled

    var label: String {
        switch self {
        case .draft:      return "Draft"
        case .posted:     return "Posted"
        case .accepted:   return "Accepted"
        case .pickedUp:   return "Picked Up"
        case .inTransit:  return "In Transit"
        case .delivered:  return "Delivered"
        case .cancelled:  return "Cancelled"
        }
    }

    var pillStyle: HHPillStyle {
        switch self {
        case .draft:                return .neutral
        case .posted:               return .info
        case .accepted, .pickedUp:  return .warning
        case .inTransit:            return .accent
        case .delivered:            return .success
        case .cancelled:            return .danger
        }
    }

    /// True while a hauler actively needs to do work.
    var isActive: Bool {
        switch self {
        case .accepted, .pickedUp, .inTransit: return true
        default: return false
        }
    }

    /// Stage index used by the progress stepper (0-based; 0 = claimed).
    var stageIndex: Int {
        switch self {
        case .accepted:   return 1
        case .pickedUp:   return 2
        case .inTransit:  return 3
        case .delivered:  return 4
        default:          return 0
        }
    }
}

// MARK: - Urgency

enum Urgency: String, Decodable, Hashable {
    case standard
    case express
}

// MARK: - Address ref (mirrors backend AddressRead; lat/lng arrive as decimal strings)

struct AddressRef: Decodable, Hashable {
    let lat: String?
    let lng: String?

    /// Parsed latitude, or nil if the address hasn't been geocoded yet.
    var latitude: Double? { lat.flatMap(Double.init) }
    var longitude: Double? { lng.flatMap(Double.init) }
}

// MARK: - API Load (mirrors backend LoadRead schema)

struct APILoad: Decodable, Identifiable, Hashable {
    let id: String
    let shipperId: String
    let haulerId: String?
    let referenceCode: String?
    let title: String
    let description: String?
    let photoUrls: [String]
    let weightLbs: Int
    let lengthFt: Double?
    let widthFt: Double?
    let heightFt: Double?
    let pickupAddress: String
    let pickupCity: String
    let pickupState: String
    let pickupZip: String
    let pickupWindowStart: Date
    let pickupWindowEnd: Date
    let dropoffAddress: String
    let dropoffCity: String
    let dropoffState: String
    let dropoffZip: String
    let dropoffBy: Date
    let pickupAddressRef: AddressRef?
    let dropoffAddressRef: AddressRef?
    let estimatedDistanceMiles: Double
    let urgency: Urgency
    let calculatedPriceCents: Int
    let status: LoadStatus
    let acceptedAt: Date?
    let pickedUpAt: Date?
    let deliveredAt: Date?
    let cancelledAt: Date?
    let createdAt: Date
    let updatedAt: Date

    // MARK: - Computed helpers

    var isExpress: Bool { urgency == .express }

    /// Hauler's 85 % payout.
    var payoutCents: Int { Int(Double(calculatedPriceCents) * 0.85) }

    /// Minutes since the load was posted (clamped to 0).
    var postedMinAgo: Int { max(0, Int(Date().timeIntervalSince(createdAt) / 60)) }

    var pickupWindowDisplay: String {
        let df = DateFormatter()
        df.dateFormat = "MMM d, h:mm a"
        return df.string(from: pickupWindowStart)
    }

    var dropoffByDisplay: String {
        let df = DateFormatter()
        df.dateFormat = "MMM d, h:mm a"
        return df.string(from: dropoffBy)
    }

    // Stable identity / equality
    static func == (lhs: APILoad, rhs: APILoad) -> Bool { lhs.id == rhs.id }
    func hash(into hasher: inout Hasher) { hasher.combine(id) }
}

// MARK: - Create load request (mirrors backend LoadCreate; web PostLoadPage fields)

/// Body for POST /api/loads. Property names are camelCase; APIClient converts
/// to snake_case and encodes Dates as ISO-8601 UTC. Nil optionals are omitted,
/// letting the backend apply its defaults.
struct CreateLoadRequest: Encodable {
    let title: String
    let description: String?
    let weightLbs: Int
    let lengthFt: Double?
    let widthFt: Double?
    let heightFt: Double?
    let pickupAddress: String
    let pickupCity: String
    let pickupState: String
    let pickupZip: String
    let pickupWindowStart: Date
    let pickupWindowEnd: Date
    let dropoffAddress: String
    let dropoffCity: String
    let dropoffState: String
    let dropoffZip: String
    let dropoffBy: Date
    let estimatedDistanceMiles: Double
    let urgency: Urgency
}

extension Urgency: Encodable {}

// MARK: - Booking event (mirrors backend BookingEventRead schema)

enum BookingEventType: String, Decodable, Hashable {
    case accepted
    case pickedUp  = "picked_up"
    case inTransit = "in_transit"
    case delivered
    case cancelled

    var label: String {
        switch self {
        case .accepted:  return "Hauler claimed the load"
        case .pickedUp:  return "Picked up"
        case .inTransit: return "In transit"
        case .delivered: return "Delivered"
        case .cancelled: return "Cancelled"
        }
    }

    var icon: String {
        switch self {
        case .accepted:  return "checkmark.seal.fill"
        case .pickedUp:  return "shippingbox.fill"
        case .inTransit: return "truck.box.fill"
        case .delivered: return "flag.checkered"
        case .cancelled: return "xmark.circle.fill"
        }
    }
}

struct APIBookingEvent: Decodable, Identifiable, Hashable {
    let id: String
    let loadId: String
    let eventType: BookingEventType
    let actorUserId: String
    let createdAt: Date

    var createdAtDisplay: String {
        let df = DateFormatter()
        df.dateFormat = "MMM d, h:mm a"
        return df.string(from: createdAt)
    }

    static func == (lhs: APIBookingEvent, rhs: APIBookingEvent) -> Bool { lhs.id == rhs.id }
    func hash(into hasher: inout Hasher) { hasher.combine(id) }
}
