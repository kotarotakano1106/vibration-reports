import { describe, expect, it } from "vitest";

import { ApiError, parseErrorDetail } from "@/lib/errors/api-error";

describe("ApiError", () => {
  it("creates a missing base URL error", () => {
    const error = ApiError.missingBaseUrl();

    expect(error).toBeInstanceOf(Error);
    expect(error.name).toBe("ApiError");
    expect(error.message).toBe(
      "NEXT_PUBLIC_API_BASE_URLが設定されていません。",
    );
    expect(error.status).toBeNull();
    expect(error.detail).toBeNull();
  });

  it("preserves the cause of a network error", () => {
    const cause = new TypeError("fetch failed");
    const error = ApiError.networkError(cause);

    expect(error.message).toBe(
      "サーバーへ接続できませんでした。ネットワーク状態を確認してください。",
    );
    expect(error.status).toBeNull();
    expect(error.detail).toBeNull();
    expect(error.cause).toBe(cause);
  });

  it.each([
    [400, "入力またはCSVファイルが不正です。"],
    [404, "対象のCSVまたは実ファイルが見つかりません。"],
    [409, "同一内容のレポートがすでに登録されています。"],
    [422, "入力内容を確認してください。"],
    [500, "ファイルまたはデータベースの保存に失敗しました。"],
    [
      502,
      "AIレポートの生成に失敗しました。時間をおいて再試行してください。",
    ],
    [503, "サーバーでエラーが発生しました。(HTTP 503)"],
  ])("uses the default message for HTTP %i", (status, message) => {
    const error = ApiError.fromHttpStatus(status, null);

    expect(error.status).toBe(status);
    expect(error.detail).toBeNull();
    expect(error.message).toBe(message);
  });

  it("uses an API detail as the user-facing message", () => {
    const error = ApiError.fromHttpStatus(400, "CSV列が不足しています。");

    expect(error.status).toBe(400);
    expect(error.detail).toBe("CSV列が不足しています。");
    expect(error.message).toBe("CSV列が不足しています。");
  });
});

describe("parseErrorDetail", () => {
  it.each([null, undefined, "error", 500, true])(
    "returns null for a non-object body: %s",
    (body) => {
      expect(parseErrorDetail(body)).toBeNull();
    },
  );

  it("returns a string detail", () => {
    expect(parseErrorDetail({ detail: "入力が不正です。" })).toBe(
      "入力が不正です。",
    );
  });

  it("joins Pydantic validation messages", () => {
    const body = {
      detail: [
        { loc: ["body", "query"], msg: "値が必要です。" },
        { loc: ["body", "limit"], msg: "1以上を指定してください。" },
      ],
    };

    expect(parseErrorDetail(body)).toBe(
      "値が必要です。 / 1以上を指定してください。",
    );
  });

  it("ignores invalid array entries", () => {
    expect(
      parseErrorDetail({ detail: [null, "invalid", {}, { msg: 123 }] }),
    ).toBe("123");
  });

  it("returns null when no usable detail exists", () => {
    expect(parseErrorDetail({ detail: [] })).toBeNull();
    expect(parseErrorDetail({ detail: { msg: "not an array" } })).toBeNull();
  });
});
