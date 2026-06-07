import SwiftUI
import SafariServices

/// Presents an `SFSafariViewController` as a SwiftUI sheet. Used to show Stripe's
/// hosted Connect onboarding page; the caller refreshes profile state on dismiss.
struct SafariView: UIViewControllerRepresentable {
    let url: URL

    func makeUIViewController(context: Context) -> SFSafariViewController {
        SFSafariViewController(url: url)
    }

    func updateUIViewController(_ controller: SFSafariViewController, context: Context) {}
}
