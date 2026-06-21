import Foundation

// MARK: - Payment method (shipper card)

/// Saved card summary returned by GET/POST /api/me/payment-method.
/// Mirrors backend `PaymentMethodInfo`.
struct PaymentMethodInfo: Decodable, Hashable {
    let brand: String
    let last4: String
    let expMonth: Int
    let expYear: Int

    /// e.g. "Visa •••• 4242"
    var display: String {
        "\(brand.capitalized) •••• \(last4)"
    }

    /// Zero-padded "MM/YY".
    var expiryDisplay: String {
        String(format: "%02d/%02d", expMonth, expYear % 100)
    }
}

/// Body for POST /api/me/payment-method.
struct SavePaymentMethodRequest: Encodable {
    let paymentMethodId: String
}

// MARK: - Connect onboarding

/// Response from POST /api/me/connect-onboarding.
struct ConnectOnboardingResponse: Decodable {
    let url: String
}

/// Response from POST /api/me/payment-method/setup-intent.
struct SetupIntentResponse: Decodable {
    let clientSecret: String
}

// MARK: - Billing address update

/// PATCH /api/me body for the billing-address section. Only the billing fields
/// are sent; nil optionals are omitted by the encoder, leaving them unchanged.
struct BillingAddressUpdate: Encodable {
    let billingSameAsHome: Bool
    let billingAddressLine1: String?
    let billingAddressCity: String?
    let billingAddressState: String?
    let billingAddressZip: String?
}

// MARK: - Payment status

/// Lifecycle status of a load's payment. Mirrors backend `PaymentStatus`.
enum PaymentStatus: String, Decodable, Hashable {
    case pending
    case authorized
    case captured
    case transferred
    case refunded
    case failed

    var label: String {
        switch self {
        case .pending:      return "Awaiting confirmation"
        case .authorized:   return "Funds held"
        case .captured:     return "Captured"
        case .transferred:  return "Paid to hauler"
        case .refunded:     return "Refunded"
        case .failed:       return "Payment failed"
        }
    }

    var pillStyle: HHPillStyle {
        switch self {
        case .pending:      return .neutral
        case .authorized:   return .info
        case .captured:     return .accent
        case .transferred:  return .success
        case .refunded:     return .warning
        case .failed:       return .danger
        }
    }
}

/// Full payment record from GET /api/loads/{id}/payment. Mirrors `PaymentRead`.
struct Payment: Decodable, Identifiable, Hashable {
    let id: String
    let loadId: String
    let amountCents: Int
    let platformFeeCents: Int
    let haulerPayoutCents: Int
    let status: PaymentStatus
    let stripePaymentIntentId: String?
    let stripeTransferId: String?
    let authorizedAt: Date?
    let capturedAt: Date?
    let transferredAt: Date?
    let refundedAt: Date?
    let createdAt: Date
    let updatedAt: Date
}
