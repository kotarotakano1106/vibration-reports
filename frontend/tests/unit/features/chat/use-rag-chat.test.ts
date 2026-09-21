import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { RagChatResponse } from "@/features/chat/types/chat";

const { sendRagChatMock } = vi.hoisted(() => ({
  sendRagChatMock: vi.fn(),
}));

vi.mock("@/features/chat/api/chat", () => ({
  sendRagChat: sendRagChatMock,
}));

import { useRagChat } from "@/features/chat/hooks/useRagChat";

const response: RagChatResponse = {
  query: "MOTOR-001の状態を教えてください。",
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

function createDeferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });

  return { promise, resolve, reject };
}

describe("useRagChat", () => {
  beforeEach(() => {
    sendRagChatMock.mockReset();
  });

  it("starts with the idle state", () => {
    const { result } = renderHook(() => useRagChat());

    expect(result.current.isPending).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("sets the pending state and returns a successful response", async () => {
    const deferred = createDeferred<RagChatResponse>();
    sendRagChatMock.mockReturnValue(deferred.promise);
    const { result } = renderHook(() => useRagChat());

    let requestPromise!: Promise<RagChatResponse | null>;
    act(() => {
      requestPromise = result.current.send({ query: response.query });
    });

    expect(result.current.isPending).toBe(true);
    expect(result.current.error).toBeNull();
    expect(sendRagChatMock).toHaveBeenCalledWith(
      { query: response.query },
      expect.any(AbortSignal),
    );

    await act(async () => {
      deferred.resolve(response);
      await expect(requestPromise).resolves.toEqual(response);
    });

    expect(result.current.isPending).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("stores an Error returned by the API", async () => {
    const error = new Error("AI回答を取得できませんでした。");
    sendRagChatMock.mockRejectedValue(error);
    const { result } = renderHook(() => useRagChat());

    await act(async () => {
      await expect(
        result.current.send({ query: "状態を確認" }),
      ).resolves.toBeNull();
    });

    expect(result.current.isPending).toBe(false);
    expect(result.current.error).toBe(error);
  });

  it("converts a non-Error rejection to the fallback Error", async () => {
    sendRagChatMock.mockRejectedValue("unexpected failure");
    const { result } = renderHook(() => useRagChat());

    await act(async () => {
      await result.current.send({ query: "状態を確認" });
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe(
      "AI回答の取得に失敗しました。",
    );
  });

  it("aborts the previous request when a new request starts", async () => {
    const first = createDeferred<RagChatResponse>();
    const second = createDeferred<RagChatResponse>();
    sendRagChatMock
      .mockReturnValueOnce(first.promise)
      .mockReturnValueOnce(second.promise);
    const { result } = renderHook(() => useRagChat());

    let firstPromise!: Promise<RagChatResponse | null>;
    let secondPromise!: Promise<RagChatResponse | null>;

    act(() => {
      firstPromise = result.current.send({ query: "最初の質問" });
    });
    const firstSignal = sendRagChatMock.mock.calls[0][1] as AbortSignal;

    act(() => {
      secondPromise = result.current.send({ query: "次の質問" });
    });
    const secondSignal = sendRagChatMock.mock.calls[1][1] as AbortSignal;

    expect(firstSignal.aborted).toBe(true);
    expect(secondSignal.aborted).toBe(false);
    expect(result.current.isPending).toBe(true);

    await act(async () => {
      first.reject(new DOMException("Aborted", "AbortError"));
      await expect(firstPromise).resolves.toBeNull();
    });

    expect(result.current.error).toBeNull();
    expect(result.current.isPending).toBe(true);

    await act(async () => {
      second.resolve(response);
      await expect(secondPromise).resolves.toEqual(response);
    });

    expect(result.current.isPending).toBe(false);
  });

  it("reset aborts the active request and restores the initial state", async () => {
    const deferred = createDeferred<RagChatResponse>();
    sendRagChatMock.mockReturnValue(deferred.promise);
    const { result } = renderHook(() => useRagChat());

    let requestPromise!: Promise<RagChatResponse | null>;
    act(() => {
      requestPromise = result.current.send({ query: "状態を確認" });
    });
    const signal = sendRagChatMock.mock.calls[0][1] as AbortSignal;

    act(() => {
      result.current.reset();
    });

    expect(signal.aborted).toBe(true);
    expect(result.current.isPending).toBe(false);
    expect(result.current.error).toBeNull();

    await act(async () => {
      deferred.reject(new DOMException("Aborted", "AbortError"));
      await expect(requestPromise).resolves.toBeNull();
    });

    await waitFor(() => {
      expect(result.current.isPending).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });
});
