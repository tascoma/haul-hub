import SwiftUI
import UIKit
import StripePaymentSheet
import StripePayments

/// Shipper screen to add/replace the default card (via Stripe PaymentSheet) and
/// edit the billing address. Mirrors the web PaymentMethodPage.
struct PaymentMethodView: View {
    @EnvironmentObject private var session: AuthSession
    @Environment(\.apiClient) private var api

    // ── Card ─────────────────────────────────────────────────────────────────
    @State private var savedCard: PaymentMethodInfo? = nil
    @State private var cardLoaded = false
    @State private var cardStatus: ActionStatus = .idle

    // ── Billing address ──────────────────────────────────────────────────────
    @State private var sameAsHome = true
    @State private var line1 = ""
    @State private var city = ""
    @State private var state = ""
    @State private var zip = ""
    @State private var billingStatus: ActionStatus = .idle

    private var payments: PaymentsClient { PaymentsClient(api: api) }
    private var me: Me? { session.me }

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                cardCard
                billingCard
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 20)
        }
        .background(HHColor.ink50.ignoresSafeArea())
        .navigationTitle("Payment Method")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear { seedBilling() }
        .task {
            guard !cardLoaded else { return }
            await loadSavedCard()
        }
    }

    // MARK: - Card card

    private var cardCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Default Card")
                .font(HHFont.titleSm)
                .foregroundStyle(HHColor.ink900)

            if let card = savedCard {
                HStack(spacing: 12) {
                    ZStack {
                        RoundedRectangle(cornerRadius: HHRadius.sm)
                            .fill(HHColor.ink900)
                            .frame(width: 46, height: 32)
                        Image(systemName: "creditcard.fill")
                            .foregroundStyle(.white)
                    }
                    VStack(alignment: .leading, spacing: 2) {
                        Text(card.display)
                            .font(HHFont.smallBold)
                            .foregroundStyle(HHColor.ink900)
                        Text("Expires \(card.expiryDisplay)")
                            .font(HHFont.micro)
                            .foregroundStyle(HHColor.ink500)
                    }
                    Spacer()
                }
            } else {
                Text("No card on file. Add one to pay for loads you post.")
                    .font(HHFont.small)
                    .foregroundStyle(HHColor.ink500)
            }

            Button(cardStatus.isWorking
                   ? "Opening…"
                   : (savedCard == nil ? "Add card" : "Replace card")) {
                Task { await addCard() }
            }
            .buttonStyle(HHAccentButtonStyle(height: 44))
            .disabled(cardStatus.isWorking)

            if let msg = cardStatus.message {
                Text(msg)
                    .font(HHFont.micro)
                    .foregroundStyle(cardStatus.isError ? HHColor.danger : HHColor.success)
            }
        }
        .hhCard()
    }

    // MARK: - Billing address card

    private var billingCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Billing Address")
                .font(HHFont.titleSm)
                .foregroundStyle(HHColor.ink900)

            Toggle(isOn: $sameAsHome) {
                Text("Same as home address")
                    .font(HHFont.smallBold)
                    .foregroundStyle(HHColor.ink900)
            }
            .tint(HHColor.accent)

            if !sameAsHome {
                pmField("Street address", text: $line1)
                HStack(spacing: 12) {
                    pmField("City", text: $city)
                    pmField("State", text: $state)
                }
                pmField("ZIP", text: $zip, keyboard: .numberPad)
            }

            Button(billingStatus.isWorking ? "Saving…" : "Save billing address") {
                Task { await saveBilling() }
            }
            .buttonStyle(HHDarkButtonStyle(height: 44))
            .disabled(billingStatus.isWorking)

            if let msg = billingStatus.message {
                Text(msg)
                    .font(HHFont.micro)
                    .foregroundStyle(billingStatus.isError ? HHColor.danger : HHColor.success)
            }
        }
        .hhCard()
    }

    @ViewBuilder
    private func pmField(
        _ title: String,
        text: Binding<String>,
        keyboard: UIKeyboardType = .default
    ) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(HHFont.smallBold)
                .foregroundStyle(HHColor.ink700)
            TextField(title, text: text)
                .keyboardType(keyboard)
                .padding(12)
                .background(HHColor.paper)
                .overlay(
                    RoundedRectangle(cornerRadius: HHRadius.sm)
                        .strokeBorder(HHColor.ink200, lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: HHRadius.sm))
        }
    }

    // MARK: - Card actions

    private func loadSavedCard() async {
        defer { cardLoaded = true }
        savedCard = try? await payments.paymentMethod()
    }

    private func addCard() async {
        cardStatus = .working
        do {
            let clientSecret = try await payments.createSetupIntent()

            var config = PaymentSheet.Configuration()
            config.merchantDisplayName = "Haul Hub"
            let sheet = PaymentSheet(
                setupIntentClientSecret: clientSecret,
                configuration: config
            )

            guard let presenter = Self.topViewController() else {
                cardStatus = .error("Could not present the card form.")
                return
            }

            let result: PaymentSheetResult = await withCheckedContinuation { cont in
                sheet.present(from: presenter) { cont.resume(returning: $0) }
            }

            switch result {
            case .completed:
                let pmId = try await retrievePaymentMethodId(clientSecret: clientSecret)
                savedCard = try await payments.savePaymentMethod(pmId)
                cardStatus = .saved("Card saved.")
                try? await Task.sleep(for: .seconds(3))
                if case .saved = cardStatus { cardStatus = .idle }
            case .canceled:
                cardStatus = .idle
            case .failed(let error):
                cardStatus = .error(error.localizedDescription)
            }
        } catch {
            cardStatus = .error(apiMsg(error))
        }
    }

    /// Re-fetch the confirmed SetupIntent to recover its PaymentMethod id, which
    /// the existing POST /me/payment-method endpoint needs to set the default.
    private func retrievePaymentMethodId(clientSecret: String) async throws -> String {
        try await withCheckedThrowingContinuation { cont in
            STPAPIClient.shared.retrieveSetupIntent(withClientSecret: clientSecret) { intent, error in
                if let error {
                    cont.resume(throwing: error)
                } else if let pmId = intent?.paymentMethodID {
                    cont.resume(returning: pmId)
                } else {
                    cont.resume(throwing: APIError.invalidResponse)
                }
            }
        }
    }

    // MARK: - Billing actions

    private func seedBilling() {
        guard let p = me?.profile else { return }
        sameAsHome = p.billingSameAsHome
        line1 = p.billingAddressLine1 ?? ""
        city  = p.billingAddressCity ?? ""
        state = p.billingAddressState ?? ""
        zip   = p.billingAddressZip ?? ""
    }

    private func saveBilling() async {
        billingStatus = .working
        let body = BillingAddressUpdate(
            billingSameAsHome: sameAsHome,
            billingAddressLine1: sameAsHome ? nil : (line1.isEmpty ? nil : line1),
            billingAddressCity:  sameAsHome ? nil : (city.isEmpty ? nil : city),
            billingAddressState: sameAsHome ? nil : (state.isEmpty ? nil : state),
            billingAddressZip:   sameAsHome ? nil : (zip.isEmpty ? nil : zip)
        )
        do {
            try await payments.updateBilling(body)
            await session.refresh()
            billingStatus = .saved("Billing address saved.")
            try? await Task.sleep(for: .seconds(3))
            if case .saved = billingStatus { billingStatus = .idle }
        } catch {
            billingStatus = .error(apiMsg(error))
        }
    }

    // MARK: - Helpers

    private func apiMsg(_ err: Error) -> String {
        (err as? LocalizedError)?.errorDescription ?? "Something went wrong — please try again."
    }

    private static func topViewController() -> UIViewController? {
        let scene = UIApplication.shared.connectedScenes
            .first { $0.activationState == .foregroundActive } as? UIWindowScene
        guard var top = scene?.keyWindow?.rootViewController else { return nil }
        while let presented = top.presentedViewController { top = presented }
        return top
    }
}

// MARK: - Action status

private enum ActionStatus: Equatable {
    case idle, working
    case saved(String)
    case error(String)

    var isWorking: Bool { self == .working }

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
