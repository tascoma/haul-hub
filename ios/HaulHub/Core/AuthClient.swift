import Foundation

/// Reference-type token cache backed by the Keychain.
/// Holds the token in memory after login so the next request doesn't race
/// against a Keychain read; persists to and restores from Keychain across launches.
private final class TokenStore: TokenProvider {
    private var inMemoryToken: String?

    init() {
        inMemoryToken = KeychainStore.loadToken()
    }

    func token() -> String? { inMemoryToken }

    func set(_ token: String) {
        inMemoryToken = token
        KeychainStore.saveToken(token)
    }

    func clear() {
        inMemoryToken = nil
        KeychainStore.deleteToken()
    }
}

/// Thin wrapper over APIClient for /api/auth + /api/me endpoints.
struct AuthClient {
    /// The underlying client. Exposed so the app can inject it into the SwiftUI
    /// environment, ensuring all views share the same in-memory token store.
    let api: APIClient
    private let tokenStore: TokenStore

    init() {
        let tokenStore = TokenStore()
        self.tokenStore = tokenStore
        self.api = APIClient(tokenProvider: tokenStore)
    }

    func signup(email: String, password: String, fullName: String?, roles: [SignupRole]) async throws -> Me {
        let res: TokenResponse = try await api.post(
            "/api/auth/signup",
            body: SignupRequest(email: email, password: password, fullName: fullName, roles: roles)
        )
        tokenStore.set(res.accessToken)
        return try await me()
    }

    func login(email: String, password: String) async throws -> Me {
        let res: TokenResponse = try await api.post(
            "/api/auth/login",
            body: LoginRequest(email: email, password: password)
        )
        tokenStore.set(res.accessToken)
        return try await me()
    }

    func me() async throws -> Me {
        try await api.get("/api/me")
    }

    func onboardingStatus() async throws -> OnboardingStatus {
        try await api.get("/api/me/onboarding-status")
    }

    func logout() {
        tokenStore.clear()
    }
}
