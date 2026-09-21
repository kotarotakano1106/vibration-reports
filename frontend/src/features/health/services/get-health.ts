import type { HealthResponse } from "../types/health";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

export async function getHealth(): Promise<HealthResponse> {
  if (!apiBaseUrl) {
    throw new Error(
      "NEXT_PUBLIC_API_BASE_URLが設定されていません。",
    );
  }

  const response = await fetch(`${apiBaseUrl}/health`, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(
      `FastAPIとの通信に失敗しました。HTTP ${response.status}`,
    );
  }

  return (await response.json()) as HealthResponse;
}