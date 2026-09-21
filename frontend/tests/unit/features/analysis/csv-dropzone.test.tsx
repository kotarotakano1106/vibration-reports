import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CsvDropzone } from "@/features/analysis/components/CsvDropzone";

describe("CsvDropzone", () => {
  it("shows file-selection guidance and button", () => {
    render(<CsvDropzone onSelect={vi.fn()} />);
    expect(screen.getByText("CSVファイルを選択してください")).toBeVisible();
    expect(screen.getByText("ファイルを選択")).toBeVisible();
  });

  it("accepts CSV files", () => {
    const { container } = render(<CsvDropzone onSelect={vi.fn()} />);
    const input = container.querySelector('input[type="file"]');
    expect(input).toHaveAttribute("accept", ".csv,text/csv");
  });

  it("calls onSelect with the selected file", () => {
    const onSelect = vi.fn();
    const { container } = render(<CsvDropzone onSelect={onSelect} />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["a,b"], "measurement.csv", { type: "text/csv" });
    fireEvent.change(input, { target: { files: [file] } });
    expect(onSelect).toHaveBeenCalledWith(file);
  });

  it("does not call onSelect when no file is selected", () => {
    const onSelect = vi.fn();
    const { container } = render(<CsvDropzone onSelect={onSelect} />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [] } });
    expect(onSelect).not.toHaveBeenCalled();
  });
});
