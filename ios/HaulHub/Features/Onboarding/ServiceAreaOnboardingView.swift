import SwiftUI

private struct AddressCreate: Encodable {
    let line1: String
    let line2: String?
    let city: String
    let state: String
    let postalCode: String
    let country: String
}

private struct AddressResponse: Decodable {
    let id: String
}

private struct HaulerProfilePatch: Encodable {
    let homeBaseAddressId: String
    let serviceRadiusMiles: Int
}

private struct HaulerProfileResponse: Decodable {
    let userId: String
}

struct ServiceAreaOnboardingView: View {
    @EnvironmentObject private var session: AuthSession
    @Environment(\.apiClient) private var api

    @State private var line1 = ""
    @State private var line2 = ""
    @State private var city = ""
    @State private var stateCode = ""
    @State private var postalCode = ""
    @State private var radius: Double = 25
    @State private var submitting = false
    @State private var error: String?

    var body: some View {
        ScrollView {
            VStack(spacing: 18) {
                Text("Where do you haul?")
                    .font(HHFont.title)
                Text("We'll match you to loads within your service radius of this address.")
                    .font(HHFont.small)
                    .foregroundStyle(HHColor.ink500)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 24)

                VStack(spacing: 12) {
                    labeled("Street address") {
                        TextField("", text: $line1).textFieldStyle()
                    }
                    labeled("Apt / unit (optional)") {
                        TextField("", text: $line2).textFieldStyle()
                    }
                    HStack(spacing: 12) {
                        labeled("City") { TextField("", text: $city).textFieldStyle() }
                        labeled("State") {
                            TextField("OR", text: $stateCode)
                                .textInputAutocapitalization(.characters)
                                .autocorrectionDisabled()
                                .textFieldStyle()
                        }
                    }
                    labeled("ZIP code") {
                        TextField("", text: $postalCode).keyboardType(.numberPad).textFieldStyle()
                    }
                    labeled("Service radius: \(Int(radius)) miles") {
                        Slider(value: $radius, in: 5...250, step: 5)
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
                    Text(submitting ? "Saving…" : "Finish setup")
                }
                .buttonStyle(HHAccentButtonStyle())
                .disabled(submitting || line1.isEmpty || city.isEmpty || stateCode.isEmpty || postalCode.isEmpty)
                .padding(.horizontal, 20)
            }
            .padding(.top, 12)
        }
        .background(HHColor.ink50.ignoresSafeArea())
    }

    private func submit() async {
        error = nil
        submitting = true
        do {
            let addr: AddressResponse = try await api.post(
                "/api/me/addresses/raw",
                body: AddressCreate(
                    line1: line1,
                    line2: line2.isEmpty ? nil : line2,
                    city: city,
                    state: stateCode,
                    postalCode: postalCode,
                    country: "US"
                )
            )
            let _: HaulerProfileResponse = try await api.patch(
                "/api/me/hauler-profile",
                body: HaulerProfilePatch(
                    homeBaseAddressId: addr.id,
                    serviceRadiusMiles: Int(radius)
                )
            )
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
