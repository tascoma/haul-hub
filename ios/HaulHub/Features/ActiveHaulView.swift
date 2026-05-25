import SwiftUI

struct ActiveHaulView: View {
    private let haul = MockData.activeHaul

    private struct Stage {
        let label: String
        let done: Bool
        let current: Bool
    }

    private var stages: [Stage] {
        let idx = haul.stageIndex
        let titles = ["Claimed", "En route to pickup", "Picked up", "In transit", "Delivered"]
        return titles.enumerated().map { i, label in
            Stage(label: label, done: i < idx, current: i == idx)
        }
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 14) {
                    mapBlock
                    statusTrail
                    shipperContactCard
                    nextStepTile
                }
                .padding(.horizontal, 18)
                .padding(.bottom, 110)
            }
            .background(HHColor.ink50)
            .safeAreaInset(edge: .bottom, spacing: 0) {
                stickyCTA
            }
            .navigationTitle("")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("ACTIVE HAUL · \(haul.base.id)")
                            .font(.system(size: 11, weight: .semibold)).tracking(0.5)
                            .foregroundStyle(HHColor.ink500)
                        Text(haul.base.title)
                            .font(HHFont.titleSm)
                    }
                    .padding(.leading, 4)
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Image(systemName: "ellipsis")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundStyle(HHColor.ink900)
                        .frame(width: 36, height: 36)
                        .background(HHColor.ink100)
                        .clipShape(Circle())
                }
            }
        }
    }

    private var mapBlock: some View {
        HHMapView(progress: 0.62, live: true, label: "In transit")
            .frame(height: 230)
            .clipShape(RoundedRectangle(cornerRadius: HHRadius.lg, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: HHRadius.lg, style: .continuous)
                    .strokeBorder(HHColor.ink200, lineWidth: 1)
            )
            .overlay(alignment: .topTrailing) {
                HStack(spacing: 6) {
                    Image(systemName: "clock.fill").font(.system(size: 11, weight: .bold))
                    Text("\(haul.etaMin) min · \(String(format: "%.1f", haul.milesRemaining)) mi")
                        .font(.system(size: 12, weight: .bold))
                }
                .foregroundStyle(.white)
                .padding(.horizontal, 12).padding(.vertical, 6)
                .background(HHColor.ink900)
                .clipShape(Capsule())
                .padding(12)
            }
    }

    private var statusTrail: some View {
        VStack(spacing: 10) {
            HStack {
                Text("Status")
                    .font(.system(size: 14, weight: .bold)).tracking(-0.2)
                    .foregroundStyle(HHColor.ink900)
                Spacer()
                HStack(spacing: 4) {
                    Circle().fill(HHColor.success).frame(width: 8, height: 8)
                    Text("On schedule")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundStyle(HHColor.success)
                }
            }

            ZStack(alignment: .top) {
                // Background rail
                GeometryReader { geo in
                    let inset = geo.size.width * 0.1
                    Rectangle()
                        .fill(HHColor.ink200)
                        .frame(width: geo.size.width - inset * 2, height: 2)
                        .position(x: geo.size.width / 2, y: 11)

                    // Filled progress
                    let progressWidth: CGFloat = {
                        if let last = stages.lastIndex(where: { $0.done }) {
                            // proportional fill up through current
                            let segments = CGFloat(stages.count - 1)
                            let fraction = (CGFloat(last) + (stages[last+1 < stages.count ? last+1 : last].current ? 1.0 : 0)) / segments
                            return (geo.size.width - inset * 2) * fraction
                        }
                        return 0
                    }()
                    Rectangle()
                        .fill(HHColor.accent)
                        .frame(width: progressWidth, height: 2)
                        .position(x: inset + progressWidth / 2, y: 11)
                }
                .frame(height: 22)

                HStack(spacing: 0) {
                    ForEach(Array(stages.enumerated()), id: \.offset) { _, stage in
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

    private var shipperContactCard: some View {
        HStack(spacing: 12) {
            HHAvatar(initials: haul.base.shipper.initials, size: 44)
            VStack(alignment: .leading, spacing: 2) {
                Text(haul.base.shipper.name).font(HHFont.smallBold)
                Text("Shipper · waiting at dropoff")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(HHColor.ink500)
            }
            Spacer()
            Image(systemName: "message.fill")
                .font(.system(size: 16, weight: .semibold))
                .foregroundStyle(HHColor.ink900)
                .frame(width: 38, height: 38)
                .background(HHColor.ink100)
                .clipShape(Circle())
            Image(systemName: "phone.fill")
                .font(.system(size: 16, weight: .semibold))
                .foregroundStyle(.white)
                .frame(width: 38, height: 38)
                .background(HHColor.ink900)
                .clipShape(Circle())
        }
        .hhCard()
    }

    private var nextStepTile: some View {
        HStack(spacing: 12) {
            Image(systemName: "shippingbox.fill")
                .font(.system(size: 18))
                .foregroundStyle(HHColor.ink700)
                .frame(width: 40, height: 40)
                .background(HHColor.paper)
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            VStack(alignment: .leading, spacing: 2) {
                Text("Next: confirm delivery")
                    .font(.system(size: 13, weight: .semibold))
                Text("Take a photo of dropped cargo + signature.")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(HHColor.ink500)
            }
            Spacer()
        }
        .padding(16)
        .background(HHColor.ink100)
        .clipShape(RoundedRectangle(cornerRadius: HHRadius.md, style: .continuous))
    }

    private var stickyCTA: some View {
        VStack {
            Button {
                // Mark delivered (mocked)
            } label: {
                HStack {
                    Text("Slide to mark delivered")
                    Image(systemName: "arrow.right")
                }
            }
            .buttonStyle(HHAccentButtonStyle())
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

#Preview {
    ActiveHaulView()
}
