import SwiftUI

/// Shipper form to post a new load. Mirrors the web PostLoadPage field set
/// and submits to POST /api/loads via LoadsClient.
struct PostLoadView: View {
    @Environment(\.apiClient) private var apiClient

    // Item
    @State private var title = ""
    @State private var description = ""
    @State private var weightLbs = ""
    @State private var lengthFt = ""
    @State private var widthFt = ""
    @State private var heightFt = ""

    // Pickup
    @State private var pickupAddress = ""
    @State private var pickupCity = ""
    @State private var pickupState = ""
    @State private var pickupZip = ""
    @State private var pickupWindowStart = Date().addingTimeInterval(86_400)
    @State private var pickupWindowEnd = Date().addingTimeInterval(86_400 + 4 * 3600)

    // Dropoff
    @State private var dropoffAddress = ""
    @State private var dropoffCity = ""
    @State private var dropoffState = ""
    @State private var dropoffZip = ""
    @State private var dropoffBy = Date().addingTimeInterval(2 * 86_400)

    // Logistics
    @State private var distanceMiles: Double?
    @State private var routing = false
    @State private var routeError: String?
    @State private var urgency: Urgency = .standard

    @State private var submitting = false
    @State private var error: String?
    @State private var postedLoad: APILoad?

    private var client: LoadsClient { LoadsClient(api: apiClient) }

    private var pickupComplete: Bool {
        !pickupAddress.isEmpty && !pickupCity.isEmpty && !pickupState.isEmpty && !pickupZip.isEmpty
    }

    private var dropoffComplete: Bool {
        !dropoffAddress.isEmpty && !dropoffCity.isEmpty && !dropoffState.isEmpty && !dropoffZip.isEmpty
    }

    /// Changes whenever any address field does; drives route recalculation.
    private var routeKey: String {
        [pickupAddress, pickupCity, pickupState, pickupZip,
         dropoffAddress, dropoffCity, dropoffState, dropoffZip].joined(separator: "|")
    }

