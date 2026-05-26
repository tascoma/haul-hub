import SwiftUI

@main
struct HaulHubApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(\.apiClient, APIClient())
        }
    }
}
