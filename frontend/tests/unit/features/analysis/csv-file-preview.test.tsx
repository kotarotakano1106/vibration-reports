import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CsvFilePreview } from "@/features/analysis/components/CsvFilePreview";

function createFile(name: string, size: number): File {
  return new File([new Uint8Array(size)], name, { type: "text/csv" });
}

describe("CsvFilePreview", () => {
  it("shows the selected CSV filename", () => {
    render(<CsvFilePreview file={createFile("measurement.csv", 1024)} />);

    expect(screen.getByText("measurement.csv")).toBeVisible();
  });

  it.each([
    [1, "1 KB"],
    [1024, "1 KB"],
    [1025, "2 KB"],
    [2048, "2 KB"],
  ])("rounds a %i-byte file size up to %s", (size, expected) => {
    render(<CsvFilePreview file={createFile("measurement.csv", size)} />);

    expect(screen.getByText(expected)).toBeVisible();
  });

  it("shows zero kilobytes for an empty file", () => {
    render(<CsvFilePreview file={createFile("empty.csv", 0)} />);

    expect(screen.getByText("empty.csv")).toBeVisible();
    expect(screen.getByText("0 KB")).toBeVisible();
  });
});
