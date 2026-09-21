import { describe, expect, it } from "vitest";

describe("Frontend test environment", () => {
  it("runs with jsdom", () => {
    const element = document.createElement("div");
    element.textContent = "ready";

    expect(element).toHaveTextContent("ready");
  });
});