    private var canSubmit: Bool {
        !title.isEmpty
            && Int(weightLbs) ?? 0 > 0
            && pickupComplete
            && dropoffComplete
            && (distanceMiles ?? 0) > 0
            && pickupWindowEnd >= pickupWindowStart
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                if let load = postedLoad {
                    successCard(load)
                } else {
                    form
                }
            }
            .background(HHColor.ink50.ignoresSafeArea())
            .navigationTitle("Post a load")
            .task(id: routeKey) { await recomputeDistance() }
        }
    }

    // MARK: - Form

    private var form: some View {
        VStack(spacing: 22) {
            section("Item") {
                labeled("Title") {
                    TextField("e.g. Upright piano", text: $title).hhField()
                }
                labeled("Description (optional)") {
                    TextField("Anything the hauler should know", text: $description, axis: .vertical)
                        .lineLimit(2...4)
                        .hhField()
                }
                labeled("Weight (lb)") {
                    TextField("1500", text: $weightLbs).keyboardType(.numberPad).hhField()
                }
                HStack(spacing: 10) {
                    labeled("Length (ft)") {
                        TextField("—", text: $lengthFt).keyboardType(.decimalPad).hhField()
                    }
                    labeled("Width (ft)") {
                        TextField("—", text: $widthFt).keyboardType(.decimalPad).hhField()
                    }
                    labeled("Height (ft)") {
                        TextField("—", text: $heightFt).keyboardType(.decimalPad).hhField()
                    }
                }
            }

            section("Pickup") {
                labeled("Address") {
                    TextField("123 Main St", text: $pickupAddress).hhField()
                }
                addressRow(city: $pickupCity, state: $pickupState, zip: $pickupZip)
                labeled("Window start") {
                    DatePicker("", selection: $pickupWindowStart).labelsHidden()
                }
                labeled("Window end") {
                    DatePicker("", selection: $pickupWindowEnd, in: pickupWindowStart...).labelsHidden()
                }
            }

            section("Dropoff") {
                labeled("Address") {
                    TextField("456 Elm St", text: $dropoffAddress).hhField()
                }
                addressRow(city: $dropoffCity, state: $dropoffState, zip: $dropoffZip)
                labeled("Deliver by") {
                    DatePicker("", selection: $dropoffBy).labelsHidden()
                }
            }

            section("Logistics") {
                labeled("Estimated distance") {
                    distanceDisplay
                }
                labeled("Urgency") {
                    Picker("", selection: $urgency) {
                        Text("Standard").tag(Urgency.standard)
                        Text("Express").tag(Urgency.express)
                    }
                    .pickerStyle(.segmented)
                }
            }

            if let error {
                HHErrorBanner(message: error).padding(.horizontal, 20)
            }

            Button {
                Task { await submit() }
            } label: {
                Text(submitting ? "Posting…" : "Post load")
            }
            .buttonStyle(HHAccentButtonStyle())
            .disabled(submitting || !canSubmit)
            .padding(.horizontal, 20)
        }
        .padding(.vertical, 16)
    }

    private func addressRow(city: Binding<String>, state: Binding<String>, zip: Binding<String>) -> some View {
        HStack(spacing: 10) {
            labeled("City") { TextField("Austin", text: city).hhField() }
            labeled("State") {
                TextField("TX", text: state)
                    .textInputAutocapitalization(.characters)
                    .hhField()
            }
            labeled("ZIP") {
                TextField("78701", text: zip).keyboardType(.numbersAndPunctuation).hhField()
            }
        }
    }

    // MARK: - Distance display

    @ViewBuilder
    private var distanceDisplay: some View {
        Group {
            if routing {
                HStack(spacing: 8) {
                    ProgressView()
                    Text("Calculating route…")
                        .font(HHFont.small)
                        .foregroundStyle(HHColor.ink500)
                }
            } else if let distanceMiles {
                HStack {
                    Text(String(format: "%.1f mi", distanceMiles))
                        .font(HHFont.bodyBold)
                        .foregroundStyle(HHColor.ink900)
                    Spacer()
                    Text("driving distance")
                        .font(HHFont.small)
                        .foregroundStyle(HHColor.ink500)
                }
            } else if let routeError {
                Text(routeError)
                    .font(HHFont.small)
                    .foregroundStyle(HHColor.danger)
            } else {
                Text("Fill in both addresses to calculate")
                    .font(HHFont.small)
                    .foregroundStyle(HHColor.ink400)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .hhField()
    }

    // MARK: - Success

    private func successCard(_ load: APILoad) -> some View {
        VStack(spacing: 14) {
            ZStack {
                Circle().fill(HHColor.accentSoft).frame(width: 56, height: 56)
                Image(systemName: "checkmark")
                    .font(.system(size: 24, weight: .bold))
                    .foregroundStyle(HHColor.accentText)
            }
            .padding(.top, 24)
            Text("Load posted")
                .font(HHFont.title)
                .foregroundStyle(HHColor.ink900)
            Text("\(load.title) is live. Track it from the Tracking tab as haulers respond.")
                .font(HHFont.small)
                .foregroundStyle(HHColor.ink600)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 28)
            HHRowKV(key: "Quoted price", value: HHFormat.money(cents: load.calculatedPriceCents), big: true)
                .padding(.horizontal, 24)
            Button("Post another") { resetForm() }
                .buttonStyle(HHGhostButtonStyle())
                .padding(.horizontal, 20)
                .padding(.top, 4)
        }
    }

    // MARK: - Actions

    private func submit() async {
        error = nil
        submitting = true
        let body = CreateLoadRequest(
            title: title,
            description: description.isEmpty ? nil : description,
            weightLbs: Int(weightLbs) ?? 0,
            lengthFt: Double(lengthFt),
            widthFt: Double(widthFt),
            heightFt: Double(heightFt),
            pickupAddress: pickupAddress,
            pickupCity: pickupCity,
            pickupState: pickupState,
            pickupZip: pickupZip,
            pickupWindowStart: pickupWindowStart,
            pickupWindowEnd: pickupWindowEnd,
            dropoffAddress: dropoffAddress,
            dropoffCity: dropoffCity,
            dropoffState: dropoffState,
            dropoffZip: dropoffZip,
            dropoffBy: dropoffBy,
            estimatedDistanceMiles: distanceMiles ?? 0,
            urgency: urgency
        )
        do {
            postedLoad = try await client.createLoad(body)
        } catch let err as APIError {
            error = err.errorDescription
        } catch {
            self.error = error.localizedDescription
        }
        submitting = false
    }

    private func resetForm() {
        title = ""; description = ""; weightLbs = ""
        lengthFt = ""; widthFt = ""; heightFt = ""
        pickupAddress = ""; pickupCity = ""; pickupState = ""; pickupZip = ""
        dropoffAddress = ""; dropoffCity = ""; dropoffState = ""; dropoffZip = ""
        distanceMiles = nil; routeError = nil; urgency = .standard
        postedLoad = nil; error = nil
    }

    /// Geocode + route both addresses into a driving distance. Debounced and
    /// auto-cancelled by `.task(id:)` whenever an address field changes.
    private func recomputeDistance() async {
        guard pickupComplete, dropoffComplete else {
            distanceMiles = nil
            routeError = nil
            return
        }
        // Debounce typing; cancellation (a newer edit) bails out here.
        do { try await Task.sleep(for: .milliseconds(600)) } catch { return }

        routing = true
        routeError = nil
        defer { routing = false }
        do {
            let miles = try await RouteDistance.miles(
                from: fullAddress(pickupAddress, pickupCity, pickupState, pickupZip),
                to: fullAddress(dropoffAddress, dropoffCity, dropoffState, dropoffZip)
            )
            guard !Task.isCancelled else { return }
            distanceMiles = (miles * 10).rounded() / 10
        } catch is CancellationError {
            // Superseded by a newer edit; leave state for the next run.
        } catch {
            distanceMiles = nil
            routeError = (error as? LocalizedError)?.errorDescription
                ?? "Couldn't route these addresses"
        }
    }

    private func fullAddress(_ line1: String, _ city: String, _ state: String, _ zip: String) -> String {
        "\(line1), \(city), \(state) \(zip)"
    }

    // MARK: - Layout helpers

    @ViewBuilder
    private func section<Content: View>(_ title: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title.uppercased())
                .font(.system(size: 11, weight: .bold))
                .tracking(0.6)
                .foregroundStyle(HHColor.ink500)
            content()
        }
        .padding(16)
        .hhCard()
        .padding(.horizontal, 16)
    }

    @ViewBuilder
    private func labeled<Content: View>(_ label: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label).font(HHFont.smallBold).foregroundStyle(HHColor.ink700)
            content()
        }
    }
}

private extension View {
    func hhField() -> some View {
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

#Preview {
    PostLoadView()
}
