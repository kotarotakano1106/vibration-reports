import { afterEach, describe, expect, it, vi } from "vitest";

const originalBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

async function importGetHealth() {
  vi.resetModules();
  return import("@/features/health/services/get-health");
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.resetModules();

  if (originalBaseUrl === undefined) {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
  } else {
    process.env.NEXT_PUBLIC_API_BASE_URL = originalBaseUrl;
  }
});

describe("getHealth", () => {
  it("throws when NEXT_PUBLIC_API_BASE_URL is missing", async () => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    const { getHealth } = await importGetHealth();

    await expect(getHealth()).rejects.toThrow(
      "NEXT_PUBLIC_API_BASE_URLが設定されていません。",
    );
  });

  it("gets the health status from FastAPI", async () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          status: "ok",
          service: "vibration-reports-api",
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { getHealth } = await importGetHealth();

    await expect(getHealth()).resolves.toEqual({
      status: "ok",
      service: "vibration-reports-api",
    });
    expect(fetchMock).toHaveBeenCalledOnce();
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/health",
      {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
        cache: "no-store",
      },
    );
  });

  it("throws an error containing the HTTP status", async () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 503 })),
    );
    const { getHealth } = await importGetHealth();

    await expect(getHealth()).rejects.toThrow(
      "FastAPIとの通信に失敗しました。HTTP 503",
    );
  });

  it("propagates a fetch network error", async () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";
    const networkError = new TypeError("Failed to fetch");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(networkError));
    const { getHealth } = await importGetHealth();

    await expect(getHealth()).rejects.toBe(networkError);
  });
});
