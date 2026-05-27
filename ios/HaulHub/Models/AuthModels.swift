import Foundation

enum SignupRole: String, Codable, CaseIterable, Identifiable {
    case customer, hauler
    var id: String { rawValue }
}

struct SignupRequest: Encodable {
    let email: String
    let password: String
    let fullName: String?
    let roles: [SignupRole]
}

struct LoginRequest: Encodable {
    let email: String
    let password: String
}

struct TokenResponse: Decodable {
    let accessToken: String
    let tokenType: String
}

struct UserProfile: Decodable {
    let userId: String
    let fullName: String?
    let displayName: String?
    let phone: String?
    let avatarUrl: String?
    let bio: String?
    let preferredLanguage: String
    let timezone: String
    let shipperEnabled: Bool
    let haulerEnabled: Bool
    let marketingOptIn: Bool
}

struct Me: Decodable {
    let id: String
    let email: String
    let phone: String?
    let profile: UserProfile
}

/// Mirrors `HaulerProfileRead` from the backend schema.
struct HaulerProfileData: Decodable {
    let userId: String
    let companyName: String?
    let businessType: String?
    let yearsExperience: Int?
    let bio: String?
    let serviceRadiusMiles: Int
    let acceptsDisposalJobs: Bool
    let acceptsDonationRuns: Bool
    let acceptsHazardous: Bool
    let currentlyAvailable: Bool
    let verifiedAt: Date?
}

enum OnboardingStep: String, Codable {
    case profile
    case haulerProfile = "hauler_profile"
    case haulerVehicle = "hauler_vehicle"
    case haulerServiceArea = "hauler_service_area"
    case done
}

struct OnboardingChecks: Decodable {
    let hasVehicle: Bool
    let hasServiceArea: Bool
}

struct OnboardingStatus: Decodable {
    let profileComplete: Bool
    let customerReady: Bool
    let haulerReady: Bool
    let nextStep: OnboardingStep
    let checks: OnboardingChecks
}
