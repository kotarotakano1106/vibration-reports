import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ChatMessageList } from "@/features/chat/components/ChatMessageList";
import type { ChatMessage } from "@/features/chat/types/chat";

const messages: ChatMessage[] = [
  { id: "user-001", role: "user", content: "状態を確認" },
  { id: "assistant-001", role: "assistant", content: "正常です。" },
];

describe("ChatMessageList", () => {
  it("shows guidance when there are no messages and no request is pending", () => {
    render(<ChatMessageList messages={[]} />);

    expect(
      screen.getByText("過去レポートについて質問してください。"),
    ).toBeVisible();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });

  it("renders all messages", () => {
    render(<ChatMessageList messages={messages} />);

    expect(screen.getByText("状態を確認")).toBeVisible();
    expect(screen.getByText("正常です。")).toBeVisible();
    expect(
      screen.queryByText("過去レポートについて質問してください。"),
    ).not.toBeInTheDocument();
  });

  it("shows progress while an answer is pending", () => {
    render(<ChatMessageList messages={messages} isPending />);

    expect(screen.getByRole("progressbar")).toBeVisible();
    expect(
      screen.getByText("過去レポートを検索し、回答を作成しています..."),
    ).toBeVisible();
  });

  it("hides empty guidance when pending with no messages", () => {
    render(<ChatMessageList messages={[]} isPending />);

    expect(
      screen.queryByText("過去レポートについて質問してください。"),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toBeVisible();
  });
});
