import SwiftUI

struct LoadDetailView: View {
    let load: APILoad
    /// Called after a successful claim so the parent can refresh its list.
    var onClaimed: (() -> Void)? = nil

    @Environment(\.apiClient)  private var apiClient
    @EnvironmentObject private var session: AuthSession
    @Environment(\.dismiss)    private var dismiss

    @State private var current: APILoad
    @State private var showingClaimSheet = false
    @State private var isClaiming = false
    @State private var error: String?

    private var client: LoadsClient { LoadsClient(api: apiClient) }

    init(load: APILoad, onClaimed: (() -> Void)? = nil) {
        self.load      = load
        self.onClaimed = onClaimed
        _current       = State(initialValue: load)
    }

    // MARK: - Derived

    private var payoutCents: Int { current.payoutCents }
    private var feeCents: Int    { current.calculatedPriceCents - payoutCents }

    /// Can the signed-in user claim this load right now?
    private var canClaim: Bool {
        guard let me = session.me else { return false }
        return current.status == .posted
            && current.haulerId == nil
            && current.shipperId != me.id
    }

    // MARK: - Body

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                titleBlock
                mapBlock
                routeCard
                statsRow
                payoutHero
                if let error {
                    HHErrorBanner(message: error)
                }
            }
            .padding(.horizontal, 18)
            .padding(.bottom, canClaim ? 120 : 32)
        }
        .background(HHColor.ink50)
        .safeAreaInset(edge: .bottom, spacing: 0) {
            if canClaim { stickyCTA }
        }
        .toolbar(.hidden, for: .navigationBar)
        .overlay(alignment: .topLeading) { topBar }
        .sheet(isPresented: $showingClaimSheet) {
            ClaimSheetView(
                load: current,
                payoutCents: payoutCents,
                feeCents: feeCents,
                isBusy: isClaiming,
                onConfirm: { await claimLoad() }
            )
            .presentationDetents([.medium, .large])
            .presentationDragIndicator(.visible)
        }
    }

    // MARK: - Claim action

    private func claimLoad() async {
        isClaiming = true
        error = nil
        do {
            let updated = try await client.accept(id: current.id)
            current = updated
            showingClaimSheet = false
            onClaimed?()
            dismiss()
        } catch let err as APIError {
            error = err.errorDescription
            showingClaimSheet = false
        } catch {
            self.error = error.localizedDescription
            showingClaimSheet = false
        }
        isClaiming = false
    }

    // MARK: - Top nav bar

    private var topBar: some View {
        HStack {
            Button { dismiss() } label: {
                Image(systemName: "chevron.left")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundStyle(HHColor.ink900)
                    .frame(width: 36, height: 36)
                    .background(HHColor.ink100)
                    .clipShape(Circle())
            }
            Spacer()
        }
        .padding(.horizontal, 18)
        .padding(.top, 8)
    }

    // MARK: - Content blocks

    private var titleBlock: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 6) {
                if current.isExpress {
                    HHPill(text: "EXPRESS", icon: "bolt.fill", style: .accent)
                }
                HHPill(text: current.status.label, style: current.status.pillStyle)
                Text(current.postedMinAgo < 60
                     ? "\(current.postedMinAgo)m ago"
                     : "\(current.postedMinAgo / 60)h ago")
                    .font(.system(size: 10.5, weight: .semibold))
                    .foregroundStyle(HHColor.ink500)
            }
            Text(current.title).font(HHFont.title)
            if let d = current.description {
                Text(d)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundStyle(HHColor.ink600)
            }
        }
        .padding(.top, 52)
    }

    private var mapBlock: some View {
        HHRouteMapView(load: current)
            .frame(height: 160)
            .clipShape(RoundedRectangle(cornerRadius: HHRadius.md, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: HHRadius.md, style: .continuous)
                    .strokeBorder(HHColor.ink200, lineWidth: 1)
            )
    }

    private var routeCard: some View {
        VStack(spacing: 12) {
            HHRouteStack(
                from: .init(
                    where_: "\(current.pickupAddress), \(current.pickupCity)",
                    sub: current.pickupWindowDisplay
                ),
                to: .init(
                    where_: "\(current.dropoffAddress), \(current.dropoffCity)",
                    sub: "Deliver by \(current.dropoffByDisplay)"
                )
            )
            Divider().background(HHColor.ink200)
            HStack {
                Text("\(Int(current.estimatedDistanceMiles)) mi")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(HHColor.ink600)
                Spacer()
                if current.isExpress {
                    Text("Express — priority pickup")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundStyle(HHColor.accentText)
                }
            }
        }
        .hhCard()
    }

    private var statsRow: some View {
        HStack(spacing: 1) {
            statBox(
                value: "\(current.weightLbs.formatted())",
                label: "lb"
            )
            statBox(
                value: current.lengthFt.map {
                    String(format: "%g × %g", $0, current.widthFt ?? 0)
                } ?? "—",
                label: "ft (L × W)"
            )
            statBox(
                value: current.heightFt.map { String(format: "%g", $0) } ?? "—",
                label: "ft tall"
            )
        }
        .background(HHColor.ink200)
        .clipShape(RoundedRectangle(cornerRadius: HHRadius.md, style: .continuous))
    }

    private func statBox(value: String, label: String) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(HHFont.display(size: 18))
                .monospacedDigit()
                .foregroundStyle(HHColor.ink900)
            Text(label.uppercased())
                .font(.system(size: 10, weight: .semibold))
                .tracking(0.5)
                .foregroundStyle(HHColor.ink500)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 12)
        .background(HHColor.paper)
    }

    private var payoutHero: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 4) {
                Text("YOUR PAYOUT")
                    .font(.system(size: 11, weight: .semibold))
                    .tracking(0.5)
                    .foregroundStyle(Color.white.opacity(0.55))
                Text(HHFormat.money(cents: payoutCents))
                    .font(HHFont.headlineLG)
                    .monospacedDigit()
                    .foregroundStyle(.white)
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 4) {
                Text("Total \(HHFormat.moneyShort(cents: current.calculatedPriceCents)) · fee \(HHFormat.moneyShort(cents: feeCents))")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(Color.white.opacity(0.55))
                Text("Paid 24 h after delivery")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(Color.white.opacity(0.55))
            }
        }
        .hhCard(dark: true)
    }

    private var stickyCTA: some View {
        VStack(spacing: 8) {
            Button { showingClaimSheet = true } label: {
                HStack(spacing: 8) {
                    Text("Claim this load · \(HHFormat.money(cents: payoutCents))")
                    Image(systemName: "arrow.right")
                }
            }
            .buttonStyle(HHAccentButtonStyle())
            .disabled(isClaiming)

            Text("You can cancel up to 30 min before pickup, free")
                .font(.system(size: 11, weight: .medium))
                .foregroundStyle(HHColor.ink500)
        }
        .padding(.horizontal, 18)
        .padding(.top, 14)
        .padding(.bottom, 16)
        .background(HHColor.ink50)
        .overlay(alignment: .top) {
            Rectangle().fill(HHColor.ink200).frame(height: 1)
        }
        .shadow(color: Color.black.opacity(0.06), radius: 8, y: -3)
    }
}

