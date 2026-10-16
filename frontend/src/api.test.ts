import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "./api";

describe("API client", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("returns decoded service data", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify([{ id: 1, name: "checkout-api" }]), { status: 200 })));

    await expect(api.services()).resolves.toEqual([{ id: 1, name: "checkout-api" }]);
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/services"), expect.objectContaining({ headers: expect.objectContaining({ Authorization: "Bearer operator-demo" }) }));
  });

  it("surfaces backend validation errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Invalid telemetry" }), { status: 422 })));

    await expect(api.services()).rejects.toThrow("Invalid telemetry");
  });
});
