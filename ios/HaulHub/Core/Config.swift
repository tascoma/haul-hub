import Foundation

enum Config {
    static var apiBaseURL: URL {
        let raw = ProcessInfo.processInfo.environment["API_BASE_URL"]
            ?? "http://127.0.0.1:8000"
        guard let url = URL(string: raw) else {
            fatalError("Invalid API_BASE_URL: \(raw)")
        }
        return url
    }
}
