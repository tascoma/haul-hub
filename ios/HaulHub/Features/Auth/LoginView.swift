import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var session: AuthSession
    @Binding var showLogin: Bool

    @State private var email = ""
    @State private var password = ""
    @State private var submitting = false

    var body: some View {
        VStack(spacing: 20) {
            Spacer().frame(height: 20)
            HHLogomark(size: 40)
            Text("Welcome back")
                .font(HHFont.title)
            VStack(spacing: 12) {
                field("Email", text: $email, keyboard: .emailAddress)
                secureField("Password", text: $password)
            }
            .padding(.horizontal, 20)

            if let err = session.error {
                Text(err)
                    .font(HHFont.small)
                    .foregroundStyle(HHColor.danger)
                    .padding(.horizontal, 20)
            }

            Button {
                Task {
                    submitting = true
                    await session.login(email: email, password: password)
                    submitting = false
                }
            } label: {
                Text(submitting ? "Signing in…" : "Log in")
            }
            .buttonStyle(HHAccentButtonStyle())
            .disabled(submitting)
            .padding(.horizontal, 20)

            Button {
                showLogin = false
            } label: {
                Text("Need an account? Sign up")
                    .font(HHFont.small)
                    .foregroundStyle(HHColor.ink600)
            }
            Spacer()
        }
        .background(HHColor.ink50.ignoresSafeArea())
    }

    private func field(_ label: String, text: Binding<String>, keyboard: UIKeyboardType = .default) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label).font(HHFont.smallBold).foregroundStyle(HHColor.ink700)
            TextField("", text: text)
                .keyboardType(keyboard)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .padding(12)
                .background(HHColor.paper)
                .overlay(
                    RoundedRectangle(cornerRadius: HHRadius.sm)
                        .strokeBorder(HHColor.ink200, lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: HHRadius.sm))
        }
    }

    private func secureField(_ label: String, text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label).font(HHFont.smallBold).foregroundStyle(HHColor.ink700)
            SecureField("", text: text)
                .padding(12)
                .background(HHColor.paper)
                .overlay(
                    RoundedRectangle(cornerRadius: HHRadius.sm)
                        .strokeBorder(HHColor.ink200, lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: HHRadius.sm))
        }
    }
}
