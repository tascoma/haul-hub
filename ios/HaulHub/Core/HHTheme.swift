import SwiftUI

// MARK: - Haul Hub design tokens
// Ported from the design bundle's CSS custom properties.
enum HHColor {
    static let accent      = Color(red: 1.00, green: 0.36, blue: 0.16) // #FF5C28
    static let accentHover = Color(red: 0.90, green: 0.28, blue: 0.08) // #E64715
    static let accentSoft  = Color(red: 1.00, green: 0.91, blue: 0.87) // #FFE9DF
    static let accentText  = Color(red: 0.70, green: 0.23, blue: 0.06) // #B33A0F

    static let ink900 = Color(red: 0.043, green: 0.071, blue: 0.125)   // #0B1220
    static let ink800 = Color(red: 0.106, green: 0.133, blue: 0.192)   // #1B2231
    static let ink700 = Color(red: 0.208, green: 0.235, blue: 0.302)   // #353C4D
    static let ink600 = Color(red: 0.353, green: 0.392, blue: 0.471)   // #5A6478
    static let ink500 = Color(red: 0.486, green: 0.525, blue: 0.604)   // #7C869A
    static let ink400 = Color(red: 0.647, green: 0.682, blue: 0.753)   // #A5AEC0
    static let ink300 = Color(red: 0.824, green: 0.843, blue: 0.878)   // #D2D7E0
    static let ink200 = Color(red: 0.906, green: 0.918, blue: 0.941)   // #E7EAF0
    static let ink100 = Color(red: 0.949, green: 0.957, blue: 0.973)   // #F2F4F8
    static let ink50  = Color(red: 0.973, green: 0.976, blue: 0.988)   // #F8F9FC
    static let paper  = Color.white

    static let success     = Color(red: 0.106, green: 0.549, blue: 0.337) // #1B8C56
    static let successSoft = Color(red: 0.871, green: 0.957, blue: 0.910) // #DEF4E8
    static let warning     = Color(red: 0.722, green: 0.455, blue: 0.106) // #B8741B
    static let warningSoft = Color(red: 0.988, green: 0.922, blue: 0.820) // #FCEBD1
    static let danger      = Color(red: 0.788, green: 0.165, blue: 0.165) // #C92A2A
    static let dangerSoft  = Color(red: 0.992, green: 0.886, blue: 0.886) // #FDE2E2
    static let info        = Color(red: 0.122, green: 0.400, blue: 0.878) // #1F66E0
    static let infoSoft    = Color(red: 0.878, green: 0.918, blue: 0.984) // #E0EAFB
}

enum HHRadius {
    static let xs: CGFloat = 6
    static let sm: CGFloat = 10
    static let md: CGFloat = 14
    static let lg: CGFloat = 20
    static let xl: CGFloat = 28
}

// MARK: - Typography
// Uses the system SF Pro stack, matching the design which targets -apple-system.
enum HHFont {
    static func display(size: CGFloat, weight: Font.Weight = .bold) -> Font {
        .system(size: size, weight: weight, design: .default)
    }
    static func text(size: CGFloat, weight: Font.Weight = .regular) -> Font {
        .system(size: size, weight: weight, design: .default)
    }
    static func mono(size: CGFloat, weight: Font.Weight = .regular) -> Font {
        .system(size: size, weight: weight, design: .monospaced)
    }

    // Common roles
    static let headlineXL  = display(size: 48, weight: .bold)
    static let headlineLG  = display(size: 36, weight: .bold)
    static let headlineMD  = display(size: 26, weight: .bold)
    static let title       = display(size: 22, weight: .bold)
    static let titleSm     = display(size: 17, weight: .bold)
    static let body        = text(size: 15, weight: .regular)
    static let bodyBold    = text(size: 15, weight: .semibold)
    static let small       = text(size: 13, weight: .regular)
    static let smallBold   = text(size: 13, weight: .semibold)
    static let caps        = text(size: 11, weight: .semibold)
    static let micro       = text(size: 11, weight: .medium)
}

// MARK: - Card / pill / button modifiers

