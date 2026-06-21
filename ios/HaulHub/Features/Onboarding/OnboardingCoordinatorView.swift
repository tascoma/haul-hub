import SwiftUI

/// Switches between the right onboarding step view based on AuthSession.phase.
/// Step views call `session.advance()` after success, which re-fetches the
/// onboarding-status endpoint and updates the phase, which re-renders us.
struct OnboardingCoordinatorView: View {
    let step: OnboardingStep

    var body: some View {
        NavigationStack {
            content
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .topBarTrailing) {
                        LogoutButton()
                    }
                }
        }
    }

    @ViewBuilder private var content: some View {
        switch step {
        case .profile: ProfileOnboardingView()
        case .haulerProfile: HaulerProfileOnboardingView()
        case .haulerVehicle: VehicleOnboardingView()
        case .haulerServiceArea: ServiceAreaOnboardingView()
        case .haulerDocuments: DocumentsOnboardingView()
        case .haulerVerification: BackgroundCheckOnboardingView()
        case .done: ProgressView()  // Should not be reached; root will swap to ready.
        }
    }
}

private struct LogoutButton: View {
    @EnvironmentObject private var session: AuthSession
    var body: some View {
        Button("Sign out") { session.logout() }
            .font(HHFont.small)
            .foregroundStyle(HHColor.ink600)
    }
}
