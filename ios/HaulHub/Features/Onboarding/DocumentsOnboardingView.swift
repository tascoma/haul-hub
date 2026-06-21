import PhotosUI
import SwiftUI

struct DocumentsOnboardingView: View {
    @EnvironmentObject private var session: AuthSession
    @Environment(\.apiClient) private var api

    // Insurance
    @State private var insuranceItem: PhotosPickerItem?
    @State private var insuranceImageData: Data?
    @State private var carrierName = ""
    @State private var policyNumber = ""
    @State private var expiresOn = Date()
    @State private var hasExpiresOn = false

    // Driver's license
    @State private var licenseItem: PhotosPickerItem?
    @State private var licenseImageData: Data?

    @State private var submitting = false
    @State private var error: String?

    var body: some View {
        ScrollView {
            VStack(spacing: 18) {
                Text("Verification documents")
                    .font(HHFont.title)
                Text("We need proof of insurance and a driver's license before you can accept jobs.")
                    .font(HHFont.small)
                    .foregroundStyle(HHColor.ink500)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 24)

                // ─── Insurance certificate ─────────────────────────────────────
                VStack(alignment: .leading, spacing: 12) {
                    Text("Proof of insurance")
                        .font(HHFont.smallBold)
                        .foregroundStyle(HHColor.ink700)

                    PhotosPicker(selection: $insuranceItem, matching: .images) {
                        Label(
                            insuranceImageData != nil ? "Change insurance certificate" : "Choose insurance certificate",
                            systemImage: "doc.badge.plus"
                        )
                        .font(HHFont.small)
                        .frame(maxWidth: .infinity)
                        .padding(12)
                        .background(HHColor.paper)
                        .overlay(
                            RoundedRectangle(cornerRadius: HHRadius.sm)
                                .strokeBorder(HHColor.ink200, lineWidth: 1)
                        )
                        .clipShape(RoundedRectangle(cornerRadius: HHRadius.sm))
                    }
                    .onChange(of: insuranceItem) { _, item in
                        Task {
                            insuranceImageData = try? await item?.loadTransferable(type: Data.self)
                        }
                    }

                    if insuranceImageData != nil {
                        Text("✓ File selected")
                            .font(HHFont.small)
                            .foregroundStyle(HHColor.success)
                    }

                    labeled("Insurance carrier") {
                        TextField("e.g. State Farm", text: $carrierName).textFieldStyle()
                    }
                    labeled("Policy number") {
                        TextField("e.g. POL-123456", text: $policyNumber).textFieldStyle()
                    }

                    Toggle("Enter policy expiry date", isOn: $hasExpiresOn)
                    if hasExpiresOn {
                        DatePicker("Expiry", selection: $expiresOn, displayedComponents: .date)
                            .datePickerStyle(.compact)
                    }
                }
                .padding(14)
                .background(HHColor.paper)
                .overlay(
                    RoundedRectangle(cornerRadius: HHRadius.md)
                        .strokeBorder(HHColor.ink200, lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: HHRadius.md))
                .padding(.horizontal, 20)

                // ─── Driver's license ──────────────────────────────────────────
                VStack(alignment: .leading, spacing: 12) {
                    Text("Driver's license")
                        .font(HHFont.smallBold)
                        .foregroundStyle(HHColor.ink700)

                    PhotosPicker(selection: $licenseItem, matching: .images) {
                        Label(
                            licenseImageData != nil ? "Change driver's license photo" : "Choose driver's license photo",
                            systemImage: "creditcard.viewfinder"
                        )
                        .font(HHFont.small)
                        .frame(maxWidth: .infinity)
                        .padding(12)
                        .background(HHColor.paper)
                        .overlay(
                            RoundedRectangle(cornerRadius: HHRadius.sm)
                                .strokeBorder(HHColor.ink200, lineWidth: 1)
                        )
                        .clipShape(RoundedRectangle(cornerRadius: HHRadius.sm))
                    }
                    .onChange(of: licenseItem) { _, item in
                        Task {
                            licenseImageData = try? await item?.loadTransferable(type: Data.self)
                        }
                    }

                    if licenseImageData != nil {
                        Text("✓ File selected")
                            .font(HHFont.small)
                            .foregroundStyle(HHColor.success)
                    }
                }
                .padding(14)
                .background(HHColor.paper)
                .overlay(
                    RoundedRectangle(cornerRadius: HHRadius.md)
                        .strokeBorder(HHColor.ink200, lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: HHRadius.md))
                .padding(.horizontal, 20)

                if let error {
                    Text(error)
                        .font(HHFont.small)
                        .foregroundStyle(HHColor.danger)
                        .padding(.horizontal, 20)
                }

                Button {
                    Task { await submit() }
                } label: {
                    Text(submitting ? "Uploading…" : "Continue")
                }
                .buttonStyle(HHAccentButtonStyle())
                .disabled(submitting || insuranceImageData == nil || licenseImageData == nil)
                .padding(.horizontal, 20)
            }
            .padding(.top, 12)
        }
        .background(HHColor.ink50.ignoresSafeArea())
    }

    private func submit() async {
        guard let insuranceData = insuranceImageData, let licenseData = licenseImageData else {
            error = "Please select both an insurance certificate and a driver's license photo."
            return
        }
        error = nil
        submitting = true
        do {
            let expiryString: String? = hasExpiresOn ? ISO8601DateFormatter().string(from: expiresOn).prefix(10).description : nil
            async let ins: EmptyResponse = uploadMultipart(
                path: "/api/me/documents/upload",
                fileData: insuranceData,
                filename: "insurance.jpg",
                mimeType: "image/jpeg",
                fields: [
                    "kind": "insurance_certificate",
                    "carrier_name": carrierName.isEmpty ? nil : carrierName,
                    "policy_number": policyNumber.isEmpty ? nil : policyNumber,
                    "expires_on": expiryString,
                ]
            )
            async let lic: EmptyResponse = uploadMultipart(
                path: "/api/me/verifications/upload",
                fileData: licenseData,
                filename: "license.jpg",
                mimeType: "image/jpeg",
                fields: ["kind": "drivers_license"]
            )
            _ = try await (ins, lic)
            await session.advance()
        } catch {
            self.error = (error as? LocalizedError)?.errorDescription ?? "Upload failed"
        }
        submitting = false
    }

    private func uploadMultipart<T: Decodable>(
        path: String,
        fileData: Data,
        filename: String,
        mimeType: String,
        fields: [String: String?]
    ) async throws -> T {
        let boundary = UUID().uuidString
        let url = Config.apiBaseURL.appendingPathComponent(path)
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        if let token = KeychainStore.loadToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        var body = Data()
        for (key, value) in fields {
            guard let value else { continue }
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(key)\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(value)\r\n".data(using: .utf8)!)
        }
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8)!)
        body.append(fileData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else { throw APIError.invalidResponse }
        guard (200..<300).contains(http.statusCode) else {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw APIError.http(status: http.statusCode, body: body)
        }
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return try decoder.decode(T.self, from: data)
    }
}

private struct EmptyResponse: Decodable {}

@ViewBuilder
private func labeled<Content: View>(_ label: String, @ViewBuilder content: () -> Content) -> some View {
    VStack(alignment: .leading, spacing: 6) {
        Text(label).font(HHFont.smallBold).foregroundStyle(HHColor.ink700)
        content()
    }
}

private extension View {
    func textFieldStyle() -> some View {
        self
            .padding(12)
            .background(HHColor.paper)
            .overlay(
                RoundedRectangle(cornerRadius: HHRadius.sm)
                    .strokeBorder(HHColor.ink200, lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: HHRadius.sm))
    }
}
