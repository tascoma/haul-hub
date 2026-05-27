import SwiftUI

// MARK: - Private request body types

private struct PersonalPatch: Encodable {
    let fullName: String
    let displayName: String?
    let phone: String?
    let bio: String?
}

private struct PrefsPatch: Encodable {
    let preferredLanguage: String
    let timezone: String
    let marketingOptIn: Bool
}

private struct PwPatch: Encodable {
    let currentPassword: String
    let newPassword: String
}

private enum BizType: String, CaseIterable, Codable, Identifiable {
    case individual, llc, corporation, partnership
    var id: String { rawValue }
    var label: String {
        switch self {
        case .individual: return "Individual / sole proprietor"
        case .llc: return "LLC"
        case .corporation: return "Corporation"
        case .partnership: return "Partnership"
        }
    }
}

private struct HaulerPatch: Encodable {
    let companyName: String?
    let businessType: BizType
    let yearsExperience: Int?
    let bio: String?
    let serviceRadiusMiles: Int
    let acceptsDisposalJobs: Bool
    let acceptsDonationRuns: Bool
    let acceptsHazardous: Bool
    let currentlyAvailable: Bool
}

// MARK: - Save state

private enum SaveStatus: Equatable {
    case idle, saving
    case saved(String)
    case error(String)

    var isSaving: Bool { self == .saving }

    var message: String? {
        switch self {
        case .saved(let m): return m
        case .error(let m): return m
        default: return nil
        }
    }

    var isError: Bool {
        if case .error = self { return true }
        return false
    }
}

// MARK: - Constants

private let kLanguages: [(code: String, name: String)] = [
    ("en", "English"), ("es", "Spanish"), ("fr", "French"),
    ("pt", "Portuguese"), ("zh", "Chinese"),
]

private let kTimezones = [
    "America/New_York", "America/Chicago", "America/Denver",
    "America/Los_Angeles", "America/Phoenix", "America/Anchorage",
    "Pacific/Honolulu",
]

// MARK: - ProfileView

struct ProfileView: View {
    @EnvironmentObject private var session: AuthSession
    @Environment(\.apiClient) private var api

    // ── Personal info ────────────────────────────────────────────────────────
    @State private var fullName = ""
    @State private var displayName = ""
    @State private var phone = ""
    @State private var bio = ""
    @State private var personalStatus: SaveStatus = .idle

    // ── Preferences ──────────────────────────────────────────────────────────
    @State private var language = "en"
    @State private var timezone = "America/Los_Angeles"
    @State private var marketingOptIn = false
    @State private var prefsStatus: SaveStatus = .idle

    // ── Password ─────────────────────────────────────────────────────────────
    @State private var currentPw = ""
    @State private var newPw = ""
    @State private var confirmPw = ""
    @State private var pwStatus: SaveStatus = .idle

    // ── Hauler ───────────────────────────────────────────────────────────────
    @State private var haulerProfile: HaulerProfileData? = nil
    @State private var haulerLoaded = false
    @State private var companyName = ""
    @State private var bizType: BizType = .individual
    @State private var yearsExp = ""
    @State private var haulerBio = ""
    @State private var serviceRadius = "25"
    @State private var acceptsDisposal = true
    @State private var acceptsDonation = true
    @State private var acceptsHazardous = false
    @State private var currentlyAvailable = false
    @State private var haulerStatus: SaveStatus = .idle

