import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ReportList } from "@/features/reports/components/ReportList";
import type { Report } from "@/features/reports/types/report";

const reports: Report[] = [
  { id: "1", uploadedFileId: "f1", date: "2026-09-18", period: "09:00", file: "a.csv", status: "正常", anomalyCount: "0", equipmentId: "MOTOR-001", createdBy: "user-a" },
  { id: "2", uploadedFileId: "f2", date: "2026-09-17", period: "10:00", file: "b.csv", status: "注意", anomalyCount: "2", equipmentId: "MOTOR-002", createdBy: "user-b" },
];

describe("ReportList", () => {
  it("renders the title, controls, headers, and report rows", () => {
    render(<ReportList reports={reports} onSelect={vi.fn()} />);
    expect(screen.getByRole("heading", { name: "レポート一覧" })).toBeVisible();
    expect(screen.getByPlaceholderText("レポート名、設備IDで検索")).toBeVisible();
    expect(screen.getByText("2026-09-18")).toBeVisible();
    expect(screen.getByText("MOTOR-002")).toBeVisible();
    expect(screen.getByText("2件中 1-2件")).toBeVisible();
  });

  it("renders zero rows for an empty list", () => {
    render(<ReportList reports={[]} onSelect={vi.fn()} />);
    expect(screen.getByText("0件中 0-0件")).toBeVisible();
    expect(screen.queryByRole("button", { name: /の操作$/ })).not.toBeInTheDocument();
  });

  it("passes selection from a row to onSelect", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(<ReportList reports={reports} onSelect={onSelect} />);
    await user.click(screen.getByRole("button", { name: "2026-09-18の操作" }));
    expect(onSelect).toHaveBeenCalledWith(reports[0]);
  });
});
