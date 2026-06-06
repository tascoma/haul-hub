import Foundation

enum Config {
    static var apiBaseURL: URL {
        let raw = ProcessInfo.processInfo.environment["API_BASE_URL"]
            ?? "http://127.0.0.1:8000"
        guard let url = URL(string: raw) else {
            fatalError("Invalid API_BASE_URL: \(raw)")
        }
        return url
    }

    /// Stripe publishable key used to initialize the Stripe SDK. Reads
    /// `STRIPE_PUBLISHABLE_KEY` from the environment, falling back to a test key
    /// placeholder so the app still launches in development.
    static var stripePublishableKey: String {
        ProcessInfo.processInfo.environment["STRIPE_PUBLISHABLE_KEY"]
            ?? "pk_test_placeholder"
    }
}
