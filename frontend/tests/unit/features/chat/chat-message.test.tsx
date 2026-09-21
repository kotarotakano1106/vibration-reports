import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ChatMessage } from "@/features/chat/components/ChatMessage";
import type { ChatMessage as ChatMessageType } from "@/features/chat/types/chat";

const assistantMessage: ChatMessageType = {
  id: "assistant-001",
  role: "assistant",
  content: "振動状態を確認しました。",
  sources: [
    {
      report_chunk_id: "chunk-001",
      report_id: "report-001",
      chunk_type: "analysis_summary",
      equipment_id: "MOTOR-001",
      measurement_date: "2026-09-18",
      similarity: 0.91234,
    },
  ],
};

describe("ChatMessage", () => {
  it("shows a user message without sources", () => {
    render(
      <ChatMessage
        message={{ id: "user-001", role: "user", content: "状態を確認" }}
      />,
    );

    expect(screen.getByText("状態を確認")).toBeVisible();
    expect(screen.queryByText("参照元")).not.toBeInTheDocument();
  });

  it("shows assistant source information with a known chunk label", () => {
    render(<ChatMessage message={assistantMessage} />);

    expect(screen.getByText("振動状態を確認しました。")).toBeVisible();
    expect(screen.getByText("参照元")).toBeVisible();
    expect(
      screen.getByText("分析概要 / MOTOR-001 / 2026-09-18"),
    ).toBeVisible();
    expect(
      screen.getByTitle("類似度: 0.912"),
    ).toBeInTheDocument();
  });

  it("uses the raw chunk type and fallback date when no label or date exists", () => {
    render(
      <ChatMessage
        message={{
          ...assistantMessage,
          sources: [
            {
              ...assistantMessage.sources![0],
              report_chunk_id: "chunk-002",
              chunk_type: "custom_chunk",
              measurement_date: null,
              similarity: 0.5,
            },
          ],
        }}
      />,
    );

    expect(
      screen.getByText("custom_chunk / MOTOR-001 / 日付未設定"),
    ).toBeVisible();
    expect(screen.getByTitle("類似度: 0.500")).toBeInTheDocument();
  });

  it("does not show the source section for an assistant message with no sources", () => {
    render(
      <ChatMessage
        message={{
          id: "assistant-002",
          role: "assistant",
          content: "参照情報はありません。",
          sources: [],
        }}
      />,
    );

    expect(screen.getByText("参照情報はありません。")).toBeVisible();
    expect(screen.queryByText("参照元")).not.toBeInTheDocument();
  });
});
