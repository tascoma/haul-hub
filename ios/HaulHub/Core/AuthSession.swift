import Foundation
import SwiftUI

/// Root auth state: who is signed in, where they are in onboarding, and the
/// actions to mutate that state. Held as a single source of truth at the app root.
@MainActor
final class AuthSession: ObservableObject {
    enum Phase {
        case loading            // bootstrapping: checking keychain + fetching /me
        case signedOut
        case onboarding(OnboardingStep)
        case ready(Me)
    }

    @Published private(set) var phase: Phase = .loading
    @Published private(set) var me: Me?
    @Published var error: String?

    private let client: AuthClient

    /// The shared API client — inject this into the SwiftUI environment so every
    /// view uses the same in-memory token store that gets populated on login.
    var apiClient: APIClient { client.api }

    init(client: AuthClient = AuthClient()) {
        self.client = client
    }

    func bootstrap() async {
        guard KeychainStore.loadToken() != nil else {
            phase = .signedOut
            return
        }
        await refresh()
    }

    func signup(email: String, password: String, fullName: String?, roles: [SignupRole]) async {
        error = nil
        do {
            let me = try await client.signup(
                email: email, password: password, fullName: fullName, roles: roles
            )
            self.me = me
            await advance()
        } catch {
            self.error = (error as? LocalizedError)?.errorDescription ?? "Sign up failed"
            phase = .signedOut
        }
    }

    func login(email: String, password: String) async {
        error = nil
        do {
            let me = try await client.login(email: email, password: password)
            self.me = me
            await advance()
        } catch {
            self.error = (error as? LocalizedError)?.errorDescription ?? "Login failed"
            phase = .signedOut
        }
    }

    /// Re-fetch /me + /me/onboarding-status and update the phase accordingly.
    /// Call this after any onboarding step completes.
    func advance() async {
        do {
            let me = try await client.me()
            self.me = me
            let status = try await client.onboardingStatus()
            if status.nextStep == .done {
                phase = .ready(me)
            } else {
                phase = .onboarding(status.nextStep)
            }
        } catch {
            self.error = (error as? LocalizedError)?.errorDescription ?? "Could not refresh"
        }
    }

    func refresh() async {
        await advance()
    }

    func logout() {
        client.logout()
        me = nil
        phase = .signedOut
    }
}
