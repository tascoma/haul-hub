import SwiftUI

struct ActiveHaulView: View {
    @Environment(\.apiClient) private var apiClient

    @State private var activeHaul: APILoad?
    @State private var isLoading = false
    @State private var error: String?
    @State private var isBusy = false

    private var client: LoadsClient { LoadsClient(api: apiClient) }

    // MARK: - Stage model

    private struct Stage {
        let label: String
        let done: Bool
        let current: Bool
    }

    private func stages(for haul: APILoad) -> [Stage] {
        let idx = haul.status.stageIndex
        let titles = ["Claimed", "En route", "Picked up", "In transit", "Delivered"]
        return titles.enumerated().map { i, label in
            Stage(label: label, done: i < idx, current: i == idx)
        }
    }

    // MARK: - Body

    var body: some View {
        NavigationStack {
            Group {
                if isLoading && activeHaul == nil {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(HHColor.ink50)
                } else if let haul = activeHaul {
                    haulContent(haul)
                } else {
                    emptyState
                }
            }
            .background(HHColor.ink50)
            .refreshable { await load() }
            .navigationTitle("")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    if let haul = activeHaul {
                        VStack(alignment: .leading, spacing: 2) {
                            Text("ACTIVE HAUL")
                                .font(.system(size: 11, weight: .semibold))
                                .tracking(0.5)
                                .foregroundStyle(HHColor.ink500)
                            Text(haul.title)
                                .font(HHFont.titleSm)
                                .lineLimit(1)
                        }
                        .padding(.leading, 4)
                    } else {
                        Text("Active Haul")
                            .font(HHFont.title)
                            .padding(.leading, 4)
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button { Task { await load() } } label: {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundStyle(HHColor.ink900)
                            .frame(width: 36, height: 36)
                            .background(HHColor.ink100)
                            .clipShape(Circle())
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .task { await load() }
    }

    // MARK: - Haul content

    @ViewBuilder
    private func haulContent(_ haul: APILoad) -> some View {
        ScrollView {
            VStack(spacing: 14) {
                mapBlock(haul)
                statusTrail(haul)
                routeCard(haul)
                payoutCard(haul)
                if let error { HHErrorBanner(message: error) }
            }
            .padding(.horizontal, 18)
            .padding(.bottom, 110)
        }
        .safeAreaInset(edge: .bottom, spacing: 0) {
            actionCTA(haul)
        }
    }

    // MARK: - Empty state

    private var emptyState: some View {
        VStack(spacing: 16) {
            ZStack {
                Circle().fill(HHColor.ink100).frame(width: 80, height: 80)
                Image(systemName: "truck.box")
                    .font(.system(size: 32))
                    .foregroundStyle(HHColor.ink400)
            }
            Text("No active haul")
                .font(HHFont.title)
                .foregroundStyle(HHColor.ink900)
            Text("Once you claim a load from the feed, it'll appear here so you can track progress and mark stages.")
                .font(.system(size: 13))
                .foregroundStyle(HHColor.ink500)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(.bottom, 40)
    }

    // MARK: - Content blocks

    private func mapBlock(_ haul: APILoad) -> some View {
        HHMapView(
            progress: progressFraction(haul),
            live: haul.status == .inTransit,
            label: haul.status.label
        )
        .frame(height: 230)
        .clipShape(RoundedRectangle(cornerRadius: HHRadius.lg, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: HHRadius.lg, style: .continuous)
                .strokeBorder(HHColor.ink200, lineWidth: 1)
        )
        .overlay(alignment: .topTrailing) {
            HStack(spacing: 6) {
                Circle().fill(HHColor.success).frame(width: 8, height: 8)
                Text(haul.status.label)
                    .font(.system(size: 12, weight: .bold))
                    .foregroundStyle(.white)
            }
            .padding(.horizontal, 12).padding(.vertical, 6)
            .background(HHColor.ink900)
            .clipShape(Capsule())
            .padding(12)
        }
    }

    private func statusTrail(_ haul: APILoad) -> some View {
        let stageList = stages(for: haul)
        return VStack(spacing: 10) {
            HStack {
                Text("Progress")
                    .font(.system(size: 14, weight: .bold))
                    .tracking(-0.2)
                    .foregroundStyle(HHColor.ink900)
                Spacer()
                HStack(spacing: 4) {
                    Circle().fill(HHColor.success).frame(width: 8, height: 8)
                    Text("On track")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundStyle(HHColor.success)
                }
            }

            ZStack(alignment: .top) {
                // Rail
                GeometryReader { geo in
                    let inset = geo.size.width * 0.1
                    let available = geo.size.width - inset * 2
                    let segments = CGFloat(stageList.count - 1)
                    let filled = segments > 0
                        ? available * (CGFloat(haul.status.stageIndex) / segments)
                        : 0

                    Rectangle()
                        .fill(HHColor.ink200)
                        .frame(width: available, height: 2)
                        .position(x: geo.size.width / 2, y: 11)

                    Rectangle()
                        .fill(HHColor.accent)
                        .frame(width: max(0, filled), height: 2)
                        .position(x: inset + max(0, filled) / 2, y: 11)
                }
                .frame(height: 22)

                // Stage dots
                HStack(spacing: 0) {
                    ForEach(Array(stageList.enumerated()), id: \.offset) { _, stage in
                        VStack(spacing: 6) {
                            ZStack {
                                if stage.current {
                                    Circle()
                                        .fill(HHColor.accent.opacity(0.18))
                                        .frame(width: 32, height: 32)
                                }
                                Circle()
                                    .fill(stage.done || stage.current ? HHColor.accent : HHColor.ink200)
                                    .frame(width: 22, height: 22)
                                if stage.done && !stage.current {
                                    Image(systemName: "checkmark")
                                        .font(.system(size: 11, weight: .bold))
                                        .foregroundStyle(.white)
                                } else if stage.current {
                                    Circle().fill(.white).frame(width: 8, height: 8)
                                }
                            }
                            Text(stage.label)
                                .font(.system(size: 10, weight: stage.current ? .bold : .medium))
                                .foregroundStyle(stage.current ? HHColor.ink900 : HHColor.ink500)
                                .multilineTextAlignment(.center)
                                .lineLimit(2)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                        .frame(maxWidth: .infinity)
                    }
                }
            }
        }
        .hhCard(padding: 14)
    }

    private func routeCard(_ haul: APILoad) -> some View {
        HHRouteStack(
            from: .init(
                where_: "\(haul.pickupAddress), \(haul.pickupCity)",
                sub: haul.pickupWindowDisplay
            ),
            to: .init(
                where_: "\(haul.dropoffAddress), \(haul.dropoffCity)",
                sub: "Deliver by \(haul.dropoffByDisplay)"
            )
        )
        .hhCard()
    }

    private func payoutCard(_ haul: APILoad) -> some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 4) {
                Text("YOUR PAYOUT")
                    .font(.system(size: 11, weight: .semibold))
                    .tracking(0.5)
                    .foregroundStyle(Color.white.opacity(0.55))
                Text(HHFormat.money(cents: haul.payoutCents))
                    .font(HHFont.headlineMD)
                    .monospacedDigit()
                    .foregroundStyle(.white)
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 4) {
                Text("\(Int(haul.estimatedDistanceMiles)) mi · \(HHFormat.weight(lb: haul.weightLbs))")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(Color.white.opacity(0.55))
                Text("Paid 24 h after delivery")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(Color.white.opacity(0.55))
            }
        }
        .hhCard(dark: true)
    }

    // MARK: - CTA

    @ViewBuilder
    private func actionCTA(_ haul: APILoad) -> some View {
        if let config = ctaConfig(for: haul) {
            VStack(spacing: 8) {
                Button {
                    Task { await performAction(config, haul: haul) }
                } label: {
                    if isBusy {
                        HStack(spacing: 8) {
                            ProgressView().tint(.white)
                            Text("Updating…")
                        }
                    } else {
                        HStack(spacing: 8) {
                            Text(config.label)
                            Image(systemName: "arrow.right")
                        }
                    }
                }
                .buttonStyle(HHAccentButtonStyle())
                .disabled(isBusy)
            }
            .padding(.horizontal, 18)
            .padding(.top, 14)
            .padding(.bottom, 16)
            .background(
                LinearGradient(
                    colors: [HHColor.ink50.opacity(0), HHColor.ink50],
                    startPoint: .top, endPoint: .bottom
                )
            )
        }
    }

    // MARK: - Helpers

    private struct CTAConfig {
        let label: String
        let action: (String) async throws -> APILoad
    }

    private func ctaConfig(for haul: APILoad) -> CTAConfig? {
        switch haul.status {
        case .accepted:
            return CTAConfig(label: "Mark as picked up") { try await client.markPickedUp(id: $0) }
        case .pickedUp:
            return CTAConfig(label: "Mark in transit") { try await client.markInTransit(id: $0) }
        case .inTransit:
            return CTAConfig(label: "Mark delivered") { try await client.markDelivered(id: $0) }
        default:
            return nil
        }
    }

    private func performAction(_ config: CTAConfig, haul: APILoad) async {
        isBusy = true
        error = nil
        do {
            let updated = try await config.action(haul.id)
            activeHaul = updated.status.isActive ? updated : nil
        } catch let err as APIError {
            error = err.errorDescription
        } catch {
            self.error = error.localizedDescription
        }
        isBusy = false
    }

    private func progressFraction(_ haul: APILoad) -> Double {
        let total = 4.0
        return Double(haul.status.stageIndex) / total
    }

    private func load() async {
        isLoading = true
        error = nil
        do {
            let hauls = try await client.myHauls()
            activeHaul = hauls.first(where: { $0.status.isActive })
        } catch let err as APIError {
            error = err.errorDescription
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }
}

#Preview {
    ActiveHaulView()
        .environmentObject(AuthSession())
}
