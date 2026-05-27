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
