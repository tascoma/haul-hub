import SwiftUI

/// Shipper-framed load detail: route, cargo, the price the shipper pays, and a
/// booking-event timeline fetched from GET /api/loads/{id}/events. Read-only —
/// no payout/claim framing (that's the hauler's LoadDetailView).
struct ShipperLoadDetailView: View {
    let load: APILoad

    @Environment(\.apiClient) private var apiClient

    @State private var events: [APIBookingEvent] = []
    @State private var isLoadingEvents = false
    @State private var error: String?

    private var client: LoadsClient { LoadsClient(api: apiClient) }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                titleBlock
                mapBlock
                routeCard
                statsRow
                priceCard
                timelineCard
                if let error {
                    HHErrorBanner(message: error)
                }
            }
            .padding(.horizontal, 18)
            .padding(.vertical, 16)
        }
        .background(HHColor.ink50)
        .navigationTitle("Tracking")
        .navigationBarTitleDisplayMode(.inline)
        .task { await loadEvents() }
    }

    // MARK: - Blocks

    private var titleBlock: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 6) {
                if load.isExpress {
                    HHPill(text: "EXPRESS", icon: "bolt.fill", style: .accent)
                }
                HHPill(text: load.status.label, style: load.status.pillStyle)
            }
            Text(load.title).font(HHFont.title)
            if let d = load.description {
                Text(d)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundStyle(HHColor.ink600)
            }
        }
    }

    private var mapBlock: some View {
        HHMapView(
            progress: Double(load.status.stageIndex) / 4.0,
            live: load.status == .inTransit,
            label: "\(load.pickupCity) → \(load.dropoffCity)"
        )
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
                    where_: "\(load.pickupAddress), \(load.pickupCity)",
                    sub: load.pickupWindowDisplay
                ),
                to: .init(
                    where_: "\(load.dropoffAddress), \(load.dropoffCity)",
                    sub: "Deliver by \(load.dropoffByDisplay)"
                )
            )
            Divider().background(HHColor.ink200)
            HStack {
                Text("\(Int(load.estimatedDistanceMiles)) mi")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(HHColor.ink600)
                Spacer()
                if load.isExpress {
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
            statBox(value: "\(load.weightLbs.formatted())", label: "lb")
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

    private var priceCard: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("PRICE YOU'LL PAY")
                    .font(.system(size: 11, weight: .semibold))
                    .tracking(0.5)
                    .foregroundStyle(Color.white.opacity(0.55))
                Text(HHFormat.money(cents: load.calculatedPriceCents))
                    .font(HHFont.headlineLG)
                    .monospacedDigit()
                    .foregroundStyle(.white)
            }
            Spacer()
            Text("Charged on delivery")
                .font(.system(size: 12, weight: .medium))
                .foregroundStyle(Color.white.opacity(0.55))
        }
        .hhCard(dark: true)
    }

    // MARK: - Timeline

    private var timelineCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("TIMELINE")
                .font(.system(size: 11, weight: .semibold))
                .tracking(0.5)
                .foregroundStyle(HHColor.ink500)

            if isLoadingEvents && events.isEmpty {
                ProgressView().frame(maxWidth: .infinity)
            } else if events.isEmpty {
                HStack(spacing: 10) {
                    Image(systemName: "clock")
                        .foregroundStyle(HHColor.ink400)
                    Text("Posted — waiting for a hauler to claim it.")
                        .font(.system(size: 13, weight: .medium))
                        .foregroundStyle(HHColor.ink500)
                }
            } else {
                VStack(alignment: .leading, spacing: 0) {
                    ForEach(Array(events.enumerated()), id: \.element.id) { idx, event in
                        timelineRow(event, isLast: idx == events.count - 1)
                    }
                }
            }
        }
        .hhCard()
    }

    private func timelineRow(_ event: APIBookingEvent, isLast: Bool) -> some View {
        HStack(alignment: .top, spacing: 12) {
            VStack(spacing: 0) {
                ZStack {
                    Circle().fill(HHColor.accentSoft).frame(width: 30, height: 30)
                    Image(systemName: event.eventType.icon)
                        .font(.system(size: 13, weight: .bold))
                        .foregroundStyle(HHColor.accentText)
                }
                if !isLast {
                    Rectangle()
                        .fill(HHColor.ink200)
                        .frame(width: 2)
                        .frame(maxHeight: .infinity)
                }
            }
            .frame(width: 30)

            VStack(alignment: .leading, spacing: 2) {
                Text(event.eventType.label)
                    .font(HHFont.smallBold)
                    .foregroundStyle(HHColor.ink900)
                Text(event.createdAtDisplay)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(HHColor.ink500)
            }
            .padding(.bottom, isLast ? 0 : 18)
        }
    }

    // MARK: - Data

    private func loadEvents() async {
        isLoadingEvents = true
        error = nil
        do {
            events = try await client.events(id: load.id)
        } catch let err as APIError {
            error = err.errorDescription
        } catch {
            self.error = error.localizedDescription
        }
        isLoadingEvents = false
    }
}
