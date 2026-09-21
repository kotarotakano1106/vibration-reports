type ApiErrorParams = {
  message: string;
  status: number | null;
  detail: string | null;
  cause?: unknown;
};

export class ApiError extends Error {
  readonly status: number | null;
  readonly detail: string | null;

  constructor({ message, status, detail, cause }: ApiErrorParams) {
    super(message, { cause });
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }

  static missingBaseUrl(): ApiError {
    return new ApiError({
      message: "NEXT_PUBLIC_API_BASE_URLが設定されていません。",
      status: null,
      detail: null,
    });
  }

  static networkError(cause: unknown): ApiError {
    return new ApiError({
      message: "サーバーへ接続できませんでした。ネットワーク状態を確認してください。",
      status: null,
      detail: null,
      cause,
    });
  }

  static fromHttpStatus(status: number, detail: string | null): ApiError {
    return new ApiError({
      message: resolveUserMessage(status, detail),
      status,
      detail,
    });
  }
}

function resolveUserMessage(status: number, detail: string | null): string {
  switch (status) {
    case 400:
      return detail ?? "入力またはCSVファイルが不正です。";
    case 404:
      return detail ?? "対象のCSVまたは実ファイルが見つかりません。";
    case 409:
      return detail ?? "同一内容のレポートがすでに登録されています。";
    case 422:
      return detail ?? "入力内容を確認してください。";
    case 500:
      return detail ?? "ファイルまたはデータベースの保存に失敗しました。";
    case 502:
      return detail ?? "AIレポートの生成に失敗しました。時間をおいて再試行してください。";
    default:
      return detail ?? `サーバーでエラーが発生しました。(HTTP ${status})`;
  }
}

/** FastAPIの{"detail": string | 配列(Pydantic 422)}形式を安全に解析する。 */
export function parseErrorDetail(body: unknown): string | null {
  if (body === null || typeof body !== "object") {
    return null;
  }

  const detail = (body as { detail?: unknown }).detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (item !== null && typeof item === "object" && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }

        return null;
      })
      .filter((message): message is string => message !== null);

    return messages.length > 0 ? messages.join(" / ") : null;
  }

  return null;
}
