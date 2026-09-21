import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ReportListItem } from "@/features/reports/components/ReportListItem";
import type { Report } from "@/features/reports/types/report";

const report: Report = {
  id: "report-001",
  uploadedFileId: "file-001",
  date: "2026-09-18",
  period: "09:00-10:00",
  file: "measurement.csv",
  status: "注意",
  anomalyCount: "2件",
  equipmentId: "MOTOR-002",
  createdBy: "開発担当者",
};

function renderItem(item: Report = report, onSelect = vi.fn()) {
  render(
    <table>
      <tbody>
        <ReportListItem report={item} onSelect={onSelect} />
      </tbody>
    </table>,
  );
  return onSelect;
}

describe("ReportListItem", () => {
  it("shows report information", () => {
    renderItem();

    expect(screen.getByText("2026-09-18")).toBeVisible();
    expect(screen.getByText("09:00-10:00")).toBeVisible();
    expect(screen.getByText("MOTOR-002")).toBeVisible();
    expect(screen.getByText("measurement.csv")).toBeVisible();
    expect(screen.getByText("注意")).toBeVisible();
    expect(screen.getByText("2件")).toBeVisible();
    expect(screen.getByText("開発担当者")).toBeVisible();
  });

  it("shows fallback values when equipment and creator are missing", () => {
    renderItem({ ...report, equipmentId: undefined, createdBy: undefined });

    expect(screen.getByText("MOTOR-001")).toBeVisible();
    expect(screen.getByText("開発ユーザー")).toBeVisible();
  });

  it.each(["異常", "注意", "正常"] as const)(
    "renders the %s status",
    (status) => {
      renderItem({ ...report, status });
      expect(screen.getByText(status)).toBeVisible();
    },
  );

  it("calls onSelect with the report when the action button is clicked", async () => {
    const user = userEvent.setup();
    const onSelect = renderItem();

    await user.click(
      screen.getByRole("button", { name: "2026-09-18の操作" }),
    );

    expect(onSelect).toHaveBeenCalledOnce();
    expect(onSelect).toHaveBeenCalledWith(report);
  });
});