// MARK: - Claim confirmation sheet

struct ClaimSheetView: View {
    let load: APILoad
    let payoutCents: Int
    let feeCents: Int
    var isBusy: Bool = false
    var onConfirm: (() async -> Void)? = nil

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 14) {
            ZStack {
                Circle().fill(HHColor.accentSoft).frame(width: 56, height: 56)
                Image(systemName: "shippingbox.fill")
                    .font(.system(size: 24))
                    .foregroundStyle(HHColor.accentText)
            }
            .padding(.top, 8)

            Text("Claim this load?")
                .font(HHFont.title)
                .foregroundStyle(HHColor.ink900)

            Text("You'll be on the hook for pickup and delivery — confirm if you're committed.")
                .font(.system(size: 13, weight: .medium))
                .foregroundStyle(HHColor.ink600)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 20)

            VStack(spacing: 4) {
                HHRowKV(key: "Load price",
                        value: HHFormat.money(cents: load.calculatedPriceCents))
                HHRowKV(key: "Platform fee (15 %)",
                        value: "−\(HHFormat.money(cents: feeCents))",
                        muted: true)
                Divider().background(HHColor.ink200).padding(.vertical, 4)
                HHRowKV(key: "Your payout",
                        value: HHFormat.money(cents: payoutCents),
                        big: true)
            }
            .padding(14)
            .background(HHColor.ink50)
            .clipShape(RoundedRectangle(cornerRadius: HHRadius.md, style: .continuous))

            Button {
                Task { await onConfirm?() }
            } label: {
                if isBusy {
                    HStack(spacing: 8) {
                        ProgressView().tint(.white)
                        Text("Claiming…")
                    }
                } else {
                    Text("Confirm claim")
                }
            }
            .buttonStyle(HHAccentButtonStyle())
            .disabled(isBusy)

            Button("Not yet") { dismiss() }
                .buttonStyle(HHGhostButtonStyle())
                .disabled(isBusy)
        }
        .padding(.horizontal, 18)
        .padding(.top, 10)
        .padding(.bottom, 30)
    }
}
