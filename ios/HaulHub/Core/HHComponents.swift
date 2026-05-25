import SwiftUI

// MARK: - Logomark

struct HHLogomark: View {
    var size: CGFloat = 32

    var body: some View {
        HStack(spacing: 10) {
            ZStack {
                RoundedRectangle(cornerRadius: size * 0.27, style: .continuous)
                    .fill(HHColor.ink900)
                Image(systemName: "shippingbox.fill")
                    .font(.system(size: size * 0.48, weight: .bold))
                    .foregroundStyle(HHColor.accent)
            }
            .frame(width: size, height: size)

            Text("Haul Hub")
                .font(.system(size: size * 0.5, weight: .heavy))
                .tracking(-0.5)
                .foregroundStyle(HHColor.ink900)
        }
    }
}

// MARK: - Avatar

struct HHAvatar: View {
    let initials: String
    var size: CGFloat = 40
    var dark: Bool = false

    var body: some View {
        ZStack {
            if dark {
                LinearGradient(
                    colors: [HHColor.ink900, HHColor.ink700],
                    startPoint: .topLeading, endPoint: .bottomTrailing
                )
            } else {
                LinearGradient(
                    colors: [HHColor.ink200, HHColor.ink300],
                    startPoint: .topLeading, endPoint: .bottomTrailing
                )
            }
            Text(initials)
                .font(.system(size: size * 0.36, weight: .bold))
                .foregroundStyle(dark ? .white : HHColor.ink700)
        }
        .frame(width: size, height: size)
        .clipShape(Circle())
    }
}

// MARK: - Route stack (pickup → dropoff dots + rail)

struct HHRouteStack: View {
    struct Stop {
        let where_: String
        let sub: String?
    }
    let from: Stop
    let to: Stop

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            VStack(spacing: 0) {
                Circle()
                    .fill(HHColor.ink900)
                    .frame(width: 12, height: 12)
                    .overlay(
                        Circle().strokeBorder(HHColor.ink100, lineWidth: 4)
                            .frame(width: 20, height: 20)
                    )
                    .padding(.top, 4)
                // Dashed rail
                RouteRail()
                    .stroke(HHColor.ink300, style: StrokeStyle(lineWidth: 2, dash: [3, 4]))
                    .frame(width: 2)
                    .frame(maxHeight: .infinity)
                Circle()
                    .fill(HHColor.accent)
                    .frame(width: 12, height: 12)
                    .overlay(
                        Circle().strokeBorder(HHColor.accentSoft, lineWidth: 4)
                            .frame(width: 20, height: 20)
                    )
                    .padding(.bottom, 4)
            }
            .frame(width: 20)

            VStack(alignment: .leading, spacing: 14) {
                stopView(from)
                stopView(to)
            }
        }
    }

    @ViewBuilder
    private func stopView(_ s: Stop) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(s.where_)
                .font(HHFont.smallBold)
                .foregroundStyle(HHColor.ink900)
            if let sub = s.sub {
                Text(sub)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(HHColor.ink500)
            }
        }
    }
}

private struct RouteRail: Shape {
    func path(in rect: CGRect) -> Path {
        var p = Path()
        p.move(to: CGPoint(x: rect.midX, y: 0))
        p.addLine(to: CGPoint(x: rect.midX, y: rect.maxY))
        return p
    }
}

// MARK: - Stylized SVG-like map placeholder

