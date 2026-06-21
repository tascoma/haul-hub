import SafariServices
import SwiftUI

private struct EmptyRequest: Encodable {}

private struct IdentitySessionResponse: Decodable {
    let clientSecret: String
    let url: String
}

struct BackgroundCheckOnboardingView: View {
    @EnvironmentObject private var session: AuthSession
    @Environment(\.apiClient) private var api

    @State private var status: ViewStatus = .idle
    @State private var error: String?
    @State private var safariURL: URL?

    private enum ViewStatus { case idle, loading, pending, error }

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                Text("Background check")
                    .font(HHFont.title)
                Text("We partner with Stripe Identity to verify your identity as part of our background screening. You'll complete a short document and selfie check.")
                    .font(HHFont.small)
                    .foregroundStyle(HHColor.ink500)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 24)

                VStack(alignment: .leading, spacing: 10) {
                    Text("What to have ready:")
                        .font(HHFont.smallBold)
                        .foregroundStyle(HHColor.ink700)
                    HStack(alignment: .top, spacing: 8) {
                        Text("•")
                        Text("Government-issued photo ID (driver's license or passport)")
                            .font(HHFont.small)
                            .foregroundStyle(HHColor.ink600)
                    }
                    HStack(alignment: .top, spacing: 8) {
                        Text("•")
                        Text("A device with a working camera for the selfie step")
                            .font(HHFont.small)
                            .foregroundStyle(HHColor.ink600)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(14)
                .background(HHColor.ink50)
                .overlay(
                    RoundedRectangle(cornerRadius: HHRadius.md)
                        .strokeBorder(HHColor.ink200, lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: HHRadius.md))
                .padding(.horizontal, 20)

                if status == .pending {
                    VStack(spacing: 8) {
                        Text("✓ Verification submitted")
                            .font(HHFont.smallBold)
                            .foregroundStyle(HHColor.success)
                        Text("We'll review it shortly. Tap Continue to proceed.")
                            .font(HHFont.small)
                            .foregroundStyle(HHColor.ink500)
                            .multilineTextAlignment(.center)
                    }
                    .padding(14)
                    .background(HHColor.successSoft)
                    .clipShape(RoundedRectangle(cornerRadius: HHRadius.md))
                    .padding(.horizontal, 20)
                }

                if let error {
                    Text(error)
                        .font(HHFont.small)
                        .foregroundStyle(HHColor.danger)
                        .padding(.horizontal, 20)
                }

                if status == .pending {
                    Button {
                        Task { await session.advance() }
                    } label: {
                        Text("Continue")
                    }
                    .buttonStyle(HHAccentButtonStyle())
                    .padding(.horizontal, 20)
                } else {
                    Button {
                        Task { await startVerification() }
                    } label: {
                        Text(status == .loading ? "Starting…" : "Start identity verification")
                    }
                    .buttonStyle(HHAccentButtonStyle())
                    .disabled(status == .loading)
                    .padding(.horizontal, 20)
                }

                if status == .pending {
                    Button("Already verified — refresh status") {
                        Task { await session.advance() }
                    }
                    .font(HHFont.small)
                    .foregroundStyle(HHColor.ink500)
                }
            }
            .padding(.top, 12)
        }
        .background(HHColor.ink50.ignoresSafeArea())
        .sheet(item: $safariURL) { url in
            SafariView(url: url)
                .ignoresSafeArea()
                .onDisappear {
                    // After the user returns from Safari, mark as pending so they
                    // can tap Continue. The webhook updates the backend status async.
                    if status == .loading || status == .idle {
                        status = .pending
                    }
                }
        }
    }

    private func startVerification() async {
        error = nil
        status = .loading
        do {
            let response: IdentitySessionResponse = try await api.post(
                "/api/me/stripe-identity-session", body: EmptyRequest()
            )
            guard let url = URL(string: response.url) else {
                throw APIError.invalidResponse
            }
            safariURL = url
        } catch {
            self.error = (error as? LocalizedError)?.errorDescription ?? "Could not start verification"
            status = .error
        }
    }
}

// MARK: - Helpers

private struct SafariView: UIViewControllerRepresentable {
    let url: URL
    func makeUIViewController(context: Context) -> SFSafariViewController {
        SFSafariViewController(url: url)
    }
    func updateUIViewController(_ vc: SFSafariViewController, context: Context) {}
}

extension URL: @retroactive Identifiable {
    public var id: String { absoluteString }
}