struct HHCard: ViewModifier {
    var padding: CGFloat = 16
    var dark: Bool = false
    func body(content: Content) -> some View {
        content
            .padding(padding)
            .background(dark ? HHColor.ink900 : HHColor.paper)
            .clipShape(RoundedRectangle(cornerRadius: HHRadius.md, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: HHRadius.md, style: .continuous)
                    .strokeBorder(dark ? HHColor.ink900 : HHColor.ink200, lineWidth: 1)
            )
            .shadow(color: Color.black.opacity(dark ? 0 : 0.04), radius: 2, x: 0, y: 1)
    }
}

extension View {
    func hhCard(padding: CGFloat = 16, dark: Bool = false) -> some View {
        modifier(HHCard(padding: padding, dark: dark))
    }
}

// MARK: - Pill

enum HHPillStyle {
    case neutral, accent, success, warning, danger, info, solid, solidAccent

    var bg: Color {
        switch self {
        case .neutral: return HHColor.ink100
        case .accent: return HHColor.accentSoft
        case .success: return HHColor.successSoft
        case .warning: return HHColor.warningSoft
        case .danger: return HHColor.dangerSoft
        case .info: return HHColor.infoSoft
        case .solid: return HHColor.ink900
        case .solidAccent: return HHColor.accent
        }
    }

    var fg: Color {
        switch self {
        case .neutral: return HHColor.ink700
        case .accent: return HHColor.accentText
        case .success: return HHColor.success
        case .warning: return HHColor.warning
        case .danger: return HHColor.danger
        case .info: return HHColor.info
        case .solid, .solidAccent: return .white
        }
    }
}

struct HHPill: View {
    let text: String
    var icon: String? = nil
    var style: HHPillStyle = .neutral

    var body: some View {
        HStack(spacing: 4) {
            if let icon { Image(systemName: icon).font(.system(size: 9, weight: .bold)) }
            Text(text)
                .font(.system(size: 10.5, weight: .bold))
                .tracking(0.5)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 5)
        .foregroundStyle(style.fg)
        .background(style.bg)
        .clipShape(Capsule())
    }
}

// MARK: - Primary button styles

struct HHAccentButtonStyle: ButtonStyle {
    var height: CGFloat = 52
    func makeBody(configuration: Configuration) -> some View {
        Label(configuration: configuration, height: height)
    }

    private struct Label: View {
        let configuration: Configuration
        let height: CGFloat
        @Environment(\.isEnabled) private var isEnabled

        var body: some View {
            configuration.label
                .font(.system(size: 16, weight: .semibold))
                .foregroundStyle(.white)
                .frame(maxWidth: .infinity)
                .frame(height: height)
                .background(configuration.isPressed ? HHColor.accentHover : HHColor.accent)
                .clipShape(RoundedRectangle(cornerRadius: HHRadius.md, style: .continuous))
                .opacity(isEnabled ? 1 : 0.4)
        }
    }
}

struct HHDarkButtonStyle: ButtonStyle {
    var height: CGFloat = 52
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 16, weight: .semibold))
            .foregroundStyle(.white)
            .frame(maxWidth: .infinity)
            .frame(height: height)
            .background(configuration.isPressed ? HHColor.ink700 : HHColor.ink900)
            .clipShape(RoundedRectangle(cornerRadius: HHRadius.md, style: .continuous))
    }
}

struct HHGhostButtonStyle: ButtonStyle {
    var height: CGFloat = 52
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 16, weight: .semibold))
            .foregroundStyle(HHColor.ink900)
            .frame(maxWidth: .infinity)
            .frame(height: height)
            .background(configuration.isPressed ? HHColor.ink200 : HHColor.ink100)
            .clipShape(RoundedRectangle(cornerRadius: HHRadius.md, style: .continuous))
    }
}

// MARK: - Formatters

enum HHFormat {
    static func money(cents: Int) -> String {
        let dollars = Double(cents) / 100.0
        return String(format: "$%.2f", dollars)
    }
    static func moneyShort(cents: Int) -> String {
        let dollars = Int((Double(cents) / 100.0).rounded())
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        return "$" + (formatter.string(from: NSNumber(value: dollars)) ?? "\(dollars)")
    }
    static func weight(lb: Int) -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        return (formatter.string(from: NSNumber(value: lb)) ?? "\(lb)") + " lb"
    }
}
