import Foundation

/// API client for all load / haul operations.
struct LoadsClient {
    private struct EmptyRequest: Encodable {}

    private let api: APIClient

    init(api: APIClient) {
        self.api = api
    }

    // MARK: - Browse / Discovery

    /// All posted loads available to claim.
    /// Pass optional `city` / `state` to narrow results (URL-encoded internally).
    func listAvailable(city: String? = nil, state: String? = nil) async throws -> [APILoad] {
        var path = "/api/loads"
        var params: [String] = []
        if let c = city, !c.isEmpty {
            params.append("city=\(c.urlEncoded)")
        }
        if let s = state, !s.isEmpty {
            params.append("state=\(s.urlEncoded)")
        }
        if !params.isEmpty { path += "?" + params.joined(separator: "&") }
        return try await api.get(path)
    }

    /// Fetch a single load by ID.
    func load(id: String) async throws -> APILoad {
        try await api.get("/api/loads/\(id)")
    }

    // MARK: - My data

    /// Loads the current user has claimed as hauler (all statuses).
    func myHauls() async throws -> [APILoad] {
        try await api.get("/api/me/hauls")
    }

    /// Loads the current user has posted as shipper (all statuses).
    func myLoads() async throws -> [APILoad] {
        try await api.get("/api/me/loads")
    }

    // MARK: - Lifecycle actions (hauler)

    /// Claim a posted load.
    func accept(id: String) async throws -> APILoad {
        try await api.post("/api/loads/\(id)/accept", body: EmptyRequest())
    }

    /// Confirm cargo has been picked up.
    func markPickedUp(id: String) async throws -> APILoad {
        try await api.post("/api/loads/\(id)/pickup", body: EmptyRequest())
    }

    /// Confirm the truck is en route to dropoff.
    func markInTransit(id: String) async throws -> APILoad {
        try await api.post("/api/loads/\(id)/in-transit", body: EmptyRequest())
    }

    /// Confirm delivery complete.
    func markDelivered(id: String) async throws -> APILoad {
        try await api.post("/api/loads/\(id)/deliver", body: EmptyRequest())
    }
}

// MARK: - String URL helper

private extension String {
    var urlEncoded: String {
        addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? self
    }
}
