import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ChatInput } from "@/features/chat/components/ChatInput";

describe("ChatInput", () => {
  it("starts with an empty input and disabled submit button", () => {
    render(<ChatInput onSend={vi.fn()} />);

    expect(screen.getByRole("textbox", { name: "AIへの質問" })).toHaveValue("");
    expect(screen.getByRole("button", { name: "質問を送信" })).toBeDisabled();
  });

  it("enables submit after the user enters a message", async () => {
    const user = userEvent.setup();
    render(<ChatInput onSend={vi.fn()} />);

    await user.type(
      screen.getByRole("textbox", { name: "AIへの質問" }),
      "振動状態を教えてください。",
    );

    expect(screen.getByRole("button", { name: "質問を送信" })).toBeEnabled();
  });

  it("trims and sends a message, then clears the input", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);
    const input = screen.getByRole("textbox", { name: "AIへの質問" });

    await user.type(input, "  異常の有無を教えてください。  ");
    await user.click(screen.getByRole("button", { name: "質問を送信" }));

    expect(onSend).toHaveBeenCalledOnce();
    expect(onSend).toHaveBeenCalledWith("異常の有無を教えてください。");
    expect(input).toHaveValue("");
  });

  it("submits the message by pressing Enter", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    await user.type(
      screen.getByRole("textbox", { name: "AIへの質問" }),
      "最新状態を確認{Enter}",
    );

    expect(onSend).toHaveBeenCalledWith("最新状態を確認");
  });

  it("does not submit a whitespace-only message", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);
    const input = screen.getByRole("textbox", { name: "AIへの質問" });

    fireEvent.change(input, { target: { value: "   " } });
    fireEvent.submit(input.closest("form")!);

    expect(onSend).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "質問を送信" })).toBeDisabled();
  });

  it("disables input and shows progress while disabled", () => {
    render(<ChatInput onSend={vi.fn()} disabled />);

    expect(screen.getByRole("textbox", { name: "AIへの質問" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "質問を送信" })).toBeDisabled();
    expect(screen.getByRole("progressbar")).toBeVisible();
  });
});
