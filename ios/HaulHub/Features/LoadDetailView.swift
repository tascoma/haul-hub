import SwiftUI

struct LoadDetailView: View {
    let load: Load
    @Environment(\.dismiss) private var dismiss
    @State private var showingClaimSheet = false

    var payoutCents: Int { Int(Double(load.priceCents) * 0.85) }
    var feeCents: Int { load.priceCents - payoutCents }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                titleBlock
                mapBlock
                routeCard
                statsRow
                shipperCard
                payoutHero
            }
            .padding(.horizontal, 18)
            .padding(.bottom, 110)
        }
        .background(HHColor.ink50)
        .safeAreaInset(edge: .bottom, spacing: 0) {
            stickyCTA
        }
        .toolbar(.hidden, for: .navigationBar)
        .overlay(alignment: .topLeading) { topBar }
        .sheet(isPresented: $showingClaimSheet) {
            ClaimSheetView(load: load, payoutCents: payoutCents, feeCents: feeCents)
                .presentationDetents([.medium, .large])
                .presentationDragIndicator(.visible)
        }
    }

    // MARK: - Header / nav

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
            Image(systemName: "square.and.arrow.up")
                .font(.system(size: 16, weight: .semibold))
                .foregroundStyle(HHColor.ink900)
                .frame(width: 36, height: 36)
                .background(HHColor.ink100)
                .clipShape(Circle())
            Image(systemName: "ellipsis")
                .font(.system(size: 16, weight: .semibold))
                .foregroundStyle(HHColor.ink900)
                .frame(width: 36, height: 36)
                .background(HHColor.ink100)
                .clipShape(Circle())
        }
        .padding(.horizontal, 18)
        .padding(.top, 8)
    }

    private var titleBlock: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 6) {
                if load.urgency == .express {
                    HHPill(text: "EXPRESS", icon: "bolt.fill", style: .accent)
                }
                HHPill(text: VehicleLabel.describe(load.vehicleNeeds))
                Text("\(load.postedMinAgo)m ago")
                    .font(.system(size: 10.5, weight: .semibold))
                    .foregroundStyle(HHColor.ink500)
            }
            Text(load.title).font(HHFont.title)
            if let d = load.description {
                Text(d)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundStyle(HHColor.ink600)
            }
        }
        .padding(.top, 52)
    }

    private var mapBlock: some View {
        HHMapView(label: "\(load.pickup.city) → \(load.dropoff.city)")
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
                from: .init(where_: "\(load.pickup.street), \(load.pickup.city)",
                            sub: load.pickupWindow),
                to: .init(where_: "\(load.dropoff.street), \(load.dropoff.city)",
                          sub: load.dropoffBy)
            )
            Divider().background(HHColor.ink200)
            HStack {
                Text("\(load.miles) mi · ~3h 10m drive")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(HHColor.ink600)
                Spacer()
                Text("Tolls covered")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(HHColor.accentText)
            }
        }
        .hhCard()
    }

    private var statsRow: some View {
        HStack(spacing: 1) {
            statBox(value: "\(load.weightLbs)", label: "lb")
            statBox(
                value: load.lengthFt.map { String(format: "%g × %g", $0, load.widthFt ?? 0) } ?? "—",
                label: "ft (L × W)"
            )
            statBox(value: load.heightFt.map { String(format: "%g", $0) } ?? "—", label: "ft tall")
        }
        .background(HHColor.ink200)
        .clipShape(RoundedRectangle(cornerRadius: HHRadius.md, style: .continuous))
    }

    private func statBox(value: String, label: String) -> some View {
        VStack(spacing: 4) {
            Text(value).font(HHFont.display(size: 18)).monospacedDigit()
                .foregroundStyle(HHColor.ink900)
            Text(label.uppercased())
                .font(.system(size: 10, weight: .semibold)).tracking(0.5)
                .foregroundStyle(HHColor.ink500)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 12)
        .background(HHColor.paper)
    }

    private var shipperCard: some View {
        HStack(spacing: 12) {
            HHAvatar(initials: load.shipper.initials, size: 56)
            VStack(alignment: .leading, spacing: 4) {
                Text(load.shipper.name).font(HHFont.smallBold).foregroundStyle(HHColor.ink900)
                HStack(spacing: 6) {
                    HStack(spacing: 2) {
                        Image(systemName: "star.fill").font(.system(size: 11))
                            .foregroundStyle(HHColor.accent)
                        Text(String(format: "%.1f", load.shipper.rating))
                            .font(.system(size: 12, weight: .bold))
                            .foregroundStyle(HHColor.ink900)
                    }
                    Text("·").foregroundStyle(HHColor.ink400)
                    Text("\(load.shipper.jobs) shipments")
                        .font(.system(size: 12)).foregroundStyle(HHColor.ink600)
                    Text("·").foregroundStyle(HHColor.ink400)
                    HStack(spacing: 3) {
                        Image(systemName: "checkmark.shield.fill").font(.system(size: 10))
                        Text("ID verified").font(.system(size: 12, weight: .semibold))
                    }
                    .foregroundStyle(HHColor.success)
                }
            }
            Spacer()
        }
        .hhCard()
    }

    private var payoutHero: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 4) {
                Text("YOUR PAYOUT")
                    .font(.system(size: 11, weight: .semibold)).tracking(0.5)
                    .foregroundStyle(Color.white.opacity(0.55))
                Text(HHFormat.money(cents: payoutCents))
                    .font(HHFont.headlineLG)
                    .monospacedDigit()
                    .foregroundStyle(.white)
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 4) {
                Text("Total \(HHFormat.moneyShort(cents: load.priceCents)) · fee \(HHFormat.moneyShort(cents: feeCents))")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(Color.white.opacity(0.55))
                Text("Paid 24h after delivery")
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
            Text("You can cancel up to 30 min before pickup, free")
                .font(.system(size: 11, weight: .medium))
                .foregroundStyle(HHColor.ink500)
        }
        .padding(.horizontal, 18)
        .padding(.top, 14).padding(.bottom, 16)
        .background(
            LinearGradient(
                colors: [HHColor.ink50.opacity(0), HHColor.ink50],
                startPoint: .top, endPoint: .bottom
            )
        )
    }
}

// MARK: - Claim sheet

struct ClaimSheetView: View {
    let load: Load
    let payoutCents: Int
    let feeCents: Int
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 14) {
            ZStack {
                Circle().fill(HHColor.accentSoft).frame(width: 56, height: 56)
                Image(systemName: "shippingbox.fill")
                    .font(.system(size: 24)).foregroundStyle(HHColor.accentText)
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
                HHRowKV(key: "Load price", value: HHFormat.money(cents: load.priceCents))
                HHRowKV(key: "Platform fee (15%)",
                        value: "−\(HHFormat.money(cents: feeCents))", muted: true)
                HHRowKV(key: "Express bonus", value: "+$25.00", positive: true)
                Divider().background(HHColor.ink200).padding(.vertical, 4)
                HHRowKV(key: "Your payout",
                        value: HHFormat.money(cents: payoutCents), big: true)
            }
            .padding(14)
            .background(HHColor.ink50)
            .clipShape(RoundedRectangle(cornerRadius: HHRadius.md, style: .continuous))

            Button("Confirm claim") { dismiss() }
                .buttonStyle(HHAccentButtonStyle())
            Button("Not yet") { dismiss() }
                .buttonStyle(HHGhostButtonStyle())
        }
        .padding(.horizontal, 18)
        .padding(.top, 10).padding(.bottom, 30)
    }
}

#Preview {
    NavigationStack {
        LoadDetailView(load: MockData.heroLoad)
    }
}
