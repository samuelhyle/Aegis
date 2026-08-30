import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient, getApiClient } from "@/lib/api/client";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

describe("ApiClient", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    apiClient.setApiKey("");
  });

  describe("getHealth", () => {
    it("calls the health endpoint", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: "healthy", service: "aegis", version: "1.0" }),
      });
      const result = await apiClient.getHealth();
      expect(result.status).toBe("healthy");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/health"),
        expect.any(Object)
      );
    });
  });

  describe("listPatients", () => {
    it("fetches patients with default params", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ patients: [], total: 0, has_more: false }),
      });
      const result = await apiClient.listPatients();
      expect(result.patients).toEqual([]);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/v1/patients?limit=50&offset=0"),
        expect.any(Object)
      );
    });

    it("passes custom limit and offset", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ patients: [], total: 0, has_more: false }),
      });
      await apiClient.listPatients(25, 10);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/v1/patients?limit=25&offset=10"),
        expect.any(Object)
      );
    });
  });

  describe("getPatient", () => {
    it("fetches patient by ID", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ patient_id: "p1", first_name: "John" }),
      });
      const result = await apiClient.getPatient("p1");
      expect(result.patient_id).toBe("p1");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/v1/patients/p1"),
        expect.any(Object)
      );
    });
  });

  describe("runInvestigation", () => {
    it("sends POST request", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ trace_id: "t1", conclusion: "test" }),
      });
      await apiClient.runInvestigation("p1", "What is wrong?");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/v1/investigations"),
        expect.objectContaining({ method: "POST" })
      );
    });
  });

  describe("listTraces", () => {
    it("builds query params correctly", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ traces: [], total: 0, has_more: false }),
      });
      await apiClient.listTraces("p1", true, 10, 5);
      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toContain("patient_id=p1");
      expect(url).toContain("reviewed=true");
      expect(url).toContain("limit=10");
      expect(url).toContain("offset=5");
    });

    it("omits undefined optional params", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ traces: [], total: 0, has_more: false }),
      });
      await apiClient.listTraces(undefined, undefined, 50, 0);
      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).not.toContain("patient_id");
      expect(url).not.toContain("reviewed");
    });
  });

  describe("reviewTrace", () => {
    it("sends review decision", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ trace_id: "t1", reviewed: true }),
      });
      await apiClient.reviewTrace("t1", "approved", "reviewer1", "Looks good");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/v1/traces/t1/review"),
        expect.objectContaining({ method: "POST" })
      );
      const body = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(body.decision).toBe("approved");
      expect(body.reviewer_id).toBe("reviewer1");
      expect(body.notes).toBe("Looks good");
    });
  });

  describe("searchVectors", () => {
    it("builds search query", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ results: [], total: 0 }),
      });
      await apiClient.searchVectors("diabetes", "p1", ["condition"], 5);
      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toContain("query=diabetes");
      expect(url).toContain("patient_id=p1");
      expect(url).toContain("source_types=condition");
      expect(url).toContain("top_k=5");
    });
  });

  describe("error handling", () => {
    it("throws on non-OK response", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: "Not Found",
        json: () => Promise.resolve({ detail: "Patient not found" }),
      });
      await expect(apiClient.getPatient("missing")).rejects.toThrow("Patient not found");
    });

    it("throws generic error when no detail", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
        json: () => Promise.resolve({}),
      });
      await expect(apiClient.getHealth()).rejects.toThrow("API error: 500");
    });

    it("handles JSON parse errors gracefully", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: "Bad Request",
        json: () => Promise.reject(new Error("invalid json")),
      });
      await expect(apiClient.getHealth()).rejects.toThrow("Bad Request");
    });
  });

  describe("API key handling", () => {
    it("includes API key in headers when set", async () => {
      apiClient.setApiKey("test-key-123");
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: "ok" }),
      });
      await apiClient.getHealth();
      const headers = mockFetch.mock.calls[0][1].headers;
      expect(headers["X-API-Key"]).toBe("test-key-123");
    });

    it("does not include API key when not set", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: "ok" }),
      });
      await apiClient.getHealth();
      const headers = mockFetch.mock.calls[0][1].headers;
      expect(headers["X-API-Key"]).toBeUndefined();
    });
  });

  describe("getApiClient", () => {
    it("returns the singleton apiClient", () => {
      expect(getApiClient()).toBe(apiClient);
    });
  });
});
