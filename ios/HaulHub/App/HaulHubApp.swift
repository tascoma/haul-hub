import SwiftUI

@main
struct HaulHubApp: App {
    @StateObject private var session = AuthSession()

    var body: some Scene {
        WindowGroup {
            ContentView()
                // Share the same APIClient (and its in-memory TokenStore) that
                // AuthSession uses, so the token is available to all views the
                // moment login or signup sets it — no Keychain read required.
                .environment(\.apiClient, session.apiClient)
                .environmentObject(session)
                .task {
                    await session.bootstrap()
                }
        }
    }
}
