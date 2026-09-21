import { beforeEach, describe, expect, it, vi } from "vitest";

import type { RagChatRequest, RagChatResponse } from "@/features/chat/types/chat";
import { ApiError } from "@/lib/errors/api-error";

const { apiRequestMock } = vi.hoisted(() => ({
  apiRequestMock: vi.fn(),
}));

vi.mock("@/lib/api/client", () => ({
  apiRequest: apiRequestMock,
}));

import { sendRagChat } from "@/features/chat/api/chat";

const request: RagChatRequest = {
  query: "MOTOR-001の振動状態を教えてください。",
  limit: 5,
  equipment_id: "MOTOR-001",
  measurement_date_from: "2026-09-01",
  measurement_date_to: "2026-09-18",
  chunk_types: ["summary", "analysis"],
};

const response: RagChatResponse = {
  query: request.query,
  answer: "注意が必要な振動が確認されています。",
  source_count: 1,
  sources: [
    {
      report_chunk_id: "chunk-001",
      report_id: "report-001",
      chunk_type: "analysis",
      equipment_id: "MOTOR-001",
      measurement_date: "2026-09-18",
      similarity: 0.91,
    },
  ],
};

describe("sendRagChat", () => {
  beforeEach(() => {
    apiRequestMock.mockReset();
  });

  it("posts the complete chat request and returns the response", async () => {
    apiRequestMock.mockResolvedValue(response);

    await expect(sendRagChat(request)).resolves.toEqual(response);

    expect(apiRequestMock).toHaveBeenCalledOnce();
    expect(apiRequestMock).toHaveBeenCalledWith("/api/v1/chat", {
      method: "POST",
      json: request,
      signal: undefined,
    });
  });

  it("posts a request containing only the required query", async () => {
    const minimalRequest: RagChatRequest = {
      query: "最新の状態を教えてください。",
    };
    apiRequestMock.mockResolvedValue({
      query: minimalRequest.query,
      answer: "該当する情報があります。",
      source_count: 0,
      sources: [],
    } satisfies RagChatResponse);

    await sendRagChat(minimalRequest);

    expect(apiRequestMock).toHaveBeenCalledWith("/api/v1/chat", {
      method: "POST",
      json: minimalRequest,
      signal: undefined,
    });
  });

  it("passes an AbortSignal to apiRequest", async () => {
    const controller = new AbortController();
    apiRequestMock.mockResolvedValue(response);

    await sendRagChat(request, controller.signal);

    expect(apiRequestMock).toHaveBeenCalledWith("/api/v1/chat", {
      method: "POST",
      json: request,
      signal: controller.signal,
    });
  });

  it("passes the original request object without normalizing values", async () => {
    const unnormalizedRequest: RagChatRequest = {
      query: "  状態を教えてください。  ",
      equipment_id: null,
      measurement_date_from: null,
      measurement_date_to: null,
      chunk_types: [],
    };
    apiRequestMock.mockResolvedValue(response);

    await sendRagChat(unnormalizedRequest);

    expect(apiRequestMock).toHaveBeenCalledWith("/api/v1/chat", {
      method: "POST",
      json: unnormalizedRequest,
      signal: undefined,
    });
  });

  it("propagates an API request error", async () => {
    const error = ApiError.fromHttpStatus(
      502,
      "AI回答の生成に失敗しました。",
    );
    apiRequestMock.mockRejectedValue(error);

    await expect(sendRagChat(request)).rejects.toBe(error);
    expect(apiRequestMock).toHaveBeenCalledOnce();
  });
});
