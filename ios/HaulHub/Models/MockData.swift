import Foundation

// Mock data ported from the design's seed (project/src/data.js).
// Used to render the design without a backend.

enum Urgency: String {
    case standard, express
}

struct Address: Hashable {
    let street: String
    let city: String
    let state: String
    let zip: String
}

struct Shipper: Hashable {
    let name: String
    let rating: Double
    let jobs: Int
    let initials: String
    var business: Bool = false
}

struct Hauler: Hashable {
    let name: String
    let initials: String
    let rating: Double
    let jobs: Int
    let vehicle: String
    let plate: String
}

struct Load: Identifiable, Hashable {
    let id: String
    let title: String
    var description: String? = nil
    let weightLbs: Int
    var lengthFt: Double? = nil
    var widthFt: Double? = nil
    var heightFt: Double? = nil
    let pickup: Address
    let dropoff: Address
    let pickupWindow: String
    let dropoffBy: String
    let miles: Int
    let urgency: Urgency
    let priceCents: Int
    let postedMinAgo: Int
    let shipper: Shipper
    let vehicleNeeds: String  // pickup, box_truck, etc.
    let photoCount: Int
}

enum VehicleLabel {
    static func describe(_ key: String) -> String {
        switch key {
        case "pickup": return "Pickup truck"
        case "pickup_with_trailer": return "Pickup + trailer"
        case "flatbed": return "Flatbed"
        case "box_truck": return "Box truck"
        case "cargo_van": return "Cargo van"
        case "semi": return "Semi"
        default: return "Other"
        }
    }
}

enum MockData {
    static let hauls: [Load] = [
        Load(
            id: "L-2841",
            title: "Restored 1968 Ford pickup",
            description: "Project truck — drives onto trailer. Has key. Owner can help load.",
            weightLbs: 3400, lengthFt: 17, widthFt: 6.5, heightFt: 5.5,
            pickup: Address(street: "418 Linden Ave", city: "Austin", state: "TX", zip: "78704"),
            dropoff: Address(street: "2110 W 7th St", city: "Fort Worth", state: "TX", zip: "76107"),
            pickupWindow: "Today, 2:00 – 5:00 PM",
            dropoffBy: "Tomorrow by 8 PM",
            miles: 195, urgency: .express, priceCents: 48500, postedMinAgo: 4,
            shipper: Shipper(name: "Maya R.", rating: 4.9, jobs: 12, initials: "MR"),
            vehicleNeeds: "pickup_with_trailer", photoCount: 3
        ),
        Load(
            id: "L-2839",
            title: "IKEA sectional + dining set",
            weightLbs: 480,
            pickup: Address(street: "1290 Maple Dr", city: "Round Rock", state: "TX", zip: "78664"),
            dropoff: Address(street: "88 Cedar Park Ln", city: "Austin", state: "TX", zip: "78731"),
            pickupWindow: "Sat, 9 AM – 12 PM",
            dropoffBy: "Sat by 6 PM",
            miles: 24, urgency: .standard, priceCents: 8900, postedMinAgo: 12,
            shipper: Shipper(name: "Devon K.", rating: 4.7, jobs: 4, initials: "DK"),
            vehicleNeeds: "cargo_van", photoCount: 5
        ),
        Load(
            id: "L-2837",
            title: "Pallet of landscaping pavers",
            weightLbs: 2200,
            pickup: Address(street: "Home Depot · 1200 Barbara Jordan", city: "Austin", state: "TX", zip: "78723"),
            dropoff: Address(street: "4509 Speedway", city: "Austin", state: "TX", zip: "78751"),
            pickupWindow: "Today, anytime",
            dropoffBy: "Today by 7 PM",
            miles: 8, urgency: .standard, priceCents: 12400, postedMinAgo: 21,
            shipper: Shipper(name: "Greenleaf Co.", rating: 4.8, jobs: 38, initials: "GC", business: true),
            vehicleNeeds: "flatbed", photoCount: 2
        ),
        Load(
            id: "L-2835",
            title: "Upright piano — careful hands",
            weightLbs: 520,
            pickup: Address(street: "801 Brazos St", city: "Austin", state: "TX", zip: "78701"),
            dropoff: Address(street: "5511 Parkcrest Dr", city: "Austin", state: "TX", zip: "78731"),
            pickupWindow: "Sun, 10 AM – 1 PM",
            dropoffBy: "Sun by 5 PM",
            miles: 11, urgency: .standard, priceCents: 18500, postedMinAgo: 38,
            shipper: Shipper(name: "Elena V.", rating: 5.0, jobs: 2, initials: "EV"),
            vehicleNeeds: "box_truck", photoCount: 4
        ),
    ]

    static let heroLoad = hauls[0]

    struct ActiveHaul {
        let base: Load
        let stageIndex: Int      // 0 claimed, 1 en route, 2 picked up, 3 in transit, 4 delivered
        let haulerPayoutCents: Int
        let platformFeeCents: Int
        let milesRemaining: Double
        let etaMin: Int
    }

    static let activeHaul = ActiveHaul(
        base: hauls[2],
        stageIndex: 3,
        haulerPayoutCents: 10540,
        platformFeeCents: 1860,
        milesRemaining: 3.4,
        etaMin: 11
    )

    struct TrackedShipment {
        let base: Load
        let hauler: Hauler
        let milesRemaining: Double
        let etaMin: Int
    }

    static let trackedShipment = TrackedShipment(
        base: hauls[3],
        hauler: Hauler(
            name: "Jordan T.", initials: "JT", rating: 4.94, jobs: 312,
            vehicle: "Box truck · 16 ft", plate: "TX 8FE-3920"
        ),
        milesRemaining: 2.1, etaMin: 6
    )
}