    private var me: Me? { session.me }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    headerCard
                    personalCard
                    prefsCard
                    passwordCard
                    if me?.profile.haulerEnabled == true {
                        haulerCard
                    }
                    signOutButton
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 20)
            }
            .background(HHColor.ink50.ignoresSafeArea())
            .navigationTitle("Profile")
        }
        .onAppear { seedForm() }
        .task {
            guard me?.profile.haulerEnabled == true, !haulerLoaded else { return }
            await loadHaulerProfile()
        }
    }

    // MARK: - Header card

    private var headerCard: some View {
        HStack(spacing: 14) {
            HHAvatar(initials: initials, size: 56, dark: true)

            VStack(alignment: .leading, spacing: 4) {
                if let name = me?.profile.fullName, !name.isEmpty {
                    Text(name)
                        .font(HHFont.titleSm)
                        .foregroundStyle(HHColor.ink900)
                        .lineLimit(1)
                } else {
                    Text("Add your name")
                        .font(HHFont.titleSm)
                        .foregroundStyle(HHColor.ink400)
                }

                if let dn = me?.profile.displayName, !dn.isEmpty {
                    Text("\u{201C}\(dn)\u{201D}")
                        .font(HHFont.small)
                        .foregroundStyle(HHColor.ink500)
                }

                Text(me?.email ?? "")
                    .font(HHFont.small)
                    .foregroundStyle(HHColor.ink500)
                    .lineLimit(1)

                HStack(spacing: 6) {
                    if me?.profile.shipperEnabled == true {
                        HHPill(text: "Shipper", style: .info)
                    }
                    if me?.profile.haulerEnabled == true {
                        HHPill(text: "Hauler", style: .accent)
                        if haulerProfile?.verifiedAt != nil {
                            HHPill(text: "Verified", style: .success)
                        }
                    }
                }
                .padding(.top, 2)
            }

            Spacer()
        }
        .hhCard()
    }

    // MARK: - Personal info card

    private var personalCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Personal Info")
                .font(HHFont.titleSm)
                .foregroundStyle(HHColor.ink900)

            hhLabeled("Full name") {
                TextField("Your legal name", text: $fullName)
                    .textInputAutocapitalization(.words)
                    .hhField()
            }

            hhLabeled("Display name (optional)") {
                TextField("How you appear to others", text: $displayName)
                    .textInputAutocapitalization(.words)
                    .hhField()
            }

            hhLabeled("Phone number") {
                TextField("+1 555 000 0000", text: $phone)
                    .keyboardType(.phonePad)
                    .hhField()
            }

            hhLabeled("Bio (optional)") {
                TextEditor(text: $bio)
                    .frame(minHeight: 80)
                    .padding(8)
                    .hhEditorField()
            }

            hhSaveRow(status: personalStatus, label: "Save personal info", accent: true) {
                Task { await savePersonal() }
            }
        }
        .hhCard()
    }

    // MARK: - Preferences card

    private var prefsCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Preferences")
                .font(HHFont.titleSm)
                .foregroundStyle(HHColor.ink900)

            hhLabeled("Language") {
                Picker("Language", selection: $language) {
                    ForEach(kLanguages, id: \.code) { lang in
                        Text(lang.name).tag(lang.code)
                    }
                }
                .pickerStyle(.menu)
                .hhPickerField()
            }

            hhLabeled("Timezone") {
                Picker("Timezone", selection: $timezone) {
                    ForEach(kTimezones, id: \.self) { tz in
                        Text(
                            tz
                                .replacingOccurrences(of: "America/", with: "")
                                .replacingOccurrences(of: "_", with: " ")
                        )
                        .tag(tz)
                    }
                }
                .pickerStyle(.menu)
                .hhPickerField()
            }

            Toggle(isOn: $marketingOptIn) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Marketing emails")
                        .font(HHFont.smallBold)
                        .foregroundStyle(HHColor.ink900)
                    Text("Receive tips, load alerts, and platform news.")
                        .font(HHFont.micro)
                        .foregroundStyle(HHColor.ink500)
                }
            }
            .tint(HHColor.accent)

            hhSaveRow(status: prefsStatus, label: "Save preferences", accent: false) {
                Task { await savePrefs() }
            }
        }
        .hhCard()
    }

    // MARK: - Change password card

    private var passwordCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Change Password")
                .font(HHFont.titleSm)
                .foregroundStyle(HHColor.ink900)

            hhLabeled("Current password") {
                SecureField("", text: $currentPw)
                    .textContentType(.password)
                    .hhField()
            }

            hhLabeled("New password (min 8 chars)") {
                SecureField("", text: $newPw)
                    .textContentType(.newPassword)
                    .hhField()
            }

            hhLabeled("Confirm new password") {
                SecureField("", text: $confirmPw)
                    .textContentType(.newPassword)
                    .hhField()
            }

            hhSaveRow(status: pwStatus, label: "Change password", accent: false) {
                Task { await savePassword() }
            }
        }
        .hhCard()
    }

    // MARK: - Hauler settings card

    private var haulerCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Text("Hauler Settings")
                    .font(HHFont.titleSm)
                    .foregroundStyle(HHColor.ink900)
                Spacer()
                if let hp = haulerProfile {
                    HHPill(
                        text: hp.verifiedAt != nil ? "Verified" : "Pending",
                        style: hp.verifiedAt != nil ? .success : .warning
                    )
                }
            }

            hhLabeled("Company name (optional)") {
                TextField("Your business name", text: $companyName)
                    .hhField()
            }

            hhLabeled("Business type") {
                Picker("Business type", selection: $bizType) {
                    ForEach(BizType.allCases) { t in
                        Text(t.label).tag(t)
                    }
                }
                .pickerStyle(.menu)
                .hhPickerField()
            }

            HStack(spacing: 12) {
                hhLabeled("Years experience") {
                    TextField("e.g. 5", text: $yearsExp)
                        .keyboardType(.numberPad)
                        .hhField()
                }
                hhLabeled("Radius (miles)") {
                    TextField("25", text: $serviceRadius)
                        .keyboardType(.numberPad)
                        .hhField()
                }
            }

            hhLabeled("Hauler bio (optional)") {
                TextEditor(text: $haulerBio)
                    .frame(minHeight: 80)
                    .padding(8)
                    .hhEditorField()
            }

            VStack(alignment: .leading, spacing: 10) {
                Text("Job preferences")
                    .font(HHFont.smallBold)
                    .foregroundStyle(HHColor.ink700)

                Toggle("Disposal jobs (junk → landfill)", isOn: $acceptsDisposal)
                Toggle("Donation runs", isOn: $acceptsDonation)
                Toggle("Hazardous materials", isOn: $acceptsHazardous)

                Divider()

                Toggle("Currently available for new loads", isOn: $currentlyAvailable)
            }
            .padding(14)
            .background(HHColor.paper)
            .overlay(
                RoundedRectangle(cornerRadius: HHRadius.md)
                    .strokeBorder(HHColor.ink200, lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: HHRadius.md))
            .tint(HHColor.accent)

            hhSaveRow(status: haulerStatus, label: "Save hauler settings", accent: true) {
                Task { await saveHauler() }
            }
        }
        .hhCard()
    }

    // MARK: - Sign-out button

    private var signOutButton: some View {
        Button("Sign Out") { session.logout() }
            .buttonStyle(HHGhostButtonStyle())
            .padding(.bottom, 4)
    }

    // MARK: - Shared sub-view helpers

    @ViewBuilder
    private func hhLabeled<Content: View>(
        _ title: String,
        @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(HHFont.smallBold)
                .foregroundStyle(HHColor.ink700)
            content()
        }
    }

    @ViewBuilder
    private func hhSaveRow(
        status: SaveStatus,
        label: String,
        accent: Bool,
        action: @escaping () -> Void
    ) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            if accent {
                Button(status.isSaving ? "Saving…" : label) { action() }
                    .buttonStyle(HHAccentButtonStyle(height: 44))
                    .disabled(status.isSaving)
            } else {
                Button(status.isSaving ? "Saving…" : label) { action() }
                    .buttonStyle(HHDarkButtonStyle(height: 44))
                    .disabled(status.isSaving)
            }
            if let msg = status.message {
                Text(msg)
                    .font(HHFont.micro)
                    .foregroundStyle(status.isError ? HHColor.danger : HHColor.success)
            }
        }
    }

    // MARK: - Computed helpers

    private var initials: String {
        let source = (me?.profile.fullName?.trimmingCharacters(in: .whitespaces))
                  .flatMap { $0.isEmpty ? nil : $0 }
                  ?? me?.email ?? "?"
        let parts = source.split(separator: " ").prefix(2)
        guard !parts.isEmpty else { return String(source.prefix(1)).uppercased() }
        return parts.compactMap { $0.first.map { String($0).uppercased() } }.joined()
    }

    // MARK: - Data loading

    private func seedForm() {
        guard let p = me?.profile else { return }
        fullName    = p.fullName ?? ""
        displayName = p.displayName ?? ""
        phone       = p.phone ?? me?.phone ?? ""
        bio         = p.bio ?? ""
        language    = p.preferredLanguage
        timezone    = p.timezone
        marketingOptIn = p.marketingOptIn
    }

    private func loadHaulerProfile() async {
        defer { haulerLoaded = true }
        do {
            let hp: HaulerProfileData = try await api.get("/api/me/hauler-profile")
            haulerProfile = hp
            companyName       = hp.companyName ?? ""
            if let btStr = hp.businessType, let bt = BizType(rawValue: btStr) { bizType = bt }
            yearsExp          = hp.yearsExperience.map { String($0) } ?? ""
            haulerBio         = hp.bio ?? ""
            serviceRadius     = String(hp.serviceRadiusMiles)
            acceptsDisposal   = hp.acceptsDisposalJobs
            acceptsDonation   = hp.acceptsDonationRuns
            acceptsHazardous  = hp.acceptsHazardous
            currentlyAvailable = hp.currentlyAvailable
        } catch {
            // Hauler profile not yet created — form defaults remain
        }
    }

    // MARK: - Save handlers

    private func savePersonal() async {
        personalStatus = .saving
        do {
            let _: Me = try await api.patch("/api/me", body: PersonalPatch(
                fullName:    fullName,
                displayName: displayName.isEmpty ? nil : displayName,
                phone:       phone.isEmpty ? nil : phone,
                bio:         bio.isEmpty ? nil : bio
            ))
            await session.refresh()
            personalStatus = .saved("Personal info saved.")
            try? await Task.sleep(for: .seconds(3))
            if case .saved = personalStatus { personalStatus = .idle }
        } catch {
            personalStatus = .error(apiMsg(error))
        }
    }

    private func savePrefs() async {
        prefsStatus = .saving
        do {
            let _: Me = try await api.patch("/api/me", body: PrefsPatch(
                preferredLanguage: language,
                timezone:          timezone,
                marketingOptIn:    marketingOptIn
            ))
            await session.refresh()
            prefsStatus = .saved("Preferences saved.")
            try? await Task.sleep(for: .seconds(3))
            if case .saved = prefsStatus { prefsStatus = .idle }
        } catch {
            prefsStatus = .error(apiMsg(error))
        }
    }

    private func savePassword() async {
        guard !newPw.isEmpty else {
            pwStatus = .error("Enter a new password.")
            return
        }
        guard newPw == confirmPw else {
            pwStatus = .error("New passwords don't match.")
            return
        }
        guard newPw.count >= 8 else {
            pwStatus = .error("Password must be at least 8 characters.")
            return
        }
        pwStatus = .saving
        do {
            try await api.patchVoid("/api/me/password", body: PwPatch(
                currentPassword: currentPw,
                newPassword:     newPw
            ))
            currentPw = ""; newPw = ""; confirmPw = ""
            pwStatus = .saved("Password changed.")
            try? await Task.sleep(for: .seconds(3))
            if case .saved = pwStatus { pwStatus = .idle }
        } catch {
            pwStatus = .error(apiMsg(error))
        }
    }

    private func saveHauler() async {
        haulerStatus = .saving
        let body = HaulerPatch(
            companyName:         companyName.isEmpty ? nil : companyName,
            businessType:        bizType,
            yearsExperience:     Int(yearsExp),
            bio:                 haulerBio.isEmpty ? nil : haulerBio,
            serviceRadiusMiles:  Int(serviceRadius) ?? 25,
            acceptsDisposalJobs: acceptsDisposal,
            acceptsDonationRuns: acceptsDonation,
            acceptsHazardous:    acceptsHazardous,
            currentlyAvailable:  currentlyAvailable
        )
        do {
            let hp: HaulerProfileData = try await api.patch("/api/me/hauler-profile", body: body)
            haulerProfile = hp
            haulerStatus = .saved("Hauler settings saved.")
            try? await Task.sleep(for: .seconds(3))
            if case .saved = haulerStatus { haulerStatus = .idle }
        } catch {
            haulerStatus = .error(apiMsg(error))
        }
    }

    private func apiMsg(_ err: Error) -> String {
        (err as? LocalizedError)?.errorDescription ?? "Save failed — please try again."
    }
}

// MARK: - File-scoped view modifiers

private extension View {
    /// Standard single-line text field style.
    func hhField() -> some View {
        padding(12)
            .background(HHColor.paper)
            .overlay(
                RoundedRectangle(cornerRadius: HHRadius.sm)
                    .strokeBorder(HHColor.ink200, lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: HHRadius.sm))
    }

    /// Multi-line TextEditor style (no inner padding — caller sets it).
    func hhEditorField() -> some View {
        background(HHColor.paper)
            .overlay(
                RoundedRectangle(cornerRadius: HHRadius.sm)
                    .strokeBorder(HHColor.ink200, lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: HHRadius.sm))
    }

    /// Menu-style Picker wrapper.
    func hhPickerField() -> some View {
        frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(HHColor.paper)
            .overlay(
                RoundedRectangle(cornerRadius: HHRadius.sm)
                    .strokeBorder(HHColor.ink200, lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: HHRadius.sm))
    }
}

#Preview {
    ProfileView()
        .environmentObject(AuthSession())
}
