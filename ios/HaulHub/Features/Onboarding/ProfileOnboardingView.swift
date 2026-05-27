import SwiftUI

private struct ProfilePatch: Encodable {
    let fullName: String
    let phone: String
}

struct ProfileOnboardingView: View {
    @EnvironmentObject private var session: AuthSession
    @Environment(\.apiClient) private var api

    @State private var fullName: String = ""
    @State private var phone: String = ""
    @State private var submitting = false
    @State private var error: String?

    var body: some View {
        ScrollView {
            VStack(spacing: 18) {
                Text("Tell us about you")
                    .font(HHFont.title)
                Text("We need a name and phone number on file before you can use Haul Hub.")
                    .font(HHFont.small)
                    .foregroundStyle(HHColor.ink500)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 24)

                VStack(spacing: 12) {
                    labeled("Full name") {
                        TextField("", text: $fullName)
                            .textInputAutocapitalization(.words)
                            .textFieldStyle()
                    }
                    labeled("Phone") {
                        TextField("+15551234567", text: $phone)
                            .keyboardType(.phonePad)
                            .textFieldStyle()
                    }
                }
                .padding(.horizontal, 20)

                if let error {
                    Text(error)
                        .font(HHFont.small)
                        .foregroundStyle(HHColor.danger)
                        .padding(.horizontal, 20)
                }

                Button {
                    Task { await submit() }
                } label: {
                    Text(submitting ? "Saving…" : "Continue")
                }
                .buttonStyle(HHAccentButtonStyle())
                .disabled(submitting || fullName.isEmpty || phone.isEmpty)
                .padding(.horizontal, 20)
            }
            .padding(.top, 12)
        }
        .background(HHColor.ink50.ignoresSafeArea())
        .onAppear {
            if let me = session.me {
                fullName = me.profile.fullName ?? ""
                phone = me.profile.phone ?? me.phone ?? ""
            }
        }
    }

    private func submit() async {
        error = nil
        submitting = true
        do {
            let _: Me = try await api.patch("/api/me", body: ProfilePatch(fullName: fullName, phone: phone))
            await session.advance()
        } catch {
            self.error = (error as? LocalizedError)?.errorDescription ?? "Could not save"
        }
        submitting = false
    }
}

@ViewBuilder
private func labeled<Content: View>(_ label: String, @ViewBuilder content: () -> Content) -> some View {
    VStack(alignment: .leading, spacing: 6) {
        Text(label).font(HHFont.smallBold).foregroundStyle(HHColor.ink700)
        content()
    }
}

private extension View {
    func textFieldStyle() -> some View {
        self
            .padding(12)
            .background(HHColor.paper)
            .overlay(
                RoundedRectangle(cornerRadius: HHRadius.sm)
                    .strokeBorder(HHColor.ink200, lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: HHRadius.sm))
    }
}
