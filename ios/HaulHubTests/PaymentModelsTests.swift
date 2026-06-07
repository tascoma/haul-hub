import XCTest
@testable import HaulHub

// MARK: - URLProtocol stub

/// Intercepts requests so PaymentsClient can be exercised against canned
/// responses without a live backend.
final class StubURLProtocol: URLProtocol {
    /// (statusCode, body) for the next request. Reset per test.
    static var responder: ((URLRequest) -> (Int, Data))?

    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        let (status, data) = Self.responder?(request) ?? (500, Data())
        let response = HTTPURLResponse(
            url: request.url!,
            statusCode: status,
            httpVersion: nil,
            headerFields: ["Content-Type": "application/json"]
        )!
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        client?.urlProtocol(self, didLoad: data)
        client?.urlProtocolDidFinishLoading(self)
    }

    override func stopLoading() {}
}

private struct NilTokenProvider: TokenProvider {
    func token() -> String? { nil }
}

final class PaymentModelsTests: XCTestCase {

    private func makeClient(status: Int, json: String) -> PaymentsClient {
        StubURLProtocol.responder = { _ in (status, Data(json.utf8)) }
        let config = URLSessionConfiguration.ephemeral
        config.protocolClasses = [StubURLProtocol.self]
        let session = URLSession(configuration: config)
        let api = APIClient(session: session, tokenProvider: NilTokenProvider())
        return PaymentsClient(api: api)
    }

    override func tearDown() {
        StubURLProtocol.responder = nil
        super.tearDown()
    }

    // MARK: - Decoding

    func testPaymentDecodesFromSnakeCaseJSON() async throws {
        let json = """
        {"id":"pay_1","load_id":"load_1","amount_cents":50000,
         "platform_fee_cents":5000,"hauler_payout_cents":45000,
         "status":"authorized","stripe_payment_intent_id":"pi_1",
         "stripe_transfer_id":null,"authorized_at":"2026-06-06T10:00:00Z",
         "captured_at":null,"transferred_at":null,"refunded_at":null,
         "created_at":"2026-06-06T09:00:00Z","updated_at":"2026-06-06T10:00:00Z"}
        """
        let client = makeClient(status: 200, json: json)
        let payment = try await client.payment(loadId: "load_1")
        XCTAssertEqual(payment?.amountCents, 50000)
        XCTAssertEqual(payment?.platformFeeCents, 5000)
        XCTAssertEqual(payment?.haulerPayoutCents, 45000)
        XCTAssertEqual(payment?.status, .authorized)
        XCTAssertEqual(payment?.stripePaymentIntentId, "pi_1")
        XCTAssertNil(payment?.stripeTransferId)
        XCTAssertNotNil(payment?.authorizedAt)
    }

    func testPaymentMethodDecodesAndFormats() async throws {
        let json = #"{"brand":"visa","last4":"4242","exp_month":12,"exp_year":2027}"#
        let client = makeClient(status: 200, json: json)
        let pm = try await client.paymentMethod()
        XCTAssertEqual(pm?.last4, "4242")
        XCTAssertEqual(pm?.display, "Visa •••• 4242")
        XCTAssertEqual(pm?.expiryDisplay, "12/27")
    }

    // MARK: - 404 → nil mapping

    func testPaymentNotFoundReturnsNil() async throws {
        let client = makeClient(status: 404, json: #"{"detail":"No payment yet"}"#)
        let payment = try await client.payment(loadId: "missing")
        XCTAssertNil(payment)
    }

    func testPaymentMethodNotFoundReturnsNil() async throws {
        let client = makeClient(status: 404, json: #"{"detail":"No payment method saved"}"#)
        let pm = try await client.paymentMethod()
        XCTAssertNil(pm)
    }

    func testServerErrorStillThrows() async {
        let client = makeClient(status: 500, json: #"{"detail":"boom"}"#)
        do {
            _ = try await client.payment(loadId: "x")
            XCTFail("Expected a 500 to throw")
        } catch {
            // expected
        }
    }

    // MARK: - Status mapping

    func testPaymentStatusLabels() {
        XCTAssertEqual(PaymentStatus.pending.label, "Awaiting confirmation")
        XCTAssertEqual(PaymentStatus.authorized.label, "Funds held")
        XCTAssertEqual(PaymentStatus.transferred.label, "Paid to hauler")
        XCTAssertEqual(PaymentStatus.failed.label, "Payment failed")
    }
}
