import SwiftUI

struct HaulerHomeView: View {
    @Environment(\.apiClient) private var apiClient
    @EnvironmentObject private var session: AuthSession

    @State private var loads: [APILoad] = []
    @State private var myHauls: [APILoad] = []
    @State private var isLoading = false
    @State private var error: String?
    @State private var selectedLoad: APILoad?

    private var client: LoadsClient { LoadsClient(api: apiClient) }

    // MARK: - Earnings helpers

    private var weekEarningsCents: Int {
        let weekAgo = Calendar.current.date(byAdding: .weekOfYear, value: -1, to: Date()) ?? Date()
        return myHauls
            .filter { $0.status == .delivered && ($0.deliveredAt ?? $0.updatedAt) >= weekAgo }
            .reduce(0) { $0 + $1.payoutCents }
    }

    private var weekTrips: Int {
        let weekAgo = Calendar.current.date(byAdding: .weekOfYear, value: -1, to: Date()) ?? Date()
        return myHauls
            .filter { $0.status == .delivered && ($0.deliveredAt ?? $0.updatedAt) >= weekAgo }
            .count
    }

    // MARK: - Body

    var body: some View {
        NavigationStack {
            Group {
                if isLoading && loads.isEmpty {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(HHColor.ink50)
                } else {
                    ScrollView {
                        VStack(spacing: 14) {
                            earningsStrip

                            if let error {
                                HHErrorBanner(message: error)
                            }

                            if loads.isEmpty {
                                emptyState
                            } else {
                                ForEach(Array(loads.enumerated()), id: \.element.id) { idx, load in
                                    Button { selectedLoad = load } label: {
                                        FeedCard(load: load, featured: idx == 0)
                                    }
                                    .buttonStyle(.plain)
                                }
                            }
                        }
                        .padding(.horizontal, 18)
                        .padding(.bottom, 24)
                    }
                    .refreshable { await refresh() }
                }
            }
            .background(HHColor.ink50)
            .navigationTitle("")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Available Loads")
                            .font(HHFont.title)
                        HStack(spacing: 4) {
                            Circle().fill(HHColor.success).frame(width: 6, height: 6)
                            Text("Online · \(loads.count) near you")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundStyle(HHColor.ink500)
                        }
                    }
                    .padding(.leading, 4)
                }
                ToolbarItem(placement: .topBarTrailing) {
                    circleIcon(systemName: "arrow.clockwise") { Task { await refresh() } }
                }
            }
            .safeAreaInset(edge: .top, spacing: 0) { filterBar }
            .navigationDestination(item: $selectedLoad) { load in
                LoadDetailView(load: load) {
                    // Refresh feed after a successful claim
                    Task { await refresh() }
                }
            }
        }
        .task { await refresh() }
    }

    // MARK: - Data

    private func refresh() async {
        isLoading = true
        error = nil
        async let availableTask = client.listAvailable()
        async let haulsTask    = client.myHauls()
        do {
            let (available, hauled) = try await (availableTask, haulsTask)
            loads   = available
            myHauls = hauled
        } catch let err as APIError {
            error = err.errorDescription
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }

    // MARK: - Subviews

    private func circleIcon(systemName: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Image(systemName: systemName)
                .font(.system(size: 16, weight: .semibold))
                .foregroundStyle(HHColor.ink700)
                .frame(width: 38, height: 38)
                .background(HHColor.ink100)
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        }
        .buttonStyle(.plain)
    }

    private var filterBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                filterChip("All loads", active: true)
                filterChip("Express +", active: false)
                filterChip("$50 +", active: false)
            }
            .padding(.horizontal, 18)
            .padding(.vertical, 10)
        }
        .background(HHColor.ink50)
        .overlay(alignment: .bottom) {
            Divider().background(HHColor.ink200)
        }
    }

    private func filterChip(_ title: String, active: Bool) -> some View {
        Text(title)
            .font(.system(size: 12, weight: .semibold))
            .padding(.horizontal, 12)
            .padding(.vertical, 7)
            .foregroundStyle(active ? .white : HHColor.ink700)
            .background(active ? HHColor.ink900 : HHColor.ink100)
            .clipShape(Capsule())
    }

    private var earningsStrip: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("THIS WEEK")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundStyle(HHColor.ink500)
                    .tracking(0.5)
                Text(weekEarningsCents > 0
                     ? HHFormat.money(cents: weekEarningsCents)
                     : "$0.00")
                    .font(HHFont.display(size: 20, weight: .bold))
                    .monospacedDigit()
                    .foregroundStyle(HHColor.ink900)
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 2) {
                Text("\(weekTrips) trips this week")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundStyle(HHColor.ink500)
                let active = myHauls.filter(\.status.isActive).count
                if active > 0 {
                    HStack(spacing: 4) {
                        Circle().fill(HHColor.accent).frame(width: 6, height: 6)
                        Text("\(active) active haul\(active == 1 ? "" : "s")")
                            .font(.system(size: 12, weight: .semibold))
                    }
                    .foregroundStyle(HHColor.accentText)
                }
            }
        }
        .padding(12)
        .background(HHColor.paper)
        .overlay(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .strokeBorder(HHColor.ink200, lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    private var emptyState: some View {
        VStack(spacing: 12) {
            Image(systemName: "tray")
                .font(.system(size: 36))
                .foregroundStyle(HHColor.ink400)
            Text("No loads available")
                .font(HHFont.titleSm)
                .foregroundStyle(HHColor.ink900)
            Text("Pull to refresh or check back soon.")
                .font(.system(size: 13))
                .foregroundStyle(HHColor.ink500)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 48)
    }
}

// MARK: - Feed card

struct FeedCard: View {
    let load: APILoad
    var featured: Bool = false

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack(alignment: .top, spacing: 12) {
                VStack(alignment: .leading, spacing: 8) {
                    // Pills row
                    HStack(spacing: 6) {
                        if load.isExpress {
                            HHPill(text: "EXPRESS", icon: "bolt.fill", style: .accent)
                        } else {
                            HHPill(text: "STANDARD")
                        }
                        HHPill(text: load.status.label, style: load.status.pillStyle)
                        Text(load.postedMinAgo < 60
                             ? "\(load.postedMinAgo)m ago"
                             : "\(load.postedMinAgo / 60)h ago")
                            .font(.system(size: 10.5, weight: .semibold))
                            .foregroundStyle(HHColor.ink500)
                    }

                    // Title
                    Text(load.title)
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundStyle(HHColor.ink900)
                        .lineLimit(2)

                    // Route
                    HHRouteStack(
                        from: .init(
                            where_: "\(load.pickupCity), \(load.pickupState)",
                            sub: load.pickupWindowDisplay
                        ),
                        to: .init(
                            where_: "\(load.dropoffCity), \(load.dropoffState)",
                            sub: "by \(load.dropoffByDisplay)"
                        )
                    )
                }

                Spacer(minLength: 8)

                // Price column
                VStack(alignment: .trailing, spacing: 6) {
                    Text(HHFormat.moneyShort(cents: load.calculatedPriceCents))
                        .font(HHFont.headlineMD)
                        .monospacedDigit()
                        .foregroundStyle(HHColor.ink900)
                    Text("\(Int(load.estimatedDistanceMiles)) mi · \(HHFormat.weight(lb: load.weightLbs))")
                        .font(.system(size: 11, weight: .medium))
                        .foregroundStyle(HHColor.ink500)
                }
            }
        }
        .padding(14)
        .background(HHColor.paper)
        .overlay(
            RoundedRectangle(cornerRadius: HHRadius.md, style: .continuous)
                .strokeBorder(
                    featured ? HHColor.accent : HHColor.ink200,
                    lineWidth: featured ? 1.5 : 1
                )
        )
        .clipShape(RoundedRectangle(cornerRadius: HHRadius.md, style: .continuous))
        .shadow(
            color: featured ? HHColor.accent.opacity(0.15) : Color.black.opacity(0.04),
            radius: featured ? 10 : 2, x: 0, y: featured ? 5 : 1
        )
        .overlay(alignment: .topLeading) {
            if featured {
                HStack(spacing: 4) {
                    Image(systemName: "bolt.fill").font(.system(size: 10, weight: .bold))
                    Text("TOP MATCH")
                        .font(.system(size: 10, weight: .bold)).tracking(0.5)
                }
                .foregroundStyle(.white)
                .padding(.horizontal, 10).padding(.vertical, 5)
                .background(HHColor.accent)
                .clipShape(Capsule())
                .offset(x: 12, y: -10)
            }
        }
    }
}

// MARK: - Shared error banner (used across hauler / shipper views)

struct HHErrorBanner: View {
    let message: String
    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(HHColor.danger)
            Text(message)
                .font(.system(size: 13, weight: .medium))
                .foregroundStyle(HHColor.danger)
                .lineLimit(2)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(HHColor.dangerSoft)
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
    }
}

#Preview {
    HaulerHomeView()
        .environmentObject(AuthSession())
}
