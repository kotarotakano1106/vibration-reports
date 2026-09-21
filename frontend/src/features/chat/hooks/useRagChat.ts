"use client";

import { useCallback, useRef, useState } from "react";

import { sendRagChat } from "../api/chat";
import type {
  RagChatRequest,
  RagChatResponse,
} from "../types/chat";

function toError(value: unknown): Error {
  if (value instanceof Error) {
    return value;
  }

  return new Error("AI回答の取得に失敗しました。");
}

export function useRagChat() {
  const [isPending, setIsPending] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const send = useCallback(
    async (
      input: RagChatRequest,
    ): Promise<RagChatResponse | null> => {
      abortControllerRef.current?.abort();
      const controller = new AbortController();
      abortControllerRef.current = controller;

      setIsPending(true);
      setError(null);

      try {
        return await sendRagChat(input, controller.signal);
      } catch (cause) {
        if (controller.signal.aborted) {
          return null;
        }

        setError(toError(cause));
        return null;
      } finally {
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
          setIsPending(false);
        }
      }
    },
    [],
  );

  const reset = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setIsPending(false);
    setError(null);
  }, []);

  return {
    error,
    isPending,
    send,
    reset,
  };
}
