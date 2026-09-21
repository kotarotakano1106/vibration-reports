import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { apiRequest, buildApiUrl } from "@/lib/api/client";
import { ApiError } from "@/lib/errors/api-error";

const originalBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

describe("buildApiUrl", () => {
  afterEach(() => {
    if (originalBaseUrl === undefined) {
      delete process.env.NEXT_PUBLIC_API_BASE_URL;
    } else {
      process.env.NEXT_PUBLIC_API_BASE_URL = originalBaseUrl;
    }
  });

  it("joins the base URL and path without duplicate slashes", () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000///";

    expect(buildApiUrl("///api/v1/reports")).toBe(
      "http://localhost:8000/api/v1/reports",
    );
  });

  it("throws ApiError when the base URL is missing", () => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;

    expect(() => buildApiUrl("/health")).toThrowError(ApiError);
    expect(() => buildApiUrl("/health")).toThrow(
      "NEXT_PUBLIC_API_BASE_URLが設定されていません。",
    );
  });
});

describe("apiRequest", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    if (originalBaseUrl === undefined) {
      delete process.env.NEXT_PUBLIC_API_BASE_URL;
    } else {
      process.env.NEXT_PUBLIC_API_BASE_URL = originalBaseUrl;
    }
  });

  it("sends a GET request and returns JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(apiRequest<{ status: string }>("/health")).resolves.toEqual({
      status: "ok",
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/health",
      expect.objectContaining({
        method: "GET",
        headers: { Accept: "application/json" },
        cache: "no-store",
      }),
    );
  });

  it("serializes a JSON request body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ answer: "ok" }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await apiRequest("/api/v1/chat", {
      method: "POST",
      json: { query: "状態を確認" },
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/chat",
      expect.objectContaining({
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: "状態を確認" }),
      }),
    );
  });

  it("sends FormData without setting Content-Type", async () => {
    const formData = new FormData();
    formData.append("equipment_id", "MOTOR-001");
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    await apiRequest("/api/v1/files", {
      method: "POST",
      formData,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/files",
      expect.objectContaining({
        method: "POST",
        headers: { Accept: "application/json" },
        body: formData,
      }),
    );
  });

  it("returns undefined for an empty successful response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 204 })),
    );

    await expect(apiRequest<void>("/health")).resolves.toBeUndefined();
  });

  it("converts an HTTP JSON error to ApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "対象が見つかりません。" }), {
          status: 404,
        }),
      ),
    );

    const error = await apiRequest("/api/v1/reports/missing").catch(
      (caught) => caught,
    );

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 404,
      detail: "対象が見つかりません。",
      message: "対象が見つかりません。",
    });
  });

  it("uses plain text from a non-JSON error response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("Service unavailable", { status: 503 })),
    );

    await expect(apiRequest("/health")).rejects.toMatchObject({
      status: 503,
      detail: "Service unavailable",
      message: "Service unavailable",
    });
  });

  it("uses the default message for an empty error response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );

    await expect(apiRequest("/health")).rejects.toMatchObject({
      status: 500,
      detail: null,
      message: "ファイルまたはデータベースの保存に失敗しました。",
    });
  });

  it("converts a fetch failure to a network ApiError", async () => {
    const cause = new TypeError("Failed to fetch");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(cause));

    const error = await apiRequest("/health").catch((caught) => caught);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: null,
      detail: null,
      cause,
    });
  });
});
