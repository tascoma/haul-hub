import SwiftUI

struct ShipperHomeView: View {
    private let tracked = MockData.trackedShipment

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    liveHero
                    quickTiles
                    pastShipments
                }
                .padding(.horizontal, 18)
                .padding(.bottom, 24)
            }
            .background(HHColor.ink50)
            .navigationTitle("")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Tuesday")
                            .font(.system(size: 12, weight: .medium))
                            .foregroundStyle(HHColor.ink500)
                        Text("Welcome, Maya")
                            .font(HHFont.title)
                    }
                    .padding(.leading, 4)
                }
                ToolbarItem(placement: .topBarTrailing) {
                    HHAvatar(initials: "MR", size: 40)
                }
            }
        }
    }

    private var liveHero: some View {
        VStack(spacing: 0) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("LIVE · ARRIVING")
                        .font(.system(size: 11, weight: .semibold)).tracking(0.5)
                        .foregroundStyle(HHColor.accent)
                    Text("\(tracked.etaMin) min")
                        .font(HHFont.headlineLG)
                        .monospacedDigit()
                        .foregroundStyle(.white)
                }
                Spacer()
                VStack(alignment: .trailing, spacing: 2) {
                    Text("\(tracked.base.title.prefix(30))")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundStyle(Color.white.opacity(0.7))
                        .lineLimit(1)
                    Text("\(tracked.hauler.name) · \(String(format: "%.1f", tracked.milesRemaining)) mi")
                        .font(.system(size: 11, weight: .medium))
                        .foregroundStyle(Color.white.opacity(0.5))
                }
            }
            .padding(.bottom, 12)

            HHMapView(progress: 0.78, live: true)
                .frame(height: 120)
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .strokeBorder(Color.white.opacity(0.12), lineWidth: 1)
                )

            Button("Track shipment") {}
                .buttonStyle(HHAccentButtonStyle(height: 44))
                .padding(.top, 12)
        }
        .padding(16)
        .background(HHColor.ink900)
        .clipShape(RoundedRectangle(cornerRadius: HHRadius.lg, style: .continuous))
    }

    private var quickTiles: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("NEED TO MOVE SOMETHING?")
                .font(.system(size: 11, weight: .semibold)).tracking(0.5)
                .foregroundStyle(HHColor.ink500)

            HStack(spacing: 8) {
                quickTile(label: "Post a load", sub: "Get matched in mins",
                          icon: "plus", iconBg: HHColor.accent, iconFg: .white)
                quickTile(label: "Get an estimate", sub: "Price before posting",
                          icon: "dollarsign", iconBg: HHColor.ink100, iconFg: HHColor.ink700)
            }
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
            Text(label).font(.system(size: 13, weight: .bold))
                .foregroundStyle(HHColor.ink900)
            Text(sub).font(.system(size: 11, weight: .medium))
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

    private var pastShipments: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Past shipments")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundStyle(HHColor.ink900)
                Spacer()
                Text("All")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(HHColor.accentText)
            }

            ForEach(pastShipmentMocks, id: \.title) { shipment in
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
                        Text("\(shipment.from) → \(shipment.to) · \(shipment.when)")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundStyle(HHColor.ink500)
                    }
                    Spacer()
                    Text(HHFormat.moneyShort(cents: shipment.priceCents))
                        .font(.system(size: 13, weight: .bold))
                        .monospacedDigit()
                        .foregroundStyle(HHColor.ink900)
                }
                .padding(.vertical, 8)
                Divider().background(HHColor.ink100)
            }
        }
    }

    private struct ShipmentRow {
        let title: String
        let from: String
        let to: String
        let when: String
        let priceCents: Int
    }

    private var pastShipmentMocks: [ShipmentRow] {
        [
            .init(title: "Living room set", from: "Austin", to: "Round Rock", when: "Yesterday", priceCents: 8900),
            .init(title: "Office chairs (8)", from: "Austin", to: "Austin", when: "Mon", priceCents: 6700),
            .init(title: "Garage sale haul", from: "Cedar Park", to: "Austin", when: "Fri", priceCents: 4200),
        ]
    }
}

#Preview {
    ShipperHomeView()
}
