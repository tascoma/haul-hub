import SwiftUI

struct ShipperHomeView: View {
    @Environment(\.apiClient)  private var apiClient
    @EnvironmentObject private var session: AuthSession

    @State private var shipments: [APILoad] = []
    @State private var isLoading = false
    @State private var error: String?

    private var client: LoadsClient { LoadsClient(api: apiClient) }

    // MARK: - Derived data

    /// The most recent in-transit or accepted shipment.
    private var liveShipment: APILoad? {
        shipments.first(where: { $0.status == .inTransit || $0.status == .accepted || $0.status == .pickedUp })
    }

    private var pastShipments: [APILoad] {
        Array(shipments.filter { $0.status == .delivered }.prefix(5))
    }

    private var firstName: String {
        session.me?.profile.fullName?.split(separator: " ").first.map(String.init) ?? "there"
    }

    private var greeting: String {
        let hour = Calendar.current.component(.hour, from: Date())
        switch hour {
        case 5..<12:  return "Good morning"
        case 12..<17: return "Good afternoon"
        default:      return "Good evening"
        }
    }

    // MARK: - Body

    var body: some View {
        NavigationStack {
            Group {
                if isLoading && shipments.isEmpty {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(HHColor.ink50)
                } else {
                    ScrollView {
                        VStack(spacing: 16) {
                            if let live = liveShipment {
                                liveHero(live)
                            } else {
                                quickTiles
                            }
                            statsStrip
                            if !pastShipments.isEmpty {
                                pastSection
                            }
                            if let error {
                                HHErrorBanner(message: error)
                                    .padding(.horizontal, 18)
                            }
                        }
                        .padding(.bottom, 24)
                    }
                    .refreshable { await load() }
                }
            }
            .background(HHColor.ink50)
            .navigationTitle("")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(greeting)
                            .font(.system(size: 12, weight: .medium))
                            .foregroundStyle(HHColor.ink500)
                        Text(firstName)
                            .font(HHFont.title)
                    }
                    .padding(.leading, 4)
                }
                ToolbarItem(placement: .topBarTrailing) {
                    HHAvatar(
                        initials: initials,
                        size: 40
                    )
                }
            }
        }
        .task { await load() }
    }

    private var initials: String {
        guard let name = session.me?.profile.fullName else {
            return session.me.map { String($0.email.prefix(2)).uppercased() } ?? "?"
        }
        let parts = name.split(separator: " ")
        if parts.count >= 2 {
            return "\(parts[0].prefix(1))\(parts[1].prefix(1))".uppercased()
        }
        return String(name.prefix(2)).uppercased()
    }

    // MARK: - Live hero

    private func liveHero(_ load: APILoad) -> some View {
        VStack(spacing: 0) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("LIVE · \(load.status.label.uppercased())")
                        .font(.system(size: 11, weight: .semibold))
                        .tracking(0.5)
                        .foregroundStyle(HHColor.accent)
                    Text(load.title)
                        .font(HHFont.titleSm)
                        .foregroundStyle(.white)
                        .lineLimit(2)
                }
                Spacer()
                VStack(alignment: .trailing, spacing: 2) {
                    HHPill(text: load.status.label, style: .solidAccent)
                    Text("\(load.pickupCity) → \(load.dropoffCity)")
                        .font(.system(size: 11, weight: .medium))
                        .foregroundStyle(Color.white.opacity(0.5))
                }
            }
            .padding(.bottom, 12)

            HHMapView(
                progress: Double(load.status.stageIndex) / 4.0,
                live: load.status == .inTransit
            )
            .frame(height: 120)
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .strokeBorder(Color.white.opacity(0.12), lineWidth: 1)
            )

            // Route preview
            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 2) {
                    Text(load.pickupAddress)
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundStyle(Color.white.opacity(0.8))
                        .lineLimit(1)
                    Text("\(load.pickupCity), \(load.pickupState)")
                        .font(.system(size: 11))
                        .foregroundStyle(Color.white.opacity(0.45))
                }
                Image(systemName: "arrow.right")
                    .font(.system(size: 11, weight: .bold))
                    .foregroundStyle(HHColor.accent)
                VStack(alignment: .leading, spacing: 2) {
                    Text(load.dropoffAddress)
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundStyle(Color.white.opacity(0.8))
                        .lineLimit(1)
                    Text("\(load.dropoffCity), \(load.dropoffState)")
                        .font(.system(size: 11))
                        .foregroundStyle(Color.white.opacity(0.45))
                }
            }
            .padding(.top, 12)
        }
        .padding(16)
        .background(HHColor.ink900)
        .clipShape(RoundedRectangle(cornerRadius: HHRadius.lg, style: .continuous))
        .padding(.horizontal, 18)
        .padding(.top, 8)
    }

    // MARK: - Quick tiles (no active shipment)

    private var quickTiles: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("NEED TO MOVE SOMETHING?")
                .font(.system(size: 11, weight: .semibold))
                .tracking(0.5)
                .foregroundStyle(HHColor.ink500)
                .padding(.horizontal, 18)
                .padding(.top, 8)

            HStack(spacing: 8) {
                quickTile(
                    label: "Post a load",
                    sub: "Get matched in minutes",
                    icon: "plus",
                    iconBg: HHColor.accent,
                    iconFg: .white
                )
                quickTile(
                    label: "Get an estimate",
                    sub: "Price before posting",
                    icon: "dollarsign",
                    iconBg: HHColor.ink100,
                    iconFg: HHColor.ink700
                )
            }
            .padding(.horizontal, 18)
        }
    }

    private func quickTile(label: String, sub: String, icon: String,
                           iconBg: Color, iconFg: Color) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 18, weight: .bold))
                .foregroundStyle(iconFg)
                .frame(width: 36, height: 36)
                .background(iconBg)
                .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
            Text(label)
                .font(.system(size: 13, weight: .bold))
                .foregroundStyle(HHColor.ink900)
            Text(sub)
                .font(.system(size: 11, weight: .medium))
                .foregroundStyle(HHColor.ink500)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(14)
        .background(HHColor.paper)
        .overlay(
            RoundedRectangle(cornerRadius: HHRadius.md, style: .continuous)
                .strokeBorder(HHColor.ink200, lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: HHRadius.md, style: .continuous))
    }

    // MARK: - Stats strip

    private var statsStrip: some View {
        let posted    = shipments.filter { $0.status == .posted }.count
        let inMotion  = shipments.filter { $0.status.isActive }.count
        let delivered = shipments.filter { $0.status == .delivered }.count

        return HStack(spacing: 1) {
            statBox(value: "\(posted)",    label: "Posted")
            statBox(value: "\(inMotion)",  label: "In motion")
            statBox(value: "\(delivered)", label: "Delivered")
        }
        .background(HHColor.ink200)
        .clipShape(RoundedRectangle(cornerRadius: HHRadius.md, style: .continuous))
        .padding(.horizontal, 18)
    }

    private func statBox(value: String, label: String) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(HHFont.display(size: 20, weight: .bold))
                .monospacedDigit()
                .foregroundStyle(HHColor.ink900)
            Text(label.uppercased())
                .font(.system(size: 10.5, weight: .semibold))
                .tracking(0.5)
                .foregroundStyle(HHColor.ink500)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 14)
        .background(HHColor.paper)
    }

    // MARK: - Past shipments

    private var pastSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Past shipments")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundStyle(HHColor.ink900)
                Spacer()
                Text("All (\(shipments.filter { $0.status == .delivered }.count))")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(HHColor.accentText)
            }

            ForEach(pastShipments) { shipment in
                HStack(spacing: 12) {
                    Image(systemName: "checkmark")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundStyle(HHColor.success)
                        .frame(width: 36, height: 36)
                        .background(HHColor.successSoft)
                        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                    VStack(alignment: .leading, spacing: 2) {
                        Text(shipment.title)
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundStyle(HHColor.ink900)
                            .lineLimit(1)
                        Text("\(shipment.pickupCity) → \(shipment.dropoffCity)")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundStyle(HHColor.ink500)
                    }
                    Spacer()
                    Text(HHFormat.moneyShort(cents: shipment.calculatedPriceCents))
                        .font(.system(size: 13, weight: .bold))
                        .monospacedDigit()
                        .foregroundStyle(HHColor.ink900)
                }
                .padding(.vertical, 8)
                Divider().background(HHColor.ink100)
            }
        }
        .padding(.horizontal, 18)
    }

    // MARK: - Data

    private func load() async {
        isLoading = true
        error = nil
        do {
            shipments = try await client.myLoads()
        } catch let err as APIError {
            error = err.errorDescription
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }
}

#Preview {
    ShipperHomeView()
        .environmentObject(AuthSession())
}
