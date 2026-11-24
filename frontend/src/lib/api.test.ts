import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "./api";

describe("apiFetch", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("returns parsed JSON on a successful response and attaches /api/v1 and bearer token", async () => {
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ status: "ok", app_env: "dev", firestore: "ok" }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );
    vi.stubGlobal("fetch", mockFetch);

    const result = await apiFetch<{
      status: string;
      app_env: string;
      firestore: string;
    }>("/health", { token: "test-token" });

    expect(result).toEqual({ status: "ok", app_env: "dev", firestore: "ok" });
    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://localhost:8000/api/v1/health");
    expect(init.headers).toMatchObject({
      Accept: "application/json",
      Authorization: "Bearer test-token",
    });
  });

  it("turns backend error format into a typed ApiError", async () => {
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            code: "NOT_FOUND",
            message_bn: "অনুরোধ করা তথ্য পাওয়া যায়নি।",
            message_en: "Requested resource was not found.",
          },
        }),
        {
          status: 404,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );
    vi.stubGlobal("fetch", mockFetch);

    await expect(apiFetch("/missing")).rejects.toSatisfy((err: unknown) => {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.code).toBe("NOT_FOUND");
      expect(apiErr.messageEn).toBe("Requested resource was not found.");
      expect(apiErr.messageBn).toBe("অনুরোধ করা তথ্য পাওয়া যায়নি।");
      expect(apiErr.status).toBe(404);
      return true;
    });
  });

  it("turns a network failure into a clear ApiError", async () => {
    const mockFetch = vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));
    vi.stubGlobal("fetch", mockFetch);

    await expect(apiFetch("/health")).rejects.toSatisfy((err: unknown) => {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.code).toBe("NETWORK_ERROR");
      expect(apiErr.status).toBe(0);
      expect(apiErr.messageEn).toContain("Unable to reach the backend server");
      expect(apiErr.messageBn.length).toBeGreaterThan(0);
      return true;
    });
  });
});
