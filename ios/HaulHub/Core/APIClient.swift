import Foundation

enum APIError: Error, LocalizedError {
    case invalidResponse
    case http(status: Int, body: String)
    case decoding(Error)
    case transport(Error)

    var errorDescription: String? {
        switch self {
        case .invalidResponse: return "Invalid response from server"
        case .http(let status, let body): return "HTTP \(status): \(body)"
        case .decoding(let err): return "Decode failed: \(err.localizedDescription)"
        case .transport(let err): return "Transport: \(err.localizedDescription)"
        }
    }
}

/// Provides the bearer token used on every authed request. Swappable for tests.
protocol TokenProvider {
    func token() -> String?
}

struct KeychainTokenProvider: TokenProvider {
    func token() -> String? { KeychainStore.loadToken() }
}

struct APIClient {
    private let base: URL
    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder
    private let tokenProvider: TokenProvider

    init(
        base: URL = Config.apiBaseURL,
        session: URLSession = .shared,
        tokenProvider: TokenProvider = KeychainTokenProvider()
    ) {
        self.base = base
        self.session = session
        self.tokenProvider = tokenProvider

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        // FastAPI / Pydantic may return ISO 8601 dates with or without
        // fractional seconds (e.g. "2024-01-15T10:30:00Z" or
        // "2024-01-15T10:30:00.123456Z"). Try both formats.
        let fmtFrac = ISO8601DateFormatter()
        fmtFrac.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        let fmtBasic = ISO8601DateFormatter()
        fmtBasic.formatOptions = [.withInternetDateTime]
        decoder.dateDecodingStrategy = .custom { dec in
            let container = try dec.singleValueContainer()
            let str = try container.decode(String.self)
            if let d = fmtFrac.date(from: str) { return d }
            if let d = fmtBasic.date(from: str) { return d }
            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "Cannot parse ISO8601 date: \(str)"
            )
        }
        self.decoder = decoder

        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.dateEncodingStrategy = .iso8601
        self.encoder = encoder
    }

    func get<T: Decodable>(_ path: String) async throws -> T {
        try await send(path: path, method: "GET", body: Optional<Empty>.none)
    }

    func post<Body: Encodable, T: Decodable>(_ path: String, body: Body) async throws -> T {
        try await send(path: path, method: "POST", body: body)
    }

    /// POST with no response body decoding (e.g. fire-and-forget).
    func postVoid<Body: Encodable>(_ path: String, body: Body) async throws {
        let _: Empty = try await send(path: path, method: "POST", body: body, allowEmpty: true)
    }

    func put<Body: Encodable, T: Decodable>(_ path: String, body: Body) async throws -> T {
        try await send(path: path, method: "PUT", body: body)
    }

    func patch<Body: Encodable, T: Decodable>(_ path: String, body: Body) async throws -> T {
        try await send(path: path, method: "PATCH", body: body)
    }

    /// PATCH that ignores the response body. Useful when an endpoint returns 200
    /// with content we don't need to decode (e.g. enable-hauler idempotent case).
    func patchVoid<Body: Encodable>(_ path: String, body: Body) async throws {
        let _: Empty = try await send(path: path, method: "PATCH", body: body, allowEmpty: true)
    }

    func delete(_ path: String) async throws {
        let _: Empty = try await send(path: path, method: "DELETE", body: Optional<Empty>.none, allowEmpty: true)
    }

    private struct Empty: Codable {}

    private func send<Body: Encodable, T: Decodable>(
        path: String,
        method: String,
        body: Body?,
        allowEmpty: Bool = false,
        skipAuth: Bool = false
    ) async throws -> T {
        let url = base.appendingPathComponent(path)
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        if !skipAuth, let token = tokenProvider.token() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        if let body {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            do {
                request.httpBody = try encoder.encode(body)
            } catch {
                throw APIError.decoding(error)
            }
        }

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            throw APIError.transport(error)
        }

        guard let http = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard (200..<300).contains(http.statusCode) else {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw APIError.http(status: http.statusCode, body: body)
        }

        if allowEmpty, T.self == Empty.self {
            return Empty() as! T
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decoding(error)
        }
    }
}
