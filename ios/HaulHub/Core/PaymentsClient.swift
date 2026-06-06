import Foundation

/// API client for Stripe-backed payment flows: hauler Connect onboarding,
/// shipper card setup, billing address, and per-load payment status.
/// Thin wrapper over `APIClient`, mirroring `LoadsClient`.
struct PaymentsClient {
    private struct EmptyRequest: Encodable {}

    private let api: APIClient

    init(api: APIClient) {
        self.api = api
    }

    // MARK: - Hauler Connect onboarding

    /// Create (or refresh) a Stripe Express onboarding link for the hauler.
    func connectOnboarding() async throws -> URL {
        let resp: ConnectOnboardingResponse =
            try await api.post("/api/me/connect-onboarding", body: EmptyRequest())
        guard let url = URL(string: resp.url) else {
            throw APIError.invalidResponse
        }
        return url
    }

    // MARK: - Shipper payment method

    /// Create a SetupIntent and return its client_secret for the Stripe SDK.
    func createSetupIntent() async throws -> String {
        let resp: SetupIntentResponse =
            try await api.post("/api/me/payment-method/setup-intent", body: EmptyRequest())
        return resp.clientSecret
    }

    /// Attach a confirmed PaymentMethod as the shipper's default card.
    func savePaymentMethod(_ paymentMethodId: String) async throws -> PaymentMethodInfo {
        try await api.post(
            "/api/me/payment-method",
            body: SavePaymentMethodRequest(paymentMethodId: paymentMethodId)
        )
    }

    /// The shipper's saved card, or nil if none is saved (404).
    func paymentMethod() async throws -> PaymentMethodInfo? {
        do {
            return try await api.get("/api/me/payment-method")
        } catch let error where Self.isNotFound(error) {
            return nil
        }
    }

    /// Update the shipper's billing address (PATCH /me).
    func updateBilling(_ body: BillingAddressUpdate) async throws {
        let _: Me = try await api.patch("/api/me", body: body)
    }

    // MARK: - Load payment status

    /// The payment record for a load, or nil before a hauler accepts (404).
    func payment(loadId: String) async throws -> Payment? {
        do {
            return try await api.get("/api/loads/\(loadId)/payment")
        } catch let error where Self.isNotFound(error) {
            return nil
        }
    }

    // MARK: - Helpers

    private static func isNotFound(_ error: Error) -> Bool {
        if case APIError.http(let status, _) = error { return status == 404 }
        return false
    }
}
