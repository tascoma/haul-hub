import SwiftUI

struct SignupView: View {
    @EnvironmentObject private var session: AuthSession
    @Binding var showLogin: Bool

    @State private var email = ""
    @State private var password = ""
    @State private var fullName = ""
    @State private var wantsCustomer = true
    @State private var wantsHauler = false
    @State private var submitting = false
    @State private var localError: String?

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                HHLogomark(size: 40)
                    .padding(.top, 24)
                Text("Create your account")
                    .font(HHFont.title)
                Text("Post a load or claim one — Haul Hub matches you with a hauler in minutes.")
                    .font(HHFont.small)
                    .foregroundStyle(HHColor.ink500)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 24)

                VStack(spacing: 12) {
                    field("Full name", text: $fullName)
                    field("Email", text: $email, keyboard: .emailAddress, autocap: .never)
                    secureField("Password (min 8 chars)", text: $password)

                    rolePicker
                }
                .padding(.horizontal, 20)

                if let err = localError ?? session.error {
                    Text(err)
                        .font(HHFont.small)
                        .foregroundStyle(HHColor.danger)
                        .padding(.horizontal, 20)
                }

                Button {
                    Task { await submit() }
                } label: {
                    Text(submitting ? "Creating…" : "Sign up")
                }
                .buttonStyle(HHAccentButtonStyle())
                .disabled(submitting)
                .padding(.horizontal, 20)

                Button {
                    showLogin = true
                } label: {
                    Text("Already have an account? Log in")
                        .font(HHFont.small)
                        .foregroundStyle(HHColor.ink600)
                }
                .padding(.bottom, 24)
            }
        }
        .background(HHColor.ink50.ignoresSafeArea())
    }

    private var rolePicker: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("How will you use Haul Hub?")
                .font(HHFont.smallBold)
                .foregroundStyle(HHColor.ink700)
            Toggle(isOn: $wantsCustomer) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("I need things hauled").font(HHFont.bodyBold)
                    Text("Post loads and get matched with haulers.")
                        .font(HHFont.small).foregroundStyle(HHColor.ink500)
                }
            }
            Toggle(isOn: $wantsHauler) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("I want to haul for others").font(HHFont.bodyBold)
                    Text("Claim loads near you and get paid.")
                        .font(HHFont.small).foregroundStyle(HHColor.ink500)
                }
            }
        }
        .padding(14)
        .background(HHColor.paper)
        .overlay(
            RoundedRectangle(cornerRadius: HHRadius.md)
                .strokeBorder(HHColor.ink200, lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: HHRadius.md))
    }

    private func field(
        _ label: String,
        text: Binding<String>,
        keyboard: UIKeyboardType = .default,
        autocap: TextInputAutocapitalization = .sentences
    ) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label).font(HHFont.smallBold).foregroundStyle(HHColor.ink700)
            TextField("", text: text)
                .keyboardType(keyboard)
                .textInputAutocapitalization(autocap)
                .autocorrectionDisabled(keyboard == .emailAddress)
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

    private func submit() async {
        localError = nil
        var roles: [SignupRole] = []
        if wantsCustomer { roles.append(.customer) }
        if wantsHauler { roles.append(.hauler) }
        guard !roles.isEmpty else {
            localError = "Pick at least one role."
            return
        }
        guard password.count >= 8 else {
            localError = "Password must be at least 8 characters."
            return
        }
        submitting = true
        await session.signup(email: email, password: password, fullName: fullName.isEmpty ? nil : fullName, roles: roles)
        submitting = false
    }
}
