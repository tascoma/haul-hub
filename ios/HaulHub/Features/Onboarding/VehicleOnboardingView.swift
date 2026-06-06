import SwiftUI

private enum VehicleType: String, CaseIterable, Codable, Identifiable {
    case pickup
    case pickupWithTrailer = "pickup_with_trailer"
    case flatbed
    case boxTruck = "box_truck"
    case cargoVan = "cargo_van"
    case semi
    case dumpTruck = "dump_truck"
    case rollOff = "roll_off"
    case other
    var id: String { rawValue }
    var label: String {
        switch self {
        case .pickup: return "Pickup truck"
        case .pickupWithTrailer: return "Pickup w/ trailer"
        case .flatbed: return "Flatbed"
        case .boxTruck: return "Box truck"
        case .cargoVan: return "Cargo van"
        case .semi: return "Semi"
        case .dumpTruck: return "Dump truck"
        case .rollOff: return "Roll-off"
        case .other: return "Other"
        }
    }
}

private struct VehicleCreate: Encodable {
    let nickname: String?
    let vehicleType: VehicleType
    let make: String?
    let model: String?
    let year: Int?
    let maxPayloadLbs: Int?
    let hasLiftGate: Bool
    let hasDolly: Bool
    let hasStraps: Bool
    let hasBlankets: Bool
    let isDefault: Bool
}

private struct VehicleResponse: Decodable {
    let id: String
}

struct VehicleOnboardingView: View {
    @EnvironmentObject private var session: AuthSession
    @Environment(\.apiClient) private var api

    @State private var nickname = ""
    @State private var vehicleType: VehicleType = .pickup
    @State private var make = ""
    @State private var model = ""
    @State private var year = ""
    @State private var maxPayload = ""
    @State private var hasLiftGate = false
    @State private var hasDolly = false
    @State private var hasStraps = false
    @State private var hasBlankets = false
    @State private var submitting = false
    @State private var error: String?

    var body: some View {
        ScrollView {
            VStack(spacing: 18) {
                Text("Add your vehicle")
                    .font(HHFont.title)
                Text("We use this to match you with loads you can actually carry. You can add more later.")
                    .font(HHFont.small)
                    .foregroundStyle(HHColor.ink500)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 24)

                VStack(spacing: 12) {
                    labeled("Nickname (optional)") {
                        TextField("e.g. Big Blue", text: $nickname).textFieldStyle()
                    }
                    labeled("Vehicle type") {
                        Picker("", selection: $vehicleType) {
                            ForEach(VehicleType.allCases) { v in
                                Text(v.label).tag(v)
                            }
                        }
                        .pickerStyle(.menu)
                        .padding(8)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(HHColor.paper)
                        .overlay(
                            RoundedRectangle(cornerRadius: HHRadius.sm)
                                .strokeBorder(HHColor.ink200, lineWidth: 1)
                        )
                        .clipShape(RoundedRectangle(cornerRadius: HHRadius.sm))
                    }
                    HStack(spacing: 12) {
                        labeled("Make") { TextField("", text: $make).textFieldStyle() }
                        labeled("Model") { TextField("", text: $model).textFieldStyle() }
                    }
                    HStack(spacing: 12) {
                        labeled("Year") {
                            TextField("", text: $year).keyboardType(.numberPad).textFieldStyle()
                        }
                        labeled("Max payload (lbs)") {
                            TextField("", text: $maxPayload).keyboardType(.numberPad).textFieldStyle()
                        }
                    }
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Equipment")
                            .font(HHFont.smallBold)
                            .foregroundStyle(HHColor.ink700)
                        Toggle("Lift gate", isOn: $hasLiftGate)
                        Toggle("Dolly", isOn: $hasDolly)
                        Toggle("Tie-down straps", isOn: $hasStraps)
                        Toggle("Moving blankets", isOn: $hasBlankets)
                    }
                    .padding(14)
                    .background(HHColor.paper)
                    .overlay(
                        RoundedRectangle(cornerRadius: HHRadius.md)
                            .strokeBorder(HHColor.ink200, lineWidth: 1)
                    )
                    .clipShape(RoundedRectangle(cornerRadius: HHRadius.md))
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
                .disabled(submitting)
                .padding(.horizontal, 20)
            }
            .padding(.top, 12)
        }
        .background(HHColor.ink50.ignoresSafeArea())
    }

    private func submit() async {
        error = nil
        submitting = true
        let body = VehicleCreate(
            nickname: nickname.isEmpty ? nil : nickname,
            vehicleType: vehicleType,
            make: make.isEmpty ? nil : make,
            model: model.isEmpty ? nil : model,
            year: Int(year),
            maxPayloadLbs: Int(maxPayload),
            hasLiftGate: hasLiftGate,
            hasDolly: hasDolly,
            hasStraps: hasStraps,
            hasBlankets: hasBlankets,
            isDefault: true
        )
        do {
            let _: VehicleResponse = try await api.post("/api/me/vehicles", body: body)
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
