import XCTest
@testable import HaulHub

final class HaulHubTests: XCTestCase {
    func testConfigHasDefaultBaseURL() {
        XCTAssertNotNil(Config.apiBaseURL.host)
    }
}
