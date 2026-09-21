import { apiRequest } from "@/lib/api/client";
import { apiPaths } from "@/lib/api/paths";

import type {
  RagChatRequest,
  RagChatResponse,
} from "../types/chat";

export function sendRagChat(
  input: RagChatRequest,
  signal?: AbortSignal,
): Promise<RagChatResponse> {
  return apiRequest<RagChatResponse>(apiPaths.chat, {
    method: "POST",
    json: input,
    signal,
  });
}
