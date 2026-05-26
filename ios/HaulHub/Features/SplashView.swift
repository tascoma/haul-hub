import SwiftUI

/// Splash / first-run screen — leads into the main tab shell.
struct SplashView: View {
    @Binding var hasEntered: Bool

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [HHColor.paper, HHColor.paper, HHColor.accentSoft],
                startPoint: .top, endPoint: .bottom
            )
            .ignoresSafeArea()

            // Faint route ribbon
            GeometryReader { geo in
                let w = geo.size.width
                let h = geo.size.height
                ZStack {
                    Path { p in
                        p.move(to: CGPoint(x: -20, y: h * 0.8))
                        p.addQuadCurve(
                            to: CGPoint(x: w + 20, y: h * 0.7),
                            control: CGPoint(x: w * 0.5, y: h * 0.72)
                        )
                    }
                    .stroke(HHColor.accent, style: StrokeStyle(lineWidth: 2, lineCap: .round, dash: [2, 6]))
                    .opacity(0.5)

                    Circle().fill(HHColor.ink900).frame(width: 12, height: 12)
                        .position(x: w * 0.22, y: h * 0.77)
                    Circle().fill(HHColor.accent).frame(width: 12, height: 12)
                        .position(x: w * 0.88, y: h * 0.73)
                }
            }
            .allowsHitTesting(false)

            VStack(alignment: .leading, spacing: 0) {
                HHLogomark(size: 36)
                    .padding(.top, 24)
                Spacer()

                Text("The shortest distance between ")
                    .font(.system(size: 38, weight: .bold)).tracking(-1.2)
                    .foregroundStyle(HHColor.ink900)
                +
                Text("here").foregroundStyle(HHColor.accentText)
                    .font(.system(size: 38, weight: .bold)).tracking(-1.2)
                +
                Text(" and ")
                    .font(.system(size: 38, weight: .bold)).tracking(-1.2)
                    .foregroundStyle(HHColor.ink900)
                +
                Text("there.").foregroundStyle(HHColor.accentText)
                    .font(.system(size: 38, weight: .bold)).tracking(-1.2)

                Text("Post a load or claim one. Pickup truck to flatbed, couches to project cars — Haul Hub matches you with a hauler in minutes.")
                    .font(.system(size: 15, weight: .medium))
                    .foregroundStyle(HHColor.ink600)
                    .padding(.top, 14)
                    .padding(.bottom, 22)

                Button("Get started") { hasEntered = true }
                    .buttonStyle(HHDarkButtonStyle())
                    .padding(.bottom, 10)
                Button("I already have an account") { hasEntered = true }
                    .buttonStyle(HHGhostButtonStyle())

                Text("By continuing you agree to our Terms & Privacy.")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundStyle(HHColor.ink400)
                    .frame(maxWidth: .infinity)
                    .padding(.top, 14)
            }
            .padding(.horizontal, 24)
            .padding(.bottom, 32)
        }
    }
}

#Preview {
    SplashView(hasEntered: .constant(false))
}
