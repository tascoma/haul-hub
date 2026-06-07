import SwiftUI

/// Read-only payment breakdown shown on load-detail screens. Hauler view
/// emphasizes the payout; shipper view emphasizes the total charged.
struct PaymentStatusCard: View {
    let payment: Payment
    /// True on the hauler side (highlight payout); false on the shipper side.
    var emphasizePayout: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("PAYMENT")
                    .font(.system(size: 11, weight: .semibold))
                    .tracking(0.5)
                    .foregroundStyle(HHColor.ink500)
                Spacer()
                HHPill(text: payment.status.label, style: payment.status.pillStyle)
            }

            VStack(spacing: 0) {
                HHRowKV(key: "Load price",
                        value: HHFormat.money(cents: payment.amountCents))
                HHRowKV(key: "Platform fee",
                        value: "−\(HHFormat.money(cents: payment.platformFeeCents))",
                        muted: true)
                Divider().background(HHColor.ink200).padding(.vertical, 4)
                if emphasizePayout {
                    HHRowKV(key: "Your payout",
                            value: HHFormat.money(cents: payment.haulerPayoutCents),
                            positive: true,
                            big: true)
                } else {
                    HHRowKV(key: "Total charged",
                            value: HHFormat.money(cents: payment.amountCents),
                            big: true)
                }
            }
        }
        .hhCard()
    }
}