struct HHMapView: View {
    var progress: Double = 0.55
    var live: Bool = false
    var label: String? = nil

    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width
            let h = geo.size.height
            ZStack {
                HHColor.ink100

                // Park
                RoundedRectangle(cornerRadius: 6)
                    .fill(Color(red: 0.886, green: 0.937, blue: 0.898))
                    .frame(width: w * 0.18, height: h * 0.22)
                    .position(x: w * 0.51, y: h * 0.15)

                // Water blob
                Path { p in
                    p.move(to: CGPoint(x: w * 0.55, y: h * 0.85))
                    p.addQuadCurve(to: CGPoint(x: w * 1.1, y: h * 0.7),
                                   control: CGPoint(x: w * 0.7, y: h * 1.1))
                    p.addLine(to: CGPoint(x: w * 1.1, y: h * 1.1))
                    p.addLine(to: CGPoint(x: w * 0.5, y: h * 1.1))
                    p.closeSubpath()
                }
                .fill(Color(red: 0.902, green: 0.933, blue: 0.965))

                // Roads (white)
                ZStack {
                    Path { p in
                        p.move(to: CGPoint(x: 0, y: h * 0.5))
                        p.addLine(to: CGPoint(x: w, y: h * 0.5))
                    }.stroke(HHColor.paper, style: StrokeStyle(lineWidth: 9, lineCap: .round))
                    Path { p in
                        p.move(to: CGPoint(x: w * 0.3, y: 0))
                        p.addLine(to: CGPoint(x: w * 0.3, y: h))
                    }.stroke(HHColor.paper, style: StrokeStyle(lineWidth: 9, lineCap: .round))
                    Path { p in
                        p.move(to: CGPoint(x: w * 0.7, y: 0))
                        p.addLine(to: CGPoint(x: w * 0.7, y: h))
                    }.stroke(HHColor.paper, style: StrokeStyle(lineWidth: 9, lineCap: .round))
                    Path { p in
                        p.move(to: CGPoint(x: 0, y: h * 0.78))
                        p.addLine(to: CGPoint(x: w, y: h * 0.78))
                    }.stroke(HHColor.paper, style: StrokeStyle(lineWidth: 6, lineCap: .round))
                }

                // Route curve
                let start = CGPoint(x: w * 0.12, y: h * 0.72)
                let end   = CGPoint(x: w * 0.86, y: h * 0.28)
                let c1    = CGPoint(x: w * 0.35, y: h * 0.78)
                let c2    = CGPoint(x: w * 0.62, y: h * 0.18)

                // shadow
                Path { p in
                    p.move(to: CGPoint(x: start.x, y: start.y + 1.5))
                    p.addCurve(to: CGPoint(x: end.x, y: end.y + 1.5),
                               control1: CGPoint(x: c1.x, y: c1.y + 1.5),
                               control2: CGPoint(x: c2.x, y: c2.y + 1.5))
                }.stroke(HHColor.ink900.opacity(0.18), style: StrokeStyle(lineWidth: 6, lineCap: .round))
                // route
                Path { p in
                    p.move(to: start)
                    p.addCurve(to: end, control1: c1, control2: c2)
                }.stroke(HHColor.accent, style: StrokeStyle(lineWidth: 4, lineCap: .round))

                // Start / end pins
                Circle().fill(HHColor.ink900).frame(width: 12, height: 12).position(start)
                Circle().fill(HHColor.accent).frame(width: 14, height: 14).position(end)

                if live {
                    let v = cubicPoint(t: progress, p0: start, p1: c1, p2: c2, p3: end)
                    Circle()
                        .fill(HHColor.accent.opacity(0.25))
                        .frame(width: 28, height: 28)
                        .position(v)
                    Circle()
                        .fill(HHColor.paper)
                        .frame(width: 16, height: 16)
                        .overlay(Circle().fill(HHColor.accent).frame(width: 8, height: 8))
                        .position(v)
                }

                if let label {
                    HStack(spacing: 6) {
                        Image(systemName: "location.fill")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundStyle(.white)
                        Text(label)
                            .font(.system(size: 11, weight: .bold))
                            .foregroundStyle(.white)
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(HHColor.ink900)
                    .clipShape(Capsule())
                    .position(x: w - 70, y: 20)
                }
            }
        }
    }

    private func cubicPoint(t: Double,
                            p0: CGPoint, p1: CGPoint, p2: CGPoint, p3: CGPoint) -> CGPoint {
        let it = 1 - t
        let x = pow(it, 3) * p0.x + 3 * pow(it, 2) * t * p1.x
              + 3 * it * pow(t, 2) * p2.x + pow(t, 3) * p3.x
        let y = pow(it, 3) * p0.y + 3 * pow(it, 2) * t * p1.y
              + 3 * it * pow(t, 2) * p2.y + pow(t, 3) * p3.y
        return CGPoint(x: x, y: y)
    }
}

// MARK: - Key/value row (used in payout breakdown)

struct HHRowKV: View {
    let key: String
    let value: String
    var muted: Bool = false
    var positive: Bool = false
    var big: Bool = false

    var body: some View {
        HStack(alignment: .firstTextBaseline) {
            Text(key)
                .font(.system(size: big ? 14 : 13, weight: big ? .bold : .medium))
                .foregroundStyle(muted ? HHColor.ink500 : HHColor.ink700)
            Spacer()
            Text(value)
                .font(.system(size: big ? 20 : 14, weight: big ? .bold : .semibold))
                .monospacedDigit()
                .foregroundStyle(
                    positive ? HHColor.success
                    : muted ? HHColor.ink500 : HHColor.ink900
                )
        }
        .padding(.vertical, 6)
    }
}
