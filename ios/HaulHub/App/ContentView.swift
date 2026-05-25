import SwiftUI

struct ContentView: View {
    @State private var hasEntered = false

    var body: some View {
        if hasEntered {
            MainTabView()
        } else {
            SplashView(hasEntered: $hasEntered)
        }
    }
}

#Preview {
    ContentView()
}
