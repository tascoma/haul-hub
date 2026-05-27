import SwiftUI

/// Shipper's view of their posted loads, grouped into active (in flight) and
/// past (delivered/cancelled). Tapping a load opens its tracking detail.
struct ShipperTrackingView: View {
    @Environment(\.apiClient) private var apiClient

    @State private var loads: [APILoad] = []
    @State private var isLoading = false
    @State private var error: String?
    @State private var selected: APILoad?

    private var client: LoadsClient { LoadsClient(api: apiClient) }

    /// Posted + accepted + picked-up + in-transit: still in flight.
    private var active: [APILoad] {
        loads.filter { $0.status == .posted || $0.status.isActive }
    }

    private var past: [APILoad] {
        loads.filter { $0.status == .delivered || $0.status == .cancelled }
    }

    var body: some View {
        NavigationStack {
            Group {
                if isLoading && loads.isEmpty {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(HHColor.ink50)
                } else if loads.isEmpty {
                    emptyState
                } else {
                    ScrollView {
                        VStack(alignment: .leading, spacing: 16) {
                            if let error {
                                HHErrorBanner(message: error).padding(.horizontal, 18)
                            }
                            if !active.isEmpty {
                                sectionHeader("In flight")
                                ForEach(active) { load in
                                    Button { selected = load } label: { activeCard(load) }
                                        .buttonStyle(.plain)
                                }
                            }
                            if !past.isEmpty {
                                sectionHeader("Past")
                                ForEach(past) { load in
                                    Button { selected = load } label: { pastRow(load) }
                                        .buttonStyle(.plain)
                                }
                            }
                        }
                        .padding(.vertical, 16)
                    }
                    .refreshable { await load() }
                }
            }
            .background(HHColor.ink50)
            .navigationTitle("Tracking")
            .navigationDestination(item: $selected) { load in
                ShipperLoadDetailView(load: load)
            }
        }
        .task { await load() }
    }

    // MARK: - Cards

    private func activeCard(_ load: APILoad) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(load.title)
                    .font(HHFont.smallBold)
                    .foregroundStyle(HHColor.ink900)
                    .lineLimit(1)
                Spacer()
                HHPill(text: load.status.label, style: load.status.pillStyle)
            }
            Text("\(load.pickupCity) → \(load.dropoffCity)")
                .font(.system(size: 12, weight: .medium))
                .foregroundStyle(HHColor.ink500)
            miniRail(stageIndex: load.status.stageIndex)
            HStack {
                Text(HHFormat.money(cents: load.calculatedPriceCents))
                    .font(.system(size: 13, weight: .bold))
                    .monospacedDigit()
                    .foregroundStyle(HHColor.ink900)
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundStyle(HHColor.ink400)
            }
        }
        .padding(16)
        .hhCard()
        .padding(.horizontal, 16)
    }

    /// Compact 5-dot progress rail (claimed → en route → picked up → in transit → delivered).
    private func miniRail(stageIndex: Int) -> some View {
        HStack(spacing: 4) {
            ForEach(0..<5) { i in
                Capsule()
                    .fill(i <= stageIndex ? HHColor.accent : HHColor.ink200)
                    .frame(height: 4)
            }
        }
    }

    private func pastRow(_ load: APILoad) -> some View {
        HStack(spacing: 12) {
            Image(systemName: load.status == .delivered ? "checkmark" : "xmark")
                .font(.system(size: 13, weight: .bold))
                .foregroundStyle(load.status == .delivered ? HHColor.success : HHColor.danger)
                .frame(width: 36, height: 36)
                .background(load.status == .delivered ? HHColor.successSoft : HHColor.dangerSoft)
                .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
            VStack(alignment: .leading, spacing: 2) {
                Text(load.title)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(HHColor.ink900)
                    .lineLimit(1)
                Text("\(load.pickupCity) → \(load.dropoffCity)")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundStyle(HHColor.ink500)
            }
            Spacer()
            Text(HHFormat.moneyShort(cents: load.calculatedPriceCents))
                .font(.system(size: 13, weight: .bold))
                .monospacedDigit()
                .foregroundStyle(HHColor.ink900)
        }
        .padding(.horizontal, 18)
        .padding(.vertical, 8)
    }

    private func sectionHeader(_ text: String) -> some View {
        Text(text.uppercased())
            .font(.system(size: 11, weight: .bold))
            .tracking(0.6)
            .foregroundStyle(HHColor.ink500)
            .padding(.horizontal, 18)
    }

    private var emptyState: some View {
        VStack(spacing: 12) {
            Image(systemName: "truck.box")
                .font(.system(size: 36, weight: .bold))
                .foregroundStyle(HHColor.ink400)
            Text("Nothing in flight yet")
                .font(HHFont.title)
                .foregroundStyle(HHColor.ink900)
            Text("Post a load and it'll show up here as haulers respond.")
                .font(HHFont.small)
                .foregroundStyle(HHColor.ink500)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(HHColor.ink50)
    }

    // MARK: - Data

    private func load() async {
        isLoading = true
        error = nil
        do {
            loads = try await client.myLoads()
        } catch let err as APIError {
            error = err.errorDescription
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }
}

#Preview {
    ShipperTrackingView()
        .environmentObject(AuthSession())
}
