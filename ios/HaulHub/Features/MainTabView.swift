import SwiftUI

enum AppRole: String, CaseIterable, Identifiable {
    case hauler, shipper
    var id: String { rawValue }
}

struct MainTabView: View {
    @EnvironmentObject private var session: AuthSession
    @State private var role: AppRole = .hauler
    @State private var selectedTab: Int = 0

    private var hasShipper: Bool { session.me?.profile.shipperEnabled ?? true }
    private var hasHauler: Bool { session.me?.profile.haulerEnabled ?? false }
    private var hasBothRoles: Bool { hasShipper && hasHauler }

    var body: some View {
        VStack(spacing: 0) {
            if hasBothRoles {
                roleSwitcher
                    .padding(.horizontal, 18)
                    .padding(.top, 8)
                    .padding(.bottom, 6)
                    .background(HHColor.paper)
            }

            TabView(selection: $selectedTab) {
                Group {
                    if role == .hauler {
                        HaulerHomeView().tabItem {
                            Image(systemName: "list.bullet.rectangle.portrait")
                            Text("Loads")
                        }.tag(0)

                        ActiveHaulView().tabItem {
                            Image(systemName: "truck.box.fill")
                            Text("Active")
                        }.tag(1)

                        placeholder(title: "Earnings", icon: "dollarsign.circle.fill")
                            .tabItem { Image(systemName: "dollarsign.circle.fill"); Text("Earnings") }
                            .tag(2)

                        placeholder(title: "Alerts", icon: "bell.fill")
                            .tabItem { Image(systemName: "bell.fill"); Text("Alerts") }
                            .tag(3)

                        ProfileView()
                            .tabItem { Image(systemName: "person.fill"); Text("Profile") }
                            .tag(4)
                    } else {
                        ShipperHomeView().tabItem {
                            Image(systemName: "house.fill")
                            Text("Home")
                        }.tag(0)

                        PostLoadView()
                            .tabItem { Image(systemName: "plus.circle.fill"); Text("Post") }
                            .tag(1)

                        ShipperTrackingView()
                            .tabItem { Image(systemName: "truck.box.fill"); Text("Tracking") }
                            .tag(2)

                        placeholder(title: "Alerts", icon: "bell.fill")
                            .tabItem { Image(systemName: "bell.fill"); Text("Alerts") }
                            .tag(3)

                        ProfileView()
                            .tabItem { Image(systemName: "person.fill"); Text("Profile") }
                            .tag(4)
                    }
                }
            }
            .tint(HHColor.ink900)
        }
        .background(HHColor.ink50)
        .onAppear {
            // Pick the right initial role based on which flags the user has.
            if hasHauler && !hasShipper { role = .hauler }
            else if hasShipper && !hasHauler { role = .shipper }
        }
    }

    private var roleSwitcher: some View {
        HStack(spacing: 0) {
            ForEach(AppRole.allCases) { r in
                Button {
                    withAnimation(.easeInOut(duration: 0.15)) {
                        role = r
                        selectedTab = 0
                    }
                } label: {
                    Text(r.rawValue.capitalized)
                        .font(.system(size: 12.5, weight: .bold))
                        .foregroundStyle(role == r ? HHColor.ink900 : HHColor.ink500)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 6)
                        .background(role == r ? HHColor.paper : Color.clear)
                        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
                        .shadow(color: role == r ? Color.black.opacity(0.06) : .clear,
                                radius: 2, x: 0, y: 1)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(3)
        .background(HHColor.ink100)
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
    }

    private func placeholder(title: String, icon: String) -> some View {
        NavigationStack {
            VStack(spacing: 12) {
                Image(systemName: icon)
                    .font(.system(size: 36, weight: .bold))
                    .foregroundStyle(HHColor.ink400)
                Text(title)
                    .font(HHFont.title)
                    .foregroundStyle(HHColor.ink900)
                Text("Coming soon · use the loads feed or active haul to demo the design.")
                    .font(.system(size: 13))
                    .foregroundStyle(HHColor.ink500)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 32)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(HHColor.ink50)
            .navigationTitle(title)
        }
    }
}

#Preview {
    MainTabView()
}
