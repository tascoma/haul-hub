import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var session: AuthSession
    @State private var showLogin = false

    var body: some View {
        switch session.phase {
        case .loading:
            ProgressView()
                .progressViewStyle(.circular)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(HHColor.ink50.ignoresSafeArea())

        case .signedOut:
            if showLogin {
                LoginView(showLogin: $showLogin)
            } else {
                SignupView(showLogin: $showLogin)
            }

        case .onboarding(let step):
            OnboardingCoordinatorView(step: step)

        case .ready:
            MainTabView()
        }
    }
}

#Preview {
    ContentView().environmentObject(AuthSession())
}
