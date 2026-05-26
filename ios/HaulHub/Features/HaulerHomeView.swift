import SwiftUI

struct HaulerHomeView: View {
    @State private var selectedLoad: Load?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 14) {
                    earningsStrip
                    ForEach(Array(MockData.hauls.enumerated()), id: \.element.id) { idx, load in
                        Button {
                            selectedLoad = load
                        } label: {
                            FeedCard(load: load, featured: idx == 0)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(.horizontal, 18)
                .padding(.bottom, 24)
            }
            .background(HHColor.ink50)
            .navigationTitle("")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Available")
                            .font(HHFont.title)
                        HStack(spacing: 4) {
                            Circle().fill(HHColor.success).frame(width: 6, height: 6)
                            Text("Online · Austin metro")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundStyle(HHColor.ink500)
                        }
                    }
                    .padding(.leading, 4)
                }
                ToolbarItem(placement: .topBarTrailing) {
                    HStack(spacing: 6) {
                        circleIcon(systemName: "magnifyingglass")
                        ZStack(alignment: .topTrailing) {
                            circleIcon(systemName: "bell")
                            Circle().fill(HHColor.accent).frame(width: 7, height: 7).offset(x: -8, y: 8)
                        }
                    }
                }
            }
            .safeAreaInset(edge: .top, spacing: 0) {
                filterBar
            }
            .navigationDestination(item: $selectedLoad) { load in
                LoadDetailView(load: load)
            }
        }
    }

    private func circleIcon(systemName: String) -> some View {
        Image(systemName: systemName)
            .font(.system(size: 16, weight: .semibold))
            .foregroundStyle(HHColor.ink700)
            .frame(width: 38, height: 38)
            .background(HHColor.ink100)
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    private var filterBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                filterChip("Within 50 mi", active: true)
                filterChip("Box truck", active: true)
                filterChip("Express +", active: false)
                filterChip("$50+", active: false)
            }
            .padding(.horizontal, 18)
            .padding(.bottom, 10)
        }
        .background(HHColor.ink50)
    }

    private func filterChip(_ title: String, active: Bool) -> some View {
        HStack(spacing: 4) {
            Text(title)
                .font(.system(size: 12, weight: .semibold))
            if active {
                Image(systemName: "chevron.right")
                    .font(.system(size: 9, weight: .bold))
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
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
                Text("$874.20")
                    .font(HHFont.display(size: 20))
                    .monospacedDigit()
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 2) {
                Text("9 trips · 412 mi")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundStyle(HHColor.ink500)
                HStack(spacing: 4) {
                    Image(systemName: "bolt.fill").font(.system(size: 11))
                    Text("Express bonus active")
                        .font(.system(size: 12, weight: .semibold))
                }
                .foregroundStyle(HHColor.accentText)
            }
        }
        .padding(12)
        .background(HHColor.ink50)
        .overlay(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .strokeBorder(HHColor.ink200, lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}

// MARK: - Feed card

struct FeedCard: View {
    let load: Load
    var featured: Bool = false

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack(alignment: .top, spacing: 12) {
                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 6) {
                        if load.urgency == .express {
                            HHPill(text: "EXPRESS", icon: "bolt.fill", style: .accent)
                        } else {
                            HHPill(text: "STANDARD")
                        }
                        HHPill(text: VehicleLabel.describe(load.vehicleNeeds))
                        Text("\(load.postedMinAgo)m ago")
                            .font(.system(size: 10.5, weight: .semibold))
                            .foregroundStyle(HHColor.ink500)
                    }

                    Text(load.title)
                        .font(.system(size: 15, weight: .semibold, design: .default))
                        .foregroundStyle(HHColor.ink900)
                        .lineLimit(2)

                    HHRouteStack(
                        from: .init(where_: "\(load.pickup.city), \(load.pickup.state)", sub: load.pickupWindow),
                        to: .init(where_: "\(load.dropoff.city), \(load.dropoff.state)", sub: "by \(load.dropoffBy.replacingOccurrences(of: "by ", with: ""))")
                    )
                }

                Spacer()

                VStack(alignment: .trailing, spacing: 6) {
                    Text(HHFormat.moneyShort(cents: load.priceCents))
                        .font(HHFont.headlineMD)
                        .monospacedDigit()
                        .foregroundStyle(HHColor.ink900)
                    Text("\(load.miles) mi · \(HHFormat.weight(lb: load.weightLbs))")
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
            color: featured ? HHColor.accent.opacity(0.18) : Color.black.opacity(0.04),
            radius: featured ? 12 : 2, x: 0, y: featured ? 6 : 1
        )
        .overlay(alignment: .topLeading) {
            if featured {
                HStack(spacing: 4) {
                    Image(systemName: "bolt.fill").font(.system(size: 10, weight: .bold))
                    Text("NEW · NEAR YOU")
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

#Preview {
    HaulerHomeView()
}
