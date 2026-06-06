import SwiftUI

private enum BusinessType: String, CaseIterable, Codable, Identifiable {
    case individual, llc, corporation, partnership
    var id: String { rawValue }
    var label: String {
        switch self {
        case .individual: return "Individual"
        case .llc: return "LLC"
        case .corporation: return "Corporation"
        case .partnership: return "Partnership"
        }
    }
}

private struct HaulerProfilePatch: Encodable {
    let companyName: String?
    let businessType: BusinessType
    let yearsExperience: Int?
    let bio: String?
    let acceptsDisposalJobs: Bool
    let acceptsDonationRuns: Bool
    let acceptsHazardous: Bool
}

private struct HaulerProfileResponse: Decodable {
    let userId: String
}

struct HaulerProfileOnboardingView: View {
    @EnvironmentObject private var session: AuthSession
    @Environment(\.apiClient) private var api

    @State private var companyName = ""
    @State private var businessType: BusinessType = .individual
    @State private var yearsExperience = ""
    @State private var bio = ""
    @State private var acceptsDisposal = true
    @State private var acceptsDonation = true
    @State private var acceptsHazardous = false
    @State private var submitting = false
    @State private var error: String?

    var body: some View {
        ScrollView {
            VStack(spacing: 18) {
                Text("Set up your hauler profile")
                    .font(HHFont.title)
                Text("Tell customers a bit about your hauling operation.")
                    .font(HHFont.small)
                    .foregroundStyle(HHColor.ink500)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 24)

                VStack(spacing: 12) {
                    labeled("Company name (optional)") {
                        TextField("", text: $companyName).textFieldStyle()
                    }
                    labeled("Business type") {
                        Picker("", selection: $businessType) {
                            ForEach(BusinessType.allCases) { t in
                                Text(t.label).tag(t)
                            }
                        }
                        .pickerStyle(.segmented)
                    }
                    labeled("Years of hauling experience") {
                        TextField("", text: $yearsExperience)
                            .keyboardType(.numberPad)
                            .textFieldStyle()
                    }
                    labeled("Short bio (optional)") {
                        TextEditor(text: $bio)
                            .frame(minHeight: 80)
                            .padding(8)
                            .background(HHColor.paper)
                            .overlay(
                                RoundedRectangle(cornerRadius: HHRadius.sm)
                                    .strokeBorder(HHColor.ink200, lineWidth: 1)
                            )
                            .clipShape(RoundedRectangle(cornerRadius: HHRadius.sm))
                    }

                    VStack(alignment: .leading, spacing: 10) {
                        Text("What jobs will you take?")
                            .font(HHFont.smallBold)
                            .foregroundStyle(HHColor.ink700)
                        Toggle("Disposal jobs (junk → landfill / transfer station)", isOn: $acceptsDisposal)
                        Toggle("Donation runs", isOn: $acceptsDonation)
                        Toggle("Hazardous materials", isOn: $acceptsHazardous)
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
        let body = HaulerProfilePatch(
            companyName: companyName.isEmpty ? nil : companyName,
            businessType: businessType,
            yearsExperience: Int(yearsExperience),
            bio: bio.isEmpty ? nil : bio,
            acceptsDisposalJobs: acceptsDisposal,
            acceptsDonationRuns: acceptsDonation,
            acceptsHazardous: acceptsHazardous
        )
        do {
            let _: HaulerProfileResponse = try await api.patch("/api/me/hauler-profile", body: body)
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
