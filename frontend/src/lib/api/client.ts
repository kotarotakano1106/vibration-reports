import { ApiError, parseErrorDetail } from "@/lib/errors/api-error";

type ApiRequestMethod = "GET" | "POST";

type ApiRequestOptions = {
  method?: ApiRequestMethod;
  json?: unknown;
  formData?: FormData;
  signal?: AbortSignal;
};

export function buildApiUrl(path: string): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  if (!baseUrl) {
    throw ApiError.missingBaseUrl();
  }

  const normalizedBase = baseUrl.replace(/\/+$/, "");
  const normalizedPath = path.replace(/^\/+/, "");

  return `${normalizedBase}/${normalizedPath}`;
}

async function readErrorDetail(response: Response): Promise<string | null> {
  const text = await response.text();

  if (!text) {
    return null;
  }

  try {
    return parseErrorDetail(JSON.parse(text));
  } catch {
    return text;
  }
}

async function readJsonBody<TResponse>(response: Response): Promise<TResponse> {
  const text = await response.text();

  if (!text) {
    return undefined as TResponse;
  }

  return JSON.parse(text) as TResponse;
}

export async function apiRequest<TResponse>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<TResponse> {
  const url = buildApiUrl(path);
  const method = options.method ?? "GET";
  const headers: Record<string, string> = { Accept: "application/json" };

  let body: BodyInit | undefined;

  if (options.formData) {
    // FormData利用時はブラウザがboundary付きContent-Typeを自動設定するため手動指定しない
    body = options.formData;
  } else if (options.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(options.json);
  }

  let response: Response;

  try {
    response = await fetch(url, {
      method,
      headers,
      body,
      cache: "no-store",
      signal: options.signal,
    });
  } catch (cause) {
    throw ApiError.networkError(cause);
  }

  if (!response.ok) {
    const detail = await readErrorDetail(response);

    throw ApiError.fromHttpStatus(response.status, detail);
  }

  return readJsonBody<TResponse>(response);
}
